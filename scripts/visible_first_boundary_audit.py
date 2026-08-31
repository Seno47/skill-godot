#!/usr/bin/env python3
"""Audit whole-perimeter visible-first boundary contacts from resolved production physics."""

from __future__ import annotations

import argparse
from math import acos, ceil, degrees, hypot
import json
from pathlib import Path
import sys
from typing import Any

from environment_integrity_audit import (
    ContractError,
    Vec2,
    array,
    boolean,
    integer,
    number,
    obj,
    strings,
    text,
    vec2,
)
from resolved_scene_provenance_audit import (
    ProvenanceError,
    validate_scene_provenance_reference,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit deterministic inward-to-outward perimeter probes so visible geometry "
            "is contacted before any safety-only boundary."
        )
    )
    parser.add_argument("--model", required=True)
    parser.add_argument("--json-output")
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args()


def read_json(value: str) -> dict[str, Any]:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise ContractError(f"model not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"could not read model {path}: {exc}") from exc
    return obj(data, "model root")


def distance(first: Vec2, second: Vec2) -> float:
    return hypot(first[0] - second[0], first[1] - second[1])


def normalize(value: Vec2, label: str) -> Vec2:
    length = hypot(value[0], value[1])
    if length <= 1e-10:
        raise ContractError(f"{label} must not be zero")
    return value[0] / length, value[1] / length


def direction_error_degrees(first: Vec2, second: Vec2) -> float:
    first_n = normalize(first, "sample direction")
    second_n = normalize(second, "span outward direction")
    dot = max(-1.0, min(1.0, first_n[0] * second_n[0] + first_n[1] * second_n[1]))
    return degrees(acos(dot))


def segment_points(start: Vec2, end: Vec2, spacing: float) -> list[Vec2]:
    length = distance(start, end)
    if length <= 1e-10:
        raise ContractError("declared perimeter span start/end must differ")
    parts = max(1, int(ceil(length / spacing)))
    return [
        (
            start[0] + (end[0] - start[0]) * index / parts,
            start[1] + (end[1] - start[1]) * index / parts,
        )
        for index in range(parts + 1)
    ]


def audit(model: dict[str, Any]) -> dict[str, Any]:
    if model.get("schema_version") != 1:
        raise ContractError("schema_version must be 1")
    contract_id = text(model.get("contract_id"), "contract_id")
    build_id = text(model.get("build_id"), "build_id")
    raw_provenance = obj(model.get("scene_provenance"), "scene_provenance")
    try:
        provenance = validate_scene_provenance_reference(raw_provenance)
    except ProvenanceError as exc:
        raise ContractError(str(exc)) from exc
    scene_path = provenance["scene_path"]
    text(raw_provenance.get("boundary_query"), "scene_provenance.boundary_query")

    contract = obj(model.get("contract"), "contract")
    if text(contract.get("coordinate_system"), "contract.coordinate_system") != "godot_xz_y_up":
        raise ContractError("contract.coordinate_system must be godot_xz_y_up")
    hero_radius = number(contract.get("hero_radius"), "contract.hero_radius", minimum=1e-6)
    hero_height = number(contract.get("hero_height"), "contract.hero_height", minimum=1e-6)
    maximum_spacing = number(
        contract.get("maximum_sample_spacing"),
        "contract.maximum_sample_spacing",
        minimum=1e-6,
    )
    if maximum_spacing > hero_radius * 2.0 + 1e-9:
        raise ContractError(
            "contract.maximum_sample_spacing must be <= the production hero diameter"
        )
    maximum_ray_gap = number(
        contract.get("maximum_ray_bundle_gap"),
        "contract.maximum_ray_bundle_gap",
        minimum=1e-6,
    )
    if maximum_ray_gap > hero_radius + 1e-9:
        raise ContractError(
            "contract.maximum_ray_bundle_gap must be <= the production hero radius"
        )
    position_tolerance = number(
        contract.get("sample_position_tolerance"),
        "contract.sample_position_tolerance",
        minimum=0.0,
    )
    direction_tolerance = number(
        contract.get("direction_tolerance_degrees"),
        "contract.direction_tolerance_degrees",
        minimum=0.0,
    )
    minimum_clearance = number(
        contract.get("minimum_visible_to_safety_clearance"),
        "contract.minimum_visible_to_safety_clearance",
        minimum=0.0,
    )
    expected_span_count = integer(
        contract.get("expected_span_count"), "contract.expected_span_count", 1
    )
    expected_sample_count = integer(
        contract.get("expected_sample_count"), "contract.expected_sample_count", 1
    )
    maximum_invisible_first = integer(
        contract.get("maximum_invisible_first_hits"),
        "contract.maximum_invisible_first_hits",
    )
    maximum_unmapped_first = integer(
        contract.get("maximum_unmapped_first_hits"),
        "contract.maximum_unmapped_first_hits",
    )

    cause_mappings: dict[str, dict[str, set[str]]] = {}
    for index, raw in enumerate(
        array(model.get("visible_cause_mappings"), "visible_cause_mappings", nonempty=True)
    ):
        mapping = obj(raw, f"visible_cause_mappings[{index}]")
        cause_id = text(mapping.get("id"), f"visible cause mapping {index}.id")
        if cause_id in cause_mappings:
            raise ContractError(f"duplicate visible cause mapping {cause_id}")
        cause_mappings[cause_id] = {
            "object_ids": strings(
                mapping.get("object_ids"), f"visible cause mapping {cause_id}.object_ids", nonempty=True
            ),
            "collider_ids": strings(
                mapping.get("collider_ids"), f"visible cause mapping {cause_id}.collider_ids", nonempty=True
            ),
            "render_shell_ids": strings(
                mapping.get("render_shell_ids"),
                f"visible cause mapping {cause_id}.render_shell_ids",
                nonempty=True,
            ),
        }
    safety_colliders = strings(
        model.get("safety_boundary_collider_ids"),
        "safety_boundary_collider_ids",
        nonempty=True,
    )

    spans: dict[str, dict[str, Any]] = {}
    span_expected_points: dict[str, list[Vec2]] = {}
    for index, raw in enumerate(
        array(model.get("declared_perimeter_spans"), "declared_perimeter_spans", nonempty=True)
    ):
        span = obj(raw, f"declared_perimeter_spans[{index}]")
        span_id = text(span.get("id"), f"declared perimeter span {index}.id")
        if span_id in spans:
            raise ContractError(f"duplicate declared perimeter span {span_id}")
        start = vec2(span.get("start"), f"declared perimeter span {span_id}.start")
        end = vec2(span.get("end"), f"declared perimeter span {span_id}.end")
        outward = normalize(
            vec2(span.get("outward_direction"), f"declared perimeter span {span_id}.outward_direction"),
            f"declared perimeter span {span_id}.outward_direction",
        )
        spacing = number(
            span.get("sample_spacing"),
            f"declared perimeter span {span_id}.sample_spacing",
            minimum=1e-6,
        )
        if spacing > maximum_spacing + 1e-9:
            raise ContractError(
                f"declared perimeter span {span_id} sample spacing exceeds contract maximum"
            )
        points = segment_points(start, end, spacing)
        declared_count = integer(
            span.get("expected_sample_count"),
            f"declared perimeter span {span_id}.expected_sample_count",
            2,
        )
        if declared_count != len(points):
            raise ContractError(
                f"declared perimeter span {span_id} expected_sample_count {declared_count} "
                f"does not match deterministic spacing count {len(points)}"
            )
        span_safety = strings(
            span.get("safety_boundary_collider_ids"),
            f"declared perimeter span {span_id}.safety_boundary_collider_ids",
        )
        if not span_safety <= safety_colliders:
            raise ContractError(
                f"declared perimeter span {span_id} references unknown safety boundary colliders"
            )
        requires_safety = boolean(
            span.get("safety_backstop_required"),
            f"declared perimeter span {span_id}.safety_backstop_required",
        )
        if requires_safety and not span_safety:
            raise ContractError(
                f"declared perimeter span {span_id} requires a safety backstop but lists none"
            )
        text(
            span.get("raw_overview_artifact"),
            f"declared perimeter span {span_id}.raw_overview_artifact",
        )
        spans[span_id] = {
            "outward": outward,
            "safety": span_safety,
            "requires_safety": requires_safety,
        }
        span_expected_points[span_id] = points
    if len(spans) != expected_span_count:
        raise ContractError(
            f"declared perimeter has {len(spans)} spans; expected {expected_span_count}"
        )

    errors: list[str] = []
    invisible_first_count = 0
    unmapped_first_count = 0
    probe_count = 0
    used_causes: set[str] = set()
    used_safety_colliders: set[str] = set()

    def inspect_hits(label: str, raw_hits: Any, span: dict[str, Any]) -> None:
        nonlocal invisible_first_count, unmapped_first_count, probe_count
        probe_count += 1
        hits = array(raw_hits, f"{label}.ordered_hits", nonempty=True)
        parsed: list[tuple[float, str, dict[str, Any]]] = []
        previous_distance = -1.0
        for hit_index, raw_hit in enumerate(hits):
            hit = obj(raw_hit, f"{label}.ordered_hits[{hit_index}]")
            hit_distance = number(
                hit.get("distance"), f"{label}.ordered_hits[{hit_index}].distance", minimum=0.0
            )
            if hit_distance <= previous_distance + 1e-9:
                errors.append(f"{label} hit distances are not strictly increasing")
            previous_distance = hit_distance
            hit_kind = text(hit.get("kind"), f"{label}.ordered_hits[{hit_index}].kind")
            if hit_kind not in {"visible_cause", "safety_boundary", "unmapped"}:
                errors.append(f"{label} has unsupported hit kind {hit_kind}")
            parsed.append((hit_distance, hit_kind, hit))

        first_distance, first_kind, _ = parsed[0]
        if first_kind == "safety_boundary":
            invisible_first_count += 1
            errors.append(f"{label} contacts an invisible safety boundary before a visible cause")
        elif first_kind != "visible_cause":
            unmapped_first_count += 1
            errors.append(f"{label} first contact is not a mapped visible cause")

        first_visible_distance: float | None = None
        first_safety_distance: float | None = None
        for hit_distance, hit_kind, hit in parsed:
            if hit_kind == "visible_cause":
                cause_id = text(hit.get("cause_id"), f"{label} visible cause ID")
                object_id = text(hit.get("object_id"), f"{label} visible cause object_id")
                collider_id = text(hit.get("collider_id"), f"{label} visible cause collider_id")
                render_shell_id = text(
                    hit.get("render_shell_id"), f"{label} visible cause render_shell_id"
                )
                mapping = cause_mappings.get(cause_id)
                if mapping is None:
                    errors.append(f"{label} references unknown visible cause mapping {cause_id}")
                else:
                    used_causes.add(cause_id)
                    if object_id not in mapping["object_ids"]:
                        errors.append(f"{label} visible cause object {object_id} is not mapped")
                    if collider_id not in mapping["collider_ids"]:
                        errors.append(f"{label} visible cause collider {collider_id} is not mapped")
                    if render_shell_id not in mapping["render_shell_ids"]:
                        errors.append(
                            f"{label} visible cause render shell {render_shell_id} is not mapped"
                        )
                if first_visible_distance is None:
                    first_visible_distance = hit_distance
            elif hit_kind == "safety_boundary":
                collider_id = text(hit.get("collider_id"), f"{label} safety collider_id")
                if collider_id not in safety_colliders:
                    errors.append(f"{label} references unknown safety boundary collider {collider_id}")
                if collider_id not in span["safety"]:
                    errors.append(f"{label} safety boundary collider {collider_id} is not owned by its span")
                used_safety_colliders.add(collider_id)
                if first_safety_distance is None:
                    first_safety_distance = hit_distance

        if span["requires_safety"] and first_safety_distance is None:
            errors.append(f"{label} does not exercise its required safety backstop")
        if first_safety_distance is not None and first_visible_distance is not None:
            clearance = first_safety_distance - first_visible_distance
            if clearance + 1e-9 < minimum_clearance:
                errors.append(
                    f"{label} visible-to-safety clearance {clearance:.4f} is below contract minimum"
                )
        if first_kind == "visible_cause" and first_visible_distance != first_distance:
            errors.append(f"{label} first visible cause parsing is inconsistent")

    seen_sample_ids: set[str] = set()
    samples_by_span: dict[str, dict[int, dict[str, Any]]] = {span_id: {} for span_id in spans}
    samples = array(model.get("samples"), "samples", nonempty=True)
    for index, raw in enumerate(samples):
        sample = obj(raw, f"samples[{index}]")
        sample_id = text(sample.get("id"), f"samples[{index}].id")
        if sample_id in seen_sample_ids:
            raise ContractError(f"duplicate sample ID {sample_id}")
        seen_sample_ids.add(sample_id)
        span_id = text(sample.get("span_id"), f"sample {sample_id}.span_id")
        if span_id not in spans:
            raise ContractError(f"sample {sample_id} references unknown span {span_id}")
        sample_index = integer(sample.get("sample_index"), f"sample {sample_id}.sample_index")
        if sample_index in samples_by_span[span_id]:
            raise ContractError(f"span {span_id} duplicates sample index {sample_index}")
        samples_by_span[span_id][sample_index] = sample

        expected_points = span_expected_points[span_id]
        if sample_index >= len(expected_points):
            errors.append(f"sample {sample_id} index lies outside its declared span")
        else:
            origin = vec2(sample.get("origin"), f"sample {sample_id}.origin")
            if distance(origin, expected_points[sample_index]) > position_tolerance + 1e-9:
                errors.append(f"sample {sample_id} does not match its deterministic span position")
        direction = vec2(sample.get("direction"), f"sample {sample_id}.direction")
        if direction_error_degrees(direction, spans[span_id]["outward"]) > direction_tolerance + 1e-9:
            errors.append(f"sample {sample_id} does not point inward-to-outward for its span")

        probe_kind = text(sample.get("probe_kind"), f"sample {sample_id}.probe_kind")
        if probe_kind == "capsule_sweep":
            if number(sample.get("probe_radius"), f"sample {sample_id}.probe_radius", minimum=0.0) + 1e-9 < hero_radius:
                errors.append(f"sample {sample_id} capsule radius is smaller than the production hero")
            if number(sample.get("probe_height"), f"sample {sample_id}.probe_height", minimum=0.0) + 1e-9 < hero_height:
                errors.append(f"sample {sample_id} capsule height is smaller than the production hero")
            inspect_hits(f"sample {sample_id}", sample.get("ordered_hits"), spans[span_id])
        elif probe_kind == "ray_bundle":
            rays = array(sample.get("ray_probes"), f"sample {sample_id}.ray_probes", nonempty=True)
            offsets: list[float] = []
            for ray_index, raw_ray in enumerate(rays):
                ray = obj(raw_ray, f"sample {sample_id}.ray_probes[{ray_index}]")
                offset = number(
                    ray.get("lateral_offset"),
                    f"sample {sample_id}.ray_probes[{ray_index}].lateral_offset",
                )
                offsets.append(offset)
                inspect_hits(
                    f"sample {sample_id} ray {ray_index}",
                    ray.get("ordered_hits"),
                    spans[span_id],
                )
            ordered_offsets = sorted(offsets)
            if len(set(offsets)) != len(offsets):
                errors.append(f"sample {sample_id} ray bundle has duplicate lateral offsets")
            if ordered_offsets[0] > -hero_radius + position_tolerance or ordered_offsets[-1] < hero_radius - position_tolerance:
                errors.append(f"sample {sample_id} ray bundle does not cover the production hero width")
            if any(
                second - first > maximum_ray_gap + 1e-9
                for first, second in zip(ordered_offsets, ordered_offsets[1:])
            ):
                errors.append(f"sample {sample_id} ray bundle has an uncovered lateral gap")
        else:
            raise ContractError(
                f"sample {sample_id}.probe_kind must be capsule_sweep or ray_bundle"
            )

    if len(samples) != expected_sample_count:
        errors.append(f"perimeter has {len(samples)} samples; expected {expected_sample_count}")
    for span_id, expected_points in span_expected_points.items():
        expected_indices = set(range(len(expected_points)))
        actual_indices = set(samples_by_span[span_id])
        if actual_indices != expected_indices:
            missing = sorted(expected_indices - actual_indices)
            extra = sorted(actual_indices - expected_indices)
            errors.append(
                f"declared perimeter span {span_id} has sample-index gaps; missing={missing} extra={extra}"
            )
    if used_causes != set(cause_mappings):
        errors.append(
            "visible cause mappings are not exercised exactly by whole-perimeter probes"
        )
    if used_safety_colliders != safety_colliders:
        errors.append(
            "safety boundary collider manifest is not exercised exactly by whole-perimeter probes"
        )
    if invisible_first_count > maximum_invisible_first:
        errors.append(
            f"whole-perimeter probes have {invisible_first_count} invisible-first contacts; "
            f"maximum is {maximum_invisible_first}"
        )
    if unmapped_first_count > maximum_unmapped_first:
        errors.append(
            f"whole-perimeter probes have {unmapped_first_count} unmapped-first contacts; "
            f"maximum is {maximum_unmapped_first}"
        )

    raw_evidence = obj(model.get("raw_evidence"), "raw_evidence")
    if text(raw_evidence.get("source_kind"), "raw_evidence.source_kind") != "resolved_production_physics":
        errors.append("visible-first boundary evidence is not from resolved production physics")
    if text(raw_evidence.get("build_id"), "raw_evidence.build_id") != build_id:
        errors.append("visible-first boundary evidence build_id does not match the contract")
    if text(raw_evidence.get("scene_path"), "raw_evidence.scene_path") != scene_path:
        errors.append("visible-first boundary evidence scene_path does not match provenance")
    integer(raw_evidence.get("physics_map_iteration"), "raw_evidence.physics_map_iteration", 1)
    integer(raw_evidence.get("collision_mask"), "raw_evidence.collision_mask", 1)
    text(raw_evidence.get("raw_trace_artifact"), "raw_evidence.raw_trace_artifact")
    text(raw_evidence.get("raw_overview_artifact"), "raw_evidence.raw_overview_artifact")
    detected = strings(
        raw_evidence.get("detected_defect_classes"),
        "raw_evidence.detected_defect_classes",
    )
    resolved: set[str] = set()
    for index, raw in enumerate(
        array(raw_evidence.get("defect_resolutions"), "raw_evidence.defect_resolutions")
    ):
        item = obj(raw, f"raw_evidence.defect_resolutions[{index}]")
        defect_class = text(item.get("class"), f"defect resolution {index}.class")
        if defect_class in resolved:
            raise ContractError(f"duplicate defect resolution class {defect_class}")
        resolved.add(defect_class)
        for phase in ("before", "fixed", "rerun"):
            artifact = obj(item.get(phase), f"defect resolution {defect_class}.{phase}")
            text(artifact.get("build_id"), f"defect resolution {defect_class}.{phase}.build_id")
            text(
                artifact.get("raw_artifact"),
                f"defect resolution {defect_class}.{phase}.raw_artifact",
            )
        if text(
            obj(item.get("rerun"), "rerun").get("build_id"),
            f"defect resolution {defect_class}.rerun.build_id",
        ) != build_id:
            errors.append(f"defect resolution {defect_class} rerun does not match candidate build")
    if resolved != detected:
        errors.append("visible-first before/fixed/rerun classes do not match detected classes")

    return {
        "status": "pass" if not errors else "fail",
        "contract_id": contract_id,
        "build_id": build_id,
        "scene_provenance": {
            "source_kind": provenance["source_kind"],
            "scene_path": provenance["scene_path"],
            "revision_kind": provenance["revision_kind"],
            "dependency_closure_digest": provenance["dependency_closure_digest"],
            "manifest_path": provenance["manifest_path"],
            "manifest_sha256": provenance["manifest_sha256"],
            "exporter": provenance["exporter"],
            "exporter_sha256": provenance["exporter_sha256"],
            "export_preset": provenance["export_preset"],
            "export_preset_sha256": provenance["export_preset_sha256"],
        },
        "perimeter_span_count": len(spans),
        "perimeter_sample_count": len(samples),
        "physics_probe_count": probe_count,
        "visible_cause_mapping_count": len(cause_mappings),
        "safety_boundary_collider_count": len(safety_colliders),
        "invisible_first_hit_count": invisible_first_count,
        "unmapped_first_hit_count": unmapped_first_count,
        "errors": errors,
    }


def main() -> int:
    args = parse_args()
    try:
        report = audit(read_json(args.model))
        if args.json_output:
            output = Path(args.json_output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        marker = "PASS" if report["status"] == "pass" else "FAIL"
        print(
            f"[{marker}] visible-first-boundary id={report['contract_id']} "
            f"spans={report['perimeter_span_count']} samples={report['perimeter_sample_count']} "
            f"probes={report['physics_probe_count']} "
            f"invisible_first={report['invisible_first_hit_count']} "
            f"errors={len(report['errors'])}"
        )
        for error in report["errors"]:
            print(f"[ERROR] {error}")
        return 0 if report["status"] == "pass" else 1
    except ContractError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
