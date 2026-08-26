#!/usr/bin/env python3
"""Audit semantic accessibility, assistive-tech, and non-visual operation evidence."""

from contract_probe_utils import (
    array, boolean, cli_main, contract_header, finish_report, integer,
    require_coverage, require_target_pass, require_true, strings, text, trace_header,
)


def audit(model):
    contract_id, _, contract = contract_header(model)
    required_scenarios = strings(contract.get("required_scenarios"), "required_scenarios", nonempty=True)
    required_tech = strings(contract.get("required_assistive_technology"), "required_assistive_technology", nonempty=True)
    strings(contract.get("target_platforms"), "target_platforms", nonempty=True)
    traces = array(model.get("traces"), "traces", nonempty=True)
    errors, seen_ids, scenarios, technologies = [], set(), set(), set()
    for index, raw in enumerate(traces):
        trace, trace_id, scenario = trace_header(raw, index, seen_ids)
        tech = text(trace.get("assistive_technology"), f"trace {trace_id}.assistive_technology")
        scenarios.add(scenario); technologies.add(tech)
        require_target_pass(trace, trace_id, errors)
        for key in ("semantic_names_roles_states_valid", "logical_order", "actions_supported", "fully_operable", "behavioral_effect_observed", "non_color_cues"):
            require_true(trace, key, trace_id, errors)
        for key in ("focus_traps", "announcement_spam", "unlabeled_critical_controls"):
            if integer(trace.get(key), f"trace {trace_id}.{key}"):
                errors.append(f"trace {trace_id} reports non-zero {key}")
        if scenario == "dynamic_live_region":
            require_true(trace, "bounded_dynamic_announcement", trace_id, errors)
        if scenario == "subtitles":
            require_true(trace, "speaker_and_critical_audio_cues", trace_id, errors)
    require_coverage(required_scenarios, scenarios, "accessibility scenarios", errors)
    require_coverage(required_tech, technologies, "assistive technologies", errors)
    return finish_report(contract_id, traces, errors, scenario_count=len(scenarios), technology_count=len(technologies))


if __name__ == "__main__":
    raise SystemExit(cli_main("assistive accessibility", audit))
