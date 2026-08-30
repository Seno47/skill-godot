#!/usr/bin/env python3
"""Audit whole-map surface topology, camera survey, collider shells, and occluder aliases."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from math import ceil, hypot
from pathlib import Path
import sys
from typing import Any

from environment_integrity_audit import (
    ContractError,
    GroundTriangle,
    Vec2,
    array,
    boolean,
    cross,
    integer,
    number,
    obj,
    point_in_polygon,
    strings,
    text,
    top_surface_at,
    vec2,
    vec3,
)


@dataclass(frozen=True)
class Zone:
    zone_id: str
    role: str
    polygon: tuple[Vec2, ...]
    expected_family: str
    expected_classes: frozenset[str]
    fallback_classes: frozenset[str]
    max_fallback_ratio: float


@dataclass(frozen=True)
class Collider:
    collider_id: str
    source_node: str
    enabled: bool
    blocks_hero: bool
    visibility_exempt: bool
    variant_id: str
    footprint: tuple[Vec2, ...]
    min_y: float
    max_y: float
    shell_ids: tuple[str, ...]


@dataclass(frozen=True)
class RenderShell:
    shell_id: str
    source_node: str
    visible: bool
    variant_id: str
    footprint: tuple[Vec2, ...]
    min_y: float
    max_y: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit whole-map high-angle 3D coverage after local environment-integrity checks."
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


def polygon(value: Any, label: str) -> tuple[Vec2, ...]:
    result = tuple(
        vec2(item, f"{label}[{index}]")
        for index, item in enumerate(array(value, label, nonempty=True))
    )
    if len(result) < 3:
        raise ContractError(f"{label} needs at least three points")
    area = 0.0
    for index, start in enumerate(result):
        end = result[(index + 1) % len(result)]
        area += start[0] * end[1] - end[0] * start[1]
    if abs(area) <= 1e-10:
        raise ContractError(f"{label} is degenerate")
    return result


def ratio(value: Any, label: str) -> float:
    result = number(value, label, minimum=0.0)
    if result > 1.0:
        raise ContractError(f"{label} must be <= 1")
    return result


def grid_samples(footprint: tuple[Vec2, ...], step: float) -> dict[tuple[int, int], Vec2]:
    min_x = min(point[0] for point in footprint)
    max_x = max(point[0] for point in footprint)
    min_z = min(point[1] for point in footprint)
    max_z = max(point[1] for point in footprint)
    x_count = max(1, int(ceil((max_x - min_x) / step)))
    z_count = max(1, int(ceil((max_z - min_z) / step)))
    dx = (max_x - min_x) / x_count
    dz = (max_z - min_z) / z_count
    result: dict[tuple[int, int], Vec2] = {}
    for x_index in range(x_count):
        x = min_x + (x_index + 0.5) * dx
        for z_index in range(z_count):
            z = min_z + (z_index + 0.5) * dz
            if point_in_polygon((x, z), list(footprint)):
                result[(x_index, z_index)] = (x, z)
    return result


def point_segment_distance(point: Vec2, start: Vec2, end: Vec2) -> float:
    dx, dz = end[0] - start[0], end[1] - start[1]
    length_squared = dx * dx + dz * dz
    if length_squared <= 1e-20:
        return hypot(point[0] - start[0], point[1] - start[1])
    projection = (
        (point[0] - start[0]) * dx + (point[1] - start[1]) * dz
    ) / length_squared
    projection = max(0.0, min(1.0, projection))
    nearest = (start[0] + projection * dx, start[1] + projection * dz)
    return hypot(point[0] - nearest[0], point[1] - nearest[1])


def point_polygon_distance(point: Vec2, shape: tuple[Vec2, ...]) -> float:
    if point_in_polygon(point, list(shape)):
        return 0.0
    return min(
        point_segment_distance(point, start, shape[(index + 1) % len(shape)])
        for index, start in enumerate(shape)
    )


def parse_triangles(value: Any) -> list[GroundTriangle]:
    triangles: list[GroundTriangle] = []
    seen: set[str] = set()
    for index, raw in enumerate(array(value, "render_ground_triangles", nonempty=True)):
        item = obj(raw, f"render_ground_triangles[{index}]")
        triangle_id = text(item.get("id"), f"render_ground_triangles[{index}].id")
        if triangle_id in seen:
            raise ContractError(f"duplicate render-ground triangle ID {triangle_id}")
        seen.add(triangle_id)
        if text(item.get("source_kind"), f"triangle {triangle_id}.source_kind") != "render_mesh":
            raise ContractError(f"triangle {triangle_id} is not sourced from render_mesh")
        text(item.get("source_node"), f"triangle {triangle_id}.source_node")
        surface_class = text(item.get("surface_class"), f"triangle {triangle_id}.surface_class")
        material_id = text(item.get("material_id"), f"triangle {triangle_id}.material_id")
        vertices = tuple(
            vec3(vertex, f"triangle {triangle_id}.vertices[{corner}]")
            for corner, vertex in enumerate(
                array(item.get("vertices"), f"triangle {triangle_id}.vertices")
            )
        )
        if len(vertices) != 3:
            raise ContractError(f"triangle {triangle_id} must contain exactly three vertices")
        projected_area = abs(
            cross(
                (vertices[0][0], vertices[0][2]),
                (vertices[1][0], vertices[1][2]),
                (vertices[2][0], vertices[2][2]),
            )
        )
        if projected_area <= 1e-10:
            raise ContractError(f"triangle {triangle_id} is degenerate in XZ")
        triangles.append(
            GroundTriangle(
                triangle_id,
                surface_class,
                material_id,
                vertices,  # type: ignore[arg-type]
                (
                    min(point[0] for point in vertices),
                    min(point[2] for point in vertices),
                    max(point[0] for point in vertices),
                    max(point[2] for point in vertices),
                ),
            )
        )
    return triangles


def audit(model: dict[str, Any]) -> dict[str, Any]:
    if model.get("schema_version") != 1:
        raise ContractError("schema_version must be 1")
    contract_id = text(model.get("contract_id"), "contract_id")
    build_id = text(model.get("build_id"), "build_id")
    provenance = obj(model.get("scene_provenance"), "scene_provenance")
    if text(provenance.get("source_kind"), "scene_provenance.source_kind") != "resolved_target_scene":
        raise ContractError("scene_provenance.source_kind must be resolved_target_scene")
    scene_path = text(provenance.get("scene_path"), "scene_provenance.scene_path")
    text(provenance.get("scene_revision"), "scene_provenance.scene_revision")
    text(provenance.get("exporter"), "scene_provenance.exporter")
    text(provenance.get("visible_prop_query"), "scene_provenance.visible_prop_query")
    text(provenance.get("static_collider_query"), "scene_provenance.static_collider_query")
    text(provenance.get("occluder_query"), "scene_provenance.occluder_query")

    contract = obj(model.get("contract"), "contract")
    if text(contract.get("coordinate_system"), "contract.coordinate_system") != "godot_xz_y_up":
        raise ContractError("contract.coordinate_system must be godot_xz_y_up")
    surface_step = number(contract.get("surface_zone_sample_step"), "contract.surface_zone_sample_step", minimum=1e-6)
    survey_step = number(contract.get("survey_cell_step"), "contract.survey_cell_step", minimum=1e-6)
    surface_height_epsilon = number(contract.get("surface_height_epsilon"), "contract.surface_height_epsilon", minimum=0.0)
    probe_from_y = number(contract.get("ground_probe_from_y"), "contract.ground_probe_from_y")
    expected_surface_cell_count = integer(contract.get("expected_surface_cell_count"), "contract.expected_surface_cell_count", 1)
    expected_survey_cell_count = integer(contract.get("expected_survey_cell_count"), "contract.expected_survey_cell_count", 1)

    errors: list[str] = []
    triangles = parse_triangles(model.get("render_ground_triangles"))
    footprint = polygon(model.get("playable_footprint"), "playable_footprint")

    family_object = obj(model.get("surface_families"), "surface_families")
    surface_families = {
        text(surface_class, "surface_families key"): text(family, f"surface_families.{surface_class}")
        for surface_class, family in family_object.items()
    }
    if not surface_families:
        raise ContractError("surface_families must not be empty")

    zones: list[Zone] = []
    zone_ids: set[str] = set()
    for index, raw in enumerate(array(model.get("surface_zones"), "surface_zones", nonempty=True)):
        item = obj(raw, f"surface_zones[{index}]")
        zone_id = text(item.get("id"), f"surface_zones[{index}].id")
        if zone_id in zone_ids:
            raise ContractError(f"duplicate surface zone {zone_id}")
        zone_ids.add(zone_id)
        role = text(item.get("role"), f"surface zone {zone_id}.role")
        if role not in {"primary", "transition"}:
            raise ContractError(f"surface zone {zone_id}.role must be primary or transition")
        expected_family = text(item.get("expected_surface_family"), f"surface zone {zone_id}.expected_surface_family")
        expected_classes = frozenset(
            strings(item.get("expected_surface_classes"), f"surface zone {zone_id}.expected_surface_classes", nonempty=True)
        )
        fallback_classes = frozenset(
            strings(item.get("fallback_surface_classes"), f"surface zone {zone_id}.fallback_surface_classes")
        )
        unknown_classes = sorted((expected_classes | fallback_classes) - set(surface_families))
        if unknown_classes:
            raise ContractError(
                f"surface zone {zone_id} uses classes missing from surface_families: {', '.join(unknown_classes)}"
            )
        actual_families = {surface_families[value] for value in expected_classes}
        if actual_families != {expected_family}:
            errors.append(
                f"surface zone {zone_id} mixes semantic families {','.join(sorted(actual_families))}; "
                f"expected only {expected_family}"
            )
        zones.append(
            Zone(
                zone_id,
                role,
                polygon(item.get("polygon"), f"surface zone {zone_id}.polygon"),
                expected_family,
                expected_classes,
                fallback_classes,
                ratio(item.get("max_fallback_ratio"), f"surface zone {zone_id}.max_fallback_ratio"),
            )
        )

    zone_samples = grid_samples(footprint, surface_step)
    if len(zone_samples) != expected_surface_cell_count:
        errors.append(
            f"surface-zone grid has {len(zone_samples)} cells; expected {expected_surface_cell_count}"
        )
    assignments: dict[tuple[int, int], str] = {}
    zone_total = {zone.zone_id: 0 for zone in zones}
    zone_fallback = {zone.zone_id: 0 for zone in zones}
    zone_wrong = {zone.zone_id: 0 for zone in zones}
    zone_gaps = {zone.zone_id: 0 for zone in zones}
    for cell, point in zone_samples.items():
        owners = [zone for zone in zones if point_in_polygon(point, list(zone.polygon))]
        if len(owners) != 1:
            errors.append(
                f"surface-zone ownership at ({point[0]:.3g},{point[1]:.3g}) has {len(owners)} zones; requires exactly one"
            )
            continue
        zone = owners[0]
        assignments[cell] = zone.zone_id
        zone_total[zone.zone_id] += 1
        hit = top_surface_at(triangles, point, probe_from_y, surface_height_epsilon)
        if hit is None:
            zone_gaps[zone.zone_id] += 1
            continue
        triangle, _ = hit
        if triangle.surface_class in zone.expected_classes:
            continue
        if triangle.surface_class in zone.fallback_classes:
            zone_fallback[zone.zone_id] += 1
        else:
            zone_wrong[zone.zone_id] += 1

    for zone in zones:
        total = zone_total[zone.zone_id]
        if total == 0:
            errors.append(f"surface zone {zone.zone_id} has no playable-footprint samples")
            continue
        fallback_ratio = zone_fallback[zone.zone_id] / total
        if zone_gaps[zone.zone_id]:
            errors.append(
                f"surface zone {zone.zone_id} has {zone_gaps[zone.zone_id]} visible render-ground gap sample(s)"
            )
        if zone_wrong[zone.zone_id]:
            errors.append(
                f"surface zone {zone.zone_id} has {zone_wrong[zone.zone_id]} wrong top-surface sample(s)"
            )
        if fallback_ratio > zone.max_fallback_ratio + 1e-12:
            errors.append(
                f"surface zone {zone.zone_id} fallback exposure ratio {fallback_ratio:.4f} exceeds "
                f"{zone.max_fallback_ratio:.4f}"
            )

    observed_adjacency: set[tuple[str, str]] = set()
    for (x_index, z_index), zone_id in assignments.items():
        for neighbor in ((x_index + 1, z_index), (x_index, z_index + 1)):
            neighbor_zone = assignments.get(neighbor)
            if neighbor_zone and neighbor_zone != zone_id:
                observed_adjacency.add(tuple(sorted((zone_id, neighbor_zone))))

    adjacency_rules: dict[tuple[str, str], tuple[str, str, str]] = {}
    for index, raw in enumerate(array(model.get("surface_adjacency_rules"), "surface_adjacency_rules")):
        item = obj(raw, f"surface_adjacency_rules[{index}]")
        first = text(item.get("zone_a"), f"surface_adjacency_rules[{index}].zone_a")
        second = text(item.get("zone_b"), f"surface_adjacency_rules[{index}].zone_b")
        if first == second or first not in zone_ids or second not in zone_ids:
            raise ContractError(f"surface adjacency rule {first}/{second} must name two known zones")
        key = tuple(sorted((first, second)))
        if key in adjacency_rules:
            raise ContractError(f"duplicate surface adjacency rule {key}")
        mode = text(item.get("mode"), f"surface adjacency rule {key}.mode")
        if mode not in {"transition_band", "hard_boundary"}:
            raise ContractError(f"surface adjacency rule {key}.mode is invalid")
        cause = text(item.get("cause"), f"surface adjacency rule {key}.cause")
        artifact = text(item.get("raw_artifact"), f"surface adjacency rule {key}.raw_artifact")
        if mode == "transition_band":
            roles = {zone.role for zone in zones if zone.zone_id in key}
            if "transition" not in roles:
                errors.append(f"adjacency {key} claims transition_band without a transition zone")
        adjacency_rules[key] = (mode, cause, artifact)
    for pair in sorted(observed_adjacency - set(adjacency_rules)):
        errors.append(f"observed surface-zone adjacency {pair} lacks an authored transition/cause rule")
    for pair in sorted(set(adjacency_rules) - observed_adjacency):
        errors.append(f"stale surface-zone adjacency rule {pair} is not exercised by the playable grid")

    survey = obj(model.get("shipping_camera_survey"), "shipping_camera_survey")
    required_coverage_ratio = ratio(
        survey.get("required_coverage_ratio"), "shipping_camera_survey.required_coverage_ratio"
    )
    captures: list[tuple[str, tuple[Vec2, ...], str]] = []
    capture_ids: set[str] = set()
    artifacts: set[str] = set()
    for index, raw in enumerate(array(survey.get("captures"), "shipping_camera_survey.captures", nonempty=True)):
        item = obj(raw, f"shipping_camera_survey.captures[{index}]")
        capture_id = text(item.get("id"), f"survey capture {index}.id")
        if capture_id in capture_ids:
            raise ContractError(f"duplicate survey capture {capture_id}")
        capture_ids.add(capture_id)
        text(item.get("camera_node"), f"survey capture {capture_id}.camera_node")
        vec3(item.get("camera_position"), f"survey capture {capture_id}.camera_position")
        artifact = text(item.get("raw_artifact"), f"survey capture {capture_id}.raw_artifact")
        if artifact in artifacts:
            errors.append(f"survey capture {capture_id} reuses raw artifact {artifact}")
        artifacts.add(artifact)
        captures.append(
            (
                capture_id,
                polygon(item.get("visible_footprint"), f"survey capture {capture_id}.visible_footprint"),
                artifact,
            )
        )
    survey_cells = grid_samples(footprint, survey_step)
    if len(survey_cells) != expected_survey_cell_count:
        errors.append(
            f"shipping-camera survey grid has {len(survey_cells)} cells; expected {expected_survey_cell_count}"
        )
    uncovered = [
        point
        for point in survey_cells.values()
        if not any(point_in_polygon(point, list(capture[1])) for capture in captures)
    ]
    coverage_ratio = 1.0 - len(uncovered) / max(1, len(survey_cells))
    if coverage_ratio + 1e-12 < required_coverage_ratio:
        errors.append(
            f"shipping-camera tiled survey covers {coverage_ratio:.4f}; requires {required_coverage_ratio:.4f}; "
            f"uncovered_cells={len(uncovered)}"
        )

    shell_contract = obj(model.get("collider_shell_audit"), "collider_shell_audit")
    hero_radius = number(shell_contract.get("hero_radius"), "collider_shell_audit.hero_radius", minimum=0.0)
    hero_base_y = number(shell_contract.get("hero_base_y"), "collider_shell_audit.hero_base_y")
    hero_height = number(shell_contract.get("hero_height"), "collider_shell_audit.hero_height", minimum=1e-6)
    collider_step = number(shell_contract.get("sample_step"), "collider_shell_audit.sample_step", minimum=1e-6)
    min_shell_overlap_ratio = ratio(
        shell_contract.get("minimum_shell_overlap_ratio"),
        "collider_shell_audit.minimum_shell_overlap_ratio",
    )
    max_invisible_ratio = ratio(
        shell_contract.get("max_invisible_blocked_ratio"),
        "collider_shell_audit.max_invisible_blocked_ratio",
    )
    expected_enabled_colliders = integer(
        shell_contract.get("expected_enabled_static_collider_count"),
        "collider_shell_audit.expected_enabled_static_collider_count",
    )
    expected_visible_shells = integer(
        shell_contract.get("expected_visible_shell_count"),
        "collider_shell_audit.expected_visible_shell_count",
    )

    render_shells: dict[str, RenderShell] = {}
    for index, raw in enumerate(array(shell_contract.get("render_shells"), "collider_shell_audit.render_shells", nonempty=True)):
        item = obj(raw, f"render_shells[{index}]")
        shell_id = text(item.get("id"), f"render_shells[{index}].id")
        if shell_id in render_shells:
            raise ContractError(f"duplicate render shell {shell_id}")
        min_y = number(item.get("min_y"), f"render shell {shell_id}.min_y")
        max_y = number(item.get("max_y"), f"render shell {shell_id}.max_y")
        if max_y <= min_y:
            raise ContractError(f"render shell {shell_id} max_y must exceed min_y")
        render_shells[shell_id] = RenderShell(
            shell_id,
            text(item.get("source_node"), f"render shell {shell_id}.source_node"),
            boolean(item.get("visible"), f"render shell {shell_id}.visible"),
            text(item.get("variant_id"), f"render shell {shell_id}.variant_id"),
            polygon(item.get("footprint"), f"render shell {shell_id}.footprint"),
            min_y,
            max_y,
        )

    colliders: list[Collider] = []
    collider_ids: set[str] = set()
    for index, raw in enumerate(array(shell_contract.get("static_colliders"), "collider_shell_audit.static_colliders", nonempty=True)):
        item = obj(raw, f"static_colliders[{index}]")
        collider_id = text(item.get("id"), f"static_colliders[{index}].id")
        if collider_id in collider_ids:
            raise ContractError(f"duplicate static collider {collider_id}")
        collider_ids.add(collider_id)
        min_y = number(item.get("min_y"), f"static collider {collider_id}.min_y")
        max_y = number(item.get("max_y"), f"static collider {collider_id}.max_y")
        if max_y <= min_y:
            raise ContractError(f"static collider {collider_id} max_y must exceed min_y")
        shell_ids = tuple(
            sorted(strings(item.get("render_shell_ids"), f"static collider {collider_id}.render_shell_ids"))
        )
        blocks_hero = boolean(
            item.get("blocks_hero"), f"static collider {collider_id}.blocks_hero"
        )
        exemption_raw = item.get("visibility_exemption")
        visibility_exempt = exemption_raw is not None
        if visibility_exempt:
            exemption = obj(exemption_raw, f"static collider {collider_id}.visibility_exemption")
            text(exemption.get("reason"), f"static collider {collider_id}.visibility_exemption.reason")
            text(
                exemption.get("raw_artifact"),
                f"static collider {collider_id}.visibility_exemption.raw_artifact",
            )
            if blocks_hero:
                errors.append(
                    f"static collider {collider_id} cannot be visibility-exempt while blocks_hero=true"
                )
        colliders.append(
            Collider(
                collider_id,
                text(item.get("source_node"), f"static collider {collider_id}.source_node"),
                boolean(item.get("enabled"), f"static collider {collider_id}.enabled"),
                blocks_hero,
                visibility_exempt,
                text(item.get("variant_id"), f"static collider {collider_id}.variant_id"),
                polygon(item.get("footprint"), f"static collider {collider_id}.footprint"),
                min_y,
                max_y,
                shell_ids,
            )
        )

    enabled_colliders = [item for item in colliders if item.enabled]
    visible_shells = [item for item in render_shells.values() if item.visible]
    if len(enabled_colliders) != expected_enabled_colliders:
        errors.append(
            f"enabled static collider manifest has {len(enabled_colliders)}; expected {expected_enabled_colliders}"
        )
    if len(visible_shells) != expected_visible_shells:
        errors.append(
            f"visible render-shell manifest has {len(visible_shells)}; expected {expected_visible_shells}"
        )

    variants = {item.variant_id for item in colliders} | {item.variant_id for item in render_shells.values()}
    for variant in sorted(variants):
        collider_active = any(
            item.enabled and not item.visibility_exempt
            for item in colliders
            if item.variant_id == variant
        )
        shell_active = any(item.visible for item in render_shells.values() if item.variant_id == variant)
        if collider_active != shell_active:
            errors.append(
                f"variant {variant} is asymmetric: collider_enabled={collider_active} render_visible={shell_active}"
            )

    for collider in enabled_colliders:
        if collider.visibility_exempt:
            continue
        if not collider.shell_ids:
            errors.append(f"enabled static collider {collider.collider_id} has no render-shell mapping")
            continue
        mapped: list[RenderShell] = []
        for shell_id in collider.shell_ids:
            shell = render_shells.get(shell_id)
            if shell is None:
                errors.append(
                    f"enabled static collider {collider.collider_id} maps unknown shell {shell_id}"
                )
            elif not shell.visible:
                errors.append(
                    f"enabled static collider {collider.collider_id} maps hidden shell {shell_id}"
                )
            else:
                mapped.append(shell)
        collider_points = grid_samples(collider.footprint, collider_step).values()
        collider_points = list(collider_points)
        backed = 0
        for point in collider_points:
            if any(
                point_in_polygon(point, list(shell.footprint))
                and min(collider.max_y, shell.max_y) > max(collider.min_y, shell.min_y)
                for shell in mapped
            ):
                backed += 1
        overlap_ratio = backed / max(1, len(collider_points))
        if overlap_ratio + 1e-12 < min_shell_overlap_ratio:
            errors.append(
                f"enabled static collider {collider.collider_id} visible-shell overlap ratio "
                f"{overlap_ratio:.4f} is below {min_shell_overlap_ratio:.4f}"
            )

    raster_cells = grid_samples(footprint, collider_step)
    blocked_samples = 0
    invisible_samples = 0
    for point in raster_cells.values():
        blockers = [
            collider
            for collider in enabled_colliders
            if collider.blocks_hero
            and point_polygon_distance(point, collider.footprint) <= hero_radius
            and min(collider.max_y, hero_base_y + hero_height) > max(collider.min_y, hero_base_y)
        ]
        if not blockers:
            continue
        blocked_samples += 1
        backed = False
        for collider in blockers:
            for shell_id in collider.shell_ids:
                shell = render_shells.get(shell_id)
                if shell and shell.visible and point_polygon_distance(point, shell.footprint) <= hero_radius:
                    backed = True
                    break
            if backed:
                break
        if not backed:
            invisible_samples += 1
    invisible_ratio = invisible_samples / max(1, blocked_samples)
    if invisible_ratio > max_invisible_ratio + 1e-12:
        errors.append(
            f"hero-radius collider raster has {invisible_samples}/{blocked_samples} invisible blocked "
            f"sample(s), ratio={invisible_ratio:.4f}, maximum={max_invisible_ratio:.4f}"
        )

    occluders = obj(model.get("production_occluders"), "production_occluders")
    if text(occluders.get("source_kind"), "production_occluders.source_kind") != "resolved_production_scene":
        raise ContractError("production_occluders.source_kind must be resolved_production_scene")
    production_scene_path = text(
        occluders.get("production_scene_path"), "production_occluders.production_scene_path"
    )
    if production_scene_path != scene_path:
        errors.append(
            f"production occluder scene {production_scene_path} does not match resolved scene {scene_path}"
        )
    fade_target = number(occluders.get("fade_target"), "production_occluders.fade_target")
    restore_target = number(occluders.get("restore_target"), "production_occluders.restore_target")
    fade_tolerance = number(occluders.get("tolerance"), "production_occluders.tolerance", minimum=0.0)
    expected_occluder_roots = strings(
        occluders.get("expected_collision_roots"),
        "production_occluders.expected_collision_roots",
        nonempty=True,
    )
    visual_root_ids: set[str] = set()
    visible_visual_roots: set[str] = set()
    for index, raw in enumerate(
        array(occluders.get("visual_roots"), "production_occluders.visual_roots", nonempty=True)
    ):
        item = obj(raw, f"production_occluders.visual_roots[{index}]")
        visual_id = text(item.get("id"), f"production visual root {index}.id")
        if visual_id in visual_root_ids:
            raise ContractError(f"duplicate production visual root {visual_id}")
        visual_root_ids.add(visual_id)
        text(item.get("source_node"), f"production visual root {visual_id}.source_node")
        if boolean(item.get("visible"), f"production visual root {visual_id}.visible"):
            visible_visual_roots.add(visual_id)
    mappings: dict[str, set[str]] = {}
    collision_roots: set[str] = set()
    aliases: set[str] = set()
    for index, raw in enumerate(array(occluders.get("mappings"), "production_occluders.mappings", nonempty=True)):
        item = obj(raw, f"production_occluders.mappings[{index}]")
        mapping_id = text(item.get("id"), f"occluder mapping {index}.id")
        if mapping_id in mappings:
            raise ContractError(f"duplicate occluder mapping {mapping_id}")
        collision_root = text(item.get("collision_root"), f"occluder mapping {mapping_id}.collision_root")
        if collision_root in collision_roots:
            raise ContractError(f"duplicate production collision root {collision_root}")
        collision_roots.add(collision_root)
        item_aliases = strings(item.get("aliases"), f"occluder mapping {mapping_id}.aliases", nonempty=True)
        repeated_aliases = aliases & item_aliases
        if repeated_aliases:
            raise ContractError(f"duplicate occluder aliases: {', '.join(sorted(repeated_aliases))}")
        aliases |= item_aliases
        targets = strings(item.get("visual_root_ids"), f"occluder mapping {mapping_id}.visual_root_ids", nonempty=True)
        unknown = sorted(targets - visual_root_ids)
        if unknown:
            errors.append(
                f"occluder mapping {mapping_id} targets unknown visual roots: {', '.join(unknown)}"
            )
        hidden = sorted(targets - visible_visual_roots)
        if hidden:
            errors.append(
                f"occluder mapping {mapping_id} targets hidden production visual roots: {', '.join(hidden)}"
            )
        mappings[mapping_id] = targets
    missing_roots = sorted(expected_occluder_roots - collision_roots)
    unexpected_roots = sorted(collision_roots - expected_occluder_roots)
    if missing_roots:
        errors.append(
            f"production occluder aliases miss collision roots: {', '.join(missing_roots)}"
        )
    if unexpected_roots:
        errors.append(
            f"production occluder mappings include undeclared collision roots: {', '.join(unexpected_roots)}"
        )

    tested_mappings: set[str] = set()
    for index, raw in enumerate(array(occluders.get("traces"), "production_occluders.traces", nonempty=True)):
        item = obj(raw, f"production_occluders.traces[{index}]")
        mapping_id = text(item.get("mapping_id"), f"occluder trace {index}.mapping_id")
        if mapping_id not in mappings:
            errors.append(f"occluder trace references unknown mapping {mapping_id}")
            continue
        if mapping_id in tested_mappings:
            raise ContractError(f"duplicate occluder production trace for {mapping_id}")
        tested_mappings.add(mapping_id)
        if text(item.get("source_kind"), f"occluder trace {mapping_id}.source_kind") != "resolved_production_scene":
            errors.append(f"occluder trace {mapping_id} is synthetic rather than production-scene")
        observed_fade = number(item.get("observed_fade"), f"occluder trace {mapping_id}.observed_fade")
        observed_restore = number(item.get("observed_restore"), f"occluder trace {mapping_id}.observed_restore")
        text(item.get("raw_artifact"), f"occluder trace {mapping_id}.raw_artifact")
        if abs(observed_fade - fade_target) > fade_tolerance:
            errors.append(
                f"occluder mapping {mapping_id} fades to {observed_fade:g}; expected {fade_target:g}±{fade_tolerance:g}"
            )
        if abs(observed_restore - restore_target) > fade_tolerance:
            errors.append(
                f"occluder mapping {mapping_id} restores to {observed_restore:g}; expected {restore_target:g}±{fade_tolerance:g}"
            )
    for missing in sorted(set(mappings) - tested_mappings):
        errors.append(f"production occluder mapping {missing} lacks fade/restoration trace")

    pair_rules: dict[tuple[str, str], tuple[float, str]] = {}
    for index, raw in enumerate(array(model.get("surface_object_pair_rules"), "surface_object_pair_rules", nonempty=True)):
        item = obj(raw, f"surface_object_pair_rules[{index}]")
        object_class = text(item.get("object_class"), f"surface pair rule {index}.object_class")
        surface_class = text(item.get("surface_class"), f"surface pair rule {index}.surface_class")
        if surface_class not in surface_families:
            raise ContractError(
                f"surface/object pair rule {object_class}/{surface_class} uses an unknown surface class"
            )
        key = (object_class, surface_class)
        if key in pair_rules:
            raise ContractError(f"duplicate surface/object pair rule {key}")
        pair_rules[key] = (
            ratio(item.get("max_topmost_ratio"), f"surface pair rule {key}.max_topmost_ratio"),
            text(item.get("reason"), f"surface pair rule {key}.reason"),
        )

    pair_counts = {key: [0, 0] for key in pair_rules}
    object_classes: set[str] = set()
    object_ids: set[str] = set()
    for index, raw in enumerate(array(model.get("object_supports"), "object_supports", nonempty=True)):
        item = obj(raw, f"object_supports[{index}]")
        object_id = text(item.get("id"), f"object support {index}.id")
        if object_id in object_ids:
            raise ContractError(f"duplicate object support {object_id}")
        object_ids.add(object_id)
        object_class = text(item.get("class"), f"object support {object_id}.class")
        object_classes.add(object_class)
        support = polygon(item.get("support_polygon"), f"object support {object_id}.support_polygon")
        step = number(item.get("sample_step"), f"object support {object_id}.sample_step", minimum=1e-6)
        object_probe_y = number(item.get("probe_from_y"), f"object support {object_id}.probe_from_y")
        for point in grid_samples(support, step).values():
            hit = top_surface_at(triangles, point, object_probe_y, surface_height_epsilon)
            if hit is None:
                continue
            triangle, _ = hit
            key = (object_class, triangle.surface_class)
            if key in pair_counts:
                pair_counts[key][0] += 1
            for rule_key in pair_counts:
                if rule_key[0] == object_class:
                    pair_counts[rule_key][1] += 1
    for key, (maximum, _) in pair_rules.items():
        if key[0] not in object_classes:
            errors.append(f"surface/object pair rule {key} is not exercised by any object")
            continue
        offending, total = pair_counts[key]
        actual = offending / max(1, total)
        if actual > maximum + 1e-12:
            errors.append(
                f"surface/object pair {key} topmost ratio {actual:.4f} exceeds {maximum:.4f}"
            )

    return {
        "status": "pass" if not errors else "fail",
        "contract_id": contract_id,
        "build_id": build_id,
        "surface_zone_count": len(zones),
        "surface_cell_count": len(zone_samples),
        "observed_adjacency_count": len(observed_adjacency),
        "survey_capture_count": len(captures),
        "survey_cell_count": len(survey_cells),
        "survey_uncovered_cell_count": len(uncovered),
        "survey_coverage_ratio": coverage_ratio,
        "enabled_static_collider_count": len(enabled_colliders),
        "visible_shell_count": len(visible_shells),
        "blocked_raster_sample_count": blocked_samples,
        "invisible_blocked_sample_count": invisible_samples,
        "production_occluder_mapping_count": len(mappings),
        "production_occluder_trace_count": len(tested_mappings),
        "surface_object_pair_rule_count": len(pair_rules),
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
            f"[{marker}] environment-coverage id={report['contract_id']} "
            f"surface_cells={report['surface_cell_count']} survey={report['survey_coverage_ratio']:.4f} "
            f"colliders={report['enabled_static_collider_count']} "
            f"invisible={report['invisible_blocked_sample_count']} "
            f"occluders={report['production_occluder_trace_count']} errors={len(report['errors'])}"
        )
        for error in report["errors"]:
            print(f"[ERROR] {error}")
        return 0 if report["status"] == "pass" else 1
    except ContractError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
