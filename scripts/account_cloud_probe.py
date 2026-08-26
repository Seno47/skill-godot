#!/usr/bin/env python3
"""Audit account linking, cloud conflicts, user switching, and deletion."""

from contract_probe_utils import (
    array, boolean, cli_main, contract_header, finish_report, integer,
    require_coverage, require_target_pass, require_true, strings, text, trace_header,
)


def audit(model):
    contract_id, _, contract = contract_header(model)
    required = strings(contract.get("required_scenarios"), "required_scenarios", nonempty=True)
    text(contract.get("conflict_policy"), "conflict_policy")
    traces = array(model.get("traces"), "traces", nonempty=True)
    errors, seen_ids, observed = [], set(), set()
    conflicts = {"link_guest_conflict", "multi_device_conflict", "offline_reconnect"}
    for index, raw in enumerate(traces):
        trace, trace_id, scenario = trace_header(raw, index, seen_ids)
        observed.add(scenario)
        require_target_pass(trace, trace_id, errors)
        for key in ("safe_state", "stable_player_id", "merge_idempotent"):
            require_true(trace, key, trace_id, errors)
        for key in ("cross_user_writes", "silent_overwrites", "sensitive_log_fields"):
            if integer(trace.get(key), f"trace {trace_id}.{key}"):
                errors.append(f"trace {trace_id} reports non-zero {key}")
        if text(trace.get("local_cloud_digest"), f"trace {trace_id}.local_cloud_digest") != text(trace.get("expected_digest"), f"trace {trace_id}.expected_digest"):
            errors.append(f"trace {trace_id} resolved to an unexpected digest")
        if scenario in conflicts:
            chose = boolean(trace.get("user_choice_present"), f"trace {trace_id}.user_choice_present")
            merged = boolean(trace.get("deterministic_merge"), f"trace {trace_id}.deterministic_merge")
            backup = boolean(trace.get("preserved_backup"), f"trace {trace_id}.preserved_backup")
            if not chose and not (merged and backup):
                errors.append(f"trace {trace_id} silently resolves a conflict without choice or backup")
        if scenario in {"user_switch", "sign_out"}:
            require_true(trace, "previous_user_detached", trace_id, errors)
            require_true(trace, "new_user_isolated", trace_id, errors)
        if scenario == "account_delete":
            require_true(trace, "deletion_completed", trace_id, errors)
            require_true(trace, "local_tokens_cleared", trace_id, errors)
    require_coverage(required, observed, "account/cloud scenarios", errors)
    return finish_report(contract_id, traces, errors, scenario_count=len(observed))


if __name__ == "__main__":
    raise SystemExit(cli_main("account and cloud", audit))
