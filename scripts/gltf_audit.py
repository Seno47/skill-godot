#!/usr/bin/env python3
"""Static glTF/GLB validation and production-readiness summary."""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
from pathlib import Path
import struct
import sys
from typing import Any, Iterable
from urllib.parse import unquote, unquote_to_bytes, urlparse


IGNORED_DIRECTORIES = {".git", ".godot", ".import", ".mono", "bin", "obj"}
GLB_MAGIC = b"glTF"
JSON_CHUNK = 0x4E4F534A
BIN_CHUNK = 0x004E4942


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit glTF 2.0/GLB structure, dependencies, and useful production signals.")
    parser.add_argument("--project", default=".", help="Project directory used to resolve res:// paths.")
    parser.add_argument("--asset", action="append", help=".gltf or .glb path (repeatable); defaults to all in project.")
    parser.add_argument("--max-vertices", type=int, default=0, help="Warn above this total; 0 disables.")
    parser.add_argument("--max-triangles", type=int, default=0, help="Warn above this estimated total; 0 disables.")
    parser.add_argument("--max-external-mb", type=float, default=0, help="Warn for an external file above this size; 0 disables.")
    parser.add_argument("--json-output", help="Write the full JSON report.")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--max-details", type=int, default=60)
    parser.add_argument("--fail-on-warnings", action="store_true")
    args = parser.parse_args()
    if args.max_vertices < 0 or args.max_triangles < 0 or args.max_external_mb < 0 or args.max_details < 0:
        parser.error("budget and detail values must be non-negative")
    return args


def find_root(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    if root.is_file():
        root = root.parent
    if not root.is_dir():
        raise ValueError(f"Project directory does not exist: {root}")
    return root


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_asset(root: Path, value: str) -> Path:
    if value.startswith("res://"):
        path = root / value.removeprefix("res://").replace("/", os.sep)
    else:
        candidate = Path(value).expanduser()
        path = candidate if candidate.is_absolute() else root / candidate
    return path.resolve()


def iter_assets(root: Path) -> Iterable[Path]:
    for current, directories, files in os.walk(root):
        directories[:] = [name for name in directories if name not in IGNORED_DIRECTORIES]
        for name in files:
            if Path(name).suffix.lower() in {".gltf", ".glb"}:
                yield Path(current) / name


def load_document(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if path.suffix.lower() == ".gltf":
        return json.loads(path.read_text(encoding="utf-8-sig")), {"container": "gltf"}
    data = path.read_bytes()
    if len(data) < 12 or data[:4] != GLB_MAGIC:
        raise ValueError("invalid GLB header")
    version, declared_length = struct.unpack("<II", data[4:12])
    if version != 2:
        raise ValueError(f"unsupported GLB version {version}; expected 2")
    if declared_length != len(data):
        raise ValueError(f"GLB length header says {declared_length}, file has {len(data)} bytes")
    offset = 12
    json_payload: bytes | None = None
    chunk_count = 0
    binary_chunk_bytes = 0
    while offset + 8 <= len(data):
        length, kind = struct.unpack("<II", data[offset : offset + 8])
        offset += 8
        if offset + length > len(data):
            raise ValueError("truncated GLB chunk")
        payload = data[offset : offset + length]
        offset += length
        chunk_count += 1
        if kind == JSON_CHUNK and json_payload is None:
            json_payload = payload.rstrip(b"\x00 \t\r\n")
        elif kind == BIN_CHUNK:
            binary_chunk_bytes += len(payload)
    if json_payload is None:
        raise ValueError("GLB has no JSON chunk")
    return json.loads(json_payload.decode("utf-8")), {
        "container": "glb",
        "chunk_count": chunk_count,
        "binary_chunk_bytes": binary_chunk_bytes,
    }


def issue(level: str, asset: str, message: str) -> dict[str, str]:
    return {"level": level, "asset": asset, "message": message}


def valid_index(value: Any, collection: list[Any]) -> bool:
    return isinstance(value, int) and 0 <= value < len(collection)


def check_index(
    diagnostics: list[dict[str, str]],
    label: str,
    value: Any,
    collection: list[Any],
    target_name: str,
) -> None:
    if not valid_index(value, collection):
        diagnostics.append(issue("error", label, f"invalid {target_name} index: {value}"))


def primitive_triangles(primitive: dict[str, Any], accessors: list[Any]) -> int:
    mode = primitive.get("mode", 4)
    if mode != 4:
        return 0
    accessor_index = primitive.get("indices", primitive.get("attributes", {}).get("POSITION"))
    if valid_index(accessor_index, accessors):
        return int(accessors[accessor_index].get("count", 0)) // 3
    return 0


def external_uri(base: Path, uri: str) -> Path | None:
    parsed = urlparse(uri)
    if parsed.scheme in {"data", "http", "https"}:
        return None
    if parsed.scheme and len(parsed.scheme) > 1:
        return None
    return (base / unquote(parsed.path)).resolve()


def decode_data_uri(uri: str) -> bytes:
    if not uri.startswith("data:") or "," not in uri:
        raise ValueError("invalid data URI")
    metadata, payload = uri.split(",", 1)
    if metadata.endswith(";base64"):
        try:
            return base64.b64decode(payload, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValueError("invalid base64 data URI") from exc
    return unquote_to_bytes(payload)


def audit_asset(root: Path, path: Path, args: argparse.Namespace) -> dict[str, Any]:
    label = path.relative_to(root).as_posix() if is_within(path, root) else str(path)
    diagnostics: list[dict[str, str]] = []
    result: dict[str, Any] = {"asset": label, "diagnostics": diagnostics}
    try:
        document, container = load_document(path)
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        diagnostics.append(issue("error", label, str(exc)))
        return result
    result.update(container)

    collections = {
        name: document.get(name, [])
        for name in (
            "accessors",
            "animations",
            "buffers",
            "bufferViews",
            "cameras",
            "images",
            "materials",
            "meshes",
            "nodes",
            "samplers",
            "scenes",
            "skins",
            "textures",
        )
    }
    result["counts"] = {name: len(items) for name, items in collections.items()}
    version = str(document.get("asset", {}).get("version", ""))
    if not version.startswith("2"):
        diagnostics.append(issue("error", label, f"glTF asset.version must be 2.x, got {version or 'missing'}"))
    if "scene" in document:
        check_index(diagnostics, label, document["scene"], collections["scenes"], "default scene")

    for scene_index, scene in enumerate(collections["scenes"]):
        for node_index in scene.get("nodes", []):
            if not valid_index(node_index, collections["nodes"]):
                diagnostics.append(issue("error", label, f"scene {scene_index} references invalid node {node_index}"))
    for node_index, node in enumerate(collections["nodes"]):
        for child in node.get("children", []):
            if not valid_index(child, collections["nodes"]):
                diagnostics.append(issue("error", label, f"node {node_index} references invalid child {child}"))
        for field, target in (("mesh", "meshes"), ("skin", "skins"), ("camera", "cameras")):
            if field in node:
                check_index(diagnostics, label, node[field], collections[target], f"node {field}")

    for buffer_index, buffer in enumerate(collections["buffers"]):
        declared_length = buffer.get("byteLength")
        if not isinstance(declared_length, int) or declared_length < 1:
            diagnostics.append(issue("error", label, f"buffer {buffer_index} has invalid byteLength"))
            continue
        uri = buffer.get("uri")
        if uri is None:
            available = int(result.get("binary_chunk_bytes", 0)) if buffer_index == 0 else 0
            if result.get("container") != "glb" or available < declared_length:
                diagnostics.append(
                    issue("error", label, f"buffer {buffer_index} has no URI and insufficient GLB binary data")
                )
        elif isinstance(uri, str) and uri.startswith("data:"):
            try:
                available = len(decode_data_uri(uri))
            except ValueError as exc:
                diagnostics.append(issue("error", label, f"buffer {buffer_index}: {exc}"))
            else:
                if available < declared_length:
                    diagnostics.append(
                        issue("error", label, f"buffer {buffer_index} data has {available} bytes; declares {declared_length}")
                    )

    for view_index, view in enumerate(collections["bufferViews"]):
        check_index(diagnostics, label, view.get("buffer"), collections["buffers"], f"bufferView {view_index} buffer")
        view_length = view.get("byteLength")
        if not isinstance(view_length, int) or view_length < 1:
            diagnostics.append(issue("error", label, f"bufferView {view_index} has invalid byteLength"))
        buffer_index = view.get("buffer")
        if valid_index(buffer_index, collections["buffers"]):
            declared = collections["buffers"][buffer_index].get("byteLength")
            start = view.get("byteOffset", 0)
            length = view_length
            if (
                isinstance(declared, int)
                and isinstance(start, int)
                and isinstance(length, int)
                and (start < 0 or start + length > declared)
            ):
                diagnostics.append(issue("error", label, f"bufferView {view_index} exceeds buffer {buffer_index}"))
    valid_component_types = {5120, 5121, 5122, 5123, 5125, 5126}
    valid_accessor_types = {"SCALAR", "VEC2", "VEC3", "VEC4", "MAT2", "MAT3", "MAT4"}
    for accessor_index, accessor in enumerate(collections["accessors"]):
        if "bufferView" in accessor:
            check_index(
                diagnostics,
                label,
                accessor["bufferView"],
                collections["bufferViews"],
                f"accessor {accessor_index} bufferView",
            )
        elif "sparse" not in accessor:
            diagnostics.append(issue("error", label, f"accessor {accessor_index} has neither bufferView nor sparse data"))
        if accessor.get("componentType") not in valid_component_types:
            diagnostics.append(issue("error", label, f"accessor {accessor_index} has invalid componentType"))
        if accessor.get("type") not in valid_accessor_types:
            diagnostics.append(issue("error", label, f"accessor {accessor_index} has invalid type"))
        if not isinstance(accessor.get("count"), int) or accessor.get("count", 0) < 1:
            diagnostics.append(issue("error", label, f"accessor {accessor_index} has invalid count"))
    for image_index, image in enumerate(collections["images"]):
        if "bufferView" in image:
            check_index(
                diagnostics,
                label,
                image["bufferView"],
                collections["bufferViews"],
                f"image {image_index} bufferView",
            )
            if not image.get("mimeType"):
                diagnostics.append(issue("error", label, f"image {image_index} in a bufferView has no mimeType"))
        uri = image.get("uri")
        if isinstance(uri, str) and uri.startswith("data:"):
            try:
                if not decode_data_uri(uri):
                    diagnostics.append(issue("error", label, f"image {image_index} data URI is empty"))
            except ValueError as exc:
                diagnostics.append(issue("error", label, f"image {image_index}: {exc}"))

    vertices = 0
    triangles = 0
    primitive_count = 0
    missing_bounds = 0
    for mesh_index, mesh in enumerate(collections["meshes"]):
        for primitive_index, primitive in enumerate(mesh.get("primitives", [])):
            primitive_count += 1
            attrs = primitive.get("attributes", {})
            position = attrs.get("POSITION")
            if not valid_index(position, collections["accessors"]):
                diagnostics.append(issue("error", label, f"mesh {mesh_index} primitive {primitive_index} lacks valid POSITION"))
                continue
            position_accessor = collections["accessors"][position]
            vertices += int(position_accessor.get("count", 0))
            triangles += primitive_triangles(primitive, collections["accessors"])
            if "min" not in position_accessor or "max" not in position_accessor:
                missing_bounds += 1
            if "indices" not in primitive:
                diagnostics.append(issue("warning", label, f"mesh {mesh_index} primitive {primitive_index} is non-indexed"))
            if "NORMAL" not in attrs:
                diagnostics.append(issue("warning", label, f"mesh {mesh_index} primitive {primitive_index} has no NORMAL"))
            if "material" in primitive:
                check_index(diagnostics, label, primitive["material"], collections["materials"], "primitive material")
                if "TEXCOORD_0" not in attrs:
                    diagnostics.append(
                        issue("warning", label, f"mesh {mesh_index} primitive {primitive_index} has a material but no TEXCOORD_0")
                    )
                if valid_index(primitive["material"], collections["materials"]):
                    material = collections["materials"][primitive["material"]]
                    if "normalTexture" in material and "TANGENT" not in attrs:
                        diagnostics.append(
                            issue("warning", label, f"mesh {mesh_index} primitive {primitive_index} uses a normal map but has no TANGENT")
                        )
    result["geometry"] = {
        "primitive_count": primitive_count,
        "vertices": vertices,
        "estimated_triangles": triangles,
        "primitives_without_bounds": missing_bounds,
    }
    if missing_bounds:
        diagnostics.append(issue("warning", label, f"{missing_bounds} primitive(s) have no POSITION min/max bounds"))
    if args.max_vertices and vertices > args.max_vertices:
        diagnostics.append(issue("warning", label, f"{vertices} vertices exceed budget {args.max_vertices}"))
    if args.max_triangles and triangles > args.max_triangles:
        diagnostics.append(issue("warning", label, f"~{triangles} triangles exceed budget {args.max_triangles}"))

    for texture_index, texture in enumerate(collections["textures"]):
        if "source" in texture:
            check_index(diagnostics, label, texture["source"], collections["images"], "texture image")
        if "sampler" in texture:
            check_index(diagnostics, label, texture["sampler"], collections["samplers"], "texture sampler")
    external_files: list[dict[str, Any]] = []
    for kind in ("buffers", "images"):
        for index, item in enumerate(collections[kind]):
            uri = item.get("uri")
            if not uri:
                continue
            parsed = urlparse(uri)
            if parsed.scheme in {"http", "https"}:
                diagnostics.append(issue("error", label, f"{kind}[{index}] uses remote URI: {uri}"))
                continue
            if parsed.scheme == "data":
                try:
                    embedded_size = len(decode_data_uri(uri))
                except ValueError:
                    embedded_size = None
                external_files.append(
                    {"kind": kind, "index": index, "uri": "data:", "embedded": True, "bytes": embedded_size}
                )
                continue
            target = external_uri(path.parent, uri)
            if target is None:
                diagnostics.append(issue("warning", label, f"{kind}[{index}] URI could not be verified: {uri}"))
                continue
            if not is_within(target, path.parent.resolve()):
                diagnostics.append(issue("warning", label, f"{kind}[{index}] escapes the asset directory: {uri}"))
            if not target.is_file():
                diagnostics.append(issue("error", label, f"missing external {kind}[{index}]: {uri}"))
                continue
            size = target.stat().st_size
            external_files.append({"kind": kind, "index": index, "path": str(target), "bytes": size})
            if kind == "buffers":
                declared = item.get("byteLength")
                if isinstance(declared, int) and size < declared:
                    diagnostics.append(
                        issue("error", label, f"external buffer {uri} has {size} bytes; declares {declared}")
                    )
            if args.max_external_mb and size > args.max_external_mb * 1024 * 1024:
                diagnostics.append(
                    issue("warning", label, f"external file {uri} is {size / 1024 / 1024:.2f} MiB (budget {args.max_external_mb:.2f})")
                )
    result["external_files"] = external_files

    for skin_index, skin in enumerate(collections["skins"]):
        for joint in skin.get("joints", []):
            if not valid_index(joint, collections["nodes"]):
                diagnostics.append(issue("error", label, f"skin {skin_index} references invalid joint {joint}"))
    for animation_index, animation in enumerate(collections["animations"]):
        if not animation.get("channels"):
            diagnostics.append(issue("warning", label, f"animation {animation_index} has no channels"))
        samplers = animation.get("samplers", [])
        for sampler_index, sampler in enumerate(samplers):
            check_index(diagnostics, label, sampler.get("input"), collections["accessors"], f"animation {animation_index} sampler {sampler_index} input")
            check_index(diagnostics, label, sampler.get("output"), collections["accessors"], f"animation {animation_index} sampler {sampler_index} output")
        for channel in animation.get("channels", []):
            if not valid_index(channel.get("sampler"), samplers):
                diagnostics.append(issue("error", label, f"animation {animation_index} channel has invalid sampler {channel.get('sampler')}"))
            target_node = channel.get("target", {}).get("node")
            if target_node is not None and not valid_index(target_node, collections["nodes"]):
                diagnostics.append(issue("error", label, f"animation {animation_index} targets invalid node {target_node}"))
    return result


def main() -> int:
    args = parse_args()
    try:
        root = find_root(args.project)
        assets = [resolve_asset(root, value) for value in (args.asset or [])] or sorted(iter_assets(root))
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    missing = [str(path) for path in assets if not path.is_file()]
    if missing:
        print(f"[ERROR] Missing glTF asset(s): {', '.join(missing)}", file=sys.stderr)
        return 2
    results = [audit_asset(root, path, args) for path in assets]
    diagnostics = [item for result in results for item in result["diagnostics"]]
    errors = sum(item["level"] == "error" for item in diagnostics)
    warnings = sum(item["level"] == "warning" for item in diagnostics)
    report = {
        "project": str(root),
        "asset_count": len(results),
        "error_count": errors,
        "warning_count": warnings,
        "assets": results,
        "limitations": [
            "This audit cannot prove topology quality, UV overlap, rig deformation, material appearance, collision, scale, or animation quality.",
            "Inspect the Godot import, wrapper scene, turntable, and gameplay-camera result before acceptance.",
        ],
    }
    if args.json_output:
        output = Path(args.json_output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[INFO] {len(results)} asset(s), {errors} error(s), {warnings} warning(s)")
    shown = diagnostics[: args.max_details] if args.summary else diagnostics
    for item in shown:
        print(f"[{item['level'].upper()}] {item['asset']}: {item['message']}")
    if len(shown) < len(diagnostics):
        print(f"[INFO] {len(diagnostics) - len(shown)} additional diagnostic(s) omitted; use --json-output")
    failed = errors > 0 or (args.fail_on_warnings and warnings > 0)
    print("[FAIL] glTF audit failed" if failed else "[PASS] glTF audit passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
