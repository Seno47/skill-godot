#!/usr/bin/env python3
"""Audit engine/project upgrade fixtures, migrations, skew, and rollback."""

from contract_probe_utils import (
    ContractError, array, boolean, cli_main, contract_header, finish_report, integer,
    require_coverage, require_target_pass, require_true, strings, text, trace_header,
)


def audit(model):
    contract_id, _, contract = contract_header(model)
    required = strings(contract.get("required_scenarios"), "required_scenarios", nonempty=True)
    for key in ("source_engine", "target_engine", "source_revision", "target_revision"):
        text(contract.get(key), key)
    if not boolean(contract.get("immutable_fixtures"), "immutable_fixtures"):
        raise ContractError("upgrade fixtures must be immutable")
    traces = array(model.get("traces"), "traces", nonempty=True)
    errors, seen_ids, observed = [], set(), set()
    for index, raw in enumerate(traces):
        trace, trace_id, scenario = trace_header(raw, index, seen_ids)
        observed.add(scenario)
        require_target_pass(trace, trace_id, errors)
        for key in ("source_fixture_hash_matched", "migration_idempotent", "stable_ids_preserved", "explicit_result"):
            require_true(trace, key, trace_id, errors)
        if integer(trace.get("data_loss_records"), f"trace {trace_id}.data_loss_records"):
            errors.append(f"trace {trace_id} loses records")
        if integer(trace.get("unclassified_errors"), f"trace {trace_id}.unclassified_errors"):
            errors.append(f"trace {trace_id} has unclassified errors")
        if scenario in {"rollback", "downgrade_rejection"}:
            require_true(trace, "backup_preserved", trace_id, errors)
        if scenario == "mixed_client_server":
            require_true(trace, "version_window_enforced", trace_id, errors)
    require_coverage(required, observed, "upgrade scenarios", errors)
    return finish_report(contract_id, traces, errors, scenario_count=len(observed))


if __name__ == "__main__":
    raise SystemExit(cli_main("upgrade compatibility", audit))
