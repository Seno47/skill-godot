#!/usr/bin/env python3
"""Audit clean-build identity, repeatability, dependencies, and credentials."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


class ContractError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit a reproducible build contract.")
    parser.add_argument("--model", required=True)
    parser.add_argument("--json-output")
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args()


def read_json(value: str) -> dict[str, Any]:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise ContractError(f"model not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"could not read model {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ContractError("model root must be an object")
    return data


def obj(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    return value


def array(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ContractError(f"{label} must be an array")
    return value


def text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value.strip()


def integer(value: Any, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContractError(f"{label} must be an integer >= {minimum}")
    return value


def boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ContractError(f"{label} must be boolean")
    return value


def strings(value: Any, label: str) -> set[str]:
    values = array(value, label)
    result = {text(item, f"{label}[{index}]") for index, item in enumerate(values)}
    if len(result) != len(values):
        raise ContractError(f"{label} contains duplicates")
    return result


def audit(model: dict[str, Any]) -> dict[str, Any]:
    if model.get("schema_version") != 1:
        raise ContractError("schema_version must be 1")
    contract_id = text(model.get("contract_id"), "contract_id")
    source_revision = text(model.get("source_revision"), "source_revision")
    contract = obj(model.get("contract"), "contract")
    engine_id = text(contract.get("engine_id"), "engine_id")
    template_hash = text(contract.get("export_template_sha256"), "export_template_sha256")
    presets = strings(contract.get("required_presets"), "required_presets")
    min_envs = integer(contract.get("minimum_clean_environments"), "minimum_clean_environments", 2)
    text(contract.get("normalization_policy"), "normalization_policy")
    if not boolean(contract.get("credentials_outside_repository"), "credentials_outside_repository"):
        raise ContractError("credentials must remain outside the repository")
    required_scenarios = strings(contract.get("required_scenarios"), "required_scenarios")
    if not presets or not required_scenarios:
        raise ContractError("required_presets and required_scenarios must not be empty")

    errors: list[str] = []
    dependency_ids: set[str] = set()
    dependencies = array(model.get("dependencies"), "dependencies")
    for index, raw in enumerate(dependencies):
        item = obj(raw, f"dependencies[{index}]")
        item_id = text(item.get("id"), f"dependencies[{index}].id")
        if item_id in dependency_ids:
            errors.append(f"duplicate dependency ID {item_id}")
        dependency_ids.add(item_id)
        text(item.get("source"), f"dependency {item_id}.source")
        text(item.get("version"), f"dependency {item_id}.version")
        license_name = text(item.get("license"), f"dependency {item_id}.license")
        if license_name.lower() in {"unknown", "tbd", "none"}:
            errors.append(f"dependency {item_id} has unresolved license")
        boolean(item.get("native"), f"dependency {item_id}.native")
        text(item.get("sha256"), f"dependency {item_id}.sha256")

    seen_ids: set[str] = set()
    seen_scenarios: set[str] = set()
    environments_by_preset: dict[str, set[str]] = {}
    hashes_by_preset: dict[str, set[str]] = {}
    smoke_by_preset: dict[str, set[str]] = {}
    builds = array(model.get("builds"), "builds")
    for index, raw in enumerate(builds):
        build = obj(raw, f"builds[{index}]")
        build_id = text(build.get("id"), f"builds[{index}].id")
        if build_id in seen_ids:
            errors.append(f"duplicate build ID {build_id}")
        seen_ids.add(build_id)
        preset = text(build.get("preset"), f"build {build_id}.preset")
        environment = text(build.get("environment"), f"build {build_id}.environment")
        scenario = text(build.get("scenario"), f"build {build_id}.scenario")
        seen_scenarios.add(scenario)
        environments_by_preset.setdefault(preset, set()).add(environment)
        if text(build.get("source_revision"), f"build {build_id}.source_revision") != source_revision:
            errors.append(f"build {build_id} uses a different source revision")
        if text(build.get("engine_id"), f"build {build_id}.engine_id") != engine_id:
            errors.append(f"build {build_id} uses a different engine")
        if text(build.get("template_sha256"), f"build {build_id}.template_sha256") != template_hash:
            errors.append(f"build {build_id} uses different export templates")
        if text(build.get("result"), f"build {build_id}.result") != "pass":
            errors.append(f"build {build_id} did not pass")
        if not boolean(build.get("clean_checkout"), f"build {build_id}.clean_checkout"):
            errors.append(f"build {build_id} is not from a clean checkout")
        normalized = text(build.get("normalized_hash"), f"build {build_id}.normalized_hash")
        smoke = text(build.get("functional_digest"), f"build {build_id}.functional_digest")
        hashes_by_preset.setdefault(preset, set()).add(normalized)
        smoke_by_preset.setdefault(preset, set()).add(smoke)
        if integer(build.get("errors"), f"build {build_id}.errors"):
            errors.append(f"build {build_id} has errors")
        if integer(build.get("warnings"), f"build {build_id}.warnings"):
            errors.append(f"build {build_id} has warnings")
        if boolean(build.get("credentials_embedded"), f"build {build_id}.credentials_embedded"):
            errors.append(f"build {build_id} embeds credentials")
        integer(build.get("output_bytes"), f"build {build_id}.output_bytes", 1)

    missing_presets = sorted(presets - set(environments_by_preset))
    if missing_presets:
        errors.append(f"missing required presets: {', '.join(missing_presets)}")
    for preset in presets:
        environments = environments_by_preset.get(preset, set())
        if len(environments) < min_envs:
            errors.append(f"preset {preset} has {len(environments)} clean environments below {min_envs}")
        if len(hashes_by_preset.get(preset, set())) > 1:
            errors.append(f"preset {preset} normalized outputs differ")
        if len(smoke_by_preset.get(preset, set())) > 1:
            errors.append(f"preset {preset} functional digests differ")
    missing_scenarios = sorted(required_scenarios - seen_scenarios)
    if missing_scenarios:
        errors.append(f"missing required scenarios: {', '.join(missing_scenarios)}")
    return {
        "status": "pass" if not errors else "fail",
        "contract_id": contract_id,
        "preset_count": len(presets),
        "build_count": len(builds),
        "dependency_count": len(dependencies),
        "errors": errors,
    }


def main() -> int:
    args = parse_args()
    try:
        report = audit(read_json(args.model))
        if args.json_output:
            output = Path(args.json_output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        marker = "PASS" if report["status"] == "pass" else "FAIL"
        print(f"[{marker}] reproducible-build id={report['contract_id']} presets={report['preset_count']} builds={report['build_count']} dependencies={report['dependency_count']} errors={len(report['errors'])}")
        for error in report["errors"]:
            print(f"[ERROR] {error}")
        return 0 if report["status"] == "pass" else 1
    except ContractError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
