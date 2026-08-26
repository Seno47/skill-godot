#!/usr/bin/env python3
"""Audit declared cross-genre progression and economy traces."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
from typing import Any


ALLOWED_CHECKS = {
    "power_challenge",
    "unlock_cadence",
    "choice_cadence",
    "failure_recovery",
    "option_viability",
    "resource_bounds",
    "source_sink_concentration",
}


class ModelError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit a project-declared progression/balance model without inventing universal thresholds."
    )
    parser.add_argument("--model", required=True, help="Progression balance JSON model.")
    parser.add_argument("--json-output", help="Optional full JSON report path.")
    parser.add_argument("--summary", action="store_true", help="Print only the compact verdict and failures.")
    return parser.parse_args()


def as_decimal(value: Any, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ModelError(f"{label} must be a finite decimal string or number")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ModelError(f"{label} is not a decimal: {value!r}") from exc
    if not result.is_finite():
        raise ModelError(f"{label} must be finite")
    return result


def string_list(value: Any, label: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ModelError(f"{label} must be an array of non-empty strings")
    if not allow_empty and not value:
        raise ModelError(f"{label} must not be empty")
    if len(set(value)) != len(value):
        raise ModelError(f"{label} must not contain duplicates")
    return value


def object_value(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ModelError(f"{label} must be an object")
    return value


def required_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ModelError(f"{label} must be a non-empty string")
    return value.strip()


def optional_bool(value: Any, label: str, default: bool = False) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise ModelError(f"{label} must be a boolean")
    return value


def check_ratio_budget(budgets: dict[str, Any]) -> tuple[Decimal, Decimal]:
    value = object_value(budgets.get("power_challenge_ratio"), "budgets.power_challenge_ratio")
    low = as_decimal(value.get("min"), "budgets.power_challenge_ratio.min")
    high = as_decimal(value.get("max"), "budgets.power_challenge_ratio.max")
    if low <= 0 or high < low:
        raise ModelError("power_challenge_ratio must satisfy 0 < min <= max")
    return low, high


def budget_decimal(
    budgets: dict[str, Any], key: str, *, share: bool = False
) -> Decimal:
    value = as_decimal(budgets.get(key), f"budgets.{key}")
    if value < 0 or (share and (value <= 0 or value > 1)):
        suffix = "in (0, 1]" if share else "non-negative"
        raise ModelError(f"budgets.{key} must be {suffix}")
    return value


def nested_amounts(
    value: Any,
    label: str,
    resource_ids: set[str],
    errors: list[str],
) -> dict[str, dict[str, Decimal]]:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return {}
    result: dict[str, dict[str, Decimal]] = {}
    for resource_id, entries in value.items():
        if resource_id not in resource_ids:
            errors.append(f"{label} names unknown resource {resource_id!r}")
            continue
        if not isinstance(entries, dict):
            errors.append(f"{label}.{resource_id} must be an object")
            continue
        converted: dict[str, Decimal] = {}
        for entry_id, raw_amount in entries.items():
            if not isinstance(entry_id, str) or not entry_id:
                errors.append(f"{label}.{resource_id} contains an invalid source/sink ID")
                continue
            try:
                amount = as_decimal(raw_amount, f"{label}.{resource_id}.{entry_id}")
            except ModelError as exc:
                errors.append(str(exc))
                continue
            if amount < 0:
                errors.append(f"{label}.{resource_id}.{entry_id} must be non-negative")
                continue
            converted[entry_id] = amount
        result[resource_id] = converted
    return result


def main() -> int:
    args = parse_args()
    model_path = Path(args.model).expanduser().resolve()
    try:
        if not model_path.is_file():
            raise ModelError(f"model not found: {model_path}")
        model = json.loads(model_path.read_text(encoding="utf-8-sig"))
        if not isinstance(model, dict):
            raise ModelError("model root must be an object")
        if model.get("schema_version") != 1:
            raise ModelError("schema_version must be 1")

        model_id = model.get("model_id")
        build_id = model.get("build_id")
        if not isinstance(model_id, str) or not model_id:
            raise ModelError("model_id must be a non-empty string")
        if not isinstance(build_id, str) or not build_id:
            raise ModelError("build_id must be a non-empty string")

        contract = object_value(model.get("contract"), "contract")
        progression_kind = required_text(
            contract.get("progression_kind"), "contract.progression_kind"
        )
        monetization_policy = required_text(
            contract.get("monetization_policy"), "contract.monetization_policy"
        )
        required_archetypes = string_list(
            contract.get("required_archetypes"), "contract.required_archetypes", allow_empty=False
        )
        required_checkpoints = string_list(
            contract.get("required_checkpoints"), "contract.required_checkpoints", allow_empty=False
        )
        required_sources = string_list(
            contract.get("required_trace_sources"), "contract.required_trace_sources", allow_empty=False
        )
        required_checks = set(
            string_list(contract.get("required_checks"), "contract.required_checks", allow_empty=False)
        )
        unknown_checks = sorted(required_checks - ALLOWED_CHECKS)
        if unknown_checks:
            raise ModelError(f"unknown required_checks: {', '.join(unknown_checks)}")

        budgets = object_value(model.get("budgets"), "budgets")
        ratio_budget = check_ratio_budget(budgets) if "power_challenge" in required_checks else None
        max_unlock_drought = (
            budget_decimal(budgets, "max_minutes_without_unlock")
            if "unlock_cadence" in required_checks
            else None
        )
        max_choice_drought = (
            budget_decimal(budgets, "max_minutes_without_meaningful_choice")
            if "choice_cadence" in required_checks
            else None
        )
        max_recovery = (
            budget_decimal(budgets, "max_failure_recovery_minutes")
            if "failure_recovery" in required_checks
            else None
        )
        max_option_share = (
            budget_decimal(budgets, "max_single_option_pick_share", share=True)
            if "option_viability" in required_checks
            else None
        )
        max_source_share = (
            budget_decimal(budgets, "max_single_reward_source_share", share=True)
            if "source_sink_concentration" in required_checks
            else None
        )
        max_sink_share = (
            budget_decimal(budgets, "max_single_resource_sink_share", share=True)
            if "source_sink_concentration" in required_checks
            else None
        )

        errors: list[str] = []
        resources_raw = model.get("resources", [])
        if not isinstance(resources_raw, list):
            raise ModelError("resources must be an array")
        resources: dict[str, dict[str, Any]] = {}
        for index, item in enumerate(resources_raw):
            resource = object_value(item, f"resources[{index}]")
            resource_id = resource.get("id")
            if not isinstance(resource_id, str) or not resource_id:
                raise ModelError(f"resources[{index}].id must be a non-empty string")
            if resource_id in resources:
                raise ModelError(f"duplicate resource ID: {resource_id}")
            floor = as_decimal(resource.get("floor", "0"), f"resources[{index}].floor")
            ceiling_raw = resource.get("ceiling")
            ceiling = (
                as_decimal(ceiling_raw, f"resources[{index}].ceiling")
                if ceiling_raw is not None
                else None
            )
            if ceiling is not None and ceiling < floor:
                raise ModelError(f"resource {resource_id} ceiling must be >= floor")
            resources[resource_id] = {
                "floor": floor,
                "ceiling": ceiling,
                "must_have_source": optional_bool(
                    resource.get("must_have_source"),
                    f"resources[{index}].must_have_source",
                ),
                "must_have_sink": optional_bool(
                    resource.get("must_have_sink"),
                    f"resources[{index}].must_have_sink",
                ),
            }
        if "resource_bounds" in required_checks and not resources:
            raise ModelError("resource_bounds requires at least one resource")

        options_raw = model.get("options", [])
        if not isinstance(options_raw, list):
            raise ModelError("options must be an array")
        options: dict[str, dict[str, Any]] = {}
        for index, item in enumerate(options_raw):
            option = object_value(item, f"options[{index}]")
            option_id = option.get("id")
            family = option.get("family")
            if not isinstance(option_id, str) or not option_id:
                raise ModelError(f"options[{index}].id must be a non-empty string")
            if option_id in options:
                raise ModelError(f"duplicate option ID: {option_id}")
            if not isinstance(family, str) or not family:
                raise ModelError(f"options[{index}].family must be a non-empty string")
            options[option_id] = {
                "family": family,
                "required_viable": optional_bool(
                    option.get("required_viable"),
                    f"options[{index}].required_viable",
                ),
            }
        if "option_viability" in required_checks and not options:
            raise ModelError("option_viability requires at least one option")

        traces_raw = model.get("traces")
        if not isinstance(traces_raw, list) or not traces_raw:
            raise ModelError("traces must be a non-empty array")

        trace_ids: set[str] = set()
        seen_archetypes: set[str] = set()
        seen_sources: set[str] = set()
        option_presented: Counter[str] = Counter()
        option_selected: Counter[str] = Counter()
        family_selected: Counter[str] = Counter()
        source_totals: dict[str, Counter[str]] = defaultdict(Counter)
        sink_totals: dict[str, Counter[str]] = defaultdict(Counter)
        ratio_values: list[Decimal] = []
        max_observed_unlock_drought = Decimal(0)
        max_observed_choice_drought = Decimal(0)
        max_observed_recovery = Decimal(0)

        for trace_index, trace_value in enumerate(traces_raw):
            trace = object_value(trace_value, f"traces[{trace_index}]")
            trace_id = trace.get("id")
            archetype = trace.get("archetype")
            source = trace.get("source")
            if not isinstance(trace_id, str) or not trace_id:
                raise ModelError(f"traces[{trace_index}].id must be a non-empty string")
            if trace_id in trace_ids:
                raise ModelError(f"duplicate trace ID: {trace_id}")
            trace_ids.add(trace_id)
            if not isinstance(archetype, str) or not archetype:
                raise ModelError(f"trace {trace_id} archetype must be a non-empty string")
            if not isinstance(source, str) or not source:
                raise ModelError(f"trace {trace_id} source must be a non-empty string")
            required_text(trace.get("strategy"), f"trace {trace_id} strategy")
            required_text(trace.get("seed"), f"trace {trace_id} seed")
            seen_archetypes.add(archetype)
            seen_sources.add(source)

            checkpoints = trace.get("checkpoints")
            if not isinstance(checkpoints, list) or not checkpoints:
                raise ModelError(f"trace {trace_id} checkpoints must be a non-empty array")
            checkpoint_ids: set[str] = set()
            previous_time: Decimal | None = None
            first_time: Decimal | None = None
            last_unlock_time: Decimal | None = None
            last_choice_time: Decimal | None = None
            saw_recovery = False

            for checkpoint_index, checkpoint_value in enumerate(checkpoints):
                checkpoint = object_value(
                    checkpoint_value, f"trace {trace_id} checkpoints[{checkpoint_index}]"
                )
                checkpoint_id = checkpoint.get("id")
                if not isinstance(checkpoint_id, str) or not checkpoint_id:
                    errors.append(f"trace {trace_id} checkpoint {checkpoint_index} has invalid id")
                    continue
                if checkpoint_id in checkpoint_ids:
                    errors.append(f"trace {trace_id} has duplicate checkpoint {checkpoint_id}")
                checkpoint_ids.add(checkpoint_id)
                try:
                    elapsed = as_decimal(
                        checkpoint.get("elapsed_minutes"),
                        f"trace {trace_id} checkpoint {checkpoint_id} elapsed_minutes",
                    )
                except ModelError as exc:
                    errors.append(str(exc))
                    continue
                if elapsed < 0:
                    errors.append(f"trace {trace_id} checkpoint {checkpoint_id} time is negative")
                if previous_time is not None and elapsed < previous_time:
                    errors.append(f"trace {trace_id} checkpoint time decreases at {checkpoint_id}")
                previous_time = elapsed
                if first_time is None:
                    first_time = elapsed
                    last_unlock_time = elapsed
                    last_choice_time = elapsed

                if "power_challenge" in required_checks:
                    try:
                        power = as_decimal(
                            checkpoint.get("player_power"),
                            f"trace {trace_id} checkpoint {checkpoint_id} player_power",
                        )
                        challenge = as_decimal(
                            checkpoint.get("challenge"),
                            f"trace {trace_id} checkpoint {checkpoint_id} challenge",
                        )
                        if power < 0 or challenge <= 0:
                            raise ModelError(
                                f"trace {trace_id} checkpoint {checkpoint_id} requires power >= 0 and challenge > 0"
                            )
                        ratio = power / challenge
                        ratio_values.append(ratio)
                        assert ratio_budget is not None
                        if ratio < ratio_budget[0] or ratio > ratio_budget[1]:
                            errors.append(
                                f"trace {trace_id} checkpoint {checkpoint_id} power/challenge ratio "
                                f"{ratio} outside [{ratio_budget[0]}, {ratio_budget[1]}]"
                            )
                    except ModelError as exc:
                        errors.append(str(exc))

                try:
                    unlocks = string_list(
                        checkpoint.get("unlocks", []),
                        f"trace {trace_id} checkpoint {checkpoint_id} unlocks",
                    )
                    presented = string_list(
                        checkpoint.get("choices_presented", []),
                        f"trace {trace_id} checkpoint {checkpoint_id} choices_presented",
                    )
                    selected = string_list(
                        checkpoint.get("choices_selected", []),
                        f"trace {trace_id} checkpoint {checkpoint_id} choices_selected",
                    )
                except ModelError as exc:
                    errors.append(str(exc))
                    unlocks, presented, selected = [], [], []

                if unlocks:
                    if last_unlock_time is not None:
                        max_observed_unlock_drought = max(
                            max_observed_unlock_drought, elapsed - last_unlock_time
                        )
                    last_unlock_time = elapsed
                if presented:
                    if last_choice_time is not None:
                        max_observed_choice_drought = max(
                            max_observed_choice_drought, elapsed - last_choice_time
                        )
                    last_choice_time = elapsed

                for option_id in presented:
                    if option_id not in options:
                        errors.append(
                            f"trace {trace_id} checkpoint {checkpoint_id} presents unknown option {option_id}"
                        )
                    option_presented[option_id] += 1
                for option_id in selected:
                    if option_id not in presented:
                        errors.append(
                            f"trace {trace_id} checkpoint {checkpoint_id} selects {option_id} without presenting it"
                        )
                    if option_id not in options:
                        errors.append(
                            f"trace {trace_id} checkpoint {checkpoint_id} selects unknown option {option_id}"
                        )
                        continue
                    option_selected[option_id] += 1
                    family_selected[options[option_id]["family"]] += 1

                if "failure_recovery" in required_checks:
                    recovery_raw = checkpoint.get("failure_recovery_minutes")
                    if recovery_raw is not None:
                        saw_recovery = True
                        try:
                            recovery = as_decimal(
                                recovery_raw,
                                f"trace {trace_id} checkpoint {checkpoint_id} failure_recovery_minutes",
                            )
                            if recovery < 0:
                                errors.append(
                                    f"trace {trace_id} checkpoint {checkpoint_id} recovery is negative"
                                )
                            max_observed_recovery = max(max_observed_recovery, recovery)
                            assert max_recovery is not None
                            if recovery > max_recovery:
                                errors.append(
                                    f"trace {trace_id} checkpoint {checkpoint_id} recovery {recovery}m "
                                    f"exceeds {max_recovery}m"
                                )
                        except ModelError as exc:
                            errors.append(str(exc))

                balances = checkpoint.get("balances", {})
                if not isinstance(balances, dict):
                    errors.append(f"trace {trace_id} checkpoint {checkpoint_id} balances must be an object")
                    balances = {}
                if "resource_bounds" in required_checks:
                    for resource_id, definition in resources.items():
                        if resource_id not in balances:
                            errors.append(
                                f"trace {trace_id} checkpoint {checkpoint_id} lacks balance for {resource_id}"
                            )
                            continue
                        try:
                            balance = as_decimal(
                                balances[resource_id],
                                f"trace {trace_id} checkpoint {checkpoint_id} balance {resource_id}",
                            )
                            if balance < definition["floor"]:
                                errors.append(
                                    f"trace {trace_id} checkpoint {checkpoint_id} {resource_id} balance "
                                    f"{balance} below floor {definition['floor']}"
                                )
                            ceiling = definition["ceiling"]
                            if ceiling is not None and balance > ceiling:
                                errors.append(
                                    f"trace {trace_id} checkpoint {checkpoint_id} {resource_id} balance "
                                    f"{balance} above ceiling {ceiling}"
                                )
                        except ModelError as exc:
                            errors.append(str(exc))

                sources = nested_amounts(
                    checkpoint.get("resource_sources", {}),
                    f"trace {trace_id} checkpoint {checkpoint_id} resource_sources",
                    set(resources),
                    errors,
                )
                sinks = nested_amounts(
                    checkpoint.get("resource_sinks", {}),
                    f"trace {trace_id} checkpoint {checkpoint_id} resource_sinks",
                    set(resources),
                    errors,
                )
                for resource_id, entries in sources.items():
                    source_totals[resource_id].update(entries)
                for resource_id, entries in sinks.items():
                    sink_totals[resource_id].update(entries)

            missing_checkpoints = sorted(set(required_checkpoints) - checkpoint_ids)
            if missing_checkpoints:
                errors.append(
                    f"trace {trace_id} lacks required checkpoints: {', '.join(missing_checkpoints)}"
                )
            if previous_time is not None and last_unlock_time is not None:
                max_observed_unlock_drought = max(
                    max_observed_unlock_drought, previous_time - last_unlock_time
                )
            if previous_time is not None and last_choice_time is not None:
                max_observed_choice_drought = max(
                    max_observed_choice_drought, previous_time - last_choice_time
                )
            if "failure_recovery" in required_checks and not saw_recovery:
                errors.append(f"trace {trace_id} has no failure_recovery_minutes observation")

        missing_archetypes = sorted(set(required_archetypes) - seen_archetypes)
        if missing_archetypes:
            errors.append(f"missing required archetypes: {', '.join(missing_archetypes)}")
        missing_sources = sorted(set(required_sources) - seen_sources)
        if missing_sources:
            errors.append(f"missing required trace sources: {', '.join(missing_sources)}")

        if max_unlock_drought is not None and max_observed_unlock_drought > max_unlock_drought:
            errors.append(
                f"maximum unlock drought {max_observed_unlock_drought}m exceeds {max_unlock_drought}m"
            )
        if max_choice_drought is not None and max_observed_choice_drought > max_choice_drought:
            errors.append(
                f"maximum meaningful-choice drought {max_observed_choice_drought}m exceeds "
                f"{max_choice_drought}m"
            )

        if "option_viability" in required_checks:
            for option_id, definition in options.items():
                if definition["required_viable"] and option_presented[option_id] == 0:
                    errors.append(f"required viable option {option_id} is never presented")
                if definition["required_viable"] and option_selected[option_id] == 0:
                    errors.append(f"required viable option {option_id} is never selected")
            for family in sorted(set(item["family"] for item in options.values())):
                total = family_selected[family]
                if total <= 0:
                    errors.append(f"option family {family} has no selected option")
                    continue
                assert max_option_share is not None
                for option_id, definition in options.items():
                    if definition["family"] != family:
                        continue
                    share = Decimal(option_selected[option_id]) / Decimal(total)
                    if share > max_option_share:
                        errors.append(
                            f"option {option_id} pick share {share} exceeds {max_option_share} in family {family}"
                        )

        concentration_metrics: dict[str, dict[str, str]] = {}
        for resource_id, definition in resources.items():
            resource_metrics: dict[str, str] = {}
            source_total = sum(source_totals[resource_id].values(), Decimal(0))
            sink_total = sum(sink_totals[resource_id].values(), Decimal(0))
            if definition["must_have_source"] and source_total <= 0:
                errors.append(f"resource {resource_id} has no positive source")
            if definition["must_have_sink"] and sink_total <= 0:
                errors.append(f"resource {resource_id} has no positive sink")
            if "source_sink_concentration" in required_checks and source_total > 0:
                source_share = max(source_totals[resource_id].values()) / source_total
                resource_metrics["largest_source_share"] = str(source_share)
                assert max_source_share is not None
                if source_share > max_source_share:
                    errors.append(
                        f"resource {resource_id} largest source share {source_share} exceeds {max_source_share}"
                    )
            if "source_sink_concentration" in required_checks and sink_total > 0:
                sink_share = max(sink_totals[resource_id].values()) / sink_total
                resource_metrics["largest_sink_share"] = str(sink_share)
                assert max_sink_share is not None
                if sink_share > max_sink_share:
                    errors.append(
                        f"resource {resource_id} largest sink share {sink_share} exceeds {max_sink_share}"
                    )
            concentration_metrics[resource_id] = resource_metrics

        report = {
            "status": "pass" if not errors else "fail",
            "model_id": model_id,
            "build_id": build_id,
            "progression_kind": progression_kind,
            "monetization_policy": monetization_policy,
            "trace_count": len(traces_raw),
            "required_checks": sorted(required_checks),
            "metrics": {
                "power_challenge_ratio_min": str(min(ratio_values)) if ratio_values else None,
                "power_challenge_ratio_max": str(max(ratio_values)) if ratio_values else None,
                "max_unlock_drought_minutes": str(max_observed_unlock_drought),
                "max_choice_drought_minutes": str(max_observed_choice_drought),
                "max_failure_recovery_minutes": str(max_observed_recovery),
                "resource_concentration": concentration_metrics,
            },
            "errors": errors,
        }

        if args.json_output:
            output_path = Path(args.json_output).expanduser().resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )

        label = "PASS" if not errors else "FAIL"
        print(
            f"[{label}] progression-balance model={model_id} traces={len(traces_raw)} "
            f"errors={len(errors)}"
        )
        if errors:
            for error in errors:
                print(f"[ERROR] {error}")
        elif not args.summary:
            print(json.dumps(report["metrics"], indent=2, ensure_ascii=False))
        return 0 if not errors else 1
    except (OSError, json.JSONDecodeError, ModelError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
