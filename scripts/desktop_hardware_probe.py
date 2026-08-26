#!/usr/bin/env python3
"""Audit real desktop hardware, renderer, display, window, and input evidence."""

from contract_probe_utils import (
    ContractError, array, boolean, cli_main, contract_header, finish_report, integer, number, obj,
    require_coverage, require_target_pass, require_true, strings, text, trace_header,
)


def audit(model):
    contract_id, _, contract = contract_header(model)
    required_scenarios = strings(contract.get("required_scenarios"), "required_scenarios", nonempty=True)
    required_profiles = strings(contract.get("required_profiles"), "required_profiles", nonempty=True)
    min_fps = number(contract.get("minimum_fps"), "minimum_fps", 1)
    max_memory = integer(contract.get("maximum_memory_mb"), "maximum_memory_mb", 1)
    profiles = {}
    for index, raw in enumerate(array(contract.get("profiles"), "profiles", nonempty=True)):
        profile = obj(raw, f"profiles[{index}]")
        profile_id = text(profile.get("id"), f"profiles[{index}].id")
        profiles[profile_id] = profile
        for key in ("os", "gpu_class", "renderer"):
            text(profile.get(key), f"profile {profile_id}.{key}")
        if not boolean(profile.get("real_machine"), f"profile {profile_id}.real_machine"):
            raise ContractError(f"profile {profile_id} is not a real machine")
    traces = array(model.get("traces"), "traces", nonempty=True)
    errors, seen_ids, scenarios, covered_profiles = [], set(), set(), set()
    for index, raw in enumerate(traces):
        trace, trace_id, scenario = trace_header(raw, index, seen_ids)
        profile_id = text(trace.get("profile"), f"trace {trace_id}.profile")
        scenarios.add(scenario); covered_profiles.add(profile_id)
        require_target_pass(trace, trace_id, errors)
        if profile_id not in profiles:
            errors.append(f"trace {trace_id} references unknown profile {profile_id}")
        for key in ("no_crash", "materials_valid", "input_recovered", "window_onscreen", "settings_persisted"):
            require_true(trace, key, trace_id, errors)
        if integer(trace.get("ui_clipping_defects"), f"trace {trace_id}.ui_clipping_defects"):
            errors.append(f"trace {trace_id} has UI clipping")
        if number(trace.get("minimum_observed_fps"), f"trace {trace_id}.minimum_observed_fps") < min_fps:
            errors.append(f"trace {trace_id} falls below FPS budget")
        if integer(trace.get("peak_memory_mb"), f"trace {trace_id}.peak_memory_mb") > max_memory:
            errors.append(f"trace {trace_id} exceeds memory budget")
    require_coverage(required_scenarios, scenarios, "desktop scenarios", errors)
    require_coverage(required_profiles, covered_profiles, "desktop profiles", errors)
    return finish_report(contract_id, traces, errors, profile_count=len(covered_profiles), scenario_count=len(scenarios))


if __name__ == "__main__":
    raise SystemExit(cli_main("desktop hardware", audit))
