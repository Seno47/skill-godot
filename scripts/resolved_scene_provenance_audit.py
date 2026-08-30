#!/usr/bin/env python3
"""Audit deterministic dependency-closure provenance for resolved Godot scenes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


class ProvenanceError(RuntimeError):
    pass


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_TOOL_ROLES = {"exporter_script", "export_presets", "project_settings"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit a Godot resolved-scene dependency manifest and recompute its canonical "
            "dependency-closure digest."
        )
    )
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--baseline")
    parser.add_argument(
        "--evidence-contract",
        action="append",
        default=[],
        help="Environment evidence contract whose provenance reference must match this manifest.",
    )
    parser.add_argument(
        "--project",
        help="Optional project root used to verify every declared res:// file and SHA-256.",
    )
    parser.add_argument("--json-output")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--print-computed-digest", action="store_true")
    return parser.parse_args()


def read_json(value: str) -> dict[str, Any]:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise ProvenanceError(f"manifest not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProvenanceError(f"could not read manifest {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ProvenanceError("manifest root must be an object")
    return data


def obj(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProvenanceError(f"{label} must be an object")
    return value


def array(value: Any, label: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list) or (nonempty and not value):
        suffix = " and not be empty" if nonempty else ""
        raise ProvenanceError(f"{label} must be an array{suffix}")
    return value


def text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProvenanceError(f"{label} must be a non-empty string")
    result = value.strip()
    if any(character in result for character in "\t\r\n"):
        raise ProvenanceError(f"{label} must not contain tabs or newlines")
    return result


def integer(value: Any, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ProvenanceError(f"{label} must be an integer >= {minimum}")
    return value


def sha256(value: Any, label: str) -> str:
    result = text(value, label).lower()
    if not SHA256_RE.fullmatch(result):
        raise ProvenanceError(f"{label} must be a lowercase 64-character SHA-256")
    return result


def resource_path(value: Any, label: str) -> str:
    result = text(value, label)
    if not result.startswith("res://"):
        raise ProvenanceError(f"{label} must be a canonical res:// path")
    if "\\" in result or "/../" in result or result.endswith("/..") or "//" in result[6:]:
        raise ProvenanceError(f"{label} is not canonical: {result}")
    return result


def string_paths(value: Any, label: str) -> list[str]:
    paths = [resource_path(item, f"{label}[{index}]") for index, item in enumerate(array(value, label))]
    if paths != sorted(paths):
        raise ProvenanceError(f"{label} must be sorted by canonical path")
    if len(paths) != len(set(paths)):
        raise ProvenanceError(f"{label} must not contain duplicates")
    return paths


def canonical_lines(manifest: dict[str, Any]) -> list[str]:
    entries = sorted(manifest["entries"], key=lambda item: item["path"])
    tools = sorted(manifest["toolchain_inputs"], key=lambda item: (item["role"], item["path"]))
    lines = [
        "skill-godot-resolved-scene-closure-v1",
        f"source_kind\t{manifest['source_kind']}",
        f"root_scene\t{manifest['root_scene']}",
        f"engine_version\t{manifest['engine_version']}",
        f"export_preset_selector\t{manifest['export_preset_selector']}",
    ]
    lines.extend(
        f"entry\t{item['path']}\t{item['kind']}\t{item['bytes']}\t{item['sha256']}"
        for item in entries
    )
    lines.extend(
        f"tool\t{item['role']}\t{item['path']}\t{item['bytes']}\t{item['sha256']}"
        for item in tools
    )
    return lines


def compute_closure_digest(manifest: dict[str, Any]) -> str:
    payload = "\n".join(canonical_lines(manifest)) + "\n"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_scene_provenance_reference(value: Any, label: str = "scene_provenance") -> dict[str, str]:
    provenance = obj(value, label)
    if text(provenance.get("source_kind"), f"{label}.source_kind") != "resolved_target_scene":
        raise ProvenanceError(f"{label}.source_kind must be resolved_target_scene")
    scene_path = resource_path(provenance.get("scene_path"), f"{label}.scene_path")
    if "scene_revision" in provenance and "dependency_closure_digest" not in provenance:
        raise ProvenanceError(
            f"{label} supplies only scene_revision/root-file provenance; "
            "resolved_target_scene requires a dependency-closure digest"
        )
    if text(provenance.get("revision_kind"), f"{label}.revision_kind") != "resolved_dependency_closure_sha256":
        raise ProvenanceError(
            f"{label}.revision_kind must be resolved_dependency_closure_sha256"
        )
    result = {
        "source_kind": "resolved_target_scene",
        "scene_path": scene_path,
        "revision_kind": "resolved_dependency_closure_sha256",
        "dependency_closure_digest": sha256(
            provenance.get("dependency_closure_digest"),
            f"{label}.dependency_closure_digest",
        ),
        "manifest_path": text(provenance.get("manifest_path"), f"{label}.manifest_path"),
        "manifest_sha256": sha256(
            provenance.get("manifest_sha256"), f"{label}.manifest_sha256"
        ),
        "exporter": resource_path(provenance.get("exporter"), f"{label}.exporter"),
        "exporter_sha256": sha256(
            provenance.get("exporter_sha256"), f"{label}.exporter_sha256"
        ),
        "export_preset": text(
            provenance.get("export_preset"), f"{label}.export_preset"
        ),
        "export_preset_sha256": sha256(
            provenance.get("export_preset_sha256"), f"{label}.export_preset_sha256"
        ),
    }
    return result


def parse_manifest(data: dict[str, Any], *, project: Path | None = None) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    if data.get("schema_version") != 1:
        raise ProvenanceError("schema_version must be 1")
    manifest_id = text(data.get("manifest_id"), "manifest_id")
    build_id = text(data.get("build_id"), "build_id")
    source_kind = text(data.get("source_kind"), "source_kind")
    if source_kind != "resolved_target_scene":
        raise ProvenanceError("source_kind must be resolved_target_scene")
    root_scene = resource_path(data.get("root_scene"), "root_scene")
    engine_version = text(data.get("engine_version"), "engine_version")
    export_preset_selector = text(
        data.get("export_preset_selector"), "export_preset_selector"
    )

    discovery = obj(data.get("dependency_discovery"), "dependency_discovery")
    if text(discovery.get("method"), "dependency_discovery.method") != "godot_resource_loader_recursive":
        raise ProvenanceError(
            "dependency_discovery.method must be godot_resource_loader_recursive"
        )
    direct = string_paths(discovery.get("direct_dependencies"), "dependency_discovery.direct_dependencies")
    recursive = string_paths(
        discovery.get("recursive_dependencies"), "dependency_discovery.recursive_dependencies"
    )
    runtime = string_paths(
        discovery.get("runtime_dependency_paths"), "dependency_discovery.runtime_dependency_paths"
    )
    if not set(direct) <= set(recursive):
        errors.append("direct_dependencies contains paths absent from recursive_dependencies")
    if root_scene in set(recursive) | set(runtime):
        errors.append("root_scene must not be repeated in dependency lists")
    declared_dependency_count = integer(
        discovery.get("declared_dependency_count"),
        "dependency_discovery.declared_dependency_count",
    )
    discovered = sorted(set(recursive) | set(runtime))
    if declared_dependency_count != len(discovered):
        errors.append(
            "declared_dependency_count does not match recursive plus runtime dependency closure"
        )

    entries: list[dict[str, Any]] = []
    entry_paths: list[str] = []
    for index, raw in enumerate(array(data.get("entries"), "entries", nonempty=True)):
        item = obj(raw, f"entries[{index}]")
        path = resource_path(item.get("path"), f"entries[{index}].path")
        entry = {
            "path": path,
            "kind": text(item.get("kind"), f"entries[{index}].kind"),
            "bytes": integer(item.get("bytes"), f"entries[{index}].bytes", 1),
            "sha256": sha256(item.get("sha256"), f"entries[{index}].sha256"),
        }
        entries.append(entry)
        entry_paths.append(path)
    if entry_paths != sorted(entry_paths):
        errors.append("entries must be sorted by canonical path")
    if len(entry_paths) != len(set(entry_paths)):
        errors.append("entries contain duplicate paths")
    expected_paths = sorted({root_scene, *discovered})
    if entry_paths != expected_paths:
        missing = sorted(set(expected_paths) - set(entry_paths))
        extra = sorted(set(entry_paths) - set(expected_paths))
        if missing:
            errors.append(f"dependency closure entries are missing: {', '.join(missing)}")
        if extra:
            errors.append(f"dependency closure entries were not discovered: {', '.join(extra)}")
    if (direct or recursive or runtime) and entry_paths == [root_scene]:
        errors.append(
            "root-file-only digest is invalid because the resolved scene declares dependencies"
        )
    root_entries = [item for item in entries if item["path"] == root_scene]
    if len(root_entries) != 1 or root_entries[0]["kind"] != "root_scene":
        errors.append("entries must contain root_scene exactly once with kind=root_scene")

    tools: list[dict[str, Any]] = []
    roles: list[str] = []
    for index, raw in enumerate(array(data.get("toolchain_inputs"), "toolchain_inputs", nonempty=True)):
        item = obj(raw, f"toolchain_inputs[{index}]")
        role = text(item.get("role"), f"toolchain_inputs[{index}].role")
        tool = {
            "role": role,
            "path": resource_path(item.get("path"), f"toolchain_inputs[{index}].path"),
            "bytes": integer(item.get("bytes"), f"toolchain_inputs[{index}].bytes", 1),
            "sha256": sha256(item.get("sha256"), f"toolchain_inputs[{index}].sha256"),
        }
        tools.append(tool)
        roles.append(role)
    if [(item["role"], item["path"]) for item in tools] != sorted(
        (item["role"], item["path"]) for item in tools
    ):
        errors.append("toolchain_inputs must be sorted by role then canonical path")
    if len(roles) != len(set(roles)):
        errors.append("toolchain_inputs contains duplicate roles")
    missing_roles = sorted(REQUIRED_TOOL_ROLES - set(roles))
    if missing_roles:
        errors.append(f"toolchain_inputs is missing required roles: {', '.join(missing_roles)}")

    normalized = {
        "schema_version": 1,
        "manifest_id": manifest_id,
        "build_id": build_id,
        "source_kind": source_kind,
        "root_scene": root_scene,
        "engine_version": engine_version,
        "export_preset_selector": export_preset_selector,
        "entries": entries,
        "toolchain_inputs": tools,
    }
    computed = compute_closure_digest(normalized)
    declared = sha256(data.get("closure_digest"), "closure_digest")
    if computed != declared:
        errors.append(
            f"closure_digest mismatch: declared {declared}, computed {computed}"
        )

    verified_count = 0
    if project is not None:
        project = project.expanduser().resolve()
        if not (project / "project.godot").is_file():
            raise ProvenanceError(f"project root lacks project.godot: {project}")
        for item in entries + tools:
            relative = item["path"][6:]
            candidate = (project / relative).resolve()
            try:
                candidate.relative_to(project)
            except ValueError:
                errors.append(f"declared path escapes project root: {item['path']}")
                continue
            if not candidate.is_file():
                errors.append(f"declared provenance file is missing: {item['path']}")
                continue
            actual_bytes = candidate.stat().st_size
            actual_hash = hashlib.sha256(candidate.read_bytes()).hexdigest()
            if actual_bytes != item["bytes"]:
                errors.append(
                    f"file size mismatch for {item['path']}: declared {item['bytes']}, actual {actual_bytes}"
                )
            if actual_hash != item["sha256"]:
                errors.append(
                    f"file SHA-256 mismatch for {item['path']}: declared {item['sha256']}, actual {actual_hash}"
                )
            if actual_bytes == item["bytes"] and actual_hash == item["sha256"]:
                verified_count += 1

    report = {
        "status": "pass" if not errors else "fail",
        "manifest_id": manifest_id,
        "build_id": build_id,
        "source_kind": source_kind,
        "root_scene": root_scene,
        "root_scene_sha256": root_entries[0]["sha256"] if root_entries else None,
        "export_preset_selector": export_preset_selector,
        "dependency_count": len(discovered),
        "entry_count": len(entries),
        "toolchain_input_count": len(tools),
        "declared_closure_digest": declared,
        "computed_closure_digest": computed,
        "filesystem_verification_requested": project is not None,
        "filesystem_verified_file_count": verified_count,
        "toolchain_inputs": tools,
        "errors": errors,
    }
    return report, canonical_lines(normalized)


def validate_evidence_contract(
    value: str,
    report: dict[str, Any],
    manifest_sha256: str,
) -> list[str]:
    contract = read_json(value)
    label = Path(value).name
    errors: list[str] = []
    if contract.get("build_id") != report["build_id"]:
        errors.append(f"{label} build_id does not match provenance manifest")
    try:
        reference = validate_scene_provenance_reference(contract.get("scene_provenance"))
    except ProvenanceError as exc:
        return [f"{label}: {exc}"]
    expected = {
        "scene_path": report["root_scene"],
        "dependency_closure_digest": report["computed_closure_digest"],
        "manifest_sha256": manifest_sha256,
        "export_preset": report["export_preset_selector"],
    }
    for key, expected_value in expected.items():
        if reference[key] != expected_value:
            errors.append(f"{label} {key} does not match provenance manifest")
    preset_tools = [
        item for item in report["toolchain_inputs"] if item["role"] == "export_presets"
    ]
    if not preset_tools or preset_tools[0]["sha256"] != reference["export_preset_sha256"]:
        errors.append(f"{label} export_preset_sha256 is absent from manifest toolchain inputs")
    exporters = [
        item
        for item in report["toolchain_inputs"]
        if item["path"] == reference["exporter"]
        and item["sha256"] == reference["exporter_sha256"]
    ]
    if not exporters:
        errors.append(f"{label} exporter path/hash is absent from manifest toolchain inputs")
    return errors


def compare_reports(baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    root_same = baseline.get("root_scene_sha256") == candidate.get("root_scene_sha256")
    closure_same = baseline.get("computed_closure_digest") == candidate.get("computed_closure_digest")
    return {
        "baseline_manifest_id": baseline.get("manifest_id"),
        "root_scene_sha256_same": root_same,
        "dependency_closure_digest_same": closure_same,
        "candidate_content_changed_beyond_root": root_same and not closure_same,
    }


def main() -> int:
    args = parse_args()
    try:
        project = Path(args.project) if args.project else None
        manifest_path = Path(args.manifest).expanduser().resolve()
        report, _ = parse_manifest(read_json(args.manifest), project=project)
        manifest_sha256 = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        report["manifest_sha256"] = manifest_sha256
        report["evidence_contract_count"] = len(args.evidence_contract)
        for contract_path in args.evidence_contract:
            report["errors"].extend(
                validate_evidence_contract(contract_path, report, manifest_sha256)
            )
        if report["errors"]:
            report["status"] = "fail"
        if args.baseline:
            baseline, _ = parse_manifest(read_json(args.baseline), project=None)
            report["baseline_comparison"] = compare_reports(baseline, report)
            if baseline["status"] != "pass":
                report["errors"].append("baseline provenance manifest does not pass")
                report["status"] = "fail"
        if args.print_computed_digest:
            print(report["computed_closure_digest"])
        if args.json_output:
            output = Path(args.json_output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if args.summary:
            print(
                f"[{'PASS' if report['status'] == 'pass' else 'FAIL'}] resolved-scene-provenance "
                f"dependencies={report['dependency_count']} entries={report['entry_count']} "
                f"tools={report['toolchain_input_count']} errors={len(report['errors'])}"
            )
            for message in report["errors"]:
                print(f"[ERROR] {message}")
        return 0 if report["status"] == "pass" else 1
    except ProvenanceError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
