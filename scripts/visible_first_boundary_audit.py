#!/usr/bin/env python3
"""Audit whole-perimeter visible-first boundary contacts from resolved production physics."""

from __future__ import annotations

import argparse
from collections import deque
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
    point_in_polygon,
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
    if model.get("schema_version") != 3:
        raise ContractError(
            "schema_version must be 3; regenerate exporter-owned production-physics "
            "reachability, collision-assembly parity and visible-limiter continuity evidence"
        )
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
    maximum_visible_contact_offset = number(
        contract.get("maximum_visible_contact_offset"),
        "contract.maximum_visible_contact_offset",
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
    minimum_unsafe_fringe_cells = integer(
        contract.get("minimum_unsafe_fringe_cell_count"),
        "contract.minimum_unsafe_fringe_cell_count",
        1,
    )
    minimum_unsafe_free_cells = integer(
        contract.get("minimum_unsafe_free_cell_count"),
        "contract.minimum_unsafe_free_cell_count",
        1,
    )
    required_unsafe_fringe_sides = strings(
        contract.get("required_unsafe_fringe_sides"),
        "contract.required_unsafe_fringe_sides",
        nonempty=True,
    )
    if not required_unsafe_fringe_sides <= {"north", "south", "east", "west"}:
        raise ContractError("contract.required_unsafe_fringe_sides contains an unknown side")
    maximum_reachable_unsafe_cells = integer(
        contract.get("maximum_reachable_unsafe_cells"),
        "contract.maximum_reachable_unsafe_cells",
    )
    maximum_inside_safe_no_ground_cells = integer(
        contract.get("maximum_inside_safe_no_ground_cells"),
        "contract.maximum_inside_safe_no_ground_cells",
    )
    maximum_unreachable_inside_free_cells = integer(
        contract.get("maximum_unreachable_inside_safe_free_cells"),
        "contract.maximum_unreachable_inside_safe_free_cells",
    )
    maximum_cell_size_ratio = number(
        contract.get("maximum_cell_size_to_hero_radius_ratio"),
        "contract.maximum_cell_size_to_hero_radius_ratio",
        minimum=1e-6,
    )

    errors: list[str] = []
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
            "collision_assembly_ids": strings(
                mapping.get("collision_assembly_ids"),
                f"visible cause mapping {cause_id}.collision_assembly_ids",
                nonempty=True,
            ),
        }
    safety_colliders = strings(
        model.get("safety_boundary_collider_ids"),
        "safety_boundary_collider_ids",
        nonempty=True,
    )

    collision_assemblies: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(
        array(model.get("collision_assemblies"), "collision_assemblies", nonempty=True)
    ):
        assembly = obj(raw, f"collision_assemblies[{index}]")
        assembly_id = text(assembly.get("id"), f"collision assembly {index}.id")
        if assembly_id in collision_assemblies:
            raise ContractError(f"duplicate collision assembly {assembly_id}")
        if text(
            assembly.get("source_kind"), f"collision assembly {assembly_id}.source_kind"
        ) != "exporter_resolved_production_scene":
            raise ContractError(
                f"collision assembly {assembly_id} is not exporter-resolved production-scene evidence"
            )
        intent = text(assembly.get("collision_intent"), f"collision assembly {assembly_id}.collision_intent")
        if intent not in {"surface_parity", "solid_volume_parity"}:
            raise ContractError(
                f"collision assembly {assembly_id}.collision_intent must be "
                "surface_parity or solid_volume_parity"
            )
        composite_kind = text(
            assembly.get("composite_kind"), f"collision assembly {assembly_id}.composite_kind"
        )
        if composite_kind not in {"single_asset", "modular_composite"}:
            raise ContractError(
                f"collision assembly {assembly_id}.composite_kind must be single_asset or modular_composite"
            )
        visible_root_path = text(
            assembly.get("visible_root_path"), f"collision assembly {assembly_id}.visible_root_path"
        )
        collision_root_path = text(
            assembly.get("collision_root_path"), f"collision assembly {assembly_id}.collision_root_path"
        )
        visible_members = strings(
            assembly.get("resolved_visible_member_paths"),
            f"collision assembly {assembly_id}.resolved_visible_member_paths",
            nonempty=True,
        )
        collider_records = array(
            assembly.get("resolved_collider_shapes"),
            f"collision assembly {assembly_id}.resolved_collider_shapes",
            nonempty=True,
        )
        collider_shapes: set[str] = set()
        concave_shapes: list[tuple[str, str]] = []
        for shape_index, raw_shape in enumerate(collider_records):
            shape = obj(
                raw_shape,
                f"collision assembly {assembly_id}.resolved_collider_shapes[{shape_index}]",
            )
            shape_path = text(shape.get("path"), f"collision assembly {assembly_id} shape path")
            if shape_path in collider_shapes:
                raise ContractError(f"collision assembly {assembly_id} duplicates collider shape {shape_path}")
            collider_shapes.add(shape_path)
            if boolean(shape.get("disabled"), f"collision assembly {assembly_id} shape {shape_path}.disabled"):
                raise ContractError(f"collision assembly {assembly_id} includes disabled collider shape {shape_path}")
            shape_class = text(
                shape.get("shape_class"), f"collision assembly {assembly_id} shape {shape_path}.shape_class"
            )
            owner_class = text(
                shape.get("owner_class"), f"collision assembly {assembly_id} shape {shape_path}.owner_class"
            )
            if shape_class == "ConcavePolygonShape3D":
                concave_shapes.append((shape_path, owner_class))
        if integer(
            assembly.get("expected_visible_member_count"),
            f"collision assembly {assembly_id}.expected_visible_member_count",
            1,
        ) != len(visible_members):
            raise ContractError(f"collision assembly {assembly_id} visible-member count is stale")
        if integer(
            assembly.get("expected_collider_shape_count"),
            f"collision assembly {assembly_id}.expected_collider_shape_count",
            1,
        ) != len(collider_shapes):
            raise ContractError(f"collision assembly {assembly_id} collider-shape count is stale")
        bound_visible: set[str] = set()
        bound_shapes: set[str] = set()
        for binding_index, raw_binding in enumerate(
            array(
                assembly.get("shape_bindings"),
                f"collision assembly {assembly_id}.shape_bindings",
                nonempty=True,
            )
        ):
            binding = obj(raw_binding, f"collision assembly {assembly_id} shape binding {binding_index}")
            visible_path = text(
                binding.get("visible_member_path"),
                f"collision assembly {assembly_id} shape binding {binding_index}.visible_member_path",
            )
            if visible_path not in visible_members:
                raise ContractError(
                    f"collision assembly {assembly_id} binding references unknown visible member {visible_path}"
                )
            bound_visible.add(visible_path)
            binding_shapes = strings(
                binding.get("collider_shape_paths"),
                f"collision assembly {assembly_id} shape binding {binding_index}.collider_shape_paths",
                nonempty=True,
            )
            if not binding_shapes <= collider_shapes:
                raise ContractError(f"collision assembly {assembly_id} binding references unknown collider shape")
            bound_shapes.update(binding_shapes)
        if bound_visible != visible_members or bound_shapes != collider_shapes:
            raise ContractError(
                f"collision assembly {assembly_id} shape bindings are not bidirectionally complete"
            )
        transform_parity = obj(
            assembly.get("global_transform_parity"),
            f"collision assembly {assembly_id}.global_transform_parity",
        )
        if text(
            transform_parity.get("source_kind"),
            f"collision assembly {assembly_id}.global_transform_parity.source_kind",
        ) != "exporter_resolved_scene_nodes":
            raise ContractError(f"collision assembly {assembly_id} transform parity is not exporter-resolved")
        if text(
            transform_parity.get("visible_root_path"),
            f"collision assembly {assembly_id}.global_transform_parity.visible_root_path",
        ) != visible_root_path or text(
            transform_parity.get("collision_root_path"),
            f"collision assembly {assembly_id}.global_transform_parity.collision_root_path",
        ) != collision_root_path:
            raise ContractError(f"collision assembly {assembly_id} transform parity references stale roots")
        origin_error = number(
            transform_parity.get("origin_error"),
            f"collision assembly {assembly_id}.global_transform_parity.origin_error",
            minimum=0.0,
        )
        basis_error = number(
            transform_parity.get("basis_error"),
            f"collision assembly {assembly_id}.global_transform_parity.basis_error",
            minimum=0.0,
        )
        maximum_origin_error = number(
            transform_parity.get("maximum_origin_error"),
            f"collision assembly {assembly_id}.global_transform_parity.maximum_origin_error",
            minimum=0.0,
        )
        maximum_basis_error = number(
            transform_parity.get("maximum_basis_error"),
            f"collision assembly {assembly_id}.global_transform_parity.maximum_basis_error",
            minimum=0.0,
        )
        required_approach_classes = strings(
            assembly.get("required_approach_classes"),
            f"collision assembly {assembly_id}.required_approach_classes",
            nonempty=True,
        )
        allowed_approach_classes = {"edge", "corner", "concavity", "module_seam", "opening_negative"}
        if not required_approach_classes <= allowed_approach_classes:
            raise ContractError(f"collision assembly {assembly_id} has an unknown approach class")
        text(assembly.get("raw_closeup_artifact"), f"collision assembly {assembly_id}.raw_closeup_artifact")
        collision_assemblies[assembly_id] = {
            "intent": intent,
            "composite_kind": composite_kind,
            "visible_members": visible_members,
            "collider_shapes": collider_shapes,
            "required_approach_classes": required_approach_classes,
        }
        if origin_error > maximum_origin_error + 1e-9 or basis_error > maximum_basis_error + 1e-9:
            errors.append(f"collision assembly {assembly_id} global render/collision roots are misregistered")
        if intent == "solid_volume_parity" and concave_shapes:
            errors.append(
                f"solid-volume collision assembly {assembly_id} uses concave surface collision that can be climbed or entered"
            )
        if intent == "surface_parity" and any(owner != "StaticBody3D" for _, owner in concave_shapes):
            errors.append(
                f"surface-parity collision assembly {assembly_id} uses concave collision on a non-static owner"
            )

    mapped_assembly_ids = {
        assembly_id
        for mapping in cause_mappings.values()
        for assembly_id in mapping["collision_assembly_ids"]
    }
    if mapped_assembly_ids != set(collision_assemblies):
        raise ContractError(
            "visible-cause mappings do not exactly cover exporter-resolved collision assemblies"
        )

    module_seam_declarations = array(
        model.get("declared_module_seams"), "declared_module_seams"
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

    invisible_first_count = 0
    unmapped_first_count = 0
    probe_count = 0
    used_causes: set[str] = set()
    used_safety_colliders: set[str] = set()

    reachability = obj(
        model.get("production_physics_reachability"),
        "production_physics_reachability",
    )
    if text(
        reachability.get("source_kind"),
        "production_physics_reachability.source_kind",
    ) != "exporter_resolved_production_physics_grid":
        errors.append("boundary reachability is adapter-declared rather than exporter-resolved")
    if text(reachability.get("build_id"), "production_physics_reachability.build_id") != build_id:
        errors.append("production physics reachability build_id does not match the candidate")
    if text(reachability.get("scene_path"), "production_physics_reachability.scene_path") != scene_path:
        errors.append("production physics reachability scene_path does not match provenance")
    integer(reachability.get("physics_frame"), "production_physics_reachability.physics_frame", 1)
    text(reachability.get("region_node_path"), "production_physics_reachability.region_node_path")
    text(reachability.get("hero_body_path"), "production_physics_reachability.hero_body_path")
    text(reachability.get("hero_shape_path"), "production_physics_reachability.hero_shape_path")
    if text(
        reachability.get("hero_shape_class"),
        "production_physics_reachability.hero_shape_class",
    ) != "CapsuleShape3D":
        errors.append("production physics reachability does not use the production hero capsule")
    measured_hero_radius = number(
        reachability.get("hero_radius"),
        "production_physics_reachability.hero_radius",
        minimum=1e-6,
    )
    measured_hero_height = number(
        reachability.get("hero_height"),
        "production_physics_reachability.hero_height",
        minimum=1e-6,
    )
    if abs(measured_hero_radius - hero_radius) > 1e-6 or abs(measured_hero_height - hero_height) > 1e-6:
        errors.append("production physics reachability hero capsule disagrees with the boundary contract")
    grid_origin = vec2(
        reachability.get("grid_origin"),
        "production_physics_reachability.grid_origin",
    )
    grid_width = integer(
        reachability.get("grid_width"),
        "production_physics_reachability.grid_width",
        2,
    )
    grid_height = integer(
        reachability.get("grid_height"),
        "production_physics_reachability.grid_height",
        2,
    )
    grid_cell_size = number(
        reachability.get("cell_size"),
        "production_physics_reachability.cell_size",
        minimum=1e-6,
    )
    if grid_cell_size > measured_hero_radius * maximum_cell_size_ratio + 1e-9:
        errors.append(
            f"production physics grid cell size {grid_cell_size:.4f} exceeds the "
            f"hero-radius sampling budget {measured_hero_radius * maximum_cell_size_ratio:.4f}"
        )
    integer(
        reachability.get("ground_collision_mask"),
        "production_physics_reachability.ground_collision_mask",
        1,
    )
    integer(
        reachability.get("blocker_collision_mask"),
        "production_physics_reachability.blocker_collision_mask",
        1,
    )
    number(
        reachability.get("query_margin"),
        "production_physics_reachability.query_margin",
        minimum=0.0,
    )
    if text(
        reachability.get("safe_region_source_kind"),
        "production_physics_reachability.safe_region_source_kind",
    ) != "production_scene_metadata":
        errors.append("production physics safe region is not owned by the production scene")
    safe_polygon = [
        vec2(value, f"production_physics_reachability.safe_region_polygon[{index}]")
        for index, value in enumerate(
            array(
                reachability.get("safe_region_polygon"),
                "production_physics_reachability.safe_region_polygon",
                nonempty=True,
            )
        )
    ]
    if len(safe_polygon) < 3:
        raise ContractError("production_physics_reachability.safe_region_polygon needs 3 points")
    cell_classes: dict[tuple[int, int], str] = {}
    cell_inside_safe: dict[tuple[int, int], bool] = {}
    unsafe_fringe_sides: set[str] = set()
    unsafe_fringe_count = 0
    unsafe_free_count = 0
    inside_safe_no_ground_count = 0
    for index, raw_cell in enumerate(
        array(reachability.get("cells"), "production_physics_reachability.cells", nonempty=True)
    ):
        cell = obj(raw_cell, f"production_physics_reachability.cells[{index}]")
        raw_coordinates = array(
            cell.get("cell"), f"production_physics_reachability.cells[{index}].cell"
        )
        if len(raw_coordinates) != 2:
            raise ContractError(f"production physics cell {index} needs two coordinates")
        coordinates = (
            integer(raw_coordinates[0], f"production physics cell {index}.x"),
            integer(raw_coordinates[1], f"production physics cell {index}.z"),
        )
        if not (0 <= coordinates[0] < grid_width and 0 <= coordinates[1] < grid_height):
            raise ContractError(f"production physics cell {coordinates} lies outside the grid")
        if coordinates in cell_classes:
            raise ContractError(f"duplicate production physics cell {coordinates}")
        world_xz = vec2(
            cell.get("world_xz"), f"production_physics_reachability.cells[{index}].world_xz"
        )
        expected_world = (
            grid_origin[0] + (coordinates[0] + 0.5) * grid_cell_size,
            grid_origin[1] + (coordinates[1] + 0.5) * grid_cell_size,
        )
        if distance(world_xz, expected_world) > position_tolerance + 1e-9:
            errors.append(f"production physics cell {coordinates} has a synthetic world position")
        declared_inside = boolean(
            cell.get("inside_safe_region"),
            f"production_physics_reachability.cells[{index}].inside_safe_region",
        )
        resolved_inside = point_in_polygon(world_xz, safe_polygon)
        if declared_inside != resolved_inside:
            errors.append(f"production physics cell {coordinates} safe-region flag is inconsistent")
        classification = text(
            cell.get("classification"),
            f"production_physics_reachability.cells[{index}].classification",
        )
        if classification not in {"free", "blocked", "no_ground"}:
            raise ContractError(f"production physics cell {coordinates} has unknown classification")
        if classification != "no_ground":
            number(
                cell.get("ground_y"),
                f"production_physics_reachability.cells[{index}].ground_y",
            )
            text(
                cell.get("ground_collider_id"),
                f"production_physics_reachability.cells[{index}].ground_collider_id",
            )
        cell_classes[coordinates] = classification
        cell_inside_safe[coordinates] = resolved_inside
        if resolved_inside and classification == "no_ground":
            inside_safe_no_ground_count += 1
        if not resolved_inside:
            unsafe_fringe_count += 1
            if classification == "free":
                unsafe_free_count += 1
            if coordinates[0] == 0:
                unsafe_fringe_sides.add("west")
            if coordinates[0] == grid_width - 1:
                unsafe_fringe_sides.add("east")
            if coordinates[1] == 0:
                unsafe_fringe_sides.add("north")
            if coordinates[1] == grid_height - 1:
                unsafe_fringe_sides.add("south")
    expected_cells = {(x, z) for z in range(grid_height) for x in range(grid_width)}
    if set(cell_classes) != expected_cells:
        errors.append("production physics grid does not exactly cover every declared cell")
    if unsafe_fringe_count < minimum_unsafe_fringe_cells:
        errors.append(
            f"production physics grid has {unsafe_fringe_count} unsafe-fringe cells; "
            f"minimum is {minimum_unsafe_fringe_cells}"
        )
    if unsafe_free_count < minimum_unsafe_free_cells:
        errors.append(
            f"production physics grid has {unsafe_free_count} free unsafe-fringe cells; "
            f"minimum is {minimum_unsafe_free_cells}"
        )
    if not required_unsafe_fringe_sides <= unsafe_fringe_sides:
        errors.append(
            "production physics grid does not exercise every required unsafe-fringe side"
        )
    start_cells: set[tuple[int, int]] = set()
    for index, raw_start in enumerate(
        array(reachability.get("starts"), "production_physics_reachability.starts", nonempty=True)
    ):
        start = obj(raw_start, f"production_physics_reachability.starts[{index}]")
        text(start.get("node_path"), f"production physics start {index}.node_path")
        world_position = array(
            start.get("world_position"), f"production physics start {index}.world_position"
        )
        if len(world_position) != 3:
            raise ContractError(f"production physics start {index} needs a 3D world position")
        for component_index, component in enumerate(world_position):
            number(component, f"production physics start {index}.world_position[{component_index}]")
        raw_cell = array(start.get("cell"), f"production physics start {index}.cell")
        if len(raw_cell) != 2:
            raise ContractError(f"production physics start {index} needs two cell coordinates")
        start_cell = (
            integer(raw_cell[0], f"production physics start {index}.cell.x"),
            integer(raw_cell[1], f"production physics start {index}.cell.z"),
        )
        if cell_classes.get(start_cell) != "free" or not cell_inside_safe.get(start_cell, False):
            errors.append(f"production physics start {index} is not free inside the safe region")
        start_cells.add(start_cell)
    reachable_cells = set(start_cells)
    queue: deque[tuple[int, int]] = deque(start_cells)
    while queue:
        current = queue.popleft()
        for dx, dz in (
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1),
        ):
            neighbor = (current[0] + dx, current[1] + dz)
            if (
                neighbor in reachable_cells
                or cell_classes.get(neighbor) != "free"
            ):
                continue
            reachable_cells.add(neighbor)
            queue.append(neighbor)
    reachable_unsafe_cells = {
        cell for cell in reachable_cells if not cell_inside_safe.get(cell, False)
    }
    unreachable_inside_free_cells = {
        cell
        for cell, classification in cell_classes.items()
        if classification == "free" and cell_inside_safe.get(cell, False) and cell not in reachable_cells
    }
    if len(reachable_unsafe_cells) > maximum_reachable_unsafe_cells:
        errors.append(
            f"production hero capsule reaches {len(reachable_unsafe_cells)} unsafe-fringe cells; "
            f"maximum is {maximum_reachable_unsafe_cells}"
        )
    if inside_safe_no_ground_count > maximum_inside_safe_no_ground_cells:
        errors.append(
            f"production safe region has {inside_safe_no_ground_count} no-ground cells; "
            f"maximum is {maximum_inside_safe_no_ground_cells}"
        )
    if len(unreachable_inside_free_cells) > maximum_unreachable_inside_free_cells:
        errors.append(
            f"production safe region has {len(unreachable_inside_free_cells)} unreachable free cells; "
            f"maximum is {maximum_unreachable_inside_free_cells}"
        )

    limiter_ledger = obj(
        model.get("visible_limiter_continuity"),
        "visible_limiter_continuity",
    )
    if text(
        limiter_ledger.get("source_kind"),
        "visible_limiter_continuity.source_kind",
    ) != "resolved_scene_visible_limiter_ledger":
        errors.append("visible limiter continuity ledger is not resolved-scene evidence")
    text(limiter_ledger.get("baseline_build_id"), "visible_limiter_continuity.baseline_build_id")
    text(
        limiter_ledger.get("baseline_manifest_path"),
        "visible_limiter_continuity.baseline_manifest_path",
    )
    baseline_manifest_sha256 = text(
        limiter_ledger.get("baseline_manifest_sha256"),
        "visible_limiter_continuity.baseline_manifest_sha256",
    ).lower()
    if len(baseline_manifest_sha256) != 64 or any(
        value not in "0123456789abcdef" for value in baseline_manifest_sha256
    ):
        raise ContractError("visible_limiter_continuity.baseline_manifest_sha256 must be SHA-256")
    baseline_limiter_ids = strings(
        limiter_ledger.get("baseline_limiter_ids"),
        "visible_limiter_continuity.baseline_limiter_ids",
        nonempty=True,
    )
    current_limiter_ids = strings(
        limiter_ledger.get("current_limiter_ids"),
        "visible_limiter_continuity.current_limiter_ids",
        nonempty=True,
    )
    mapped_current_limiter_ids = {
        object_id
        for mapping in cause_mappings.values()
        for object_id in mapping["object_ids"]
    }
    if current_limiter_ids != mapped_current_limiter_ids:
        errors.append(
            "current visible limiter ledger does not exactly match visible-cause mappings"
        )
    ledger_entries: set[str] = set()
    for index, raw_entry in enumerate(
        array(limiter_ledger.get("entries"), "visible_limiter_continuity.entries", nonempty=True)
    ):
        entry = obj(raw_entry, f"visible_limiter_continuity.entries[{index}]")
        limiter_id = text(entry.get("limiter_id"), f"visible limiter entry {index}.limiter_id")
        if limiter_id in ledger_entries:
            raise ContractError(f"duplicate visible limiter continuity entry {limiter_id}")
        ledger_entries.add(limiter_id)
        if limiter_id not in baseline_limiter_ids:
            errors.append(f"visible limiter continuity entry {limiter_id} is absent from baseline")
        disposition = text(
            entry.get("disposition"), f"visible limiter entry {limiter_id}.disposition"
        )
        replacement_ids = strings(
            entry.get("replacement_visible_cause_ids"),
            f"visible limiter entry {limiter_id}.replacement_visible_cause_ids",
        )
        affected_spans = strings(
            entry.get("affected_span_ids"),
            f"visible limiter entry {limiter_id}.affected_span_ids",
            nonempty=True,
        )
        if not affected_spans <= set(spans):
            errors.append(f"visible limiter entry {limiter_id} references unknown perimeter spans")
        if disposition == "retained":
            if limiter_id not in current_limiter_ids or replacement_ids:
                errors.append(f"retained visible limiter {limiter_id} is missing or names replacements")
        elif disposition == "replaced_with_continuity_proof":
            if limiter_id in current_limiter_ids:
                errors.append(f"replaced visible limiter {limiter_id} still appears in current IDs")
            if not replacement_ids or not replacement_ids <= current_limiter_ids:
                errors.append(f"visible limiter {limiter_id} lacks current visible replacements")
            proof = obj(
                entry.get("continuity_proof"),
                f"visible limiter entry {limiter_id}.continuity_proof",
            )
            proof_kinds = strings(
                proof.get("proof_kinds"),
                f"visible limiter entry {limiter_id}.continuity_proof.proof_kinds",
                nonempty=True,
            )
            if not {"production_physics_reachability", "visible_first_perimeter"} <= proof_kinds:
                errors.append(
                    f"visible limiter {limiter_id} replacement lacks whole-body and first-hit proof"
                )
            for phase in ("before", "fixed", "rerun"):
                artifact = obj(
                    proof.get(phase),
                    f"visible limiter entry {limiter_id}.continuity_proof.{phase}",
                )
                text(
                    artifact.get("build_id"),
                    f"visible limiter entry {limiter_id}.continuity_proof.{phase}.build_id",
                )
                text(
                    artifact.get("raw_artifact"),
                    f"visible limiter entry {limiter_id}.continuity_proof.{phase}.raw_artifact",
                )
            rerun = obj(proof.get("rerun"), "visible limiter continuity rerun")
            if text(
                rerun.get("build_id"),
                f"visible limiter entry {limiter_id}.continuity_proof.rerun.build_id",
            ) != build_id:
                errors.append(f"visible limiter {limiter_id} continuity rerun is stale")
        else:
            errors.append(
                f"visible limiter {limiter_id} has unsupported disposition {disposition}; "
                "boundary limiters cannot be deleted without mapped replacement continuity"
            )
    if ledger_entries != baseline_limiter_ids:
        errors.append("visible limiter continuity entries do not exactly cover baseline limiters")

    def inspect_hits(
        label: str,
        raw_hits: Any,
        span: dict[str, Any],
        sample_assembly_id: str,
    ) -> None:
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
                    if sample_assembly_id not in mapping["collision_assembly_ids"]:
                        errors.append(
                            f"{label} visible cause {cause_id} is not bound to collision assembly "
                            f"{sample_assembly_id}"
                        )
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
                render_contact_distance = number(
                    hit.get("render_contact_distance"),
                    f"{label} visible cause render_contact_distance",
                    minimum=0.0,
                )
                if abs(render_contact_distance - hit_distance) > maximum_visible_contact_offset + 1e-9:
                    errors.append(
                        f"{label} collider/render contact offset "
                        f"{abs(render_contact_distance - hit_distance):.4f} exceeds the visible-edge budget"
                    )
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
    sample_metadata: dict[str, tuple[str, str]] = {}
    approaches_by_assembly: dict[str, set[str]] = {
        assembly_id: set() for assembly_id in collision_assemblies
    }
    samples_by_span: dict[str, dict[int, dict[str, Any]]] = {span_id: {} for span_id in spans}
    samples = array(model.get("samples"), "samples", nonempty=True)
    for index, raw in enumerate(samples):
        sample = obj(raw, f"samples[{index}]")
        sample_id = text(sample.get("id"), f"samples[{index}].id")
        if sample_id in seen_sample_ids:
            raise ContractError(f"duplicate sample ID {sample_id}")
        seen_sample_ids.add(sample_id)
        assembly_id = text(
            sample.get("collision_assembly_id"), f"sample {sample_id}.collision_assembly_id"
        )
        if assembly_id not in collision_assemblies:
            raise ContractError(f"sample {sample_id} references unknown collision assembly {assembly_id}")
        approach_class = text(sample.get("approach_class"), f"sample {sample_id}.approach_class")
        if approach_class not in {"edge", "corner", "concavity", "module_seam", "opening_negative"}:
            raise ContractError(f"sample {sample_id} has unsupported approach class {approach_class}")
        approaches_by_assembly[assembly_id].add(approach_class)
        sample_metadata[sample_id] = (assembly_id, approach_class)
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
            inspect_hits(
                f"sample {sample_id}", sample.get("ordered_hits"), spans[span_id], assembly_id
            )
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
                    assembly_id,
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
    for assembly_id, assembly in collision_assemblies.items():
        missing_approaches = assembly["required_approach_classes"] - approaches_by_assembly[assembly_id]
        if missing_approaches:
            errors.append(
                f"collision assembly {assembly_id} lacks production-capsule approaches "
                f"for {sorted(missing_approaches)}"
            )

    seam_ids: set[str] = set()
    modular_assemblies_with_seams: set[str] = set()
    for seam_index, raw_seam in enumerate(module_seam_declarations):
        seam = obj(raw_seam, f"declared_module_seams[{seam_index}]")
        seam_id = text(seam.get("id"), f"declared module seam {seam_index}.id")
        if seam_id in seam_ids:
            raise ContractError(f"duplicate declared module seam {seam_id}")
        seam_ids.add(seam_id)
        seam_assemblies = strings(
            seam.get("collision_assembly_ids"),
            f"declared module seam {seam_id}.collision_assembly_ids",
            nonempty=True,
        )
        if not seam_assemblies <= set(collision_assemblies):
            raise ContractError(f"declared module seam {seam_id} references unknown assemblies")
        modular_assemblies_with_seams.update(seam_assemblies)
        visible_paths = strings(
            seam.get("visible_member_paths"),
            f"declared module seam {seam_id}.visible_member_paths",
            nonempty=True,
        )
        collider_paths = strings(
            seam.get("collider_shape_paths"),
            f"declared module seam {seam_id}.collider_shape_paths",
            nonempty=True,
        )
        allowed_visible_paths = set().union(
            *(collision_assemblies[value]["visible_members"] for value in seam_assemblies)
        )
        allowed_collider_paths = set().union(
            *(collision_assemblies[value]["collider_shapes"] for value in seam_assemblies)
        )
        if not visible_paths <= allowed_visible_paths or not collider_paths <= allowed_collider_paths:
            raise ContractError(f"declared module seam {seam_id} references unresolved members or shapes")
        seam_samples = strings(
            seam.get("sample_ids"), f"declared module seam {seam_id}.sample_ids", nonempty=True
        )
        for sample_id in seam_samples:
            metadata = sample_metadata.get(sample_id)
            if metadata is None:
                errors.append(f"declared module seam {seam_id} references missing sample {sample_id}")
            elif metadata[0] not in seam_assemblies or metadata[1] != "module_seam":
                errors.append(
                    f"declared module seam {seam_id} sample {sample_id} is not a matching module-seam approach"
                )
        if text(
            seam.get("visual_continuity_status"),
            f"declared module seam {seam_id}.visual_continuity_status",
        ) != "pass":
            errors.append(f"declared module seam {seam_id} has no passing visual-continuity result")
        if text(
            seam.get("collision_continuity_status"),
            f"declared module seam {seam_id}.collision_continuity_status",
        ) != "pass":
            errors.append(f"declared module seam {seam_id} has no passing collision-continuity result")
        text(seam.get("raw_closeup_artifact"), f"declared module seam {seam_id}.raw_closeup_artifact")
    for assembly_id, assembly in collision_assemblies.items():
        if assembly["composite_kind"] == "modular_composite" and assembly_id not in modular_assemblies_with_seams:
            errors.append(f"modular collision assembly {assembly_id} has no declared seam coverage")

    traversal_trials = array(model.get("solid_volume_traversal_trials"), "solid_volume_traversal_trials")
    solid_trial_approaches: dict[str, set[str]] = {
        assembly_id: set()
        for assembly_id, assembly in collision_assemblies.items()
        if assembly["intent"] == "solid_volume_parity"
    }
    trial_ids: set[str] = set()
    for trial_index, raw_trial in enumerate(traversal_trials):
        trial = obj(raw_trial, f"solid_volume_traversal_trials[{trial_index}]")
        trial_id = text(trial.get("id"), f"solid-volume traversal trial {trial_index}.id")
        if trial_id in trial_ids:
            raise ContractError(f"duplicate solid-volume traversal trial {trial_id}")
        trial_ids.add(trial_id)
        assembly_id = text(
            trial.get("collision_assembly_id"),
            f"solid-volume traversal trial {trial_id}.collision_assembly_id",
        )
        if assembly_id not in solid_trial_approaches:
            raise ContractError(
                f"solid-volume traversal trial {trial_id} references a non-solid-volume assembly"
            )
        if text(
            trial.get("source_kind"), f"solid-volume traversal trial {trial_id}.source_kind"
        ) != "production_characterbody_motion_trace":
            raise ContractError(f"solid-volume traversal trial {trial_id} is not production-body evidence")
        if text(
            trial.get("production_body_path"),
            f"solid-volume traversal trial {trial_id}.production_body_path",
        ) != text(
            reachability.get("hero_body_path"), "production_physics_reachability.hero_body_path"
        ):
            errors.append(f"solid-volume traversal trial {trial_id} uses a different body")
        approach_class = text(
            trial.get("approach_class"), f"solid-volume traversal trial {trial_id}.approach_class"
        )
        if approach_class not in collision_assemblies[assembly_id]["required_approach_classes"]:
            errors.append(f"solid-volume traversal trial {trial_id} has an undeclared approach class")
        solid_trial_approaches[assembly_id].add(approach_class)
        if not boolean(
            trial.get("blocked_before_occupied_volume"),
            f"solid-volume traversal trial {trial_id}.blocked_before_occupied_volume",
        ):
            errors.append(f"solid-volume traversal trial {trial_id} was not blocked by visible mass")
        if boolean(
            trial.get("entered_occupied_volume"),
            f"solid-volume traversal trial {trial_id}.entered_occupied_volume",
        ):
            errors.append(f"solid-volume traversal trial {trial_id} entered the occupied volume")
        elevation_gain = number(
            trial.get("maximum_elevation_gain"),
            f"solid-volume traversal trial {trial_id}.maximum_elevation_gain",
            minimum=0.0,
        )
        allowed_elevation_gain = number(
            trial.get("maximum_allowed_elevation_gain"),
            f"solid-volume traversal trial {trial_id}.maximum_allowed_elevation_gain",
            minimum=0.0,
        )
        if elevation_gain > allowed_elevation_gain + 1e-9:
            errors.append(f"solid-volume traversal trial {trial_id} climbs the impassable assembly")
        text(trial.get("raw_motion_artifact"), f"solid-volume traversal trial {trial_id}.raw_motion_artifact")
    for assembly_id, approaches in solid_trial_approaches.items():
        missing_trials = collision_assemblies[assembly_id]["required_approach_classes"] - approaches
        if missing_trials:
            errors.append(
                f"solid-volume collision assembly {assembly_id} lacks production-body traversal trials "
                f"for {sorted(missing_trials)}"
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
    text(
        raw_evidence.get("production_physics_grid_artifact"),
        "raw_evidence.production_physics_grid_artifact",
    )
    text(
        raw_evidence.get("production_physics_contact_sheet_artifact"),
        "raw_evidence.production_physics_contact_sheet_artifact",
    )
    text(
        raw_evidence.get("visible_limiter_continuity_artifact"),
        "raw_evidence.visible_limiter_continuity_artifact",
    )
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
        "collision_assembly_count": len(collision_assemblies),
        "solid_volume_collision_assembly_count": sum(
            value["intent"] == "solid_volume_parity"
            for value in collision_assemblies.values()
        ),
        "module_seam_count": len(seam_ids),
        "solid_volume_traversal_trial_count": len(trial_ids),
        "safety_boundary_collider_count": len(safety_colliders),
        "production_physics_grid_cell_count": len(cell_classes),
        "production_physics_free_cell_count": sum(
            value == "free" for value in cell_classes.values()
        ),
        "production_physics_reachable_cell_count": len(reachable_cells),
        "production_physics_unsafe_fringe_cell_count": unsafe_fringe_count,
        "production_physics_unsafe_free_cell_count": unsafe_free_count,
        "production_physics_reachable_unsafe_cell_count": len(reachable_unsafe_cells),
        "production_physics_inside_safe_no_ground_cell_count": inside_safe_no_ground_count,
        "production_physics_unreachable_inside_free_cell_count": len(
            unreachable_inside_free_cells
        ),
        "baseline_visible_limiter_count": len(baseline_limiter_ids),
        "current_visible_limiter_count": len(current_limiter_ids),
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
