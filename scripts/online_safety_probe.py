#!/usr/bin/env python3
"""Audit hostile-client, integrity, reporting, sanctions, and privacy evidence."""

from contract_probe_utils import (
    ContractError, array, boolean, cli_main, contract_header, finish_report, integer,
    require_coverage, require_target_pass, require_true, strings, trace_header,
)


def audit(model):
    contract_id, _, contract = contract_header(model)
    required = strings(contract.get("required_scenarios"), "required_scenarios", nonempty=True)
    for key in ("server_authoritative", "integrity_signal_is_not_sole_evidence", "appeal_or_review_path"):
        if not boolean(contract.get(key), key):
            raise ContractError(f"{key} must be true")
    if boolean(contract.get("secrets_embedded"), "secrets_embedded"):
        raise ContractError("online client embeds secrets")
    traces = array(model.get("traces"), "traces", nonempty=True)
    errors, seen_ids, observed = [], set(), set()
    for index, raw in enumerate(traces):
        trace, trace_id, scenario = trace_header(raw, index, seen_ids)
        observed.add(scenario)
        require_target_pass(trace, trace_id, errors)
        for key in ("safe_state", "server_validated", "sanction_idempotent", "clear_user_message"):
            require_true(trace, key, trace_id, errors)
        if boolean(trace.get("client_can_ban"), f"trace {trace_id}.client_can_ban"):
            errors.append(f"trace {trace_id} grants sanction authority to the client")
        for key in ("private_evidence_excess", "cross_user_data"):
            if integer(trace.get(key), f"trace {trace_id}.{key}"):
                errors.append(f"trace {trace_id} reports non-zero {key}")
        if scenario == "suspicious_integrity_signal":
            require_true(trace, "tiered_response", trace_id, errors)
        elif scenario == "false_positive_review":
            require_true(trace, "reversible", trace_id, errors)
            require_true(trace, "reviewed", trace_id, errors)
        elif scenario == "player_report":
            require_true(trace, "authenticated", trace_id, errors)
            require_true(trace, "rate_limited", trace_id, errors)
        elif scenario == "mute_block":
            require_true(trace, "immediate_and_persistent", trace_id, errors)
        elif scenario == "sanction_expiry":
            require_true(trace, "access_restored", trace_id, errors)
        elif scenario == "privacy_delete":
            require_true(trace, "deletion_completed", trace_id, errors)
    require_coverage(required, observed, "online-safety scenarios", errors)
    return finish_report(contract_id, traces, errors, scenario_count=len(observed))


if __name__ == "__main__":
    raise SystemExit(cli_main("online safety", audit))
