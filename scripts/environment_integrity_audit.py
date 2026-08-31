#!/usr/bin/env python3
"""Audit transformed 3D prop occupancy, surface ownership, render-ground seams, and clearance."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from math import ceil, hypot, isfinite
from pathlib import Path
import sys
from typing import Any

from resolved_scene_provenance_audit import (
    ProvenanceError,
    validate_scene_provenance_reference,
)


class ContractError(RuntimeError):
    pass


Vec2 = tuple[float, float]
Vec3 = tuple[float, float, float]


@dataclass(frozen=True)
class Volume:
    instance_id: str
    volume_id: str
    prop_class: str
    footprint: tuple[Vec2, ...]
    min_y: float
    max_y: float


@dataclass(frozen=True)
class GroundTriangle:
    triangle_id: str
    surface_class: str
    material_id: str
    vertices: tuple[Vec3, Vec3, Vec3]
    bbox: tuple[float, float, float, float]


@dataclass(frozen=True)
class SupportFootprint:
    instance_id: str
    prop_class: str
    polygon: tuple[Vec2, ...]
    plane_point: Vec3
    plane_normal: Vec3
    sample_step: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit high-angle 3D environment integrity from resolved target-scene geometry."
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


def obj(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    return value


def array(value: Any, label: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list) or (nonempty and not value):
        suffix = " and not be empty" if nonempty else ""
        raise ContractError(f"{label} must be an array{suffix}")
    return value


def text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value.strip()


def boolean(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ContractError(f"{label} must be boolean")
    return value


def integer(value: Any, label: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContractError(f"{label} must be an integer >= {minimum}")
    return value


def number(value: Any, label: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ContractError(f"{label} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{label} must be numeric") from exc
    if not isfinite(result) or (minimum is not None and result < minimum):
        suffix = f" and >= {minimum}" if minimum is not None else ""
        raise ContractError(f"{label} must be finite{suffix}")
    return result


def strings(value: Any, label: str, *, nonempty: bool = False) -> set[str]:
    values = array(value, label, nonempty=nonempty)
    result = {text(item, f"{label}[{index}]") for index, item in enumerate(values)}
    if len(result) != len(values):
        raise ContractError(f"{label} contains duplicates")
    return result


def vec2(value: Any, label: str) -> Vec2:
    raw = array(value, label)
    if len(raw) != 2:
        raise ContractError(f"{label} must contain two numbers")
    return number(raw[0], f"{label}[0]"), number(raw[1], f"{label}[1]")


def vec3(value: Any, label: str) -> Vec3:
    raw = array(value, label)
    if len(raw) != 3:
        raise ContractError(f"{label} must contain three numbers")
    return (
        number(raw[0], f"{label}[0]"),
        number(raw[1], f"{label}[1]"),
        number(raw[2], f"{label}[2]"),
    )


def transform_point(transform: dict[str, Vec3], point: Vec3) -> Vec3:
    bx, by, bz, origin = (
        transform["basis_x"],
        transform["basis_y"],
        transform["basis_z"],
        transform["origin"],
    )
    x, y, z = point
    return (
        origin[0] + bx[0] * x + by[0] * y + bz[0] * z,
        origin[1] + bx[1] * x + by[1] * y + bz[1] * z,
        origin[2] + bx[2] * x + by[2] * y + bz[2] * z,
    )


def cross3(first: Vec3, second: Vec3) -> Vec3:
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def support_height(support: SupportFootprint, point: Vec2) -> float:
    normal = support.plane_normal
    if abs(normal[1]) <= 1e-10:
        raise ContractError(
            f"support footprint for {support.instance_id} resolves to a vertical plane"
        )
    origin = support.plane_point
    return origin[1] - (
        normal[0] * (point[0] - origin[0])
        + normal[2] * (point[1] - origin[2])
    ) / normal[1]


def parse_transform(value: Any, label: str) -> dict[str, Vec3]:
    raw = obj(value, label)
    required = {"basis_x", "basis_y", "basis_z", "origin"}
    if set(raw) != required:
        raise ContractError(f"{label} must contain basis_x, basis_y, basis_z, and origin only")
    return {key: vec3(raw[key], f"{label}.{key}") for key in required}


def cross(o: Vec2, a: Vec2, b: Vec2) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def convex_hull(points: list[Vec2]) -> tuple[Vec2, ...]:
    unique = sorted(set(points))
    if len(unique) < 3:
        raise ContractError("transformed occupancy footprint must contain at least three points")
    lower: list[Vec2] = []
    for point in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 1e-10:
            lower.pop()
        lower.append(point)
    upper: list[Vec2] = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 1e-10:
            upper.pop()
        upper.append(point)
    hull = tuple(lower[:-1] + upper[:-1])
    if len(hull) < 3:
        raise ContractError("transformed occupancy footprint is degenerate")
    return hull


def local_box_corners(local_min: Vec3, local_max: Vec3) -> list[Vec3]:
    if any(local_max[index] <= local_min[index] for index in range(3)):
        raise ContractError("occupancy local_max must exceed local_min on every axis")
    return [
        (x, y, z)
        for x in (local_min[0], local_max[0])
        for y in (local_min[1], local_max[1])
        for z in (local_min[2], local_max[2])
    ]


def polygon_axes(polygon: tuple[Vec2, ...]) -> list[Vec2]:
    axes: list[Vec2] = []
    for index, start in enumerate(polygon):
        end = polygon[(index + 1) % len(polygon)]
        dx, dz = end[0] - start[0], end[1] - start[1]
        length = hypot(dx, dz)
        if length > 1e-10:
            axes.append((-dz / length, dx / length))
    return axes


def strict_overlap_depth(a: tuple[Vec2, ...], b: tuple[Vec2, ...]) -> float:
    return strict_overlap_info(a, b)[0]


def strict_overlap_info(a: tuple[Vec2, ...], b: tuple[Vec2, ...]) -> tuple[float, Vec2]:
    minimum = float("inf")
    minimum_axis: Vec2 = (0.0, 0.0)
    for axis in polygon_axes(a) + polygon_axes(b):
        projected_a = [point[0] * axis[0] + point[1] * axis[1] for point in a]
        projected_b = [point[0] * axis[0] + point[1] * axis[1] for point in b]
        overlap = min(max(projected_a), max(projected_b)) - max(min(projected_a), min(projected_b))
        if overlap <= 0.0:
            return 0.0, (0.0, 0.0)
        if overlap < minimum:
            minimum = overlap
            minimum_axis = axis
    if minimum == float("inf"):
        return 0.0, (0.0, 0.0)
    center_a = (
        sum(point[0] for point in a) / len(a),
        sum(point[1] for point in a) / len(a),
    )
    center_b = (
        sum(point[0] for point in b) / len(b),
        sum(point[1] for point in b) / len(b),
    )
    if (center_b[0] - center_a[0]) * minimum_axis[0] + (center_b[1] - center_a[1]) * minimum_axis[1] < 0.0:
        minimum_axis = (-minimum_axis[0], -minimum_axis[1])
    return minimum, minimum_axis


def pair_key(instance_a: str, volume_a: str, instance_b: str, volume_b: str) -> tuple[tuple[str, str], tuple[str, str]]:
    return tuple(sorted(((instance_a, volume_a), (instance_b, volume_b))))  # type: ignore[return-value]


def point_on_segment(point: Vec2, start: Vec2, end: Vec2, epsilon: float = 1e-8) -> bool:
    if abs(cross(start, end, point)) > epsilon:
        return False
    return (
        min(start[0], end[0]) - epsilon <= point[0] <= max(start[0], end[0]) + epsilon
        and min(start[1], end[1]) - epsilon <= point[1] <= max(start[1], end[1]) + epsilon
    )


def point_in_polygon(point: Vec2, polygon: list[Vec2]) -> bool:
    inside = False
    for index, start in enumerate(polygon):
        end = polygon[(index + 1) % len(polygon)]
        if point_on_segment(point, start, end):
            return True
        if (start[1] > point[1]) != (end[1] > point[1]):
            at_x = (end[0] - start[0]) * (point[1] - start[1]) / (end[1] - start[1]) + start[0]
            if point[0] < at_x:
                inside = not inside
    return inside


def sample_polygon(polygon: list[Vec2], step: float) -> list[Vec2]:
    samples: set[tuple[float, float]] = set()

    def add(point: Vec2) -> None:
        samples.add((round(point[0], 8), round(point[1], 8)))

    for index, start in enumerate(polygon):
        end = polygon[(index + 1) % len(polygon)]
        distance = hypot(end[0] - start[0], end[1] - start[1])
        segments = max(1, int(ceil(distance / step)))
        for part in range(segments + 1):
            t = part / segments
            add((start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * t))

    min_x, max_x = min(point[0] for point in polygon), max(point[0] for point in polygon)
    min_z, max_z = min(point[1] for point in polygon), max(point[1] for point in polygon)
    x_count = max(1, int(ceil((max_x - min_x) / step)))
    z_count = max(1, int(ceil((max_z - min_z) / step)))
    for x_index in range(x_count + 1):
        x = min_x + (max_x - min_x) * x_index / x_count
        for z_index in range(z_count + 1):
            z = min_z + (max_z - min_z) * z_index / z_count
            if point_in_polygon((x, z), polygon):
                add((x, z))
    return sorted(samples)


def triangle_height(triangle: GroundTriangle, point: Vec2, epsilon: float = 1e-8) -> float | None:
    a, b, c = triangle.vertices
    ax, az = a[0], a[2]
    bx, bz = b[0], b[2]
    cx, cz = c[0], c[2]
    denominator = (bz - cz) * (ax - cx) + (cx - bx) * (az - cz)
    if abs(denominator) <= epsilon:
        return None
    first = ((bz - cz) * (point[0] - cx) + (cx - bx) * (point[1] - cz)) / denominator
    second = ((cz - az) * (point[0] - cx) + (ax - cx) * (point[1] - cz)) / denominator
    third = 1.0 - first - second
    if first < -epsilon or second < -epsilon or third < -epsilon:
        return None
    return first * a[1] + second * b[1] + third * c[1]


def top_surface_at(
    triangles: list[GroundTriangle], point: Vec2, probe_from_y: float, height_epsilon: float
) -> tuple[GroundTriangle, float] | None:
    hits: list[tuple[float, GroundTriangle]] = []
    for triangle in triangles:
        min_x, min_z, max_x, max_z = triangle.bbox
        if not (min_x - 1e-8 <= point[0] <= max_x + 1e-8 and min_z - 1e-8 <= point[1] <= max_z + 1e-8):
            continue
        height = triangle_height(triangle, point)
        if height is not None and height <= probe_from_y + height_epsilon:
            hits.append((height, triangle))
    if not hits:
        return None
    height, triangle = max(hits, key=lambda item: item[0])
    return triangle, height


def audit(model: dict[str, Any]) -> dict[str, Any]:
    if model.get("schema_version") != 2:
        raise ContractError("schema_version must be 2; migrate intentional contacts and interface provenance")
    contract_id = text(model.get("contract_id"), "contract_id")
    build_id = text(model.get("build_id"), "build_id")
    raw_provenance = obj(model.get("scene_provenance"), "scene_provenance")
    try:
        provenance = validate_scene_provenance_reference(raw_provenance)
    except ProvenanceError as exc:
        raise ContractError(str(exc)) from exc
    scene_path = provenance["scene_path"]
    closure_digest = provenance["dependency_closure_digest"]
    exporter = provenance["exporter"]
    visible_prop_query = text(
        raw_provenance.get("visible_prop_query"), "scene_provenance.visible_prop_query"
    )
    contact_interface_query = text(
        raw_provenance.get("contact_interface_query"),
        "scene_provenance.contact_interface_query",
    )
    contract = obj(model.get("contract"), "contract")
    if text(contract.get("coordinate_system"), "contract.coordinate_system") != "godot_xz_y_up":
        raise ContractError("contract.coordinate_system must be godot_xz_y_up")
    if text(contract.get("render_ground_source"), "contract.render_ground_source") != "mesh_faces":
        raise ContractError("render_ground_source must be mesh_faces; collision-only ground is forbidden")

    horizontal_epsilon = number(contract.get("horizontal_penetration_epsilon"), "contract.horizontal_penetration_epsilon", minimum=0.0)
    vertical_epsilon = number(contract.get("vertical_penetration_epsilon"), "contract.vertical_penetration_epsilon", minimum=0.0)
    max_surface_step = number(contract.get("max_surface_sample_step"), "contract.max_surface_sample_step", minimum=1e-6)
    max_ground_step = number(contract.get("max_ground_sample_step"), "contract.max_ground_sample_step", minimum=1e-6)
    surface_height_epsilon = number(contract.get("surface_height_epsilon"), "contract.surface_height_epsilon", minimum=0.0)
    max_surface_height_delta = number(contract.get("max_surface_height_delta"), "contract.max_surface_height_delta", minimum=0.0)
    expected_visible_prop_count = integer(contract.get("expected_visible_prop_count"), "contract.expected_visible_prop_count", 1)
    require_rule_exercise = boolean(contract.get("require_vertical_rule_exercise"), "contract.require_vertical_rule_exercise")
    contact_measurement_tolerance = number(
        contract.get("contact_measurement_tolerance"),
        "contract.contact_measurement_tolerance",
        minimum=0.0,
    )

    structural = obj(contract.get("prior_structural_checks"), "contract.prior_structural_checks")
    collision = obj(structural.get("collision_coverage"), "prior_structural_checks.collision_coverage")
    boundary = obj(structural.get("boundary_coverage"), "prior_structural_checks.boundary_coverage")
    collision_covered = integer(collision.get("covered"), "collision_coverage.covered")
    collision_total = integer(collision.get("total"), "collision_coverage.total", 1)
    boundary_covered = integer(boundary.get("covered"), "boundary_coverage.covered")
    boundary_total = integer(boundary.get("total"), "boundary_coverage.total", 1)
    collision_alignment_pass = boolean(structural.get("collision_alignment_pass"), "prior_structural_checks.collision_alignment_pass")

    errors: list[str] = []
    if collision_covered != collision_total:
        errors.append(f"collision coverage is {collision_covered}/{collision_total}")
    if boundary_covered != boundary_total:
        errors.append(f"boundary coverage is {boundary_covered}/{boundary_total}")
    if not collision_alignment_pass:
        errors.append("prior collision alignment check did not pass")

    surface_rules: dict[str, set[str]] = {}
    for index, raw in enumerate(array(contract.get("surface_ownership_rules"), "contract.surface_ownership_rules", nonempty=True)):
        rule = obj(raw, f"surface_ownership_rules[{index}]")
        prop_class = text(rule.get("prop_class"), f"surface_ownership_rules[{index}].prop_class")
        if prop_class in surface_rules:
            raise ContractError(f"duplicate surface ownership rule for {prop_class}")
        surface_rules[prop_class] = strings(rule.get("allowed_surface_classes"), f"surface rule {prop_class}.allowed_surface_classes", nonempty=True)

    clearance_rules: list[tuple[str, str, float]] = []
    for index, raw in enumerate(array(contract.get("vertical_clearance_rules"), "contract.vertical_clearance_rules")):
        rule = obj(raw, f"vertical_clearance_rules[{index}]")
        clearance_rules.append(
            (
                text(rule.get("upper_class"), f"vertical_clearance_rules[{index}].upper_class"),
                text(rule.get("lower_class"), f"vertical_clearance_rules[{index}].lower_class"),
                number(rule.get("minimum_gap"), f"vertical_clearance_rules[{index}].minimum_gap", minimum=0.0),
            )
        )

    strict_contact_rules: list[dict[str, Any]] = []
    for index, raw in enumerate(array(contract.get("strict_contact_pair_rules"), "contract.strict_contact_pair_rules")):
        rule = obj(raw, f"strict_contact_pair_rules[{index}]")
        rule_id = text(rule.get("id"), f"strict_contact_pair_rules[{index}].id")
        strict_contact_rules.append(
            {
                "id": rule_id,
                "class_group_a": strings(
                    rule.get("class_group_a"),
                    f"strict contact rule {rule_id}.class_group_a",
                    nonempty=True,
                ),
                "class_group_b": strings(
                    rule.get("class_group_b"),
                    f"strict contact rule {rule_id}.class_group_b",
                    nonempty=True,
                ),
                "maximum_undeformed_render_penetration": number(
                    rule.get("maximum_undeformed_render_penetration"),
                    f"strict contact rule {rule_id}.maximum_undeformed_render_penetration",
                    minimum=0.0,
                ),
                "maximum_deformed_render_penetration": number(
                    rule.get("maximum_deformed_render_penetration"),
                    f"strict contact rule {rule_id}.maximum_deformed_render_penetration",
                    minimum=0.0,
                ),
                "minimum_contact_normal_alignment": number(
                    rule.get("minimum_contact_normal_alignment"),
                    f"strict contact rule {rule_id}.minimum_contact_normal_alignment",
                    minimum=0.0,
                ),
                "allowed_modes": strings(
                    rule.get("allowed_modes"),
                    f"strict contact rule {rule_id}.allowed_modes",
                    nonempty=True,
                ),
            }
        )
        if strict_contact_rules[-1]["minimum_contact_normal_alignment"] > 1.0:
            raise ContractError(f"strict contact rule {rule_id} normal alignment must be <= 1")
        if (
            strict_contact_rules[-1]["maximum_deformed_render_penetration"]
            < strict_contact_rules[-1]["maximum_undeformed_render_penetration"]
        ):
            raise ContractError(f"strict contact rule {rule_id} deformed budget is below undeformed budget")
        if horizontal_epsilon > strict_contact_rules[-1]["maximum_undeformed_render_penetration"]:
            raise ContractError(
                f"strict contact rule {rule_id} undeformed budget is below the audit penetration resolution"
            )

    exemption_checks = {"occupancy", "vertical_clearance"}
    resolved_interface_geometry_ids = strings(
        model.get("resolved_interface_geometry_ids"),
        "resolved_interface_geometry_ids",
    )
    exemptions: dict[tuple[tuple[str, str], tuple[str, str]], set[str]] = {}
    exemption_meta: dict[tuple[tuple[str, str], tuple[str, str]], str] = {}
    exemption_contacts: dict[tuple[tuple[str, str], tuple[str, str]], dict[str, Any]] = {}
    for index, raw in enumerate(array(model.get("intentional_overlaps"), "intentional_overlaps")):
        item = obj(raw, f"intentional_overlaps[{index}]")
        key = pair_key(
            text(item.get("instance_a"), f"intentional_overlaps[{index}].instance_a"),
            text(item.get("volume_a"), f"intentional_overlaps[{index}].volume_a"),
            text(item.get("instance_b"), f"intentional_overlaps[{index}].instance_b"),
            text(item.get("volume_b"), f"intentional_overlaps[{index}].volume_b"),
        )
        if key[0] == key[1] or key in exemptions:
            raise ContractError(f"intentional_overlaps[{index}] must name one unique cross-instance pair")
        checks = strings(item.get("checks"), f"intentional_overlaps[{index}].checks", nonempty=True)
        unknown = sorted(checks - exemption_checks)
        if unknown:
            raise ContractError(f"intentional_overlaps[{index}] has unknown checks: {', '.join(unknown)}")
        reason = text(item.get("reason"), f"intentional_overlaps[{index}].reason")
        artifact = text(item.get("raw_artifact"), f"intentional_overlaps[{index}].raw_artifact")
        contact_mode = text(item.get("contact_mode"), f"intentional_overlaps[{index}].contact_mode")
        reported_horizontal = number(
            item.get("reported_horizontal_penetration"),
            f"intentional_overlaps[{index}].reported_horizontal_penetration",
            minimum=0.0,
        )
        reported_vertical = number(
            item.get("reported_vertical_penetration"),
            f"intentional_overlaps[{index}].reported_vertical_penetration",
            minimum=0.0,
        )
        contact_normal = vec2(item.get("contact_normal_xz"), f"intentional_overlaps[{index}].contact_normal_xz")
        normal_length = hypot(contact_normal[0], contact_normal[1])
        if normal_length <= 1e-10:
            raise ContractError(f"intentional_overlaps[{index}].contact_normal_xz must not be zero")
        contact_normal = (contact_normal[0] / normal_length, contact_normal[1] / normal_length)
        interface_geometry_ids = strings(
            item.get("interface_geometry_ids"),
            f"intentional_overlaps[{index}].interface_geometry_ids",
        )
        unknown_interfaces = sorted(interface_geometry_ids - resolved_interface_geometry_ids)
        if unknown_interfaces:
            errors.append(
                f"intentional_overlaps[{index}] references unresolved interface geometry: "
                + ", ".join(unknown_interfaces)
            )
        exemptions[key] = checks
        exemption_meta[key] = f"{reason} ({artifact})"
        exemption_contacts[key] = {
            "contact_mode": contact_mode,
            "reported_horizontal": reported_horizontal,
            "reported_vertical": reported_vertical,
            "contact_normal": contact_normal,
            "interface_geometry_ids": interface_geometry_ids,
        }

    volumes: list[Volume] = []
    supports: list[SupportFootprint] = []
    instance_ids: set[str] = set()
    volume_ids: set[tuple[str, str]] = set()
    instances = array(model.get("instances"), "instances", nonempty=True)
    for index, raw in enumerate(instances):
        item = obj(raw, f"instances[{index}]")
        instance_id = text(item.get("id"), f"instances[{index}].id")
        if instance_id in instance_ids:
            raise ContractError(f"duplicate instance ID {instance_id}")
        instance_ids.add(instance_id)
        prop_class = text(item.get("class"), f"instance {instance_id}.class")
        text(item.get("source_node"), f"instance {instance_id}.source_node")
        transform = parse_transform(item.get("transform"), f"instance {instance_id}.transform")
        occupancy_required = boolean(item.get("occupancy_required"), f"instance {instance_id}.occupancy_required")
        surface_required = boolean(item.get("surface_ownership_required"), f"instance {instance_id}.surface_ownership_required")
        raw_volumes = array(item.get("volumes"), f"instance {instance_id}.volumes")
        if not occupancy_required:
            exemption = obj(
                item.get("occupancy_exemption"),
                f"instance {instance_id}.occupancy_exemption",
            )
            text(exemption.get("reason"), f"instance {instance_id}.occupancy_exemption.reason")
            text(
                exemption.get("raw_artifact"),
                f"instance {instance_id}.occupancy_exemption.raw_artifact",
            )
        if occupancy_required and not raw_volumes:
            errors.append(f"instance {instance_id} lacks full-footprint occupancy volumes")
        for volume_index, raw_volume in enumerate(raw_volumes):
            volume = obj(raw_volume, f"instance {instance_id}.volumes[{volume_index}]")
            volume_id = text(volume.get("id"), f"instance {instance_id}.volumes[{volume_index}].id")
            if (instance_id, volume_id) in volume_ids:
                raise ContractError(f"duplicate volume ID {instance_id}/{volume_id}")
            volume_ids.add((instance_id, volume_id))
            local_min = vec3(volume.get("local_min"), f"volume {instance_id}/{volume_id}.local_min")
            local_max = vec3(volume.get("local_max"), f"volume {instance_id}/{volume_id}.local_max")
            world = [transform_point(transform, point) for point in local_box_corners(local_min, local_max)]
            footprint = convex_hull([(point[0], point[2]) for point in world])
            volumes.append(
                Volume(instance_id, volume_id, prop_class, footprint, min(point[1] for point in world), max(point[1] for point in world))
            )

        raw_supports = array(item.get("support_footprints"), f"instance {instance_id}.support_footprints")
        needs_surface_ownership = surface_required or prop_class in surface_rules
        if needs_surface_ownership and prop_class not in surface_rules:
            errors.append(f"instance {instance_id} class {prop_class} has no semantic surface ownership rule")
        if needs_surface_ownership and not raw_supports:
            errors.append(f"instance {instance_id} uses origin-only placement; full support footprint is missing")
        for support_index, raw_support in enumerate(raw_supports):
            support = obj(raw_support, f"instance {instance_id}.support_footprints[{support_index}]")
            support_id = text(support.get("id"), f"instance {instance_id}.support_footprints[{support_index}].id")
            local_y = number(support.get("local_y"), f"support {instance_id}/{support_id}.local_y")
            local_points = [vec2(point, f"support {instance_id}/{support_id}.points") for point in array(support.get("points"), f"support {instance_id}/{support_id}.points", nonempty=True)]
            if len(local_points) < 3:
                raise ContractError(f"support {instance_id}/{support_id} needs at least three points")
            step = number(support.get("sample_step"), f"support {instance_id}/{support_id}.sample_step", minimum=1e-6)
            if step > max_surface_step:
                errors.append(f"support {instance_id}/{support_id} sample step {step:g} exceeds {max_surface_step:g}")
            world_points = [transform_point(transform, (point[0], local_y, point[1])) for point in local_points]
            supports.append(
                SupportFootprint(
                    instance_id,
                    prop_class,
                    tuple((point[0], point[2]) for point in world_points),
                    world_points[0],
                    cross3(transform["basis_x"], transform["basis_z"]),
                    step,
                )
            )

    if len(instances) != expected_visible_prop_count:
        errors.append(f"visible prop manifest has {len(instances)} instances; expected {expected_visible_prop_count}")

    triangles: list[GroundTriangle] = []
    triangle_ids: set[str] = set()
    for index, raw in enumerate(array(model.get("render_ground_triangles"), "render_ground_triangles", nonempty=True)):
        item = obj(raw, f"render_ground_triangles[{index}]")
        triangle_id = text(item.get("id"), f"render_ground_triangles[{index}].id")
        if triangle_id in triangle_ids:
            raise ContractError(f"duplicate render-ground triangle ID {triangle_id}")
        triangle_ids.add(triangle_id)
        if text(item.get("source_kind"), f"triangle {triangle_id}.source_kind") != "render_mesh":
            raise ContractError(f"triangle {triangle_id} is not sourced from render_mesh geometry")
        text(item.get("source_node"), f"triangle {triangle_id}.source_node")
        surface_class = text(item.get("surface_class"), f"triangle {triangle_id}.surface_class")
        material_id = text(item.get("material_id"), f"triangle {triangle_id}.material_id")
        points = tuple(vec3(value, f"triangle {triangle_id}.vertices") for value in array(item.get("vertices"), f"triangle {triangle_id}.vertices"))
        if len(points) != 3:
            raise ContractError(f"triangle {triangle_id} must contain exactly three vertices")
        projected_area = abs(cross((points[0][0], points[0][2]), (points[1][0], points[1][2]), (points[2][0], points[2][2])))
        if projected_area <= 1e-10:
            raise ContractError(f"triangle {triangle_id} is degenerate in the XZ ground plane")
        triangles.append(
            GroundTriangle(
                triangle_id,
                surface_class,
                material_id,
                points,  # type: ignore[arg-type]
                (
                    min(point[0] for point in points),
                    min(point[2] for point in points),
                    max(point[0] for point in points),
                    max(point[2] for point in points),
                ),
            )
        )

    used_exemptions: set[tuple[tuple[tuple[str, str], tuple[str, str]], str]] = set()
    strict_contact_issue_count = 0
    overlap_issues = 0
    for first_index, first in enumerate(volumes):
        for second in volumes[first_index + 1 :]:
            if first.instance_id == second.instance_id:
                continue
            horizontal, contact_axis = strict_overlap_info(first.footprint, second.footprint)
            vertical = min(first.max_y, second.max_y) - max(first.min_y, second.min_y)
            if horizontal <= horizontal_epsilon or vertical <= vertical_epsilon:
                continue
            key = pair_key(first.instance_id, first.volume_id, second.instance_id, second.volume_id)
            if "occupancy" in exemptions.get(key, set()):
                used_exemptions.add((key, "occupancy"))
                contact = exemption_contacts[key]
                if abs(contact["reported_horizontal"] - horizontal) > contact_measurement_tolerance:
                    strict_contact_issue_count += 1
                    errors.append(
                        f"intentional contact {first.instance_id}/{first.volume_id} vs "
                        f"{second.instance_id}/{second.volume_id} reports horizontal penetration "
                        f"{contact['reported_horizontal']:.4g} but resolved geometry is {horizontal:.4g}"
                    )
                if abs(contact["reported_vertical"] - vertical) > contact_measurement_tolerance:
                    strict_contact_issue_count += 1
                    errors.append(
                        f"intentional contact {first.instance_id}/{first.volume_id} vs "
                        f"{second.instance_id}/{second.volume_id} reports vertical penetration "
                        f"{contact['reported_vertical']:.4g} but resolved geometry is {vertical:.4g}"
                    )
                normal_alignment = abs(
                    contact["contact_normal"][0] * contact_axis[0]
                    + contact["contact_normal"][1] * contact_axis[1]
                )
                matching_rules = [
                    rule
                    for rule in strict_contact_rules
                    if (
                        first.prop_class in rule["class_group_a"]
                        and second.prop_class in rule["class_group_b"]
                    )
                    or (
                        second.prop_class in rule["class_group_a"]
                        and first.prop_class in rule["class_group_b"]
                    )
                ]
                if len(matching_rules) > 1:
                    raise ContractError(
                        f"intentional contact {first.prop_class}/{second.prop_class} matches multiple strict rules"
                    )
                if matching_rules:
                    rule = matching_rules[0]
                    mode = contact["contact_mode"]
                    if mode not in rule["allowed_modes"]:
                        strict_contact_issue_count += 1
                        errors.append(
                            f"strict contact rule {rule['id']} forbids mode {mode} for "
                            f"{first.instance_id}/{second.instance_id}"
                        )
                    if normal_alignment + 1e-12 < rule["minimum_contact_normal_alignment"]:
                        strict_contact_issue_count += 1
                        errors.append(
                            f"strict contact rule {rule['id']} contact-normal alignment {normal_alignment:.4f} is too low"
                        )
                    if mode == "deformed_connector":
                        if not contact["interface_geometry_ids"]:
                            strict_contact_issue_count += 1
                            errors.append(
                                f"strict contact rule {rule['id']} requires separate damaged/deformed interface geometry"
                            )
                        if horizontal > rule["maximum_deformed_render_penetration"] + 1e-12:
                            strict_contact_issue_count += 1
                            errors.append(
                                f"strict contact rule {rule['id']} deformed penetration {horizontal:.4g} exceeds budget"
                            )
                    elif horizontal > rule["maximum_undeformed_render_penetration"] + 1e-12:
                        strict_contact_issue_count += 1
                        errors.append(
                            f"strict contact rule {rule['id']} undeformed vehicle/barrier penetration "
                            f"{horizontal:.4g} exceeds {rule['maximum_undeformed_render_penetration']:.4g}"
                        )
                continue
            overlap_issues += 1
            errors.append(
                f"unintentional transformed-volume overlap {first.instance_id}/{first.volume_id} "
                f"({first.prop_class}) vs {second.instance_id}/{second.volume_id} ({second.prop_class}); "
                f"horizontal={horizontal:.4g} vertical={vertical:.4g}"
            )

    clearance_checks = 0
    clearance_issues = 0
    exercised_rules: set[tuple[str, str, float]] = set()
    for rule in clearance_rules:
        upper_class, lower_class, minimum_gap = rule
        for upper in volumes:
            if upper.prop_class != upper_class:
                continue
            for lower in volumes:
                if lower.prop_class != lower_class or upper.instance_id == lower.instance_id:
                    continue
                horizontal = strict_overlap_depth(upper.footprint, lower.footprint)
                if horizontal <= horizontal_epsilon:
                    continue
                exercised_rules.add(rule)
                clearance_checks += 1
                key = pair_key(upper.instance_id, upper.volume_id, lower.instance_id, lower.volume_id)
                if "vertical_clearance" in exemptions.get(key, set()):
                    used_exemptions.add((key, "vertical_clearance"))
                    continue
                gap = upper.min_y - lower.max_y
                if gap + vertical_epsilon < minimum_gap:
                    clearance_issues += 1
                    errors.append(
                        f"vertical clearance {upper.instance_id}/{upper.volume_id} ({upper_class}) above "
                        f"{lower.instance_id}/{lower.volume_id} ({lower_class}) is {gap:.4g}; requires {minimum_gap:.4g}"
                    )
    if require_rule_exercise:
        for upper_class, lower_class, minimum_gap in clearance_rules:
            if (upper_class, lower_class, minimum_gap) not in exercised_rules:
                errors.append(f"vertical clearance rule {upper_class}>{lower_class} was not exercised by a horizontal-overlap case")

    for key, checks in exemptions.items():
        for check in checks:
            if (key, check) not in used_exemptions:
                errors.append(f"stale intentional-overlap exemption {key} for {check}: {exemption_meta[key]}")

    surface_samples = 0
    surface_issues = 0
    for support in supports:
        allowed = surface_rules.get(support.prop_class)
        if allowed is None:
            continue
        local_issues: list[str] = []
        for point in sample_polygon(list(support.polygon), support.sample_step):
            surface_samples += 1
            contact_y = support_height(support, point)
            hit = top_surface_at(triangles, point, contact_y + max_surface_height_delta, surface_height_epsilon)
            if hit is None:
                local_issues.append(f"no render-ground at ({point[0]:.3g},{point[1]:.3g})")
                continue
            triangle, height = hit
            if triangle.surface_class not in allowed:
                local_issues.append(
                    f"{triangle.surface_class} at ({point[0]:.3g},{point[1]:.3g}); allowed={','.join(sorted(allowed))}"
                )
            elif abs(contact_y - height) > max_surface_height_delta:
                local_issues.append(
                    f"surface height delta {abs(contact_y - height):.4g} at ({point[0]:.3g},{point[1]:.3g})"
                )
        if local_issues:
            surface_issues += len(local_issues)
            errors.append(
                f"semantic surface ownership failed for {support.instance_id} ({support.prop_class}) at {len(local_issues)} "
                f"full-footprint sample(s): {'; '.join(local_issues[:5])}"
            )

    ground_samples = 0
    ground_issues = 0
    regions = array(model.get("ground_regions"), "ground_regions", nonempty=True)
    for index, raw in enumerate(regions):
        region = obj(raw, f"ground_regions[{index}]")
        region_id = text(region.get("id"), f"ground_regions[{index}].id")
        polygon = [vec2(point, f"ground region {region_id}.polygon") for point in array(region.get("polygon"), f"ground region {region_id}.polygon", nonempty=True)]
        if len(polygon) < 3:
            raise ContractError(f"ground region {region_id} needs at least three polygon points")
        step = number(region.get("sample_step"), f"ground region {region_id}.sample_step", minimum=1e-6)
        if step > max_ground_step:
            errors.append(f"ground region {region_id} sample step {step:g} exceeds {max_ground_step:g}")
        expected = strings(region.get("expected_surface_classes"), f"ground region {region_id}.expected_surface_classes", nonempty=True)
        probe_from_y = number(region.get("probe_from_y"), f"ground region {region_id}.probe_from_y")
        local_issues: list[str] = []
        for point in sample_polygon(polygon, step):
            ground_samples += 1
            hit = top_surface_at(triangles, point, probe_from_y, surface_height_epsilon)
            if hit is None:
                local_issues.append(f"visible ground gap at ({point[0]:.3g},{point[1]:.3g})")
                continue
            triangle, _ = hit
            if triangle.surface_class not in expected:
                local_issues.append(
                    f"exposed {triangle.surface_class}/{triangle.material_id} at ({point[0]:.3g},{point[1]:.3g})"
                )
        if local_issues:
            ground_issues += len(local_issues)
            errors.append(
                f"render-ground coverage/seam failure in {region_id} at {len(local_issues)} sample(s): "
                f"{' ; '.join(local_issues[:5])}"
            )

    return {
        "status": "pass" if not errors else "fail",
        "contract_id": contract_id,
        "build_id": build_id,
        "scene_provenance": {
            "source_kind": "resolved_target_scene",
            "scene_path": scene_path,
            "revision_kind": provenance["revision_kind"],
            "dependency_closure_digest": closure_digest,
            "manifest_path": provenance["manifest_path"],
            "manifest_sha256": provenance["manifest_sha256"],
            "exporter": exporter,
            "exporter_sha256": provenance["exporter_sha256"],
            "export_preset": provenance["export_preset"],
            "export_preset_sha256": provenance["export_preset_sha256"],
            "visible_prop_query": visible_prop_query,
            "contact_interface_query": contact_interface_query,
        },
        "instance_count": len(instances),
        "volume_count": len(volumes),
        "render_triangle_count": len(triangles),
        "surface_sample_count": surface_samples,
        "ground_sample_count": ground_samples,
        "clearance_check_count": clearance_checks,
        "intentional_exemption_count": len(exemptions),
        "resolved_interface_geometry_count": len(resolved_interface_geometry_ids),
        "strict_contact_rule_count": len(strict_contact_rules),
        "strict_contact_issue_count": strict_contact_issue_count,
        "unintentional_overlap_count": overlap_issues,
        "surface_issue_count": surface_issues,
        "ground_issue_count": ground_issues,
        "clearance_issue_count": clearance_issues,
        "prior_structural_checks": {
            "collision_coverage": f"{collision_covered}/{collision_total}",
            "boundary_coverage": f"{boundary_covered}/{boundary_total}",
            "collision_alignment_pass": collision_alignment_pass,
        },
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
            f"[{marker}] environment-integrity id={report['contract_id']} "
            f"instances={report['instance_count']} volumes={report['volume_count']} "
            f"surface_samples={report['surface_sample_count']} ground_samples={report['ground_sample_count']} "
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
