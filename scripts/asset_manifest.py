#!/usr/bin/env python3
"""Create and validate a provenance/status manifest for game assets."""

from __future__ import annotations

import argparse
from pathlib import Path
import json
import os
import re
import sys
import tempfile
from typing import Any


SCHEMA_VERSION = 1
STATUSES = ("candidate", "accepted", "adapted", "integrated", "verified")
SOURCE_TYPES = ("external", "generated", "user-provided", "in-house")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ATTRIBUTION_LICENSE_PATTERN = re.compile(r"(?:CC[- ]?BY|attribution)", re.IGNORECASE)


class ManifestError(RuntimeError):
    pass


def add_manifest_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--manifest", required=True, help="Path to asset manifest JSON.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage a portable JSON asset provenance and integration manifest."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create an empty manifest.")
    add_manifest_argument(init_parser)
    init_parser.add_argument(
        "--force", action="store_true", help="Replace an existing manifest explicitly."
    )

    add_parser = subparsers.add_parser("add", help="Add one asset record.")
    add_manifest_argument(add_parser)
    add_parser.add_argument("--id", required=True, help="Stable kebab-case asset ID.")
    add_parser.add_argument("--kind", required=True, help="Kebab-case asset kind.")
    add_parser.add_argument("--source-type", required=True, choices=SOURCE_TYPES)
    add_parser.add_argument("--status", choices=STATUSES, default="candidate")
    add_parser.add_argument("--source-url")
    add_parser.add_argument("--author")
    add_parser.add_argument("--license")
    add_parser.add_argument("--license-url")
    add_parser.add_argument("--attribution")
    add_parser.add_argument("--tool", help="Generation/authoring tool and version.")
    add_parser.add_argument("--acquired-on", help="Acquisition/generation date, YYYY-MM-DD.")
    add_parser.add_argument(
        "--source-file", action="append", default=[], help="Project-relative editable/source file."
    )
    add_parser.add_argument(
        "--runtime-file", action="append", default=[], help="Project-relative runtime asset file."
    )
    add_parser.add_argument(
        "--scene", action="append", default=[], help="Project-relative Godot integration scene."
    )
    add_parser.add_argument(
        "--requires-scene",
        action="store_true",
        help="Require an integration scene before integrated/verified status.",
    )
    add_parser.add_argument("--notes")

    status_parser = subparsers.add_parser("set-status", help="Advance an asset status.")
    add_manifest_argument(status_parser)
    status_parser.add_argument("--id", required=True)
    status_parser.add_argument("--status", required=True, choices=STATUSES)
    status_parser.add_argument(
        "--allow-regression",
        action="store_true",
        help="Explicitly allow moving an asset to an earlier lifecycle state.",
    )

    validate_parser = subparsers.add_parser("validate", help="Validate schema, rights, and files.")
    add_manifest_argument(validate_parser)
    validate_parser.add_argument(
        "--project", required=True, help="Godot project directory or project.godot path."
    )

    list_parser = subparsers.add_parser("list", help="List asset records.")
    add_manifest_argument(list_parser)
    list_parser.add_argument("--status", choices=STATUSES)

    return parser.parse_args()


def empty_manifest() -> dict[str, Any]:
    return {"schema_version": SCHEMA_VERSION, "assets": []}


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ManifestError(f"Manifest not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"Invalid JSON in {path}: {exc}") from exc
    except OSError as exc:
        raise ManifestError(f"Could not read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError("Manifest root must be a JSON object")
    return data


def write_manifest(path: Path, data: dict[str, Any], force: bool = True) -> None:
    path = path.expanduser().resolve()
    if path.exists() and not force:
        raise ManifestError(f"Manifest already exists: {path}; pass --force to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(payload)
            temp_name = handle.name
        os.replace(temp_name, path)
    except OSError as exc:
        if temp_name:
            try:
                Path(temp_name).unlink(missing_ok=True)
            except OSError:
                pass
        raise ManifestError(f"Could not write {path}: {exc}") from exc


def normalize_project_path(value: str) -> str:
    normalized = value.strip().replace("\\", "/")
    if normalized.startswith("res://"):
        normalized = normalized.removeprefix("res://")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def compact_object(values: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in values.items():
        if value is None or value is False or value == "" or value == []:
            continue
        result[key] = value
    return result


def make_asset(args: argparse.Namespace) -> dict[str, Any]:
    if not SLUG_PATTERN.fullmatch(args.id):
        raise ManifestError("--id must use lowercase kebab-case")
    if not SLUG_PATTERN.fullmatch(args.kind):
        raise ManifestError("--kind must use lowercase kebab-case")
    if args.acquired_on and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.acquired_on):
        raise ManifestError("--acquired-on must use YYYY-MM-DD")

    origin = compact_object(
        {
            "type": args.source_type,
            "url": args.source_url,
            "author": args.author,
            "license": args.license,
            "license_url": args.license_url,
            "attribution": args.attribution,
            "tool": args.tool,
            "acquired_on": args.acquired_on,
        }
    )
    files = {
        "source": [normalize_project_path(value) for value in args.source_file],
        "runtime": [normalize_project_path(value) for value in args.runtime_file],
        "scenes": [normalize_project_path(value) for value in args.scene],
    }
    return compact_object(
        {
            "id": args.id,
            "kind": args.kind,
            "status": args.status,
            "requires_scene": args.requires_scene,
            "origin": origin,
            "files": files,
            "notes": args.notes,
        }
    )


def get_assets(data: dict[str, Any]) -> list[Any]:
    assets = data.get("assets")
    if not isinstance(assets, list):
        raise ManifestError("Manifest field 'assets' must be an array")
    return assets


def project_root(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    if path.is_file():
        if path.name != "project.godot":
            raise ManifestError(f"Expected project.godot, got {path}")
        path = path.parent
    if not (path / "project.godot").is_file():
        raise ManifestError(f"project.godot not found in {path}")
    return path


def resolve_project_file(root: Path, value: str) -> Path | None:
    normalized = normalize_project_path(value)
    if not normalized or Path(normalized).is_absolute():
        return None
    candidate = (root / Path(normalized.replace("/", os.sep))).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def validate_manifest(
    data: dict[str, Any], root: Path | None = None
) -> tuple[list[str], list[str], set[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    referenced_files: set[str] = set()

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            f"schema_version must be {SCHEMA_VERSION}, got {data.get('schema_version')!r}"
        )
    assets = data.get("assets")
    if not isinstance(assets, list):
        return errors + ["assets must be an array"], warnings, referenced_files

    seen_ids: set[str] = set()
    runtime_owners: dict[str, str] = {}
    for index, asset in enumerate(assets):
        label = f"assets[{index}]"
        if not isinstance(asset, dict):
            errors.append(f"{label} must be an object")
            continue

        asset_id = asset.get("id")
        if not isinstance(asset_id, str) or not SLUG_PATTERN.fullmatch(asset_id):
            errors.append(f"{label}.id must be unique lowercase kebab-case")
            asset_id = label
        elif asset_id in seen_ids:
            errors.append(f"Duplicate asset id: {asset_id}")
        else:
            seen_ids.add(asset_id)
        label = str(asset_id)

        kind = asset.get("kind")
        if not isinstance(kind, str) or not SLUG_PATTERN.fullmatch(kind):
            errors.append(f"{label}: kind must be lowercase kebab-case")

        status = asset.get("status")
        if status not in STATUSES:
            errors.append(f"{label}: status must be one of {', '.join(STATUSES)}")
            status_index = 0
        else:
            status_index = STATUSES.index(status)

        origin = asset.get("origin")
        if not isinstance(origin, dict):
            errors.append(f"{label}: origin must be an object")
            origin = {}
        source_type = origin.get("type")
        if source_type not in SOURCE_TYPES:
            errors.append(f"{label}: origin.type must be one of {', '.join(SOURCE_TYPES)}")
        if source_type == "external":
            if status_index >= STATUSES.index("accepted"):
                if not origin.get("url"):
                    errors.append(f"{label}: accepted external asset needs origin.url")
                license_value = origin.get("license")
                if not license_value or str(license_value).lower() in {"unknown", "unverified"}:
                    errors.append(f"{label}: accepted external asset needs a verified license")
            elif not origin.get("license"):
                warnings.append(f"{label}: candidate external asset license is not recorded")
        if source_type == "generated" and not origin.get("tool"):
            errors.append(f"{label}: generated asset needs origin.tool")
        license_value = str(origin.get("license", ""))
        if ATTRIBUTION_LICENSE_PATTERN.search(license_value) and not origin.get("attribution"):
            warnings.append(f"{label}: attribution-like license has no attribution text")

        files = asset.get("files")
        if not isinstance(files, dict):
            errors.append(f"{label}: files must be an object")
            files = {}
        for group in ("source", "runtime", "scenes"):
            values = files.get(group, [])
            if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
                errors.append(f"{label}: files.{group} must be an array of paths")
                continue
            for value in values:
                normalized = normalize_project_path(value)
                referenced_files.add(normalized)
                if group == "runtime":
                    previous = runtime_owners.get(normalized)
                    if previous and previous != label:
                        warnings.append(
                            f"Runtime file {normalized} is assigned to both {previous} and {label}"
                        )
                    runtime_owners[normalized] = label
                if root is not None:
                    resolved = resolve_project_file(root, normalized)
                    if resolved is None:
                        errors.append(f"{label}: invalid project-relative path: {value}")
                    elif not resolved.exists():
                        errors.append(f"{label}: missing files.{group} path: {normalized}")

        runtime_files = files.get("runtime", []) if isinstance(files.get("runtime", []), list) else []
        scenes = files.get("scenes", []) if isinstance(files.get("scenes", []), list) else []
        if status_index >= STATUSES.index("integrated") and not runtime_files:
            errors.append(f"{label}: integrated/verified asset needs a runtime file")
        if (
            asset.get("requires_scene") is True
            and status_index >= STATUSES.index("integrated")
            and not scenes
        ):
            errors.append(f"{label}: integrated/verified scene-backed asset needs files.scenes")

    return errors, warnings, referenced_files


def command_init(args: argparse.Namespace) -> int:
    path = Path(args.manifest)
    write_manifest(path, empty_manifest(), force=args.force)
    print(f"[OK] Created manifest: {path.expanduser().resolve()}")
    return 0


def command_add(args: argparse.Namespace) -> int:
    path = Path(args.manifest).expanduser().resolve()
    data = load_manifest(path)
    assets = get_assets(data)
    asset = make_asset(args)
    if any(isinstance(existing, dict) and existing.get("id") == asset["id"] for existing in assets):
        raise ManifestError(f"Asset id already exists: {asset['id']}")
    assets.append(asset)
    errors, warnings, _ = validate_manifest(data)
    if errors:
        raise ManifestError("Record would make manifest invalid: " + "; ".join(errors))
    for warning in warnings:
        print(f"[WARN] {warning}")
    write_manifest(path, data)
    print(f"[OK] Added {asset['id']} ({asset['status']})")
    return 0


def command_set_status(args: argparse.Namespace) -> int:
    path = Path(args.manifest).expanduser().resolve()
    data = load_manifest(path)
    matches = [
        asset
        for asset in get_assets(data)
        if isinstance(asset, dict) and asset.get("id") == args.id
    ]
    if not matches:
        raise ManifestError(f"Asset id not found: {args.id}")
    asset = matches[0]
    current = asset.get("status")
    if current not in STATUSES:
        raise ManifestError(f"Asset {args.id} has invalid current status: {current!r}")
    if STATUSES.index(args.status) < STATUSES.index(current) and not args.allow_regression:
        raise ManifestError(
            f"Refusing status regression {current} -> {args.status}; pass --allow-regression"
        )
    asset["status"] = args.status
    errors, warnings, _ = validate_manifest(data)
    if errors:
        raise ManifestError("Status change would make manifest invalid: " + "; ".join(errors))
    for warning in warnings:
        print(f"[WARN] {warning}")
    write_manifest(path, data)
    print(f"[OK] {args.id}: {current} -> {args.status}")
    return 0


def print_validation(errors: list[str], warnings: list[str]) -> None:
    for warning in warnings:
        print(f"[WARN] {warning}")
    sys.stdout.flush()
    for error in errors:
        print(f"[ERROR] {error}", file=sys.stderr)


def command_validate(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest).expanduser().resolve()
    data = load_manifest(manifest_path)
    root = project_root(args.project)
    errors, warnings, _ = validate_manifest(data, root)
    print_validation(errors, warnings)
    if errors:
        print(f"[FAIL] {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 1
    print(f"[PASS] {len(get_assets(data))} asset(s), {len(warnings)} warning(s)")
    return 0


def command_list(args: argparse.Namespace) -> int:
    data = load_manifest(Path(args.manifest).expanduser().resolve())
    assets = [asset for asset in get_assets(data) if isinstance(asset, dict)]
    if args.status:
        assets = [asset for asset in assets if asset.get("status") == args.status]
    if not assets:
        print("No matching assets")
        return 0
    widths = {
        "id": max(2, max(len(str(asset.get("id", ""))) for asset in assets)),
        "kind": max(4, max(len(str(asset.get("kind", ""))) for asset in assets)),
        "status": max(6, max(len(str(asset.get("status", ""))) for asset in assets)),
    }
    print(
        f"{'ID':<{widths['id']}}  {'KIND':<{widths['kind']}}  "
        f"{'STATUS':<{widths['status']}}  SOURCE"
    )
    for asset in sorted(assets, key=lambda item: str(item.get("id", ""))):
        origin = asset.get("origin") if isinstance(asset.get("origin"), dict) else {}
        print(
            f"{str(asset.get('id', '')):<{widths['id']}}  "
            f"{str(asset.get('kind', '')):<{widths['kind']}}  "
            f"{str(asset.get('status', '')):<{widths['status']}}  "
            f"{origin.get('type', '')}"
        )
    return 0


def main() -> int:
    args = parse_args()
    try:
        if args.command == "init":
            return command_init(args)
        if args.command == "add":
            return command_add(args)
        if args.command == "set-status":
            return command_set_status(args)
        if args.command == "validate":
            return command_validate(args)
        if args.command == "list":
            return command_list(args)
    except ManifestError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
