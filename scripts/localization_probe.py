#!/usr/bin/env python3
"""Audit locale, plural, glyph, overflow, and runtime-switch target traces."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ALLOWED_SCENARIOS = {"menu", "dense_hud", "plural", "runtime_switch", "subtitles", "pseudolocale"}


class ContractError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit localization evidence.")
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
    items = array(value, label)
    result = {text(item, f"{label}[{index}]") for index, item in enumerate(items)}
    if len(result) != len(items):
        raise ContractError(f"{label} contains duplicates")
    return result


def audit(model: dict[str, Any]) -> dict[str, Any]:
    if model.get("schema_version") != 1:
        raise ContractError("schema_version must be 1")
    contract_id = text(model.get("contract_id"), "contract_id")
    text(model.get("build_id"), "build_id")
    contract = obj(model.get("contract"), "contract")
    locales = strings(contract.get("required_locales"), "required_locales")
    if not locales:
        raise ContractError("required_locales must not be empty")
    fallback = text(contract.get("fallback_locale"), "fallback_locale")
    if fallback not in locales:
        raise ContractError("fallback_locale must be a required locale")
    pseudolocale = text(contract.get("pseudolocale"), "pseudolocale")
    scenarios_required = strings(contract.get("required_scenarios"), "required_scenarios")
    if not scenarios_required:
        raise ContractError("required_scenarios must not be empty")
    unknown = sorted(scenarios_required - ALLOWED_SCENARIOS)
    if unknown:
        raise ContractError(f"unknown required scenarios: {', '.join(unknown)}")
    keys = strings(contract.get("required_keys"), "required_keys")
    if not keys:
        raise ContractError("required_keys must not be empty")
    plural_counts = {
        integer(value, f"required_plural_counts[{index}]")
        for index, value in enumerate(array(contract.get("required_plural_counts"), "required_plural_counts"))
    }
    max_missing = integer(contract.get("max_missing_keys"), "max_missing_keys")
    max_overflow = integer(contract.get("max_overflow_controls"), "max_overflow_controls")
    max_glyphs = integer(contract.get("max_missing_glyphs"), "max_missing_glyphs")

    errors: list[str] = []
    seen_ids: set[str] = set()
    seen_scenarios: set[str] = set()
    seen_locales: set[str] = set()
    keys_by_locale: dict[str, set[str]] = {}
    verified_plural_counts: set[int] = set()
    traces = array(model.get("traces"), "traces")
    for index, raw in enumerate(traces):
        trace = obj(raw, f"traces[{index}]")
        trace_id = text(trace.get("id"), f"traces[{index}].id")
        if trace_id in seen_ids:
            errors.append(f"duplicate trace ID {trace_id}")
        seen_ids.add(trace_id)
        locale = text(trace.get("locale"), f"trace {trace_id}.locale")
        if locale not in locales and locale != pseudolocale:
            errors.append(f"trace {trace_id} uses undeclared locale {locale}")
        scenario = text(trace.get("scenario"), f"trace {trace_id}.scenario")
        seen_locales.add(locale)
        seen_scenarios.add(scenario)
        if scenario not in ALLOWED_SCENARIOS:
            errors.append(f"trace {trace_id} has unknown scenario {scenario}")
        if text(trace.get("source"), f"trace {trace_id}.source") != "target_build":
            errors.append(f"trace {trace_id} is not target-build evidence")
        if text(trace.get("result"), f"trace {trace_id}.result") != "pass":
            errors.append(f"trace {trace_id} did not pass")
        resolved = strings(trace.get("keys_resolved"), f"trace {trace_id}.keys_resolved")
        keys_by_locale.setdefault(locale, set()).update(resolved)
        if integer(trace.get("missing_keys"), f"trace {trace_id}.missing_keys") > max_missing:
            errors.append(f"trace {trace_id} exceeds missing-key budget")
        if integer(trace.get("overflow_controls"), f"trace {trace_id}.overflow_controls") > max_overflow:
            errors.append(f"trace {trace_id} exceeds overflow budget")
        if integer(trace.get("missing_glyphs"), f"trace {trace_id}.missing_glyphs") > max_glyphs:
            errors.append(f"trace {trace_id} exceeds missing-glyph budget")
        for field, message in (
            ("placeholders_preserved", "breaks placeholders"),
            ("focus_path_valid", "breaks focus/navigation"),
            ("directional_semantics_valid", "breaks directional semantics"),
        ):
            if not boolean(trace.get(field), f"trace {trace_id}.{field}"):
                errors.append(f"trace {trace_id} {message}")
        if scenario == "plural":
            verified_plural_counts.update(
                integer(value, f"trace {trace_id}.plural_counts_verified[{position}]")
                for position, value in enumerate(
                    array(trace.get("plural_counts_verified"), f"trace {trace_id}.plural_counts_verified")
                )
            )
        elif scenario == "runtime_switch":
            if not boolean(trace.get("locale_switch_applied"), f"trace {trace_id}.locale_switch_applied"):
                errors.append(f"trace {trace_id} does not apply locale switch")
            if not boolean(trace.get("cached_text_invalidated"), f"trace {trace_id}.cached_text_invalidated"):
                errors.append(f"trace {trace_id} leaves stale cached text")
        elif scenario == "subtitles" and not boolean(
            trace.get("speaker_and_timing_valid"), f"trace {trace_id}.speaker_and_timing_valid"
        ):
            errors.append(f"trace {trace_id} has invalid subtitle speaker/timing")
        elif scenario == "pseudolocale" and locale != pseudolocale:
            errors.append(f"trace {trace_id} does not use declared pseudolocale")

    missing_scenarios = sorted(scenarios_required - seen_scenarios)
    if missing_scenarios:
        errors.append(f"missing required scenarios: {', '.join(missing_scenarios)}")
    missing_locales = sorted(locales - seen_locales)
    if missing_locales:
        errors.append(f"missing required locales: {', '.join(missing_locales)}")
    for locale in locales:
        missing_keys = sorted(keys - keys_by_locale.get(locale, set()))
        if missing_keys:
            errors.append(f"locale {locale} misses keys: {', '.join(missing_keys)}")
    missing_plural = sorted(plural_counts - verified_plural_counts)
    if missing_plural:
        errors.append("missing plural counts: " + ", ".join(map(str, missing_plural)))
    return {
        "status": "pass" if not errors else "fail",
        "contract_id": contract_id,
        "locale_count": len(locales),
        "trace_count": len(traces),
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
        print(f"[{marker}] localization id={report['contract_id']} locales={report['locale_count']} traces={report['trace_count']} errors={len(report['errors'])}")
        for error in report["errors"]:
            print(f"[ERROR] {error}")
        return 0 if report["status"] == "pass" else 1
    except ContractError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
