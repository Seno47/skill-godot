#!/usr/bin/env python3
"""Measure exported build artifacts, budgets, top contributors, and regressions."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Iterable
import zipfile


SCHEMA_VERSION = 1
PROFILE_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

CATEGORIES: dict[str, set[str]] = {
    "executable": {".dll", ".dylib", ".exe", ".so", ".wasm", ".x86", ".x86_64"},
    "package": {".aab", ".apk", ".ipa", ".pck", ".tpz", ".zip"},
    "image": {".bmp", ".dds", ".exr", ".hdr", ".jpeg", ".jpg", ".ktx", ".png", ".svg", ".tga", ".webp"},
    "model": {".dae", ".fbx", ".glb", ".gltf", ".obj"},
    "audio": {".flac", ".mp3", ".ogg", ".wav"},
    "font": {".otf", ".ttf", ".woff", ".woff2"},
    "video": {".avi", ".mp4", ".ogv", ".webm"},
    "symbol": {".dsym", ".debug", ".map", ".pdb"},
    "data": {".cfg", ".csv", ".json", ".po", ".translation", ".txt"},
}

EXTENSION_CATEGORY = {
    extension: category for category, extensions in CATEGORIES.items() for extension in extensions
}


class AuditError(RuntimeError):
    pass


def parse_pair(value: str, label: str) -> tuple[str, str]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(f"{label} must use NAME=VALUE")
    name, raw = value.split("=", 1)
    if not PROFILE_PATTERN.fullmatch(name):
        raise argparse.ArgumentTypeError(f"{label} name must use lowercase kebab-case")
    if not raw:
        raise argparse.ArgumentTypeError(f"{label} value cannot be empty")
    return name, raw


def parse_artifact(value: str) -> tuple[str, str]:
    return parse_pair(value, "--artifact")


def parse_budget(value: str) -> tuple[str, float]:
    name, raw = parse_pair(value, "--budget-mb")
    try:
        budget = float(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--budget-mb value must be numeric") from exc
    if budget < 0:
        raise argparse.ArgumentTypeError("--budget-mb value cannot be negative")
    return name, budget


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit exported build sizes and compare per-profile budgets/baselines."
    )
    parser.add_argument(
        "--artifact",
        action="append",
        type=parse_artifact,
        required=True,
        help="Artifact as PROFILE=PATH; repeatable.",
    )
    parser.add_argument(
        "--budget-mb",
        action="append",
        type=parse_budget,
        default=[],
        help="Maximum artifact size as PROFILE=MB; repeatable.",
    )
    parser.add_argument("--baseline", help="Previous JSON report from this script.")
    parser.add_argument("--json-output", help="Write the full current JSON report.")
    parser.add_argument("--top", type=int, default=10, help="Top contributor count per profile.")
    parser.add_argument("--summary", action="store_true", help="Suppress top/category detail.")
    args = parser.parse_args()
    if args.top < 0:
        parser.error("--top cannot be negative")
    return args


def category_for(name: str) -> str:
    suffix = Path(name).suffix.lower()
    return EXTENSION_CATEGORY.get(suffix, "other")


def walk_directory(path: Path) -> tuple[list[tuple[str, int]], list[str]]:
    entries: list[tuple[str, int]] = []
    warnings: list[str] = []
    for current, directories, files in os.walk(path, followlinks=False):
        current_path = Path(current)
        kept_directories: list[str] = []
        for name in directories:
            child = current_path / name
            if child.is_symlink():
                warnings.append(f"Skipped symlink directory: {child.relative_to(path).as_posix()}")
            else:
                kept_directories.append(name)
        directories[:] = kept_directories
        for name in files:
            file_path = current_path / name
            relative = file_path.relative_to(path).as_posix()
            if file_path.is_symlink():
                warnings.append(f"Skipped symlink file: {relative}")
                continue
            try:
                entries.append((relative, file_path.stat().st_size))
            except OSError as exc:
                warnings.append(f"Could not stat {relative}: {exc}")
    return entries, warnings


def walk_zip(path: Path) -> tuple[list[tuple[str, int]], int, list[str]]:
    entries: list[tuple[str, int]] = []
    uncompressed = 0
    warnings: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                normalized = info.filename.replace("\\", "/")
                if normalized.startswith("/") or ".." in Path(normalized).parts:
                    warnings.append(f"Suspicious archive entry path: {normalized}")
                entries.append((normalized, info.compress_size))
                uncompressed += info.file_size
    except (OSError, zipfile.BadZipFile) as exc:
        raise AuditError(f"Could not inspect archive {path}: {exc}") from exc
    return entries, uncompressed, warnings


def summarize_entries(entries: Iterable[tuple[str, int]]) -> tuple[dict[str, int], list[dict[str, Any]]]:
    categories: dict[str, int] = defaultdict(int)
    normalized_entries: list[dict[str, Any]] = []
    for name, size in entries:
        category = category_for(name)
        categories[category] += size
        normalized_entries.append({"path": name, "bytes": size, "category": category})
    normalized_entries.sort(key=lambda item: (-item["bytes"], item["path"]))
    return dict(sorted(categories.items())), normalized_entries


def analyze_artifact(name: str, raw_path: str) -> dict[str, Any]:
    path = Path(raw_path).expanduser().resolve()
    if not path.exists():
        raise AuditError(f"Artifact not found for {name}: {path}")

    warnings: list[str] = []
    if path.is_dir():
        entries, warnings = walk_directory(path)
        total_bytes = sum(size for _, size in entries)
        mode = "directory"
        uncompressed_bytes = None
    elif path.is_file():
        try:
            total_bytes = path.stat().st_size
        except OSError as exc:
            raise AuditError(f"Could not stat artifact {path}: {exc}") from exc
        if zipfile.is_zipfile(path):
            entries, uncompressed_bytes, warnings = walk_zip(path)
            mode = "zip-container"
        else:
            entries = [(path.name, total_bytes)]
            uncompressed_bytes = None
            mode = "file"
    else:
        raise AuditError(f"Unsupported artifact type for {name}: {path}")

    categories, normalized_entries = summarize_entries(entries)
    return {
        "path": str(path),
        "mode": mode,
        "total_bytes": total_bytes,
        "uncompressed_content_bytes": uncompressed_bytes,
        "file_count": len(entries),
        "categories": categories,
        "largest": normalized_entries,
        "warnings": warnings,
    }


def load_baseline(path_value: str | None) -> dict[str, Any] | None:
    if not path_value:
        return None
    path = Path(path_value).expanduser().resolve()
    if not path.is_file():
        raise AuditError(f"Baseline report not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuditError(f"Invalid baseline report {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != SCHEMA_VERSION:
        raise AuditError(f"Baseline schema_version must be {SCHEMA_VERSION}")
    if not isinstance(data.get("profiles"), dict):
        raise AuditError("Baseline profiles must be an object")
    return data


def baseline_size(baseline: dict[str, Any] | None, name: str) -> int | None:
    if baseline is None:
        return None
    profile = baseline.get("profiles", {}).get(name)
    if not isinstance(profile, dict):
        return None
    value = profile.get("total_bytes")
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def format_size(value: int | float) -> str:
    return f"{value / 1024 / 1024:.2f} MiB"


def write_report(path_value: str, report: dict[str, Any]) -> None:
    path = Path(path_value).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    artifacts = dict(args.artifact)
    if len(artifacts) != len(args.artifact):
        print("[ERROR] Duplicate --artifact profile name", file=sys.stderr)
        return 2
    budgets = dict(args.budget_mb)
    if len(budgets) != len(args.budget_mb):
        print("[ERROR] Duplicate --budget-mb profile name", file=sys.stderr)
        return 2
    unknown_budgets = sorted(set(budgets) - set(artifacts))
    if unknown_budgets:
        print(
            "[ERROR] Budget profile(s) have no artifact: " + ", ".join(unknown_budgets),
            file=sys.stderr,
        )
        return 2

    try:
        baseline = load_baseline(args.baseline)
        profiles = {name: analyze_artifact(name, path) for name, path in artifacts.items()}
    except AuditError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    failures = 0
    for name, profile in profiles.items():
        budget_bytes = int(budgets[name] * 1024 * 1024) if name in budgets else None
        profile["budget_bytes"] = budget_bytes
        profile["budget_status"] = (
            "fail" if budget_bytes is not None and profile["total_bytes"] > budget_bytes else "pass"
        )
        if profile["budget_status"] == "fail":
            failures += 1
        previous = baseline_size(baseline, name)
        profile["baseline_bytes"] = previous
        profile["delta_bytes"] = profile["total_bytes"] - previous if previous is not None else None
        profile["delta_percent"] = (
            (profile["total_bytes"] - previous) / previous * 100.0
            if previous not in (None, 0)
            else None
        )

        status = "FAIL" if profile["budget_status"] == "fail" else "PASS"
        pieces = [f"[{status}] {name}: {format_size(profile['total_bytes'])}"]
        if budget_bytes is not None:
            pieces.append(f"budget {format_size(budget_bytes)}")
        if previous is not None:
            delta_percent = profile["delta_percent"]
            delta_text = f"{delta_percent:+.2f}%" if delta_percent is not None else "n/a"
            pieces.append(f"baseline {format_size(previous)} ({delta_text})")
        pieces.append(f"{profile['file_count']} file(s), {profile['mode']}")
        print("; ".join(pieces))

        if not args.summary:
            if profile["categories"]:
                category_text = ", ".join(
                    f"{category}={format_size(size)}"
                    for category, size in sorted(
                        profile["categories"].items(), key=lambda item: -item[1]
                    )
                )
                print(f"[INFO] {name} categories: {category_text}")
            for item in profile["largest"][: args.top]:
                print(f"[INFO] {name} top: {format_size(item['bytes'])} {item['path']}")
        for warning in profile["warnings"]:
            print(f"[WARN] {name}: {warning}")

    report = {"schema_version": SCHEMA_VERSION, "profiles": profiles}
    if args.json_output:
        try:
            write_report(args.json_output, report)
            print(f"[INFO] Full report: {Path(args.json_output).expanduser().resolve()}")
        except OSError as exc:
            print(f"[ERROR] Could not write report: {exc}", file=sys.stderr)
            return 2

    if failures:
        print(f"[FAIL] {failures} build-size budget failure(s)", file=sys.stderr)
        return 1
    print(f"[PASS] {len(profiles)} artifact profile(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
