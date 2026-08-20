#!/usr/bin/env python3
"""Compare measured game metrics with explicit per-profile performance budgets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


SCHEMA_VERSION = 1


class BudgetError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare performance measurement JSON with per-profile budgets."
    )
    parser.add_argument("--budget", required=True, help="Budget JSON file.")
    parser.add_argument("--measurements", required=True, help="Current measurements JSON file.")
    parser.add_argument("--baseline", help="Optional previous measurements JSON for deltas/regressions.")
    parser.add_argument(
        "--profile", action="append", default=[], help="Profile to check; repeatable. Default: all budgets."
    )
    parser.add_argument("--json-output", help="Write full machine-readable result JSON.")
    parser.add_argument(
        "--summary", action="store_true", help="Print only per-profile and total summaries."
    )
    parser.add_argument(
        "--max-details", type=int, default=60, help="Maximum metric detail lines (default: 60)."
    )
    args = parser.parse_args()
    if args.max_details < 0:
        parser.error("--max-details cannot be negative")
    return args


def read_json(path_value: str, label: str) -> dict[str, Any]:
    path = Path(path_value).expanduser().resolve()
    if not path.is_file():
        raise BudgetError(f"{label} file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise BudgetError(f"Invalid JSON in {label} file {path}: {exc}") from exc
    except OSError as exc:
        raise BudgetError(f"Could not read {label} file {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise BudgetError(f"{label} root must be an object")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise BudgetError(f"{label}.schema_version must be {SCHEMA_VERSION}")
    profiles = data.get("profiles")
    if not isinstance(profiles, dict):
        raise BudgetError(f"{label}.profiles must be an object")
    return data


def number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BudgetError(f"{label} must be numeric")
    return float(value)


def metrics_for_profile(data: dict[str, Any], profile_name: str, label: str) -> dict[str, Any]:
    profile = data["profiles"].get(profile_name)
    if not isinstance(profile, dict):
        raise BudgetError(f"{label} profile missing or invalid: {profile_name}")
    metrics = profile.get("metrics")
    if not isinstance(metrics, dict):
        raise BudgetError(f"{label}.profiles.{profile_name}.metrics must be an object")
    return metrics


def baseline_value(
    baseline: dict[str, Any] | None, profile_name: str, metric_name: str
) -> float | None:
    if baseline is None:
        return None
    profile = baseline.get("profiles", {}).get(profile_name)
    if not isinstance(profile, dict) or not isinstance(profile.get("metrics"), dict):
        return None
    value = profile["metrics"].get(metric_name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def percent_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return (current - previous) / abs(previous) * 100.0


def evaluate_metric(
    profile_name: str,
    metric_name: str,
    rule: Any,
    measured_metrics: dict[str, Any],
    baseline: dict[str, Any] | None,
) -> dict[str, Any]:
    label = f"budget.profiles.{profile_name}.metrics.{metric_name}"
    if not isinstance(rule, dict):
        raise BudgetError(f"{label} must be an object with min/max")
    allowed = {"min", "max", "required", "unit", "regression_percent_max"}
    unknown = sorted(set(rule) - allowed)
    if unknown:
        raise BudgetError(f"{label} has unsupported keys: {', '.join(unknown)}")
    if "min" not in rule and "max" not in rule:
        raise BudgetError(f"{label} needs min and/or max")
    minimum = number(rule["min"], f"{label}.min") if "min" in rule else None
    maximum = number(rule["max"], f"{label}.max") if "max" in rule else None
    regression_limit = (
        number(rule["regression_percent_max"], f"{label}.regression_percent_max")
        if "regression_percent_max" in rule
        else None
    )
    required = rule.get("required", True)
    if not isinstance(required, bool):
        raise BudgetError(f"{label}.required must be boolean")

    if metric_name not in measured_metrics:
        return {
            "profile": profile_name,
            "metric": metric_name,
            "status": "fail" if required else "skip",
            "reason": "required measurement missing" if required else "optional measurement missing",
            "unit": rule.get("unit", ""),
        }

    value = number(measured_metrics[metric_name], f"measurements.{profile_name}.{metric_name}")
    previous = baseline_value(baseline, profile_name, metric_name)
    failures: list[str] = []
    if minimum is not None and value < minimum:
        failures.append(f"{value:g} < min {minimum:g}")
    if maximum is not None and value > maximum:
        failures.append(f"{value:g} > max {maximum:g}")

    delta_percent = percent_change(value, previous) if previous is not None else None
    degradation_percent: float | None = None
    if previous is not None and regression_limit is not None:
        if maximum is not None and minimum is None:
            degradation_percent = delta_percent
        elif minimum is not None and maximum is None and delta_percent is not None:
            degradation_percent = -delta_percent
        if degradation_percent is not None and degradation_percent > regression_limit:
            failures.append(
                f"degradation {degradation_percent:.2f}% > allowed {regression_limit:g}%"
            )

    return {
        "profile": profile_name,
        "metric": metric_name,
        "status": "fail" if failures else "pass",
        "value": value,
        "unit": rule.get("unit", ""),
        "min": minimum,
        "max": maximum,
        "baseline": previous,
        "change_percent": delta_percent,
        "degradation_percent": degradation_percent,
        "reason": "; ".join(failures),
    }


def detail_line(result: dict[str, Any]) -> str:
    status = result["status"].upper()
    if "value" not in result:
        return f"[{status}] {result['profile']}/{result['metric']}: {result['reason']}"
    unit = f" {result.get('unit', '')}" if result.get("unit") else ""
    limits: list[str] = []
    if result.get("min") is not None:
        limits.append(f"min {result['min']:g}")
    if result.get("max") is not None:
        limits.append(f"max {result['max']:g}")
    baseline = ""
    if result.get("baseline") is not None:
        change = result.get("change_percent")
        change_text = f", {change:+.2f}%" if change is not None else ""
        baseline = f"; baseline {result['baseline']:g}{unit}{change_text}"
    reason = f"; {result['reason']}" if result.get("reason") else ""
    return (
        f"[{status}] {result['profile']}/{result['metric']}: {result['value']:g}{unit} "
        f"({', '.join(limits)}){baseline}{reason}"
    )


def write_report(path_value: str, report: dict[str, Any]) -> None:
    path = Path(path_value).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    try:
        budget = read_json(args.budget, "budget")
        measurements = read_json(args.measurements, "measurements")
        baseline = read_json(args.baseline, "baseline") if args.baseline else None

        profile_names = args.profile or sorted(budget["profiles"])
        missing_budget_profiles = [name for name in profile_names if name not in budget["profiles"]]
        if missing_budget_profiles:
            raise BudgetError(
                "Budget profile(s) not found: " + ", ".join(missing_budget_profiles)
            )

        results: list[dict[str, Any]] = []
        for profile_name in profile_names:
            budget_metrics = metrics_for_profile(budget, profile_name, "budget")
            measured_metrics = metrics_for_profile(measurements, profile_name, "measurements")
            for metric_name, rule in budget_metrics.items():
                results.append(
                    evaluate_metric(
                        profile_name, metric_name, rule, measured_metrics, baseline
                    )
                )
    except BudgetError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    profile_summary: dict[str, dict[str, int]] = {}
    for profile_name in profile_names:
        profile_results = [result for result in results if result["profile"] == profile_name]
        profile_summary[profile_name] = {
            "pass": sum(result["status"] == "pass" for result in profile_results),
            "fail": sum(result["status"] == "fail" for result in profile_results),
            "skip": sum(result["status"] == "skip" for result in profile_results),
        }

    if not args.summary:
        for result in results[: args.max_details]:
            print(detail_line(result))
        omitted = len(results) - min(len(results), args.max_details)
        if omitted:
            print(f"[INFO] {omitted} detail line(s) omitted; use --json-output for full results")

    for name, summary in profile_summary.items():
        status = "FAIL" if summary["fail"] else "PASS"
        print(
            f"[{status}] {name}: {summary['pass']} pass, "
            f"{summary['fail']} fail, {summary['skip']} skip"
        )

    total_failures = sum(result["status"] == "fail" for result in results)
    report = {
        "schema_version": SCHEMA_VERSION,
        "profiles": profile_summary,
        "results": results,
        "status": "fail" if total_failures else "pass",
    }
    if args.json_output:
        try:
            write_report(args.json_output, report)
            print(f"[INFO] Full report: {Path(args.json_output).expanduser().resolve()}")
        except OSError as exc:
            print(f"[ERROR] Could not write report: {exc}", file=sys.stderr)
            return 2

    if total_failures:
        print(f"[FAIL] {total_failures} budget failure(s)", file=sys.stderr)
        return 1
    print(f"[PASS] {len(results)} metric check(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
