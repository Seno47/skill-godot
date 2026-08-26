#!/usr/bin/env python3
"""Audit deterministic failure injection across durable and asynchronous boundaries."""

from contract_probe_utils import (
    array, cli_main, contract_header, finish_report, integer, require_coverage,
    require_target_pass, require_true, strings, text, trace_header,
)


def audit(model):
    contract_id, _, contract = contract_header(model)
    required_targets = strings(contract.get("required_targets"), "required_targets", nonempty=True)
    required_scenarios = strings(contract.get("required_scenarios"), "required_scenarios", nonempty=True)
    minimum_seeds = integer(contract.get("minimum_distinct_seeds"), "minimum_distinct_seeds", 1)
    traces = array(model.get("traces"), "traces", nonempty=True)
    errors, seen_ids, scenarios, targets, seeds = [], set(), set(), set(), set()
    for index, raw in enumerate(traces):
        trace, trace_id, scenario = trace_header(raw, index, seen_ids)
        target = text(trace.get("target"), f"trace {trace_id}.target")
        seed = integer(trace.get("seed"), f"trace {trace_id}.seed")
        scenarios.add(scenario); targets.add(target); seeds.add(seed)
        require_target_pass(trace, trace_id, errors)
        for key in ("safe_state", "retry_or_rollback_available", "invariants_preserved"):
            require_true(trace, key, trace_id, errors)
        for key in ("unhandled_exceptions", "duplicate_durable_effects", "orphan_tasks", "hangs"):
            if integer(trace.get(key), f"trace {trace_id}.{key}"):
                errors.append(f"trace {trace_id} reports non-zero {key}")
    require_coverage(required_targets, targets, "fault targets", errors)
    require_coverage(required_scenarios, scenarios, "fault scenarios", errors)
    if "control" not in scenarios:
        errors.append("fault suite has no control scenario")
    if len(seeds) < minimum_seeds:
        errors.append(f"fault suite has {len(seeds)} distinct seeds; requires {minimum_seeds}")
    return finish_report(contract_id, traces, errors, target_count=len(targets), scenario_count=len(scenarios), seed_count=len(seeds))


if __name__ == "__main__":
    raise SystemExit(cli_main("fault injection", audit))
