#!/usr/bin/env python3
"""Fail-closed crash, hang, logging, and recovery contract audit."""

from contract_probe_utils import (
    ContractError, array, boolean, cli_main, contract_header, finish_report, integer,
    require_coverage, require_target_pass, require_true, strings, trace_header,
)


def audit(model):
    contract_id, _, contract = contract_header(model)
    required = strings(contract.get("required_scenarios"), "required_scenarios", nonempty=True)
    budget = integer(contract.get("max_data_loss_seconds"), "max_data_loss_seconds")
    for key in ("symbol_identity_recorded", "privacy_redaction_enabled"):
        if not boolean(contract.get(key), key):
            raise ContractError(f"{key} must be true")
    traces = array(model.get("traces"), "traces", nonempty=True)
    errors, seen_ids, observed = [], set(), set()
    for index, raw in enumerate(traces):
        trace, trace_id, scenario = trace_header(raw, index, seen_ids)
        observed.add(scenario)
        require_target_pass(trace, trace_id, errors)
        for key in ("recovered", "build_identity_matched", "bounded_breadcrumbs", "truthful_recovery_ui"):
            require_true(trace, key, trace_id, errors)
        if integer(trace.get("data_loss_seconds"), f"trace {trace_id}.data_loss_seconds") > budget:
            errors.append(f"trace {trace_id} exceeds data-loss budget")
        if integer(trace.get("duplicate_commits"), f"trace {trace_id}.duplicate_commits"):
            errors.append(f"trace {trace_id} duplicated durable commits")
        if strings(trace.get("sensitive_log_fields"), f"trace {trace_id}.sensitive_log_fields"):
            errors.append(f"trace {trace_id} exposes sensitive log fields")
        if scenario == "crash_relaunch":
            for key in ("previous_crash_detected", "crash_artifact_present", "safe_mode_available"):
                require_true(trace, key, trace_id, errors)
        elif scenario == "hang_watchdog":
            require_true(trace, "watchdog_triggered", trace_id, errors)
        elif scenario in {"memory_pressure", "renderer_failure"}:
            require_true(trace, "fallback_or_truthful_exit", trace_id, errors)
    require_coverage(required, observed, "crash scenarios", errors)
    return finish_report(contract_id, traces, errors, scenario_count=len(observed))


if __name__ == "__main__":
    raise SystemExit(cli_main("crash resilience", audit))
