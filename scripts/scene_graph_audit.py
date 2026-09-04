#!/usr/bin/env python3
"""Static structural audit for Godot 4 text scenes."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any, Iterable


IGNORED_DIRECTORIES = {".git", ".godot", ".import", ".mono", "bin", "obj"}
SECTION_PATTERN = re.compile(r"^\[(?P<kind>[A-Za-z_]+)(?P<body>.*)\]$")
ATTRIBUTE_PATTERN = re.compile(r'(?P<key>[A-Za-z_][\w/]*)=(?P<value>"(?:\\.|[^"\\])*"|[^\s]+)')
RESOURCE_PATTERN = re.compile(r'(?P<kind>ExtResource|SubResource)\("(?P<id>[^"]+)"\)')
NODE_PATH_PATTERN = re.compile(r'NodePath\("(?P<path>[^"]*)"\)')
FUNCTION_PATTERN = re.compile(r"^\s*func\s+(?P<name>[A-Za-z_]\w*)\s*\(", re.MULTILINE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Godot .tscn hierarchy, resource references, connections, and common scene omissions."
    )
    parser.add_argument("--project", default=".", help="Project directory or project.godot path.")
    parser.add_argument(
        "--scene",
        action="append",
        help="Scene to audit (repeatable, res:// or project-relative). Defaults to all .tscn files.",
    )
    parser.add_argument("--json-output", help="Write the full machine-readable report to this path.")
    parser.add_argument("--summary", action="store_true", help="Print only totals and bounded details.")
    parser.add_argument("--max-details", type=int, default=60, help="Maximum console diagnostics.")
    parser.add_argument("--fail-on-warnings", action="store_true")
    args = parser.parse_args()
    if args.max_details < 0:
        parser.error("--max-details must be non-negative")
    return args


def find_root(value: str) -> Path:
    candidate = Path(value).expanduser().resolve()
    if candidate.is_file():
        if candidate.name != "project.godot":
            raise ValueError(f"Expected project.godot, got: {candidate}")
        candidate = candidate.parent
    if not candidate.is_dir() or not (candidate / "project.godot").is_file():
        raise ValueError(f"Godot project not found: {candidate}")
    return candidate


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def project_path(root: Path, value: str) -> Path:
    relative = value.removeprefix("res://").replace("/", os.sep)
    result = (root / relative).resolve()
    if not is_within(result, root):
        raise ValueError(f"Path escapes project: {value}")
    return result


def iter_scenes(root: Path) -> Iterable[Path]:
    for current, directories, files in os.walk(root):
        directories[:] = [name for name in directories if name not in IGNORED_DIRECTORIES]
        for name in files:
            if name.lower().endswith(".tscn"):
                yield Path(current) / name


def decode_value(value: str) -> str:
    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value[1:-1]
    return value


def attributes(body: str) -> dict[str, str]:
    return {match.group("key"): decode_value(match.group("value")) for match in ATTRIBUTE_PATTERN.finditer(body)}


def normalized_node_path(value: str) -> str:
    if value in ("", "."):
        return "."
    parts: list[str] = []
    for part in PurePosixPath(value).parts:
        if part in ("", ".", "/"):
            continue
        if part == "..":
            if parts:
                parts.pop()
            else:
                return "<outside>"
        else:
            parts.append(part)
    return "/".join(parts) if parts else "."


def resolve_from_node(node_path: str, reference: str) -> str:
    if reference.startswith("/"):
        # Absolute NodePaths depend on the runtime scene-tree name and cannot be proven statically.
        return "<absolute>"
    base = [] if node_path == "." else node_path.split("/")
    return normalized_node_path("/".join(base + reference.split("/")))


def diagnostic(level: str, scene: str, line: int, message: str) -> dict[str, Any]:
    return {"level": level, "scene": scene, "line": line, "message": message}


def serialized_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def serialized_value_is_nonempty(value: str) -> bool:
    return value.strip() not in {"", '""', '&""', "null", "Null"}


def packed_scene_instance_resource_id(
    node: dict[str, Any], ext_resources: dict[str, dict[str, str]]
) -> str | None:
    instance = node.get("instance")
    if not instance:
        return None
    match = re.fullmatch(r'ExtResource\("([^"]+)"\)', instance)
    if not match:
        return None
    resource_id = match.group(1)
    resource = ext_resources.get(resource_id)
    if resource is None or resource.get("type") != "PackedScene":
        return None
    return resource_id


def packed_scene_anchor(
    candidate_path: str,
    paths: dict[str, dict[str, Any]],
    ext_resources: dict[str, dict[str, str]],
) -> str | None:
    candidates: list[str] = []
    for path, node in paths.items():
        if packed_scene_instance_resource_id(node, ext_resources) is None:
            continue
        if path == "." and candidate_path != ".":
            candidates.append(path)
        elif candidate_path == path or candidate_path.startswith(path + "/"):
            candidates.append(path)
    if candidates:
        return max(candidates, key=lambda value: -1 if value == "." else len(value))
    return None


def editable_packed_scene_anchor(
    candidate_path: str,
    paths: dict[str, dict[str, Any]],
    editable_paths: set[str],
    ext_resources: dict[str, dict[str, str]],
) -> str | None:
    covered = any(
        candidate_path == editable_path or candidate_path.startswith(editable_path + "/")
        for editable_path in editable_paths
    )
    if covered:
        return packed_scene_anchor(candidate_path, paths, ext_resources)
    return None


def audit_scene(root: Path, path: Path) -> dict[str, Any]:
    scene_name = path.relative_to(root).as_posix()
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    lines = text.splitlines()
    diagnostics: list[dict[str, Any]] = []
    ext_resources: dict[str, dict[str, str]] = {}
    sub_resources: dict[str, dict[str, Any]] = {}
    nodes: list[dict[str, Any]] = []
    connections: list[dict[str, Any]] = []
    editable_declarations: list[dict[str, Any]] = []
    imported_internal_references: list[dict[str, Any]] = []
    current_node: dict[str, Any] | None = None
    current_sub_resource: dict[str, Any] | None = None

    for line_number, raw in enumerate(lines, 1):
        stripped = raw.strip()
        section = SECTION_PATTERN.match(stripped)
        if section:
            current_node = None
            current_sub_resource = None
            kind = section.group("kind")
            attrs = attributes(section.group("body"))
            if kind == "ext_resource":
                resource_id = attrs.get("id")
                if resource_id:
                    attrs["_line"] = str(line_number)
                    ext_resources[resource_id] = attrs
            elif kind == "sub_resource":
                resource_id = attrs.get("id")
                if resource_id:
                    current_sub_resource = {
                        "type": attrs.get("type"),
                        "line": line_number,
                        "properties": {},
                    }
                    sub_resources[resource_id] = current_sub_resource
            elif kind == "node":
                current_node = {
                    "name": attrs.get("name", "<unnamed>"),
                    "type": attrs.get("type"),
                    "parent": attrs.get("parent"),
                    "instance": attrs.get("instance"),
                    "line": line_number,
                    "properties": {},
                }
                nodes.append(current_node)
            elif kind == "connection":
                attrs["line"] = line_number
                connections.append(attrs)
            elif kind == "editable":
                editable_declarations.append(
                    {"path": attrs.get("path"), "line": line_number}
                )
            continue
        if "=" in stripped and not stripped.startswith(";"):
            key, value = stripped.split("=", 1)
            property_data = {"value": value.strip(), "line": line_number}
            if current_node is not None:
                current_node["properties"][key.strip()] = property_data
            elif current_sub_resource is not None:
                current_sub_resource["properties"][key.strip()] = property_data

    if not nodes:
        diagnostics.append(diagnostic("error", scene_name, 1, "Scene contains no [node] sections"))
        return {
            "scene": scene_name,
            "nodes": 0,
            "resources": len(ext_resources) + len(sub_resources),
            "connections": len(connections),
            "editable_packed_scene_internal_reference_count": 0,
            "editable_packed_scene_internal_references": [],
            "diagnostics": diagnostics,
        }

    editable_paths = {
        normalized_node_path(str(item["path"]))
        for item in editable_declarations
        if item.get("path") is not None
    }
    paths: dict[str, dict[str, Any]] = {}
    for index, node in enumerate(nodes):
        parent = node["parent"]
        if index == 0:
            if parent is not None:
                diagnostics.append(diagnostic("error", scene_name, node["line"], "Root node must not declare parent"))
            node_path = "."
        else:
            if parent is None:
                diagnostics.append(diagnostic("error", scene_name, node["line"], "Non-root node has no parent"))
                node_path = f"<orphan:{index}>"
            else:
                parent_path = normalized_node_path(parent)
                node_path = node["name"] if parent_path == "." else f"{parent_path}/{node['name']}"
                node_path = normalized_node_path(node_path)
                if parent_path not in paths:
                    editable_anchor = editable_packed_scene_anchor(
                        node_path, paths, editable_paths, ext_resources
                    )
                    if editable_anchor is None:
                        diagnostics.append(
                            diagnostic("error", scene_name, node["line"], f"Parent node does not exist before child: {parent}")
                        )
                    else:
                        imported_internal_references.append(
                            {
                                "kind": "override_parent",
                                "path": parent_path,
                                "editable_instance": editable_anchor,
                                "line": node["line"],
                            }
                        )
        node["path"] = node_path
        if node_path in paths:
            diagnostics.append(diagnostic("error", scene_name, node["line"], f"Duplicate node path: {node_path}"))
        else:
            paths[node_path] = node

    for item in editable_declarations:
        raw_path = item.get("path")
        line_number = int(item["line"])
        if raw_path is None:
            diagnostics.append(
                diagnostic("error", scene_name, line_number, "[editable] section has no path")
            )
            continue
        editable_path = normalized_node_path(str(raw_path))
        if editable_path in {".", "<outside>"}:
            diagnostics.append(
                diagnostic("error", scene_name, line_number, f"Invalid editable instance path: {raw_path}")
            )
            continue
        if editable_path in paths:
            continue
        editable_anchor = packed_scene_anchor(editable_path, paths, ext_resources)
        if editable_anchor is None:
            diagnostics.append(
                diagnostic(
                    "error",
                    scene_name,
                    line_number,
                    f"Editable path is neither a local node nor internal to an ExtResource PackedScene instance: {raw_path}",
                )
            )
        else:
            imported_internal_references.append(
                {
                    "kind": "editable_declaration",
                    "path": editable_path,
                    "editable_instance": editable_anchor,
                    "line": line_number,
                }
            )

    for resource_id, resource in ext_resources.items():
        resource_path = resource.get("path", "")
        if resource_path.startswith("res://"):
            try:
                target = project_path(root, resource_path)
            except ValueError as exc:
                    diagnostics.append(diagnostic("error", scene_name, int(resource.get("_line", "1")), str(exc)))
            else:
                if not target.exists():
                    diagnostics.append(
                        diagnostic(
                            "error",
                            scene_name,
                            int(resource.get("_line", "1")),
                            f"ExtResource {resource_id} is missing: {resource_path}",
                        )
                    )

    # Scan every serialized expression, including subresources and animation data,
    # rather than only node properties.
    for match in RESOURCE_PATTERN.finditer(text):
        resource_id = match.group("id")
        exists = resource_id in (ext_resources if match.group("kind") == "ExtResource" else sub_resources)
        if not exists:
            line_number = text.count("\n", 0, match.start()) + 1
            diagnostics.append(
                diagnostic("error", scene_name, line_number, f"Undefined {match.group('kind')} id: {resource_id}")
            )

    for node in nodes:
        node_type = node.get("type")
        properties = node["properties"]
        if node_type in {"CollisionShape2D", "CollisionShape3D"} and "shape" not in properties:
            diagnostics.append(diagnostic("warning", scene_name, node["line"], f"{node_type} has no serialized shape"))
        required_visual = {"Sprite2D": "texture", "TextureRect": "texture", "MeshInstance3D": "mesh"}
        required = required_visual.get(node_type)
        if required and required not in properties:
            diagnostics.append(
                diagnostic("warning", scene_name, node["line"], f"{node_type} has no serialized {required}; verify runtime assignment")
            )
        if node_type == "TextureRect" and "expand_mode" in properties:
            stretch = properties.get("stretch_mode")
            if stretch is None or stretch["value"] in {"0", "0.0"}:
                diagnostics.append(
                    diagnostic(
                        "warning",
                        scene_name,
                        properties["expand_mode"]["line"],
                        "TextureRect serializes expand_mode while stretch_mode is default SCALE; "
                        "non-cover UI art may distort inside Containers. Use an intentional "
                        "KEEP/KEEP_ASPECT mode or document deliberate stretching.",
                    )
                )
        if node_type == "Button":
            icon = properties.get("icon")
            text_property = properties.get("text")
            text_alignment = properties.get("alignment")
            icon_alignment = properties.get("icon_alignment")
            text_is_centered = text_alignment is None or text_alignment["value"] in {"1", "1.0"}
            icon_is_left = icon_alignment is None or icon_alignment["value"] in {"0", "0.0"}
            if (
                icon
                and serialized_value_is_nonempty(icon["value"])
                and text_property
                and serialized_value_is_nonempty(text_property["value"])
                and text_is_centered
                and icon_is_left
            ):
                diagnostics.append(
                    diagnostic(
                        "warning",
                        scene_name,
                        icon["line"],
                        f"Button {node['path']} combines a left-aligned built-in icon with centered text; "
                        "the localized icon-plus-label group may not be visually centered. Assert the "
                        "compound group center across representative locales/viewports or use a "
                        "scene-authored centered inner container.",
                    )
                )

        for property_name, property_data in properties.items():
            if not (property_name.endswith("_path") or property_name.endswith("node_path") or property_name == "target"):
                continue
            for match in NODE_PATH_PATTERN.finditer(property_data["value"]):
                target = resolve_from_node(node["path"], match.group("path"))
                if target not in paths and target not in {"<absolute>", "<outside>"}:
                    editable_anchor = editable_packed_scene_anchor(
                        target, paths, editable_paths, ext_resources
                    )
                    if editable_anchor is None:
                        diagnostics.append(
                            diagnostic(
                                "warning",
                                scene_name,
                                property_data["line"],
                                f"NodePath in {node['path']}:{property_name} does not resolve: {match.group('path')}",
                            )
                        )
                    else:
                        imported_internal_references.append(
                            {
                                "kind": "node_path",
                                "path": target,
                                "editable_instance": editable_anchor,
                                "line": property_data["line"],
                            }
                        )

    expanding_styleboxes: dict[str, list[str]] = {}
    expand_properties = {
        "expand_margin_left",
        "expand_margin_top",
        "expand_margin_right",
        "expand_margin_bottom",
    }
    for resource_id, resource in sub_resources.items():
        if not str(resource.get("type", "")).startswith("StyleBox"):
            continue
        expanded = []
        for property_name in expand_properties:
            property_data = resource["properties"].get(property_name)
            value = serialized_float(property_data["value"]) if property_data else None
            if value is not None and value > 0.0:
                expanded.append(property_name.removeprefix("expand_margin_"))
        if expanded:
            expanding_styleboxes[resource_id] = sorted(expanded)

    def inside_scroll_container(node_path: str) -> bool:
        current = node_path
        while True:
            current_node_data = paths.get(current)
            if current_node_data and current_node_data.get("type") == "ScrollContainer":
                return True
            if current == ".":
                return False
            current = current.rpartition("/")[0] or "."

    for node in nodes:
        if not inside_scroll_container(node["path"]):
            continue
        focus_override = node["properties"].get("theme_override_styles/focus")
        if not focus_override:
            continue
        match = re.fullmatch(r'SubResource\("([^"]+)"\)', focus_override["value"])
        if match and match.group(1) in expanding_styleboxes:
            margins = ", ".join(expanding_styleboxes[match.group(1)])
            diagnostics.append(
                diagnostic(
                    "warning",
                    scene_name,
                    focus_override["line"],
                    f"Focus StyleBox on {node['path']} expands outside its rect ({margins}) inside a "
                    "ScrollContainer; clipping may crop the focus state and expanded art is not a hit target. "
                    "Inspect pointer/keyboard focus at runtime.",
                )
            )

    if any(node.get("type") == "ScrollContainer" for node in nodes):
        for resource in sub_resources.values():
            if resource.get("type") != "Theme":
                continue
            for property_name, property_data in resource["properties"].items():
                if not property_name.endswith("/styles/focus"):
                    continue
                match = re.fullmatch(r'SubResource\("([^"]+)"\)', property_data["value"])
                if not match or match.group(1) not in expanding_styleboxes:
                    continue
                margins = ", ".join(expanding_styleboxes[match.group(1)])
                diagnostics.append(
                    diagnostic(
                        "warning",
                        scene_name,
                        property_data["line"],
                        f"Theme focus StyleBox expands outside control rects ({margins}) in a scene with a "
                        "ScrollContainer; verify any focused descendant is not clipped.",
                    )
                )

    script_methods: dict[str, set[str]] = {}
    for resource_id, resource in ext_resources.items():
        if resource.get("type") != "Script" or not resource.get("path", "").startswith("res://"):
            continue
        try:
            script_path = project_path(root, resource["path"])
        except ValueError:
            continue
        if script_path.is_file():
            source = script_path.read_text(encoding="utf-8-sig", errors="replace")
            script_methods[resource_id] = {match.group("name") for match in FUNCTION_PATTERN.finditer(source)}

    for connection in connections:
        for endpoint in ("from", "to"):
            value = connection.get(endpoint)
            normalized_endpoint = normalized_node_path(value or "")
            if value is None:
                diagnostics.append(
                    diagnostic("error", scene_name, int(connection["line"]), f"Signal connection {endpoint} node is missing: {value}")
                )
            elif normalized_endpoint not in paths:
                editable_anchor = editable_packed_scene_anchor(
                    normalized_endpoint, paths, editable_paths, ext_resources
                )
                if editable_anchor is None:
                    diagnostics.append(
                        diagnostic("error", scene_name, int(connection["line"]), f"Signal connection {endpoint} node is missing: {value}")
                    )
                else:
                    imported_internal_references.append(
                        {
                            "kind": f"connection_{endpoint}",
                            "path": normalized_endpoint,
                            "editable_instance": editable_anchor,
                            "line": int(connection["line"]),
                        }
                    )
        target_path = normalized_node_path(connection.get("to", ""))
        target_node = paths.get(target_path)
        method = connection.get("method")
        if target_node and method:
            script_property = target_node["properties"].get("script", {}).get("value", "")
            match = re.fullmatch(r'ExtResource\("([^"]+)"\)', script_property)
            if match and match.group(1) in script_methods and method not in script_methods[match.group(1)]:
                diagnostics.append(
                    diagnostic(
                        "warning",
                        scene_name,
                        int(connection["line"]),
                        f"Connected method is not declared in target script: {target_path}.{method}",
                    )
                )

    if imported_internal_references:
        anchors = sorted({item["editable_instance"] for item in imported_internal_references})
        diagnostics.append(
            diagnostic(
                "info",
                scene_name,
                min(int(item["line"]) for item in imported_internal_references),
                f"{len(imported_internal_references)} reference(s) target internal nodes below "
                f"editable PackedScene instance(s) {', '.join(anchors)}; static hierarchy "
                "expansion is unavailable, so verify these paths by loading the scene in Godot.",
            )
        )

    return {
        "scene": scene_name,
        "nodes": len(nodes),
        "resources": len(ext_resources) + len(sub_resources),
        "connections": len(connections),
        "editable_packed_scene_internal_reference_count": len(imported_internal_references),
        "editable_packed_scene_internal_references": imported_internal_references,
        "diagnostics": diagnostics,
    }


def main() -> int:
    args = parse_args()
    try:
        root = find_root(args.project)
        if args.scene:
            scenes = [project_path(root, value) for value in args.scene]
        else:
            scenes = sorted(iter_scenes(root))
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    missing = [str(path) for path in scenes if not path.is_file()]
    if missing:
        print(f"[ERROR] Scene not found: {', '.join(missing)}", file=sys.stderr)
        return 2

    results = [audit_scene(root, path) for path in scenes]
    diagnostics = [item for result in results for item in result["diagnostics"]]
    errors = sum(item["level"] == "error" for item in diagnostics)
    warnings = sum(item["level"] == "warning" for item in diagnostics)
    report = {
        "project": str(root),
        "scene_count": len(results),
        "node_count": sum(result["nodes"] for result in results),
        "editable_packed_scene_internal_reference_count": sum(
            result["editable_packed_scene_internal_reference_count"] for result in results
        ),
        "error_count": errors,
        "warning_count": warnings,
        "scenes": results,
        "limitations": [
            "Static text-scene analysis cannot prove runtime-assigned values, imported-scene internals, or editor-unsaved nodes.",
            "Paths below an explicitly editable PackedScene instance are recorded as imported-internal limitations; Godot engine load/import is authoritative for whether those internal override, NodePath, and connection targets exist.",
            "Godot import/run remains authoritative for property types, ownership, scripts, and resource compatibility.",
            "TextureRect aspect warnings are candidates for rendered review; backgrounds and deliberate stretch art may be valid.",
            "Focus StyleBox clipping warnings cover serialized in-scene SubResources; external themes and runtime overrides still need rendered focus-state review.",
            "Built-in Button icon/text warnings cover serialized values and cannot prove runtime localization, visual-group centering, or click delivery.",
        ],
    }
    if args.json_output:
        output = Path(args.json_output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"[INFO] {len(results)} scene(s), {report['node_count']} node(s), {errors} error(s), {warnings} warning(s)")
    shown = diagnostics[: args.max_details] if args.summary else diagnostics
    for item in shown:
        print(f"[{item['level'].upper()}] {item['scene']}:{item['line']}: {item['message']}")
    if len(shown) < len(diagnostics):
        print(f"[INFO] {len(diagnostics) - len(shown)} additional diagnostic(s) omitted; use --json-output")
    failed = errors > 0 or (args.fail_on_warnings and warnings > 0)
    print("[FAIL] Scene graph audit failed" if failed else "[PASS] Scene graph audit passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
