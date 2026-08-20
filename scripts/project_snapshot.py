#!/usr/bin/env python3
"""Create a compact, machine-readable map of a Godot project before editing it."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Any, Iterable


IGNORED_DIRECTORIES = {".git", ".godot", ".import", ".mono", "bin", "obj"}
SECTION_PATTERN = re.compile(r"^\[([^]]+)\]\s*$")
SETTING_PATTERN = re.compile(r"^(?P<key>[A-Za-z0-9_./-]+)\s*=\s*(?P<value>.*)$")
NODE_PATTERN = re.compile(r'^\[node\s+(?P<body>.*)\]$', re.MULTILINE)
TYPE_PATTERN = re.compile(r'\btype="([^"]+)"')
NAME_PATTERN = re.compile(r'\bname="([^"]+)"')
EXT_RESOURCE_PATTERN = re.compile(r"^\[ext_resource\b", re.MULTILINE)
SUB_RESOURCE_PATTERN = re.compile(r"^\[sub_resource\b", re.MULTILINE)
CONNECTION_PATTERN = re.compile(r"^\[connection\b", re.MULTILINE)
FEATURE_PATTERN = re.compile(r'config/features\s*=\s*PackedStringArray\((.*?)\)', re.DOTALL)
QUOTED_PATTERN = re.compile(r'"([^"]+)"')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize a Godot project without opening large files.")
    parser.add_argument("--project", default=".", help="Project directory or project.godot path.")
    parser.add_argument("--scene", action="append", help="Additional scene to summarize (repeatable).")
    parser.add_argument("--json-output", help="Write the full report to JSON.")
    parser.add_argument("--summary", action="store_true", help="Print a compact human-readable summary.")
    parser.add_argument("--max-items", type=int, default=20, help="Limit lists in the report and console.")
    parser.add_argument(
        "--git",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include bounded git working-tree status when the project is in a repository.",
    )
    args = parser.parse_args()
    if args.max_items < 1:
        parser.error("--max-items must be positive")
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


def resolve_project_path(root: Path, value: str) -> Path | None:
    if not value.startswith("res://"):
        return None
    path = (root / value.removeprefix("res://").replace("/", os.sep)).resolve()
    return path if is_within(path, root) else None


def decode_scalar(value: str) -> Any:
    stripped = value.strip()
    if stripped.startswith('"') and stripped.endswith('"'):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return stripped[1:-1]
    if stripped in {"true", "false"}:
        return stripped == "true"
    try:
        return int(stripped)
    except ValueError:
        try:
            return float(stripped)
        except ValueError:
            return stripped


def parse_config(text: str) -> dict[str, dict[str, Any]]:
    sections: dict[str, dict[str, Any]] = {}
    current = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        section = SECTION_PATTERN.match(line)
        if section:
            current = section.group(1)
            sections.setdefault(current, {})
            continue
        setting = SETTING_PATTERN.match(line)
        if setting:
            sections.setdefault(current, {})[setting.group("key")] = decode_scalar(setting.group("value"))
    return sections


def iter_files(root: Path) -> Iterable[Path]:
    for current, directories, files in os.walk(root):
        directories[:] = [name for name in directories if name not in IGNORED_DIRECTORIES]
        for name in files:
            yield Path(current) / name


def scene_summary(root: Path, path: Path) -> dict[str, Any]:
    label = path.relative_to(root).as_posix() if is_within(path, root) else str(path)
    if not path.is_file():
        return {"path": label, "exists": False}
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    node_types: Counter[str] = Counter()
    root_name = None
    for match in NODE_PATTERN.finditer(text):
        body = match.group("body")
        type_match = TYPE_PATTERN.search(body)
        name_match = NAME_PATTERN.search(body)
        if root_name is None and name_match:
            root_name = name_match.group(1)
        node_types[type_match.group(1) if type_match else "<instanced/inherited>"] += 1
    return {
        "path": label,
        "exists": True,
        "bytes": path.stat().st_size,
        "root_name": root_name,
        "node_count": sum(node_types.values()),
        "node_types": dict(node_types.most_common()),
        "external_resources": len(EXT_RESOURCE_PATTERN.findall(text)),
        "sub_resources": len(SUB_RESOURCE_PATTERN.findall(text)),
        "connections": len(CONNECTION_PATTERN.findall(text)),
    }


def export_presets(root: Path) -> list[dict[str, Any]]:
    path = root / "export_presets.cfg"
    if not path.is_file():
        return []
    sections = parse_config(path.read_text(encoding="utf-8-sig", errors="replace"))
    result = []
    for name, values in sections.items():
        if re.fullmatch(r"preset\.\d+", name):
            result.append(
                {
                    "section": name,
                    "name": values.get("name"),
                    "platform": values.get("platform"),
                    "runnable": values.get("runnable"),
                    "export_path": values.get("export_path"),
                }
            )
    return result


def git_status(root: Path, max_items: int) -> dict[str, Any] | None:
    git = shutil.which("git")
    if git is None:
        return {"available": False}
    completed = subprocess.run(
        [git, "-C", str(root), "status", "--porcelain=v1", "--untracked-files=normal", "--", "."],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        errors="replace",
        timeout=15,
        check=False,
    )
    if completed.returncode != 0:
        return None
    entries = [line for line in completed.stdout.splitlines() if line]
    counts = Counter(line[:2] for line in entries)
    return {
        "available": True,
        "dirty": bool(entries),
        "entry_count": len(entries),
        "status_counts": dict(counts),
        "entries": entries[:max_items],
        "entries_truncated": max(0, len(entries) - max_items),
    }


def main() -> int:
    args = parse_args()
    try:
        root = find_root(args.project)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    project_text = (root / "project.godot").read_text(encoding="utf-8-sig", errors="replace")
    config = parse_config(project_text)
    application = config.get("application", {})
    display = config.get("display", {})
    rendering = config.get("rendering", {})
    main_scene = application.get("run/main_scene")
    features_match = FEATURE_PATTERN.search(project_text)
    features = QUOTED_PATTERN.findall(features_match.group(1)) if features_match else []

    files = list(iter_files(root))
    extension_counts = Counter((path.suffix.lower() or "<none>") for path in files)
    category_counts = {
        "scenes": extension_counts[".tscn"],
        "resources": extension_counts[".tres"],
        "gdscript": extension_counts[".gd"],
        "csharp": extension_counts[".cs"],
        "shaders": extension_counts[".gdshader"],
        "raster_images": sum(extension_counts[suffix] for suffix in (".png", ".jpg", ".jpeg", ".webp")),
        "models": sum(extension_counts[suffix] for suffix in (".gltf", ".glb", ".fbx", ".obj", ".blend")),
        "audio": sum(extension_counts[suffix] for suffix in (".wav", ".ogg", ".mp3")),
    }
    largest = sorted(files, key=lambda path: path.stat().st_size, reverse=True)[: args.max_items]
    top_level = sorted(path.name for path in root.iterdir() if path.is_dir() and path.name not in IGNORED_DIRECTORIES)

    requested_scenes: list[Path] = []
    if isinstance(main_scene, str):
        resolved = resolve_project_path(root, main_scene)
        if resolved:
            requested_scenes.append(resolved)
    for value in args.scene or []:
        resolved = resolve_project_path(root, value)
        candidate = resolved or (root / value).resolve()
        if candidate not in requested_scenes:
            requested_scenes.append(candidate)

    input_actions = sorted(config.get("input", {}).keys())
    autoloads = config.get("autoload", {})
    report: dict[str, Any] = {
        "schema_version": 1,
        "project": {
            "root": str(root),
            "name": application.get("config/name", root.name),
            "features": features,
            "main_scene": main_scene,
            "renderer": rendering.get("renderer/rendering_method"),
            "renderer_mobile": rendering.get("renderer/rendering_method.mobile"),
            "viewport": {
                "width": display.get("window/size/viewport_width"),
                "height": display.get("window/size/viewport_height"),
                "stretch_mode": display.get("window/stretch/mode"),
            },
        },
        "architecture": {
            "input_actions": input_actions[: args.max_items],
            "input_actions_truncated": max(0, len(input_actions) - args.max_items),
            "autoloads": dict(list(autoloads.items())[: args.max_items]),
            "enabled_plugins": config.get("editor_plugins", {}).get("enabled"),
            "top_level_directories": top_level[: args.max_items],
            "top_level_directories_truncated": max(0, len(top_level) - args.max_items),
        },
        "files": {
            "count": len(files),
            "bytes": sum(path.stat().st_size for path in files),
            "categories": category_counts,
            "extensions": dict(extension_counts.most_common(args.max_items)),
            "largest": [
                {
                    "path": path.relative_to(root).as_posix(),
                    "bytes": path.stat().st_size,
                }
                for path in largest
            ],
        },
        "scenes": [scene_summary(root, path) for path in requested_scenes],
        "export_presets": export_presets(root),
        "git": git_status(root, args.max_items) if args.git else None,
        "next_checks": [
            "Run scene_graph_audit.py for serialized scene structure.",
            "Run verify_godot_project.py --engine before claiming engine validity.",
            "Read only the dependency chain and task-relevant files after this snapshot.",
        ],
    }
    if args.json_output:
        output = Path(args.json_output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not args.summary:
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    project = report["project"]
    print(f"[PROJECT] {project['name']} | {root}")
    print(f"[ENGINE] features={','.join(features) or 'unknown'} renderer={project['renderer'] or 'default'}")
    print(f"[MAIN] {main_scene or 'not configured'}")
    print("[SOURCES] " + ", ".join(f"{key}={value}" for key, value in category_counts.items()))
    print(f"[ARCH] input={len(input_actions)} autoloads={len(autoloads)} plugins={bool(report['architecture']['enabled_plugins'])}")
    for scene in report["scenes"]:
        print(
            f"[SCENE] {scene['path']} exists={scene['exists']} nodes={scene.get('node_count', 0)} "
            f"resources={scene.get('external_resources', 0) + scene.get('sub_resources', 0)} "
            f"connections={scene.get('connections', 0)}"
        )
    if report["git"]:
        print(f"[GIT] dirty={report['git'].get('dirty')} entries={report['git'].get('entry_count', 0)}")
    if args.json_output:
        print(f"[REPORT] {Path(args.json_output).expanduser().resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
