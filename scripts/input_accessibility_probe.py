#!/usr/bin/env python3
"""Audit input-device, remapping, local-player, and accessibility traces."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ALLOWED_SCENARIOS = {
    "clean_first_use",
    "remap",
    "conflict_recovery",
    "persistence",
    "hotplug",
    "modality_switch",
    "local_join_leave",
    "focus_reentry",
    "accessibility_effect",
    "touch_layout",
}


class ContractError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit input and accessibility evidence.")
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
    text(model.get("build_id"), "build_id")
    contract = obj(model.get("contract"), "contract")
    required_devices = strings(contract.get("required_devices"), "required_devices")
    required_scenarios = strings(contract.get("required_scenarios"), "required_scenarios")
    unknown = sorted(required_scenarios - ALLOWED_SCENARIOS)
    if unknown:
        raise ContractError(f"unknown required scenarios: {', '.join(unknown)}")
    critical_actions = strings(contract.get("critical_actions"), "critical_actions")
    maximum_players = integer(contract.get("maximum_local_players"), "maximum_local_players", 1)
    minimum_touch_target = integer(
        contract.get("minimum_touch_target_px"), "minimum_touch_target_px", 1
    )
    required_features = strings(
        contract.get("required_accessibility_features"),
        "required_accessibility_features",
    )
    emergency_actions = strings(
        contract.get("emergency_navigation_actions"),
        "emergency_navigation_actions",
    )
    if not emergency_actions <= critical_actions:
        raise ContractError("emergency navigation actions must be critical actions")

    errors: list[str] = []
    bindings = array(contract.get("bindings"), "bindings")
    binding_actions: set[str] = set()
    devices_by_action: dict[str, set[str]] = {}
    for index, raw in enumerate(bindings):
        binding = obj(raw, f"bindings[{index}]")
        action = text(binding.get("action"), f"bindings[{index}].action")
        if action in binding_actions:
            errors.append(f"duplicate binding contract for action {action}")
        binding_actions.add(action)
        devices = strings(binding.get("devices"), f"binding {action}.devices")
        devices_by_action[action] = devices
        if action in critical_actions:
            if not boolean(binding.get("critical"), f"binding {action}.critical"):
                errors.append(f"critical action {action} is not marked critical")
            if not boolean(binding.get("rebindable"), f"binding {action}.rebindable"):
                errors.append(f"critical action {action} is not rebindable")
            missing_devices = sorted(required_devices - devices)
            if missing_devices:
                errors.append(
                    f"critical action {action} misses devices: {', '.join(missing_devices)}"
                )
    missing_bindings = sorted(critical_actions - binding_actions)
    if missing_bindings:
        errors.append(f"missing critical action bindings: {', '.join(missing_bindings)}")

    traces = array(model.get("traces"), "traces")
    if not traces:
        raise ContractError("traces must not be empty")
    seen_ids: set[str] = set()
    scenarios: set[str] = set()
    devices: set[str] = set()
    actions_by_device: dict[str, set[str]] = {}
    verified_features: set[str] = set()
    for index, raw in enumerate(traces):
        trace = obj(raw, f"traces[{index}]")
        trace_id = text(trace.get("id"), f"traces[{index}].id")
        if trace_id in seen_ids:
            errors.append(f"duplicate trace ID {trace_id}")
        seen_ids.add(trace_id)
        scenario = text(trace.get("scenario"), f"trace {trace_id}.scenario")
        device = text(trace.get("device"), f"trace {trace_id}.device")
        scenarios.add(scenario)
        devices.add(device)
        if scenario not in ALLOWED_SCENARIOS:
            errors.append(f"trace {trace_id} has unknown scenario {scenario}")
        if text(trace.get("source"), f"trace {trace_id}.source") != "target_build":
            errors.append(f"trace {trace_id} is not target-build evidence")
        if text(trace.get("result"), f"trace {trace_id}.result") != "pass":
            errors.append(f"trace {trace_id} did not pass")
        actions = strings(trace.get("actions_reached"), f"trace {trace_id}.actions_reached")
        actions_by_device.setdefault(device, set()).update(actions)
        text(trace.get("glyph_family"), f"trace {trace_id}.glyph_family")
        if not boolean(trace.get("focus_path_valid"), f"trace {trace_id}.focus_path_valid"):
            errors.append(f"trace {trace_id} has a broken focus/navigation path")
        duplicates = integer(
            trace.get("duplicate_input_events"), f"trace {trace_id}.duplicate_input_events"
        )
        if duplicates:
            errors.append(f"trace {trace_id} duplicates {duplicates} input events")

        if scenario == "remap":
            action = text(trace.get("remapped_action"), f"trace {trace_id}.remapped_action")
            if action not in critical_actions:
                errors.append(f"trace {trace_id} does not remap a critical action")
            if not boolean(trace.get("remap_effective"), f"trace {trace_id}.remap_effective"):
                errors.append(f"trace {trace_id} remap is ineffective")
        elif scenario == "conflict_recovery":
            if integer(
                trace.get("binding_conflicts_unresolved"),
                f"trace {trace_id}.binding_conflicts_unresolved",
            ):
                errors.append(f"trace {trace_id} leaves unresolved binding conflicts")
            if not boolean(
                trace.get("emergency_navigation_reachable"),
                f"trace {trace_id}.emergency_navigation_reachable",
            ):
                errors.append(f"trace {trace_id} strands emergency menu navigation")
        elif scenario == "persistence":
            if not boolean(trace.get("settings_persisted"), f"trace {trace_id}.settings_persisted"):
                errors.append(f"trace {trace_id} does not persist input settings")
            if not boolean(trace.get("remap_effective"), f"trace {trace_id}.remap_effective"):
                errors.append(f"trace {trace_id} loses remap after reload")
        elif scenario == "hotplug":
            if not boolean(
                trace.get("disconnect_state_explained"),
                f"trace {trace_id}.disconnect_state_explained",
            ):
                errors.append(f"trace {trace_id} has no disconnect explanation")
            if not boolean(
                trace.get("reconnect_restored_owner"),
                f"trace {trace_id}.reconnect_restored_owner",
            ):
                errors.append(f"trace {trace_id} does not restore device ownership")
        elif scenario == "modality_switch":
            if not boolean(
                trace.get("glyph_matches_last_device"),
                f"trace {trace_id}.glyph_matches_last_device",
            ):
                errors.append(f"trace {trace_id} shows stale/false input glyphs")
        elif scenario == "local_join_leave":
            players = integer(trace.get("local_players"), f"trace {trace_id}.local_players", 1)
            owners = integer(
                trace.get("unique_device_owners"), f"trace {trace_id}.unique_device_owners", 1
            )
            if maximum_players > 1 and players < maximum_players:
                errors.append(f"trace {trace_id} tests {players} players below {maximum_players}")
            if owners != players:
                errors.append(f"trace {trace_id} does not uniquely own each player device")
            if integer(trace.get("cross_player_actions"), f"trace {trace_id}.cross_player_actions"):
                errors.append(f"trace {trace_id} leaks actions across players")
            if not boolean(
                trace.get("join_leave_recovered"), f"trace {trace_id}.join_leave_recovered"
            ):
                errors.append(f"trace {trace_id} does not recover join/leave")
        elif scenario == "focus_reentry":
            if boolean(
                trace.get("input_advanced_while_unfocused"),
                f"trace {trace_id}.input_advanced_while_unfocused",
            ):
                errors.append(f"trace {trace_id} advances while unfocused")
            if not boolean(trace.get("focus_recovered"), f"trace {trace_id}.focus_recovered"):
                errors.append(f"trace {trace_id} does not recover focus")
        elif scenario == "accessibility_effect":
            verified_features.update(
                strings(trace.get("features_verified"), f"trace {trace_id}.features_verified")
            )
            if not boolean(trace.get("settings_persisted"), f"trace {trace_id}.settings_persisted"):
                errors.append(f"trace {trace_id} does not persist accessibility settings")
            if not boolean(
                trace.get("critical_meaning_preserved"),
                f"trace {trace_id}.critical_meaning_preserved",
            ):
                errors.append(f"trace {trace_id} loses critical meaning under accessibility mode")
        elif scenario == "touch_layout":
            target = integer(
                trace.get("minimum_touch_target_px"),
                f"trace {trace_id}.minimum_touch_target_px",
                1,
            )
            if target < minimum_touch_target:
                errors.append(f"trace {trace_id} touch target {target}px below {minimum_touch_target}px")

    missing_scenarios = sorted(required_scenarios - scenarios)
    missing_devices = sorted(required_devices - devices)
    if missing_scenarios:
        errors.append(f"missing required scenarios: {', '.join(missing_scenarios)}")
    if missing_devices:
        errors.append(f"missing required devices: {', '.join(missing_devices)}")
    for device in required_devices:
        missing_actions = sorted(critical_actions - actions_by_device.get(device, set()))
        if missing_actions:
            errors.append(f"device {device} misses actions: {', '.join(missing_actions)}")
    missing_features = sorted(required_features - verified_features)
    if missing_features:
        errors.append(f"unverified accessibility features: {', '.join(missing_features)}")
    if "touch" in required_devices and "touch_layout" not in scenarios:
        errors.append("touch is required without touch_layout evidence")

    return {
        "status": "pass" if not errors else "fail",
        "contract_id": contract_id,
        "trace_count": len(traces),
        "device_count": len(devices),
        "verified_accessibility_features": sorted(verified_features),
        "errors": errors,
    }


def main() -> int:
    args = parse_args()
    try:
        report = audit(read_json(args.model))
        if args.json_output:
            path = Path(args.json_output).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        marker = "PASS" if report["status"] == "pass" else "FAIL"
        print(
            f"[{marker}] input-accessibility id={report['contract_id']} "
            f"devices={report['device_count']} traces={report['trace_count']} "
            f"errors={len(report['errors'])}"
        )
        for error in report["errors"]:
            print(f"[ERROR] {error}")
        if not args.summary and not report["errors"]:
            print(json.dumps(report, indent=2))
        return 0 if report["status"] == "pass" else 1
    except ContractError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"[ERROR] output failure: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
