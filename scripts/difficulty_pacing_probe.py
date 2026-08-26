#!/usr/bin/env python3
"""Audit a declared genre-aware difficulty and pacing envelope."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
from typing import Any


GENRE_PROFILES = {
    "puzzle",
    "action",
    "horror_survival",
    "platformer_metroidvania",
    "roguelite_procedural",
    "rpg_progression",
    "strategy_management",
    "racing_vehicle",
    "extraction_survival",
    "competitive_multiplayer",
    "cooperative_director",
    "narrative",
    "sandbox_open_world",
    "idle_incremental",
    "custom",
}
CURVE_MODELS = {
    "authored_wave",
    "chapter_sawtooth",
    "director_paced",
    "skill_bands",
    "self_selected_routes",
    "run_escalation",
    "puzzle_mastery",
    "custom",
}
DIFFICULTY_DIMENSIONS = {
    "execution",
    "cognition",
    "time_pressure",
    "resource_pressure",
    "punishment",
    "uncertainty",
    "coordination",
    "navigation_information",
}
PHASES = {"teach", "practice", "twist", "combine", "test", "peak", "recovery", "choice", "reset"}
ADAPTATION_POLICIES = {"none", "explicit_difficulty", "assist_only", "adaptive_director", "matchmaking"}
WAVE_MODELS = {"authored_wave", "chapter_sawtooth", "director_paced", "run_escalation"}


class ContractError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit a project-declared difficulty envelope without imposing one universal curve."
    )
    parser.add_argument("--contract", required=True, help="Difficulty/pacing contract JSON.")
    parser.add_argument("--json-output", help="Optional full JSON report path.")
    parser.add_argument("--summary", action="store_true", help="Print only verdict and failures.")
    return parser.parse_args()


def object_value(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    return value


def required_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value.strip()


def unique_strings(value: Any, label: str, *, allow_empty: bool = True) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ContractError(f"{label} must be an array of non-empty strings")
    if not allow_empty and not value:
        raise ContractError(f"{label} must not be empty")
    if len(value) != len(set(value)):
        raise ContractError(f"{label} must not contain duplicates")
    return value


def decimal_value(value: Any, label: str, *, minimum: Decimal = Decimal(0), maximum: Decimal = Decimal(5)) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ContractError(f"{label} must be a finite decimal string or number")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ContractError(f"{label} is not a decimal") from exc
    if not result.is_finite() or result < minimum or result > maximum:
        raise ContractError(f"{label} must be in [{minimum}, {maximum}]")
    return result


def integer_value(value: Any, label: str, *, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContractError(f"{label} must be an integer >= {minimum}")
    return value


def boolean_value(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ContractError(f"{label} must be a boolean")
    return value


def main() -> int:
    args = parse_args()
    contract_path = Path(args.contract).expanduser().resolve()
    try:
        if not contract_path.is_file():
            raise ContractError(f"contract not found: {contract_path}")
        data = json.loads(contract_path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise ContractError("contract root must be an object")
        if data.get("schema_version") != 1:
            raise ContractError("schema_version must be 1")
        contract_id = required_text(data.get("contract_id"), "contract_id")
        build_id = required_text(data.get("build_id"), "build_id")

        declared = object_value(data.get("contract"), "contract")
        genre_profile = required_text(declared.get("genre_profile"), "contract.genre_profile")
        if genre_profile not in GENRE_PROFILES:
            raise ContractError(f"contract.genre_profile is unknown: {genre_profile}")
        secondary_profiles = unique_strings(declared.get("secondary_profiles", []), "contract.secondary_profiles")
        unknown_secondary = sorted(set(secondary_profiles) - GENRE_PROFILES)
        if unknown_secondary:
            raise ContractError(f"unknown secondary profiles: {', '.join(unknown_secondary)}")
        curve_model = required_text(declared.get("curve_model"), "contract.curve_model")
        if curve_model not in CURVE_MODELS:
            raise ContractError(f"contract.curve_model is unknown: {curve_model}")
        required_text(declared.get("rationale"), "contract.rationale")
        required_dimensions = unique_strings(
            declared.get("required_dimensions"), "contract.required_dimensions", allow_empty=False
        )
        unknown_dimensions = sorted(set(required_dimensions) - DIFFICULTY_DIMENSIONS)
        if unknown_dimensions:
            raise ContractError(f"unknown required dimensions: {', '.join(unknown_dimensions)}")
        required_phases = unique_strings(
            declared.get("required_phases"), "contract.required_phases", allow_empty=False
        )
        unknown_phases = sorted(set(required_phases) - PHASES)
        if unknown_phases:
            raise ContractError(f"unknown required phases: {', '.join(unknown_phases)}")
        required_cohorts = unique_strings(
            declared.get("required_cohorts"), "contract.required_cohorts", allow_empty=False
        )
        required_sources = unique_strings(
            declared.get("required_evidence_sources"),
            "contract.required_evidence_sources",
            allow_empty=False,
        )
        if "target_build" not in required_sources:
            raise ContractError("required_evidence_sources must include target_build")

        definitions = object_value(data.get("dimension_definitions"), "dimension_definitions")
        for dimension in required_dimensions:
            required_text(definitions.get(dimension), f"dimension_definitions.{dimension}")

        budgets = object_value(data.get("budgets"), "budgets")
        max_rises = integer_value(
            budgets.get("max_consecutive_challenge_rises"),
            "budgets.max_consecutive_challenge_rises",
            minimum=1,
        )
        max_novelty = integer_value(
            budgets.get("max_new_dimensions_per_beat"),
            "budgets.max_new_dimensions_per_beat",
            minimum=0,
        )
        max_peak_recovery = integer_value(
            budgets.get("max_beats_from_peak_to_recovery"),
            "budgets.max_beats_from_peak_to_recovery",
            minimum=1,
        )
        onboarding_cap = decimal_value(
            budgets.get("onboarding_pressure_cap"), "budgets.onboarding_pressure_cap"
        )
        max_typical_attempts = integer_value(
            budgets.get("max_typical_attempts_per_test"),
            "budgets.max_typical_attempts_per_test",
            minimum=1,
        )

        adaptation = object_value(data.get("adaptation"), "adaptation")
        adaptation_policy = required_text(adaptation.get("policy"), "adaptation.policy")
        if adaptation_policy not in ADAPTATION_POLICIES:
            raise ContractError(f"adaptation.policy is unknown: {adaptation_policy}")
        adaptation_surfaces = unique_strings(adaptation.get("surfaces", []), "adaptation.surfaces")
        adaptation_flags = {
            key: boolean_value(adaptation.get(key), f"adaptation.{key}")
            for key in (
                "bounded",
                "cooldown_or_hysteresis",
                "player_control_or_disclosure",
                "outcome_integrity_preserved",
                "reward_value_preserved",
                "ranked_midmatch_outcome_manipulation",
            )
        }

        errors: list[str] = []
        if adaptation_policy == "none" and adaptation_surfaces:
            errors.append("adaptation.policy none must not declare adjustment surfaces")
        if adaptation_policy != "none" and not adaptation_surfaces:
            errors.append(f"adaptation.policy {adaptation_policy} requires at least one surface")
        if adaptation_policy in {"assist_only", "adaptive_director", "matchmaking"}:
            for key in (
                "bounded",
                "cooldown_or_hysteresis",
                "player_control_or_disclosure",
                "outcome_integrity_preserved",
                "reward_value_preserved",
            ):
                if not adaptation_flags[key]:
                    errors.append(f"adaptation.{key} must be true for {adaptation_policy}")
        if adaptation_flags["ranked_midmatch_outcome_manipulation"]:
            errors.append("ranked mid-match outcome manipulation must be false")
        if genre_profile == "competitive_multiplayer" and adaptation_policy != "matchmaking":
            errors.append("competitive_multiplayer requires matchmaking rather than hidden mid-match DDA")
        if curve_model == "director_paced" and adaptation_policy != "adaptive_director":
            errors.append("director_paced requires adaptation.policy adaptive_director")

        beats_raw = data.get("beats")
        if not isinstance(beats_raw, list) or len(beats_raw) < 2:
            raise ContractError("beats must contain at least two ordered beats")
        beat_ids: list[str] = []
        seen_phases: set[str] = set()
        introduced_skills: set[str] = set()
        used_dimensions: set[str] = set()
        challenges: list[Decimal] = []
        peak_indices: list[int] = []
        recovery_indices: list[int] = []
        test_ids: list[str] = []
        branches: set[str] = set()
        combine_uses: list[list[str]] = []
        max_observed_novelty = 0

        for index, raw_beat in enumerate(beats_raw):
            beat = object_value(raw_beat, f"beats[{index}]")
            beat_id = required_text(beat.get("id"), f"beats[{index}].id")
            if beat_id in beat_ids:
                errors.append(f"duplicate beat ID: {beat_id}")
            beat_ids.append(beat_id)
            order = integer_value(beat.get("order"), f"beat {beat_id} order", minimum=1)
            if order != index + 1:
                errors.append(f"beat {beat_id} order must be {index + 1}, got {order}")
            phase = required_text(beat.get("phase"), f"beat {beat_id} phase")
            if phase not in PHASES:
                errors.append(f"beat {beat_id} has unknown phase {phase}")
            seen_phases.add(phase)
            if phase == "peak":
                peak_indices.append(index)
            if phase in {"recovery", "reset"}:
                recovery_indices.append(index)
            if phase == "test":
                test_ids.append(beat_id)

            challenge = decimal_value(beat.get("challenge"), f"beat {beat_id} challenge")
            decimal_value(beat.get("intensity"), f"beat {beat_id} intensity")
            challenges.append(challenge)
            dimensions = object_value(beat.get("dimensions"), f"beat {beat_id} dimensions")
            missing_values = sorted(set(required_dimensions) - set(dimensions))
            unknown_values = sorted(set(dimensions) - DIFFICULTY_DIMENSIONS)
            if missing_values:
                errors.append(f"beat {beat_id} lacks dimensions: {', '.join(missing_values)}")
            if unknown_values:
                errors.append(f"beat {beat_id} has unknown dimensions: {', '.join(unknown_values)}")
            for dimension, value in dimensions.items():
                parsed = decimal_value(value, f"beat {beat_id} dimension {dimension}")
                if parsed > 0:
                    used_dimensions.add(dimension)

            new_dimensions = unique_strings(
                beat.get("new_dimensions", []), f"beat {beat_id} new_dimensions"
            )
            if not set(new_dimensions) <= set(required_dimensions):
                errors.append(f"beat {beat_id} introduces an undeclared difficulty dimension")
            max_observed_novelty = max(max_observed_novelty, len(new_dimensions))
            if len(new_dimensions) > max_novelty:
                errors.append(
                    f"beat {beat_id} introduces {len(new_dimensions)} dimensions; budget is {max_novelty}"
                )

            introduces = unique_strings(
                beat.get("introduces_skills", []), f"beat {beat_id} introduces_skills"
            )
            uses = unique_strings(beat.get("uses_skills", []), f"beat {beat_id} uses_skills")
            duplicate_introductions = sorted(set(introduces) & introduced_skills)
            if duplicate_introductions:
                errors.append(
                    f"beat {beat_id} re-introduces skills: {', '.join(duplicate_introductions)}"
                )
            legal_skills = introduced_skills | set(introduces)
            future_uses = sorted(set(uses) - legal_skills)
            if future_uses:
                errors.append(f"beat {beat_id} uses skills before teaching: {', '.join(future_uses)}")
            if phase in {"combine", "test", "peak"} and introduces:
                errors.append(f"beat {beat_id} phase {phase} must not introduce an unpracticed skill")
            if phase == "combine":
                combine_uses.append(uses)
            introduced_skills.update(introduces)

            recovery_available = boolean_value(
                beat.get("recovery_available"), f"beat {beat_id} recovery_available"
            )
            if phase in {"recovery", "reset"} and not recovery_available:
                errors.append(f"beat {beat_id} is {phase} but recovery_available is false")
            onboarding = beat.get("onboarding", phase == "teach")
            if not isinstance(onboarding, bool):
                errors.append(f"beat {beat_id} onboarding must be a boolean")
            elif onboarding and challenge > onboarding_cap:
                errors.append(
                    f"beat {beat_id} onboarding challenge {challenge} exceeds cap {onboarding_cap}"
                )
            branches.add(required_text(beat.get("branch_id"), f"beat {beat_id} branch_id"))

        missing_phases = sorted(set(required_phases) - seen_phases)
        if missing_phases:
            errors.append(f"missing required phases: {', '.join(missing_phases)}")
        missing_dimensions = sorted(set(required_dimensions) - used_dimensions)
        if missing_dimensions:
            errors.append(f"required dimensions never become active: {', '.join(missing_dimensions)}")

        consecutive_rises = 0
        max_observed_rises = 0
        downward_transitions = 0
        for previous, current in zip(challenges, challenges[1:]):
            if current > previous:
                consecutive_rises += 1
                max_observed_rises = max(max_observed_rises, consecutive_rises)
            else:
                if current < previous:
                    downward_transitions += 1
                consecutive_rises = 0
        if max_observed_rises > max_rises:
            errors.append(
                f"maximum consecutive challenge rises {max_observed_rises} exceeds {max_rises}"
            )

        max_observed_peak_recovery = 0
        for peak_index in peak_indices:
            later_recovery = next((item for item in recovery_indices if item > peak_index), None)
            if later_recovery is None:
                errors.append(f"peak beat {beat_ids[peak_index]} has no later recovery/reset beat")
                continue
            distance = later_recovery - peak_index
            max_observed_peak_recovery = max(max_observed_peak_recovery, distance)
            if distance > max_peak_recovery:
                errors.append(
                    f"peak beat {beat_ids[peak_index]} reaches recovery after {distance} beats; budget is {max_peak_recovery}"
                )
        if curve_model in WAVE_MODELS:
            if not peak_indices or not recovery_indices:
                errors.append(f"curve model {curve_model} requires peak and recovery/reset phases")
            if downward_transitions == 0:
                errors.append(f"curve model {curve_model} requires at least one challenge decrease")
        if curve_model == "puzzle_mastery":
            required_puzzle_phases = {"teach", "practice", "combine", "test"}
            absent = sorted(required_puzzle_phases - seen_phases)
            if absent:
                errors.append(f"puzzle_mastery lacks phases: {', '.join(absent)}")
            if not any(len(items) >= 2 for items in combine_uses):
                errors.append("puzzle_mastery requires a combine beat using at least two learned skills")
        if curve_model == "self_selected_routes":
            if len(branches) < 2 or "choice" not in seen_phases:
                errors.append("self_selected_routes requires a choice phase and at least two branch IDs")

        observations_raw = data.get("observations")
        if not isinstance(observations_raw, list) or not observations_raw:
            raise ContractError("observations must be a non-empty array")
        observation_ids: set[str] = set()
        observed_cohorts: set[str] = set()
        observed_sources: set[str] = set()
        target_build_coverage: set[str] = set()
        typical_target_test_attempts: dict[str, int] = {}
        beat_id_set = set(beat_ids)
        for index, raw_observation in enumerate(observations_raw):
            observation = object_value(raw_observation, f"observations[{index}]")
            observation_id = required_text(observation.get("id"), f"observations[{index}].id")
            if observation_id in observation_ids:
                errors.append(f"duplicate observation ID: {observation_id}")
            observation_ids.add(observation_id)
            cohort = required_text(observation.get("cohort"), f"observation {observation_id} cohort")
            source = required_text(observation.get("source"), f"observation {observation_id} source")
            observed_cohorts.add(cohort)
            observed_sources.add(source)
            completed = unique_strings(
                observation.get("completed_beat_ids"),
                f"observation {observation_id} completed_beat_ids",
                allow_empty=False,
            )
            unknown_beats = sorted(set(completed) - beat_id_set)
            if unknown_beats:
                errors.append(
                    f"observation {observation_id} names unknown beats: {', '.join(unknown_beats)}"
                )
            if source == "target_build":
                target_build_coverage.update(completed)
            attempts = object_value(
                observation.get("test_attempts", {}), f"observation {observation_id} test_attempts"
            )
            for beat_id, value in attempts.items():
                if beat_id not in test_ids:
                    errors.append(f"observation {observation_id} records attempts for non-test beat {beat_id}")
                    continue
                parsed_attempts = integer_value(
                    value, f"observation {observation_id} attempts {beat_id}", minimum=1
                )
                if cohort == "typical" and source == "target_build":
                    typical_target_test_attempts[beat_id] = parsed_attempts

        missing_cohorts = sorted(set(required_cohorts) - observed_cohorts)
        missing_sources = sorted(set(required_sources) - observed_sources)
        missing_target_beats = sorted(beat_id_set - target_build_coverage)
        if missing_cohorts:
            errors.append(f"missing required cohorts: {', '.join(missing_cohorts)}")
        if missing_sources:
            errors.append(f"missing required evidence sources: {', '.join(missing_sources)}")
        if missing_target_beats:
            errors.append(f"target-build observations do not cover beats: {', '.join(missing_target_beats)}")
        for beat_id in test_ids:
            attempts = typical_target_test_attempts.get(beat_id)
            if attempts is None:
                errors.append(f"test beat {beat_id} lacks typical target-build attempt evidence")
            elif attempts > max_typical_attempts:
                errors.append(
                    f"test beat {beat_id} typical attempts {attempts} exceed budget {max_typical_attempts}"
                )

        report = {
            "status": "pass" if not errors else "fail",
            "contract_id": contract_id,
            "build_id": build_id,
            "genre_profile": genre_profile,
            "secondary_profiles": secondary_profiles,
            "curve_model": curve_model,
            "adaptation_policy": adaptation_policy,
            "beat_count": len(beats_raw),
            "observation_count": len(observations_raw),
            "metrics": {
                "challenge_min": str(min(challenges)),
                "challenge_max": str(max(challenges)),
                "max_consecutive_challenge_rises": max_observed_rises,
                "challenge_decreases": downward_transitions,
                "max_new_dimensions_per_beat": max_observed_novelty,
                "max_beats_from_peak_to_recovery": max_observed_peak_recovery,
                "target_build_beats_covered": len(target_build_coverage & beat_id_set),
                "required_beats": len(beat_ids),
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
            f"[{label}] difficulty-pacing contract={contract_id} genre={genre_profile} "
            f"beats={len(beats_raw)} errors={len(errors)}"
        )
        if errors:
            for error in errors:
                print(f"[ERROR] {error}")
        elif not args.summary:
            print(json.dumps(report["metrics"], indent=2, ensure_ascii=False))
        return 0 if not errors else 1
    except (OSError, json.JSONDecodeError, ContractError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
