#!/usr/bin/env python3
"""Audit game asset files and optional asset-manifest coverage without dependencies."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import os
import re
import struct
import sys
from typing import Iterable

from asset_manifest import ManifestError, load_manifest, normalize_project_path, validate_manifest


ASSET_EXTENSIONS: dict[str, set[str]] = {
    "image": {".bmp", ".dds", ".exr", ".hdr", ".jpeg", ".jpg", ".ktx", ".png", ".svg", ".tga", ".webp"},
    "model": {".blend", ".dae", ".fbx", ".glb", ".gltf", ".obj"},
    "audio": {".flac", ".mp3", ".ogg", ".wav"},
    "font": {".otf", ".ttf", ".woff", ".woff2"},
    "source-2d": {".ase", ".aseprite", ".kra", ".psb", ".psd", ".xcf"},
    "shader": {".gdshader", ".glsl", ".hlsl"},
    "video": {".avi", ".mp4", ".ogv", ".webm"},
}

EXTENSION_KIND = {
    extension: kind for kind, extensions in ASSET_EXTENSIONS.items() for extension in extensions
}

IGNORED_DIRECTORIES = {
    ".asset-workbench",
    ".git",
    ".godot",
    ".import",
    ".mono",
    "bin",
    "build",
    "obj",
}

SVG_VIEWBOX = re.compile(
    r"\bviewBox\s*=\s*['\"]\s*[-+0-9.eE]+[ ,]+[-+0-9.eE]+[ ,]+([-+0-9.eE]+)[ ,]+([-+0-9.eE]+)\s*['\"]",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Godot-project asset sizes, dimensions, duplicates, and manifest coverage."
    )
    parser.add_argument(
        "--project",
        required=True,
        help="Godot project directory or path to project.godot.",
    )
    parser.add_argument(
        "--manifest",
        help="Optional asset manifest JSON to validate and compare against scanned files.",
    )
    parser.add_argument(
        "--root",
        action="append",
        default=[],
        help="Project-relative folder to scan; repeatable. Default: entire project.",
    )
    parser.add_argument(
        "--max-file-mb",
        type=float,
        default=50.0,
        help="Warn when an asset exceeds this size; 0 disables (default: 50).",
    )
    parser.add_argument(
        "--max-texture-dimension",
        type=int,
        default=4096,
        help="Warn for known raster/vector dimensions above this value; 0 disables.",
    )
    parser.add_argument(
        "--duplicate-max-mb",
        type=float,
        default=250.0,
        help="Hash possible duplicate groups up to this per-file size; 0 disables duplicates.",
    )
    parser.add_argument(
        "--require-manifest",
        action="store_true",
        help="Warn for every scanned asset not recorded in the manifest.",
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Return failure when warnings exist.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print counts only; keep full diagnostics in --json-output when requested.",
    )
    parser.add_argument(
        "--max-warnings",
        type=int,
        default=60,
        help="Maximum warning lines to print (default: 60; 0 prints none).",
    )
    parser.add_argument(
        "--json-output",
        help="Write a machine-readable report containing all diagnostics.",
    )
    args = parser.parse_args()
    if args.max_file_mb < 0:
        parser.error("--max-file-mb cannot be negative")
    if args.max_texture_dimension < 0:
        parser.error("--max-texture-dimension cannot be negative")
    if args.duplicate_max_mb < 0:
        parser.error("--duplicate-max-mb cannot be negative")
    if args.max_warnings < 0:
        parser.error("--max-warnings cannot be negative")
    if args.require_manifest and not args.manifest:
        parser.error("--require-manifest requires --manifest")
    return args


def find_project_root(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if path.is_file():
        if path.name != "project.godot":
            raise ManifestError(f"Expected project.godot, got {path}")
        path = path.parent
    if not (path / "project.godot").is_file():
        raise ManifestError(f"project.godot not found in {path}")
    return path


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_scan_roots(project: Path, values: list[str]) -> list[Path]:
    if not values:
        return [project]
    roots: list[Path] = []
    for value in values:
        normalized = normalize_project_path(value)
        candidate = (project / Path(normalized.replace("/", os.sep))).resolve()
        if not is_within(candidate, project):
            raise ManifestError(f"Scan root escapes project: {value}")
        if not candidate.is_dir():
            raise ManifestError(f"Scan root is not a directory: {candidate}")
        roots.append(candidate)
    return roots


def iter_asset_files(roots: list[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for root in roots:
        for current, directories, files in os.walk(root):
            directories[:] = [name for name in directories if name not in IGNORED_DIRECTORIES]
            current_path = Path(current)
            for name in files:
                path = (current_path / name).absolute()
                if path in seen or path.suffix.lower() not in EXTENSION_KIND:
                    continue
                seen.add(path)
                yield path


def image_dimensions(path: Path) -> tuple[int, int] | None:
    suffix = path.suffix.lower()
    try:
        if suffix == ".png":
            with path.open("rb") as handle:
                header = handle.read(24)
            if len(header) >= 24 and header[:8] == b"\x89PNG\r\n\x1a\n":
                return struct.unpack(">II", header[16:24])
        if suffix == ".svg":
            text = path.read_text(encoding="utf-8-sig", errors="replace")[:65536]
            match = SVG_VIEWBOX.search(text)
            if match:
                width = int(round(float(match.group(1))))
                height = int(round(float(match.group(2))))
                if width > 0 and height > 0:
                    return width, height
    except (OSError, ValueError, struct.error):
        return None
    return None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def duplicate_groups(files: list[Path], max_bytes: int) -> tuple[list[list[Path]], int]:
    if max_bytes <= 0:
        return [], 0
    by_size: dict[int, list[Path]] = defaultdict(list)
    for path in files:
        try:
            size = path.stat().st_size
        except OSError:
            continue
        by_size[size].append(path)

    by_digest: dict[tuple[int, str], list[Path]] = defaultdict(list)
    skipped = 0
    for size, candidates in by_size.items():
        if len(candidates) < 2:
            continue
        if size > max_bytes:
            skipped += len(candidates)
            continue
        for path in candidates:
            try:
                by_digest[(size, sha256(path))].append(path)
            except OSError:
                continue
    return [group for group in by_digest.values() if len(group) > 1], skipped


def relative(project: Path, path: Path) -> str:
    return path.relative_to(project).as_posix()


def write_report(path_value: str, report: dict[str, object]) -> None:
    path = Path(path_value).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    try:
        project = find_project_root(args.project)
        roots = resolve_scan_roots(project, args.root)
    except ManifestError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    files = sorted(iter_asset_files(roots))
    counts = Counter(EXTENSION_KIND[path.suffix.lower()] for path in files)
    total_bytes = 0
    errors: list[str] = []
    warnings: list[str] = []

    max_file_bytes = int(args.max_file_mb * 1024 * 1024)
    for path in files:
        rel = relative(project, path)
        if path.is_symlink():
            warnings.append(f"Symlink asset file requires manual source/scope review: {rel}")
            continue
        try:
            size = path.stat().st_size
        except OSError as exc:
            errors.append(f"Could not stat {rel}: {exc}")
            continue
        total_bytes += size
        if size == 0:
            warnings.append(f"Empty asset file: {rel}")
        if max_file_bytes > 0 and size > max_file_bytes:
            warnings.append(f"Large asset ({size / 1024 / 1024:.1f} MiB): {rel}")
        if args.max_texture_dimension > 0 and EXTENSION_KIND[path.suffix.lower()] == "image":
            dimensions = image_dimensions(path)
            if dimensions and max(dimensions) > args.max_texture_dimension:
                warnings.append(
                    f"Large texture dimensions ({dimensions[0]}x{dimensions[1]}): {rel}"
                )

    duplicate_limit = int(args.duplicate_max_mb * 1024 * 1024)
    duplicates, skipped_duplicate_files = duplicate_groups(
        [path for path in files if not path.is_symlink()], duplicate_limit
    )
    for group in duplicates:
        labels = ", ".join(relative(project, path) for path in group)
        warnings.append(f"Byte-identical asset files: {labels}")

    referenced_files: set[str] = set()
    if args.manifest:
        try:
            manifest = load_manifest(Path(args.manifest).expanduser().resolve())
            manifest_errors, manifest_warnings, referenced_files = validate_manifest(
                manifest, project
            )
            errors.extend(f"Manifest: {message}" for message in manifest_errors)
            warnings.extend(f"Manifest: {message}" for message in manifest_warnings)
        except ManifestError as exc:
            errors.append(str(exc))

    scanned_paths = {relative(project, path) for path in files}
    unmanifested = sorted(scanned_paths - referenced_files) if args.manifest else []
    if args.require_manifest:
        warnings.extend(f"Asset is not in manifest: {path}" for path in unmanifested)

    print(f"[OK] Project: {project}")
    print(
        f"[INFO] Assets: {len(files)} files, {total_bytes / 1024 / 1024:.1f} MiB"
    )
    if counts:
        print("[INFO] Kinds: " + ", ".join(f"{kind}={counts[kind]}" for kind in sorted(counts)))
    if args.manifest:
        print(
            f"[INFO] Manifest coverage: {len(scanned_paths & referenced_files)}/{len(scanned_paths)} "
            f"scanned asset files"
        )
        if unmanifested and not args.require_manifest:
            print(
                f"[INFO] Unmanifested: {len(unmanifested)} "
                "(pass --require-manifest to list as warnings)"
            )
    if skipped_duplicate_files:
        print(
            f"[INFO] Duplicate hashing skipped {skipped_duplicate_files} file(s) above "
            f"{args.duplicate_max_mb:g} MiB"
        )

    visible_warnings = [] if args.summary else warnings[: args.max_warnings]
    for warning in visible_warnings:
        print(f"[WARN] {warning}")
    omitted_warnings = len(warnings) - len(visible_warnings)
    if omitted_warnings and not args.summary:
        print(
            f"[INFO] Omitted {omitted_warnings} warning(s); use --json-output for all diagnostics"
        )
    sys.stdout.flush()
    for error in errors:
        print(f"[ERROR] {error}", file=sys.stderr)

    report: dict[str, object] = {
        "schema_version": 1,
        "project": str(project),
        "summary": {
            "asset_files": len(files),
            "total_bytes": total_bytes,
            "kinds": dict(sorted(counts.items())),
            "errors": len(errors),
            "warnings": len(warnings),
            "duplicate_groups": len(duplicates),
            "duplicate_hash_skipped_files": skipped_duplicate_files,
            "manifest_referenced_scanned_files": len(scanned_paths & referenced_files),
            "unmanifested_files": len(unmanifested),
        },
        "errors": errors,
        "warnings": warnings,
        "unmanifested": unmanifested,
    }
    if args.json_output:
        try:
            write_report(args.json_output, report)
            print(f"[INFO] Full report: {Path(args.json_output).expanduser().resolve()}")
        except OSError as exc:
            print(f"[ERROR] Could not write report: {exc}", file=sys.stderr)
            return 2

    if errors:
        print(f"[FAIL] {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 1
    if warnings and args.fail_on_warnings:
        print(f"[FAIL] 0 errors, {len(warnings)} warning(s)", file=sys.stderr)
        return 1
    print(f"[PASS] 0 errors, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
