#!/usr/bin/env python3
"""Audit an extraction game's raid settlement and risk/recovery traces."""

from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
from typing import Any


ALLOWED_CHECKS = {
    "ledger_conservation",
    "death_loss",
    "settlement_idempotence",
    "recovery_path",
    "route_coverage",
    "risk_reward_gradient",
}


class ExtractionError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit extraction raid settlement, loss, route, and recovery evidence."
    )
    parser.add_argument("--model", required=True, help="Extraction loop JSON model.")
    parser.add_argument("--json-output", help="Optional JSON report path.")
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args()


def obj(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ExtractionError(f"{label} must be an object")
    return value


def text_value(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ExtractionError(f"{label} must be a non-empty string")
    return value.strip()


def text_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise ExtractionError(f"{label} must be a non-empty string array")
    if len(value) != len(set(value)):
        raise ExtractionError(f"{label} must not contain duplicates")
    return value


def decimal_value(value: Any, label: str, *, minimum: Decimal = Decimal(0)) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ExtractionError(f"{label} must be a decimal string or number")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ExtractionError(f"{label} is not a decimal") from exc
    if not result.is_finite() or result < minimum:
        raise ExtractionError(f"{label} must be finite and >= {minimum}")
    return result


def int_value(value: Any, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ExtractionError(f"{label} must be an integer >= {minimum}")
    return value


def bool_value(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ExtractionError(f"{label} must be a boolean")
    return value


def main() -> int:
    args = parse_args()
    model_path = Path(args.model).expanduser().resolve()
    try:
        if not model_path.is_file():
            raise ExtractionError(f"model not found: {model_path}")
        model = json.loads(model_path.read_text(encoding="utf-8-sig"))
        if not isinstance(model, dict) or model.get("schema_version") != 1:
            raise ExtractionError("model root must be an object with schema_version 1")
        contract_id = text_value(model.get("contract_id"), "contract_id")
        build_id = text_value(model.get("build_id"), "build_id")
        contract = obj(model.get("contract"), "contract")
        text_value(contract.get("online_scope"), "contract.online_scope")
        text_value(contract.get("secure_container_policy"), "contract.secure_container_policy")
        required_archetypes = text_list(
            contract.get("required_archetypes"), "contract.required_archetypes"
        )
        required_scenarios = text_list(
            contract.get("required_scenarios"), "contract.required_scenarios"
        )
        required_routes = text_list(contract.get("required_routes"), "contract.required_routes")
        required_checks = set(text_list(contract.get("required_checks"), "contract.required_checks"))
        unknown_checks = sorted(required_checks - ALLOWED_CHECKS)
        if unknown_checks:
            raise ExtractionError(f"unknown required checks: {', '.join(unknown_checks)}")
        allow_negative_stash = bool_value(
            contract.get("allow_negative_stash"), "contract.allow_negative_stash"
        )
        recovery_floor = decimal_value(
            contract.get("recovery_floor_value"), "contract.recovery_floor_value"
        )
        max_recovery_runs = int_value(
            contract.get("max_recovery_runs"), "contract.max_recovery_runs"
        )
        minimum_window = decimal_value(
            contract.get("minimum_extraction_window_seconds"),
            "contract.minimum_extraction_window_seconds",
        )
        max_route_share = decimal_value(
            contract.get("max_single_route_success_share"),
            "contract.max_single_route_success_share",
            minimum=Decimal("0.000001"),
        )
        if max_route_share > 1:
            raise ExtractionError("max_single_route_success_share must be <= 1")

        routes_raw = model.get("routes")
        if not isinstance(routes_raw, list) or not routes_raw:
            raise ExtractionError("routes must be a non-empty array")
        routes: dict[str, dict[str, Decimal]] = {}
        for index, raw in enumerate(routes_raw):
            route = obj(raw, f"routes[{index}]")
            route_id = text_value(route.get("id"), f"routes[{index}].id")
            if route_id in routes:
                raise ExtractionError(f"duplicate route ID: {route_id}")
            minimum_loot = decimal_value(
                route.get("minimum_loot_value"), f"route {route_id}.minimum_loot_value"
            )
            maximum_loot = decimal_value(
                route.get("maximum_loot_value"), f"route {route_id}.maximum_loot_value"
            )
            expected_loot = decimal_value(
                route.get("expected_loot_value"), f"route {route_id}.expected_loot_value"
            )
            if not minimum_loot <= expected_loot <= maximum_loot:
                raise ExtractionError(
                    f"route {route_id} must satisfy minimum <= expected <= maximum loot"
                )
            routes[route_id] = {
                "risk": decimal_value(route.get("risk_score"), f"route {route_id}.risk_score"),
                "minimum": minimum_loot,
                "maximum": maximum_loot,
                "expected": expected_loot,
            }

        errors: list[str] = []
        missing_route_definitions = sorted(set(required_routes) - set(routes))
        if missing_route_definitions:
            errors.append(f"required routes lack definitions: {', '.join(missing_route_definitions)}")
        if "risk_reward_gradient" in required_checks:
            ordered = sorted(routes.items(), key=lambda item: item[1]["risk"])
            for previous, current in zip(ordered, ordered[1:]):
                if current[1]["risk"] > previous[1]["risk"] and current[1]["expected"] < previous[1]["expected"]:
                    errors.append(
                        f"higher-risk route {current[0]} has lower expected loot than {previous[0]}"
                    )

        traces_raw = model.get("traces")
        if not isinstance(traces_raw, list) or not traces_raw:
            raise ExtractionError("traces must be a non-empty array")
        trace_ids: set[str] = set()
        settlement_ids: set[str] = set()
        seen_archetypes: set[str] = set()
        seen_scenarios: set[str] = set()
        seen_routes: set[str] = set()
        successful_routes: Counter[str] = Counter()
        maximum_ledger_delta = Decimal(0)

        for index, raw in enumerate(traces_raw):
            trace = obj(raw, f"traces[{index}]")
            trace_id = text_value(trace.get("id"), f"traces[{index}].id")
            if trace_id in trace_ids:
                raise ExtractionError(f"duplicate trace ID: {trace_id}")
            trace_ids.add(trace_id)
            text_value(trace.get("source"), f"trace {trace_id}.source")
            text_value(trace.get("profile_id"), f"trace {trace_id}.profile_id")
            text_value(trace.get("raid_id"), f"trace {trace_id}.raid_id")
            settlement_id = text_value(
                trace.get("settlement_id"), f"trace {trace_id}.settlement_id"
            )
            if settlement_id in settlement_ids:
                errors.append(f"settlement ID {settlement_id} is reused across traces")
            settlement_ids.add(settlement_id)
            archetype = text_value(trace.get("archetype"), f"trace {trace_id}.archetype")
            scenario = text_value(trace.get("scenario"), f"trace {trace_id}.scenario")
            outcome = text_value(trace.get("outcome"), f"trace {trace_id}.outcome")
            route_id = text_value(trace.get("route"), f"trace {trace_id}.route")
            seen_archetypes.add(archetype)
            seen_scenarios.add(scenario)
            seen_routes.add(route_id)
            if route_id not in routes:
                errors.append(f"trace {trace_id} uses unknown route {route_id}")

            values = {
                key: decimal_value(trace.get(key), f"trace {trace_id}.{key}")
                for key in (
                    "stash_before",
                    "entry_debits",
                    "gear_committed_value",
                    "gear_returned_value",
                    "loot_found_value",
                    "secure_capacity_value",
                    "persisted_loot_value",
                    "insurance_return_value",
                    "other_credits",
                    "settlement_fees",
                    "stash_after",
                    "extraction_window_seconds",
                )
            }
            if values["gear_returned_value"] > values["gear_committed_value"]:
                errors.append(f"trace {trace_id} returns more gear value than was committed")
            lost_gear = values["gear_committed_value"] - values["gear_returned_value"]
            if values["insurance_return_value"] > lost_gear:
                errors.append(f"trace {trace_id} insurance exceeds lost gear value")
            if values["persisted_loot_value"] > values["loot_found_value"]:
                errors.append(f"trace {trace_id} persists more loot than was found")
            if outcome == "died":
                if values["persisted_loot_value"] > values["secure_capacity_value"]:
                    errors.append(f"trace {trace_id} death persists loot beyond secure capacity")
            elif outcome == "extracted":
                successful_routes[route_id] += 1
                if values["extraction_window_seconds"] < minimum_window:
                    errors.append(
                        f"trace {trace_id} extraction window is below {minimum_window}s"
                    )
            else:
                errors.append(f"trace {trace_id} has unsupported outcome {outcome}")

            expected_after = (
                values["stash_before"]
                - values["entry_debits"]
                - values["gear_committed_value"]
                + values["gear_returned_value"]
                + values["persisted_loot_value"]
                + values["insurance_return_value"]
                + values["other_credits"]
                - values["settlement_fees"]
            )
            ledger_delta = abs(expected_after - values["stash_after"])
            maximum_ledger_delta = max(maximum_ledger_delta, ledger_delta)
            if "ledger_conservation" in required_checks and ledger_delta != 0:
                errors.append(
                    f"trace {trace_id} stash ledger mismatch: expected {expected_after}, "
                    f"observed {values['stash_after']}"
                )
            if not allow_negative_stash and values["stash_after"] < 0:
                errors.append(f"trace {trace_id} leaves a negative stash")

            attempts = int_value(
                trace.get("settlement_attempts"), f"trace {trace_id}.settlement_attempts", minimum=1
            )
            applications = int_value(
                trace.get("settlement_applications"),
                f"trace {trace_id}.settlement_applications",
                minimum=1,
            )
            if applications > attempts:
                errors.append(f"trace {trace_id} applies settlement more times than attempted")
            if "settlement_idempotence" in required_checks and applications != 1:
                errors.append(f"trace {trace_id} settlement applied {applications} times")
            if scenario == "reconnect_settlement" and attempts < 2:
                errors.append(f"trace {trace_id} does not retry settlement during reconnect")
            duplicates = int_value(
                trace.get("duplicate_item_count"), f"trace {trace_id}.duplicate_item_count"
            )
            unauthorized = int_value(
                trace.get("unauthorized_item_count"), f"trace {trace_id}.unauthorized_item_count"
            )
            if duplicates:
                errors.append(f"trace {trace_id} contains duplicated items")
            if unauthorized:
                errors.append(f"trace {trace_id} contains unauthorized items")

            recovery_runs = int_value(
                trace.get("recovery_runs"), f"trace {trace_id}.recovery_runs"
            )
            if scenario == "bankruptcy_recovery" and "recovery_path" in required_checks:
                if recovery_runs > max_recovery_runs:
                    errors.append(
                        f"trace {trace_id} recovery takes {recovery_runs} runs, budget {max_recovery_runs}"
                    )
                if values["stash_after"] < recovery_floor:
                    errors.append(
                        f"trace {trace_id} recovery stash {values['stash_after']} below {recovery_floor}"
                    )

            if route_id in routes:
                route = routes[route_id]
                found = values["loot_found_value"]
                if found < route["minimum"] or found > route["maximum"]:
                    errors.append(
                        f"trace {trace_id} loot {found} outside route {route_id} range "
                        f"[{route['minimum']}, {route['maximum']}]"
                    )

        missing_archetypes = sorted(set(required_archetypes) - seen_archetypes)
        missing_scenarios = sorted(set(required_scenarios) - seen_scenarios)
        missing_routes = sorted(set(required_routes) - seen_routes)
        if missing_archetypes:
            errors.append(f"missing required archetypes: {', '.join(missing_archetypes)}")
        if missing_scenarios:
            errors.append(f"missing required scenarios: {', '.join(missing_scenarios)}")
        if missing_routes:
            errors.append(f"missing required route traces: {', '.join(missing_routes)}")
        if "route_coverage" in required_checks:
            total_successes = sum(successful_routes.values())
            if total_successes <= 0:
                errors.append("route_coverage has no successful extraction trace")
            else:
                for route_id, count in successful_routes.items():
                    share = Decimal(count) / Decimal(total_successes)
                    if share > max_route_share:
                        errors.append(
                            f"successful extraction route {route_id} share {share} exceeds {max_route_share}"
                        )

        report = {
            "status": "pass" if not errors else "fail",
            "contract_id": contract_id,
            "build_id": build_id,
            "trace_count": len(traces_raw),
            "required_checks": sorted(required_checks),
            "observed_archetypes": sorted(seen_archetypes),
            "observed_scenarios": sorted(seen_scenarios),
            "observed_routes": sorted(seen_routes),
            "maximum_ledger_delta": str(maximum_ledger_delta),
            "errors": errors,
        }
        if args.json_output:
            output = Path(args.json_output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        label = "PASS" if not errors else "FAIL"
        print(
            f"[{label}] extraction-loop id={contract_id} traces={len(traces_raw)} "
            f"errors={len(errors)}"
        )
        for error in errors:
            print(f"[ERROR] {error}")
        if not args.summary and not errors:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if not errors else 1
    except (OSError, json.JSONDecodeError, ExtractionError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
