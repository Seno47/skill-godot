#!/usr/bin/env python3
"""Resolve one or more rubric cases into a stable fail-closed composite."""

from __future__ import annotations

from typing import Any


class CaseCompositionError(RuntimeError):
    pass


def case_definitions(rubric: dict[str, Any]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    order: list[str] = []
    definitions: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(rubric.get("cases", [])):
        if not isinstance(item, dict):
            raise CaseCompositionError(f"rubric.cases[{index}] must be an object")
        case_id = item.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise CaseCompositionError(f"rubric.cases[{index}].id must be a non-empty string")
        case_id = case_id.strip()
        if case_id in definitions:
            raise CaseCompositionError(f"duplicate rubric case ID: {case_id}")
        order.append(case_id)
        definitions[case_id] = item
    return order, definitions


def resolve_case_selector(
    rubric: dict[str, Any], selector: str
) -> tuple[str, list[str], dict[str, Any]]:
    if not isinstance(selector, str) or not selector.strip():
        raise CaseCompositionError("case selector must be a non-empty string")
    order, definitions = case_definitions(rubric)
    raw = selector.strip()
    if raw in definitions:
        return raw, [raw], definitions[raw]
    requested = [item.strip() for item in raw.replace(",", "+").split("+") if item.strip()]
    if len(requested) < 2:
        raise CaseCompositionError(f"unknown case ID: {raw}")
    if len(requested) != len(set(requested)):
        raise CaseCompositionError("composite case selector contains duplicates")
    unknown = sorted(set(requested) - set(definitions))
    if unknown:
        raise CaseCompositionError(f"unknown case IDs: {', '.join(unknown)}")
    selected = [case_id for case_id in order if case_id in requested]
    canonical = "+".join(selected)

    focus: list[str] = []
    minimum_scores: dict[str, int | float] = {}
    briefs: list[str] = []
    for case_id in selected:
        definition = definitions[case_id]
        brief = definition.get("brief")
        if isinstance(brief, str) and brief.strip():
            briefs.append(f"{case_id}: {brief.strip()}")
        case_focus = definition.get("focus", [])
        if not isinstance(case_focus, list) or any(not isinstance(item, str) for item in case_focus):
            raise CaseCompositionError(f"case {case_id}.focus must be an array of strings")
        for item in case_focus:
            if item not in focus:
                focus.append(item)
        scores = definition.get("minimum_scores", {})
        if not isinstance(scores, dict):
            raise CaseCompositionError(f"case {case_id}.minimum_scores must be an object")
        for dimension, value in scores.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise CaseCompositionError(
                    f"case {case_id}.minimum_scores.{dimension} must be numeric"
                )
            minimum_scores[dimension] = max(minimum_scores.get(dimension, value), value)

    composed = {
        "id": canonical,
        "component_cases": selected,
        "brief": "Composite fail-closed evaluation. " + " ".join(briefs),
        "focus": focus,
        "minimum_scores": minimum_scores,
    }
    return canonical, selected, composed


def gate_applies(definition: dict[str, Any], selected_cases: list[str]) -> bool:
    cases = definition.get("cases")
    if cases is None:
        return True
    if not isinstance(cases, list) or not cases:
        raise CaseCompositionError("gate cases must be a non-empty array when present")
    return any(case_id in cases for case_id in selected_cases)
