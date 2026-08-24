#!/usr/bin/env python3
"""Audit idle-game curves and run a deterministic event-driven economy smoke test."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation, getcontext
import json
from pathlib import Path
import sys
from typing import Any


getcontext().prec = 80


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate decimal idle-economy curves, milestones, and offline caps."
    )
    parser.add_argument("--model", required=True, help="Economy model JSON file.")
    parser.add_argument("--json-output", help="Write the full report as JSON.")
    parser.add_argument("--summary", action="store_true", help="Print bounded diagnostics.")
    parser.add_argument("--max-details", type=int, default=60)
    parser.add_argument("--fail-on-warnings", action="store_true")
    args = parser.parse_args()
    if args.max_details < 0:
        parser.error("--max-details must be non-negative")
    return args


def decimal_value(value: Any, path: str, errors: list[str]) -> Decimal:
    if isinstance(value, bool) or value is None:
        errors.append(f"{path} must be a decimal-compatible number or string")
        return Decimal(0)
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        errors.append(f"{path} is not a valid decimal: {value!r}")
        return Decimal(0)
    if not result.is_finite():
        errors.append(f"{path} must be finite")
        return Decimal(0)
    return result


def integer_value(value: Any, path: str, errors: list[str], default: int = 0) -> int:
    if isinstance(value, bool):
        errors.append(f"{path} must be an integer")
        return default
    try:
        result = int(value)
    except (TypeError, ValueError):
        errors.append(f"{path} must be an integer")
        return default
    if str(result) != str(value) and not isinstance(value, int):
        try:
            if Decimal(str(value)) != result:
                raise ValueError
        except (InvalidOperation, ValueError):
            errors.append(f"{path} must be an exact integer")
            return default
    return result


def normalize(raw: Any) -> tuple[dict[str, Any], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(raw, dict):
        return {}, ["model root must be an object"], []
    duration = decimal_value(raw.get("duration_seconds", "3600"), "duration_seconds", errors)
    initial_currency = decimal_value(raw.get("initial_currency", "0"), "initial_currency", errors)
    manual_rate = decimal_value(raw.get("manual_rate", "0"), "manual_rate", errors)
    offline_cap = decimal_value(raw.get("offline_cap_seconds", "0"), "offline_cap_seconds", errors)
    max_purchases = integer_value(raw.get("max_purchases", 100000), "max_purchases", errors)
    strategy = raw.get("strategy", "best_payback")
    if strategy not in {"best_payback", "cheapest"}:
        errors.append("strategy must be 'best_payback' or 'cheapest'")
    if duration <= 0:
        errors.append("duration_seconds must be greater than zero")
    if initial_currency < 0 or manual_rate < 0 or offline_cap < 0:
        errors.append("initial_currency, manual_rate, and offline_cap_seconds must be non-negative")
    if max_purchases <= 0:
        errors.append("max_purchases must be greater than zero")

    raw_generators = raw.get("generators", [])
    if not isinstance(raw_generators, list):
        errors.append("generators must be an array")
        raw_generators = []
    generators: list[dict[str, Any]] = []
    identifiers: set[str] = set()
    for index, item in enumerate(raw_generators):
        if not isinstance(item, dict):
            errors.append(f"generators[{index}] must be an object")
            continue
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier:
            errors.append(f"generators[{index}].id must be a non-empty string")
            continue
        if identifier in identifiers:
            errors.append(f"duplicate generator ID: {identifier}")
            continue
        identifiers.add(identifier)
        generator = {
            "id": identifier,
            "base_cost": decimal_value(item.get("base_cost"), f"generators[{index}].base_cost", errors),
            "cost_growth": decimal_value(item.get("cost_growth", "1"), f"generators[{index}].cost_growth", errors),
            "base_rate": decimal_value(item.get("base_rate"), f"generators[{index}].base_rate", errors),
            "rate_growth": decimal_value(item.get("rate_growth", "1"), f"generators[{index}].rate_growth", errors),
            "initial_level": integer_value(item.get("initial_level", 0), f"generators[{index}].initial_level", errors),
            "offline_level": integer_value(
                item.get("offline_level", item.get("initial_level", 0)),
                f"generators[{index}].offline_level",
                errors,
            ),
            "max_level": None,
        }
        if item.get("max_level") is not None:
            generator["max_level"] = integer_value(
                item.get("max_level"), f"generators[{index}].max_level", errors
            )
        if generator["base_cost"] <= 0 or generator["cost_growth"] <= 0:
            errors.append(f"generator {identifier} cost values must be greater than zero")
        if generator["base_rate"] <= 0 or generator["rate_growth"] <= 0:
            errors.append(f"generator {identifier} rate values must be greater than zero")
        if generator["initial_level"] < 0 or generator["offline_level"] < 0:
            errors.append(f"generator {identifier} levels must be non-negative")
        if generator["max_level"] is not None:
            if generator["max_level"] < 0:
                errors.append(f"generator {identifier}.max_level must be non-negative")
            if generator["initial_level"] > generator["max_level"]:
                errors.append(f"generator {identifier}.initial_level exceeds max_level")
        if generator["cost_growth"] < 1:
            warnings.append(f"generator {identifier} costs decrease with level")
        if generator["rate_growth"] < 1:
            warnings.append(f"generator {identifier} marginal production decreases with level")
        generators.append(generator)
    if not generators:
        warnings.append("no generators declared; only manual production can be simulated")

    raw_milestones = raw.get("milestones", [])
    if not isinstance(raw_milestones, list):
        errors.append("milestones must be an array")
        raw_milestones = []
    milestones: list[dict[str, Any]] = []
    for index, item in enumerate(raw_milestones):
        if not isinstance(item, dict):
            errors.append(f"milestones[{index}] must be an object")
            continue
        seconds = decimal_value(item.get("seconds"), f"milestones[{index}].seconds", errors)
        if seconds < 0 or seconds > duration:
            errors.append(f"milestones[{index}].seconds must be within the simulation duration")
        milestone: dict[str, Any] = {"seconds": seconds}
        for field in ("min_currency", "max_currency", "min_total_rate", "max_total_rate"):
            if field in item:
                milestone[field] = decimal_value(item[field], f"milestones[{index}].{field}", errors)
        for field in ("min_purchases", "max_purchases"):
            if field in item:
                milestone[field] = integer_value(item[field], f"milestones[{index}].{field}", errors)
        milestones.append(milestone)

    raw_samples = raw.get("offline_absence_samples", [])
    if not isinstance(raw_samples, list):
        errors.append("offline_absence_samples must be an array")
        raw_samples = []
    offline_samples = [
        decimal_value(value, f"offline_absence_samples[{index}]", errors)
        for index, value in enumerate(raw_samples)
    ]
    if any(value < 0 for value in offline_samples):
        errors.append("offline absence samples must be non-negative")
    offline_includes_manual = raw.get("offline_includes_manual", False)
    if not isinstance(offline_includes_manual, bool):
        errors.append("offline_includes_manual must be boolean")
        offline_includes_manual = False
    return {
        "duration": duration,
        "initial_currency": initial_currency,
        "manual_rate": manual_rate,
        "offline_cap": offline_cap,
        "offline_samples": offline_samples,
        "offline_includes_manual": offline_includes_manual,
        "strategy": strategy,
        "max_purchases": max_purchases,
        "generators": generators,
        "milestones": milestones,
    }, errors, warnings


def purchase_cost(generator: dict[str, Any], level: int) -> Decimal:
    return generator["base_cost"] * (generator["cost_growth"] ** level)


def marginal_rate(generator: dict[str, Any], level: int) -> Decimal:
    return generator["base_rate"] * (generator["rate_growth"] ** level)


def owned_rate(generator: dict[str, Any], level: int) -> Decimal:
    if level <= 0:
        return Decimal(0)
    growth = generator["rate_growth"]
    if growth == 1:
        return generator["base_rate"] * level
    return generator["base_rate"] * ((growth ** level) - 1) / (growth - 1)


def total_rate(model: dict[str, Any], levels: dict[str, int], include_manual: bool = True) -> Decimal:
    value = model["manual_rate"] if include_manual else Decimal(0)
    for generator in model["generators"]:
        value += owned_rate(generator, levels[generator["id"]])
    return value


def select_purchase(model: dict[str, Any], levels: dict[str, int]) -> tuple[dict[str, Any], Decimal, Decimal] | None:
    candidates: list[tuple[Decimal, Decimal, str, dict[str, Any], Decimal]] = []
    for generator in model["generators"]:
        level = levels[generator["id"]]
        if generator["max_level"] is not None and level >= generator["max_level"]:
            continue
        cost = purchase_cost(generator, level)
        gain = marginal_rate(generator, level)
        primary = cost if model["strategy"] == "cheapest" else cost / gain
        candidates.append((primary, cost, generator["id"], generator, gain))
    if not candidates:
        return None
    _, cost, _, generator, gain = min(candidates, key=lambda item: (item[0], item[1], item[2]))
    return generator, cost, gain


def snapshot(model: dict[str, Any], levels: dict[str, int], currency: Decimal, purchases: int, at: Decimal) -> dict[str, Any]:
    return {
        "seconds": str(at),
        "currency": str(currency),
        "total_rate": str(total_rate(model, levels)),
        "purchases": purchases,
        "levels": dict(sorted(levels.items())),
    }


def simulate(model: dict[str, Any], warnings: list[str]) -> dict[str, Any]:
    levels = {generator["id"]: generator["initial_level"] for generator in model["generators"]}
    currency = model["initial_currency"]
    current = Decimal(0)
    purchases = 0
    checkpoints = sorted({item["seconds"] for item in model["milestones"]} | {model["duration"]})
    snapshots: dict[str, dict[str, Any]] = {}
    halted = False
    for checkpoint in checkpoints:
        while current < checkpoint:
            candidate = select_purchase(model, levels)
            production = total_rate(model, levels)
            if candidate is None or purchases >= model["max_purchases"]:
                if purchases >= model["max_purchases"] and not halted:
                    warnings.append("simulation reached max_purchases and stopped buying")
                    halted = True
                currency += production * (checkpoint - current)
                current = checkpoint
                break
            generator, cost, _gain = candidate
            if currency >= cost:
                currency -= cost
                levels[generator["id"]] += 1
                purchases += 1
                continue
            if production <= 0:
                currency += production * (checkpoint - current)
                current = checkpoint
                break
            wait = (cost - currency) / production
            if current + wait > checkpoint:
                currency += production * (checkpoint - current)
                current = checkpoint
                break
            currency += production * wait
            current += wait
            currency -= cost
            levels[generator["id"]] += 1
            purchases += 1
        snapshots[str(checkpoint)] = snapshot(model, levels, currency, purchases, checkpoint)
    return {
        "snapshots": snapshots,
        "final": snapshots[str(model["duration"])],
    }


def curve_report(model: dict[str, Any], errors: list[str]) -> list[dict[str, Any]]:
    report: list[dict[str, Any]] = []
    for generator in model["generators"]:
        levels = {0, 1, 10, 100, generator["initial_level"], generator["offline_level"]}
        if generator["max_level"] is not None:
            levels.add(generator["max_level"])
        samples: list[dict[str, str | int]] = []
        previous_cost: Decimal | None = None
        for level in sorted(value for value in levels if value >= 0):
            cost = purchase_cost(generator, level)
            rate = marginal_rate(generator, level)
            if not cost.is_finite() or not rate.is_finite():
                errors.append(f"generator {generator['id']} curve is non-finite at level {level}")
            if previous_cost is not None and generator["cost_growth"] >= 1 and cost < previous_cost:
                errors.append(f"generator {generator['id']} cost is not monotonic at level {level}")
            previous_cost = cost
            samples.append({"level": level, "cost": str(cost), "marginal_rate": str(rate)})
        report.append({"id": generator["id"], "samples": samples})
    return report


def milestone_checks(model: dict[str, Any], simulation: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for milestone in model["milestones"]:
        observed = simulation["snapshots"][str(milestone["seconds"])]
        currency = Decimal(observed["currency"])
        rate = Decimal(observed["total_rate"])
        purchases = observed["purchases"]
        comparisons = (
            ("min_currency", currency, lambda actual, expected: actual >= expected),
            ("max_currency", currency, lambda actual, expected: actual <= expected),
            ("min_total_rate", rate, lambda actual, expected: actual >= expected),
            ("max_total_rate", rate, lambda actual, expected: actual <= expected),
            ("min_purchases", purchases, lambda actual, expected: actual >= expected),
            ("max_purchases", purchases, lambda actual, expected: actual <= expected),
        )
        for field, actual, predicate in comparisons:
            if field in milestone and not predicate(actual, milestone[field]):
                errors.append(
                    f"milestone {milestone['seconds']}s: {field}={milestone[field]} "
                    f"but observed {actual}"
                )
    return errors


def offline_report(model: dict[str, Any]) -> list[dict[str, str]]:
    levels = {generator["id"]: generator["offline_level"] for generator in model["generators"]}
    rate = total_rate(model, levels, include_manual=model["offline_includes_manual"])
    report: list[dict[str, str]] = []
    for absence in model["offline_samples"]:
        credited = min(absence, model["offline_cap"])
        report.append(
            {
                "absence_seconds": str(absence),
                "credited_seconds": str(credited),
                "production_rate": str(rate),
                "gain": str(rate * credited),
            }
        )
    return report


def main() -> int:
    args = parse_args()
    try:
        model_path = Path(args.model).expanduser().resolve()
        raw = json.loads(model_path.read_text(encoding="utf-8"))
        model, errors, warnings = normalize(raw)
        if errors:
            curves: list[dict[str, Any]] = []
            simulation: dict[str, Any] = {}
            offline: list[dict[str, str]] = []
        else:
            curves = curve_report(model, errors)
            simulation = simulate(model, warnings)
            errors.extend(milestone_checks(model, simulation))
            offline = offline_report(model)
        report = {
            "model": str(model_path),
            "strategy": model.get("strategy"),
            "curve_samples": curves,
            "simulation": simulation,
            "offline_samples": offline,
            "errors": errors,
            "warnings": sorted(set(warnings)),
        }
        report["passed"] = not errors and not (args.fail_on_warnings and report["warnings"])
        if args.json_output:
            output = Path(args.json_output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        status = "PASS" if report["passed"] else "FAIL"
        if args.summary or not args.json_output or not report["passed"]:
            final = simulation.get("final", {})
            print(
                f"[{status}] generators={len(model.get('generators', []))} "
                f"purchases={final.get('purchases', 'n/a')} rate={final.get('total_rate', 'n/a')} "
                f"errors={len(errors)} warnings={len(report['warnings'])}"
            )
            details = [*(f"[ERROR] {item}" for item in errors), *(f"[WARN] {item}" for item in report["warnings"])]
            for detail in details[: args.max_details]:
                print(detail)
            if len(details) > args.max_details:
                print(f"[INFO] {len(details) - args.max_details} additional diagnostics omitted")
        return 0 if report["passed"] else 1
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, InvalidOperation) as error:
        print(f"[ERROR] {error}")
        return 2


if __name__ == "__main__":
    sys.exit(main())

