#!/usr/bin/env python3
"""Audit road, junction, facade, furniture, closure, and visible-boundary semantics."""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass
import hashlib
import json
from math import acos, ceil, degrees, hypot
from pathlib import Path
import sys
from typing import Any

from PIL import Image

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
from environment_coverage_audit import (
    grid_samples,
    point_polygon_distance,
    point_segment_distance,
    polygon,
    ratio,
)
from resolved_scene_provenance_audit import (
    ProvenanceError,
    validate_scene_provenance_reference,
)


@dataclass(frozen=True)
class SurfaceRegion:
    region_id: str
    surface_class: str
    shape: tuple[Vec2, ...]


@dataclass(frozen=True)
class Lane:
    lane_id: str
    start_node: str
    end_node: str
    status: str
    allowed_surface_classes: frozenset[str]


@dataclass(frozen=True)
class Approach:
    approach_id: str
    junction_id: str
    inbound_lane_ids: tuple[str, ...]
    travel_direction: Vec2


@dataclass(frozen=True)
class PlacementProfile:
    profile_id: str
    allowed_surface_classes: frozenset[str]
    forbidden_surface_classes: frozenset[str]
    minimum_allowed_ratio: float
    maximum_forbidden_ratio: float
    allow_forbidden_with_closure: bool
    street_furniture: bool
    minimum_curb_setback: float
    maximum_curb_setback: float
    minimum_junction_clearance: float
    approach_required: bool
    maximum_approach_distance: float
    orientation_mode: str
    orientation_tolerance_degrees: float
    road_detail: bool
    minimum_crosswalk_clearance: float


@dataclass(frozen=True)
class PlacedObject:
    object_id: str
    object_class: str
    source_node: str
    profile_id: str
    footprint: tuple[Vec2, ...]
    anchor: Vec2
    forward: Vec2
    approach_id: str | None
    closure_id: str | None
    zone_id: str | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit exact resolved-scene road and streetscape semantics after geometry coverage."
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
    result = obj(data, "model root")
    result["__model_directory"] = str(path.parent)
    return result


def resolve_artifact(value: Any, label: str, model_directory: Path) -> Path:
    raw = text(value, label)
    supplied = Path(raw).expanduser()
    candidates = [supplied] if supplied.is_absolute() else [model_directory / supplied, Path.cwd() / supplied]
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.is_file():
            return resolved
    raise ContractError(f"{label} not found: {raw}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_artifact_hash(path: Path, expected: Any, label: str) -> None:
    declared = text(expected, label).lower()
    if len(declared) != 64 or any(character not in "0123456789abcdef" for character in declared):
        raise ContractError(f"{label} must be a SHA-256 hex digest")
    actual = sha256_file(path)
    if actual != declared:
        raise ContractError(f"{label} does not match {path}")


def srgb_to_linear(value: int) -> float:
    channel = value / 255.0
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def rgb_to_lab(pixel: tuple[int, int, int]) -> tuple[float, float, float]:
    red, green, blue = (srgb_to_linear(channel) for channel in pixel)
    x = (0.4124564 * red + 0.3575761 * green + 0.1804375 * blue) / 0.95047
    y = 0.2126729 * red + 0.7151522 * green + 0.0721750 * blue
    z = (0.0193339 * red + 0.1191920 * green + 0.9503041 * blue) / 1.08883

    def transform(value: float) -> float:
        return value ** (1.0 / 3.0) if value > 0.008856 else 7.787 * value + 16.0 / 116.0

    fx, fy, fz = transform(x), transform(y), transform(z)
    return 116.0 * fy - 16.0, 500.0 * (fx - fy), 200.0 * (fy - fz)


def delta_e(first: tuple[float, float, float], second: tuple[float, float, float]) -> float:
    return sum((left - right) ** 2 for left, right in zip(first, second)) ** 0.5


def flattened_pixels(image: Image.Image) -> list[Any]:
    getter = getattr(image, "get_flattened_data", None)
    return list(getter() if getter is not None else image.getdata())


def normalize(value: Vec2, label: str) -> Vec2:
    length = hypot(value[0], value[1])
    if length <= 1e-10:
        raise ContractError(f"{label} must not be zero")
    return value[0] / length, value[1] / length


def dot(first: Vec2, second: Vec2) -> float:
    return first[0] * second[0] + first[1] * second[1]


def centroid(shape: tuple[Vec2, ...]) -> Vec2:
    return (
        sum(point[0] for point in shape) / len(shape),
        sum(point[1] for point in shape) / len(shape),
    )


def distance(first: Vec2, second: Vec2) -> float:
    return hypot(first[0] - second[0], first[1] - second[1])


def vec3(value: Any, label: str) -> tuple[float, float, float]:
    raw = array(value, label)
    if len(raw) != 3:
        raise ContractError(f"{label} must contain three numbers")
    return (
        number(raw[0], f"{label}[0]"),
        number(raw[1], f"{label}[1]"),
        number(raw[2], f"{label}[2]"),
    )


def distance3(first: tuple[float, float, float], second: tuple[float, float, float]) -> float:
    return sum((left - right) ** 2 for left, right in zip(first, second)) ** 0.5


def standard_deviation(total: float, squared_total: float, count: int) -> float:
    if count <= 0:
        return 0.0
    mean = total / count
    return max(0.0, squared_total / count - mean * mean) ** 0.5


def sample_segment(start: Vec2, end: Vec2, step: float) -> list[Vec2]:
    length = distance(start, end)
    parts = max(1, int(ceil(length / step)))
    return [
        (
            start[0] + (end[0] - start[0]) * index / parts,
            start[1] + (end[1] - start[1]) * index / parts,
        )
        for index in range(parts + 1)
    ]


def sample_polyline_band(path: list[Vec2], step: float, clear_width: float) -> list[Vec2]:
    result: list[Vec2] = []
    half_width = clear_width / 2.0
    for start, end in zip(path, path[1:]):
        dx, dz = end[0] - start[0], end[1] - start[1]
        length = hypot(dx, dz)
        if length <= 1e-10:
            raise ContractError("junction continuity path contains a zero-length segment")
        normal = (-dz / length, dx / length)
        for point in sample_segment(start, end, step):
            result.extend(
                (
                    (point[0] - normal[0] * half_width, point[1] - normal[1] * half_width),
                    point,
                    (point[0] + normal[0] * half_width, point[1] + normal[1] * half_width),
                )
            )
    return result


def segments_intersect(first_start: Vec2, first_end: Vec2, second_start: Vec2, second_end: Vec2) -> bool:
    def orientation(a: Vec2, b: Vec2, c: Vec2) -> float:
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    values = (
        orientation(first_start, first_end, second_start),
        orientation(first_start, first_end, second_end),
        orientation(second_start, second_end, first_start),
        orientation(second_start, second_end, first_end),
    )
    epsilon = 1e-9
    if values[0] * values[1] < -epsilon and values[2] * values[3] < -epsilon:
        return True
    return any(
        abs(value) <= epsilon and point_segment_distance(point, start, end) <= epsilon
        for value, point, start, end in (
            (values[0], second_start, first_start, first_end),
            (values[1], second_end, first_start, first_end),
            (values[2], first_start, second_start, second_end),
            (values[3], first_end, second_start, second_end),
        )
    )


def polygon_distance(first: tuple[Vec2, ...], second: tuple[Vec2, ...]) -> float:
    if any(point_in_polygon(point, list(second)) for point in first) or any(
        point_in_polygon(point, list(first)) for point in second
    ):
        return 0.0
    if any(
        segments_intersect(
            start,
            first[(index + 1) % len(first)],
            other,
            second[(other_index + 1) % len(second)],
        )
        for index, start in enumerate(first)
        for other_index, other in enumerate(second)
    ):
        return 0.0
    return min(
        min(point_polygon_distance(point, second) for point in first),
        min(point_polygon_distance(point, first) for point in second),
    )


def surface_classes_at(point: Vec2, regions: list[SurfaceRegion]) -> set[str]:
    return {
        region.surface_class
        for region in regions
        if point_in_polygon(point, list(region.shape))
    }


def nearest_region_distance(
    point: Vec2, regions: list[SurfaceRegion], surface_classes: set[str]
) -> float:
    candidates = [
        point_polygon_distance(point, region.shape)
        for region in regions
        if region.surface_class in surface_classes
    ]
    return min(candidates) if candidates else float("inf")


def angle_error_degrees(first: Vec2, second: Vec2) -> float:
    first_n = normalize(first, "orientation vector")
    second_n = normalize(second, "reference vector")
    return degrees(acos(max(-1.0, min(1.0, dot(first_n, second_n)))))


def parse_cell(value: Any, label: str, width: int, height: int) -> tuple[int, int]:
    raw = array(value, label)
    if len(raw) != 2:
        raise ContractError(f"{label} must contain two integers")
    x = integer(raw[0], f"{label}[0]")
    z = integer(raw[1], f"{label}[1]")
    if x >= width or z >= height:
        raise ContractError(f"{label} lies outside {width}x{height} raster")
    return x, z


def unique_cells(
    value: Any, label: str, width: int, height: int, *, nonempty: bool = False
) -> set[tuple[int, int]]:
    raw = array(value, label, nonempty=nonempty)
    result = {
        parse_cell(item, f"{label}[{index}]", width, height)
        for index, item in enumerate(raw)
    }
    if len(result) != len(raw):
        raise ContractError(f"{label} contains duplicate cells")
    return result


def audit(model: dict[str, Any]) -> dict[str, Any]:
    if model.get("schema_version") != 5:
        raise ContractError(
            "schema_version must be 5; re-export closure-policy/topmost-surface evidence, "
            "marking-cap intersections, production placement rules, and all prior schema-v4 evidence"
        )
    contract_id = text(model.get("contract_id"), "contract_id")
    build_id = text(model.get("build_id"), "build_id")
    model_directory = Path(text(model.get("__model_directory"), "model directory"))
    raw_provenance = obj(model.get("scene_provenance"), "scene_provenance")
    try:
        provenance = validate_scene_provenance_reference(raw_provenance)
    except ProvenanceError as exc:
        raise ContractError(str(exc)) from exc
    text(raw_provenance.get("streetscape_query"), "scene_provenance.streetscape_query")
    text(raw_provenance.get("visible_surface_query"), "scene_provenance.visible_surface_query")
    junction_continuity_query = text(
        raw_provenance.get("junction_continuity_query"),
        "scene_provenance.junction_continuity_query",
    )
    road_detail_query = text(
        raw_provenance.get("road_detail_query"), "scene_provenance.road_detail_query"
    )
    visible_mesh_inventory_query = text(
        raw_provenance.get("visible_mesh_inventory_query"),
        "scene_provenance.visible_mesh_inventory_query",
    )
    rendered_material_query = text(
        raw_provenance.get("rendered_material_query"),
        "scene_provenance.rendered_material_query",
    )
    road_endpoint_query = text(
        raw_provenance.get("road_endpoint_query"), "scene_provenance.road_endpoint_query"
    )
    support_contact_query = text(
        raw_provenance.get("support_contact_query"),
        "scene_provenance.support_contact_query",
    )

    settings = obj(model.get("contract"), "contract")
    if text(settings.get("coordinate_system"), "contract.coordinate_system") != "godot_xz_y_up":
        raise ContractError("contract.coordinate_system must be godot_xz_y_up")
    sample_step = number(
        settings.get("footprint_sample_step"), "contract.footprint_sample_step", minimum=1e-6
    )
    graph_step = number(
        settings.get("graph_sample_step"), "contract.graph_sample_step", minimum=1e-6
    )
    node_tolerance = number(
        settings.get("node_tolerance"), "contract.node_tolerance", minimum=0.0
    )
    expected_regions = integer(
        settings.get("expected_surface_region_count"),
        "contract.expected_surface_region_count",
        1,
    )
    expected_objects = integer(
        settings.get("expected_placed_object_count"),
        "contract.expected_placed_object_count",
        1,
    )
    expected_buildings = integer(
        settings.get("expected_visible_building_count"),
        "contract.expected_visible_building_count",
        1,
    )
    expected_junctions = integer(
        settings.get("expected_junction_count"), "contract.expected_junction_count", 1
    )
    expected_approaches = integer(
        settings.get("expected_approach_count"), "contract.expected_approach_count", 1
    )
    expected_road_details = integer(
        settings.get("expected_road_detail_count"), "contract.expected_road_detail_count"
    )
    expected_visible_meshes = integer(
        settings.get("expected_visible_mesh_instance_count"),
        "contract.expected_visible_mesh_instance_count",
        1,
    )
    expected_support_contacts = integer(
        settings.get("expected_support_contact_count"),
        "contract.expected_support_contact_count",
    )
    expected_lane_terminations = integer(
        settings.get("expected_lane_boundary_termination_count"),
        "contract.expected_lane_boundary_termination_count",
    )
    expected_marking_chains = integer(
        settings.get("expected_marking_mesh_chain_count"),
        "contract.expected_marking_mesh_chain_count",
    )
    minimum_support_samples = integer(
        settings.get("minimum_support_contact_samples"),
        "contract.minimum_support_contact_samples",
        1,
    )
    maximum_support_gap = number(
        settings.get("maximum_support_contact_gap"),
        "contract.maximum_support_contact_gap",
        minimum=0.0,
    )

    errors: list[str] = []

    regions: list[SurfaceRegion] = []
    region_ids: set[str] = set()
    known_surface_classes: set[str] = set()
    for index, raw in enumerate(array(model.get("surface_regions"), "surface_regions", nonempty=True)):
        item = obj(raw, f"surface_regions[{index}]")
        region_id = text(item.get("id"), f"surface_regions[{index}].id")
        if region_id in region_ids:
            raise ContractError(f"duplicate surface region {region_id}")
        region_ids.add(region_id)
        surface_class = text(item.get("class"), f"surface region {region_id}.class")
        known_surface_classes.add(surface_class)
        regions.append(
            SurfaceRegion(
                region_id,
                surface_class,
                polygon(item.get("polygon"), f"surface region {region_id}.polygon"),
            )
        )
    if len(regions) != expected_regions:
        errors.append(f"surface region manifest has {len(regions)}; expected {expected_regions}")

    graph = obj(model.get("road_graph"), "road_graph")
    nodes: dict[str, Vec2] = {}
    node_kinds: dict[str, str] = {}
    for index, raw in enumerate(array(graph.get("nodes"), "road_graph.nodes", nonempty=True)):
        item = obj(raw, f"road_graph.nodes[{index}]")
        node_id = text(item.get("id"), f"road_graph.nodes[{index}].id")
        if node_id in nodes:
            raise ContractError(f"duplicate road node {node_id}")
        nodes[node_id] = vec2(item.get("position"), f"road node {node_id}.position")
        node_kinds[node_id] = text(item.get("kind"), f"road node {node_id}.kind")

    lanes: dict[str, Lane] = {}
    for index, raw in enumerate(array(graph.get("lanes"), "road_graph.lanes", nonempty=True)):
        item = obj(raw, f"road_graph.lanes[{index}]")
        lane_id = text(item.get("id"), f"road_graph.lanes[{index}].id")
        if lane_id in lanes:
            raise ContractError(f"duplicate lane {lane_id}")
        start_node = text(item.get("from"), f"lane {lane_id}.from")
        end_node = text(item.get("to"), f"lane {lane_id}.to")
        if start_node not in nodes or end_node not in nodes:
            errors.append(f"lane {lane_id} references unknown endpoint")
        status = text(item.get("status"), f"lane {lane_id}.status")
        if status not in {"open", "closed"}:
            raise ContractError(f"lane {lane_id}.status must be open or closed")
        allowed = frozenset(
            strings(item.get("allowed_surface_classes"), f"lane {lane_id}.allowed_surface_classes", nonempty=True)
        )
        unknown = sorted(allowed - known_surface_classes)
        if unknown:
            raise ContractError(f"lane {lane_id} uses unknown surfaces: {', '.join(unknown)}")
        lanes[lane_id] = Lane(lane_id, start_node, end_node, status, allowed)
        if start_node in nodes and end_node in nodes:
            wrong = [
                point
                for point in sample_segment(nodes[start_node], nodes[end_node], graph_step)
                if not (surface_classes_at(point, regions) & set(allowed))
            ]
            if wrong:
                errors.append(
                    f"lane {lane_id} leaves its authored road/intersection surfaces at {len(wrong)} sample(s)"
                )

    junction_centers: dict[str, Vec2] = {}
    junction_lanes: dict[str, tuple[set[str], set[str]]] = {}
    junction_kinds: dict[str, str] = {}
    for index, raw in enumerate(array(graph.get("junctions"), "road_graph.junctions", nonempty=True)):
        item = obj(raw, f"road_graph.junctions[{index}]")
        junction_id = text(item.get("id"), f"road_graph.junctions[{index}].id")
        if junction_id in junction_centers:
            raise ContractError(f"duplicate junction {junction_id}")
        center = vec2(item.get("center"), f"junction {junction_id}.center")
        junction_kind = text(item.get("kind"), f"junction {junction_id}.kind")
        if junction_kind not in {"cross", "t", "other"}:
            raise ContractError(f"junction {junction_id}.kind must be cross, t, or other")
        inbound = strings(item.get("inbound_lane_ids"), f"junction {junction_id}.inbound_lane_ids", nonempty=True)
        outbound = strings(item.get("outbound_lane_ids"), f"junction {junction_id}.outbound_lane_ids", nonempty=True)
        for lane_id in sorted(inbound | outbound):
            if lane_id not in lanes:
                errors.append(f"junction {junction_id} references unknown lane {lane_id}")
        movements = array(item.get("legal_movements"), f"junction {junction_id}.legal_movements", nonempty=True)
        for movement_index, raw_movement in enumerate(movements):
            movement = obj(raw_movement, f"junction {junction_id}.legal_movements[{movement_index}]")
            source = text(movement.get("from"), f"junction {junction_id} movement.from")
            target = text(movement.get("to"), f"junction {junction_id} movement.to")
            if source not in inbound or target not in outbound:
                errors.append(
                    f"junction {junction_id} legal movement {source}->{target} does not join declared inbound/outbound lanes"
                )
        junction_centers[junction_id] = center
        junction_lanes[junction_id] = inbound, outbound
        junction_kinds[junction_id] = junction_kind
    if len(junction_centers) != expected_junctions:
        errors.append(f"junction manifest has {len(junction_centers)}; expected {expected_junctions}")

    approaches: dict[str, Approach] = {}
    for index, raw in enumerate(array(graph.get("approaches"), "road_graph.approaches", nonempty=True)):
        item = obj(raw, f"road_graph.approaches[{index}]")
        approach_id = text(item.get("id"), f"road_graph.approaches[{index}].id")
        if approach_id in approaches:
            raise ContractError(f"duplicate approach {approach_id}")
        junction_id = text(item.get("junction_id"), f"approach {approach_id}.junction_id")
        inbound = tuple(sorted(strings(item.get("inbound_lane_ids"), f"approach {approach_id}.inbound_lane_ids", nonempty=True)))
        if junction_id not in junction_centers:
            errors.append(f"approach {approach_id} references unknown junction {junction_id}")
        elif not set(inbound) <= junction_lanes[junction_id][0]:
            errors.append(f"approach {approach_id} is not a subset of junction {junction_id} inbound lanes")
        direction = normalize(vec2(item.get("travel_direction"), f"approach {approach_id}.travel_direction"), f"approach {approach_id}.travel_direction")
        approaches[approach_id] = Approach(approach_id, junction_id, inbound, direction)
    if len(approaches) != expected_approaches:
        errors.append(f"approach manifest has {len(approaches)}; expected {expected_approaches}")

    sidewalk_nodes: dict[str, Vec2] = {}
    for index, raw in enumerate(array(graph.get("sidewalk_nodes"), "road_graph.sidewalk_nodes", nonempty=True)):
        item = obj(raw, f"road_graph.sidewalk_nodes[{index}]")
        node_id = text(item.get("id"), f"road_graph.sidewalk_nodes[{index}].id")
        if node_id in sidewalk_nodes:
            raise ContractError(f"duplicate sidewalk node {node_id}")
        sidewalk_nodes[node_id] = vec2(item.get("position"), f"sidewalk node {node_id}.position")
        if not (surface_classes_at(sidewalk_nodes[node_id], regions) & {"sidewalk_clear", "crosswalk"}):
            errors.append(f"sidewalk node {node_id} is not on sidewalk_clear/crosswalk")

    sidewalk_segments: list[tuple[str, str, str]] = []
    sidewalk_degree = {node_id: 0 for node_id in sidewalk_nodes}
    for index, raw in enumerate(array(graph.get("sidewalk_segments"), "road_graph.sidewalk_segments")):
        item = obj(raw, f"road_graph.sidewalk_segments[{index}]")
        segment_id = text(item.get("id"), f"sidewalk segment {index}.id")
        start = text(item.get("from"), f"sidewalk segment {segment_id}.from")
        end = text(item.get("to"), f"sidewalk segment {segment_id}.to")
        if start not in sidewalk_nodes or end not in sidewalk_nodes:
            errors.append(f"sidewalk segment {segment_id} references unknown node")
        else:
            sidewalk_degree[start] += 1
            sidewalk_degree[end] += 1
            wrong = [
                point
                for point in sample_segment(sidewalk_nodes[start], sidewalk_nodes[end], graph_step)
                if not (surface_classes_at(point, regions) & {"sidewalk_clear", "crosswalk"})
            ]
            if wrong:
                errors.append(f"sidewalk segment {segment_id} leaves the clear pedestrian route")
        sidewalk_segments.append((segment_id, start, end))

    continuity = obj(model.get("junction_corner_continuity"), "junction_corner_continuity")
    continuity_step = number(
        continuity.get("maximum_sample_spacing"),
        "junction_corner_continuity.maximum_sample_spacing",
        minimum=1e-6,
    )
    minimum_clear_width = number(
        continuity.get("minimum_clear_width"),
        "junction_corner_continuity.minimum_clear_width",
        minimum=1e-6,
    )
    allowed_corner_surfaces = strings(
        continuity.get("allowed_top_surface_classes"),
        "junction_corner_continuity.allowed_top_surface_classes",
        nonempty=True,
    )
    forbidden_corner_surfaces = strings(
        continuity.get("forbidden_top_surface_classes"),
        "junction_corner_continuity.forbidden_top_surface_classes",
        nonempty=True,
    )
    unknown_corner_surfaces = sorted(
        (allowed_corner_surfaces | forbidden_corner_surfaces) - known_surface_classes
    )
    if unknown_corner_surfaces:
        raise ContractError(
            "junction corner continuity uses unknown surfaces: "
            + ", ".join(unknown_corner_surfaces)
        )
    required_continuity_roles = {
        f"{approach_id}:{side}_return"
        for approach_id in approaches
        for side in ("left", "right")
    } | {
        f"{junction_id}:t_opposite_continuous"
        for junction_id, kind in junction_kinds.items()
        if kind == "t"
    }
    absence_roles: set[str] = set()
    for index, raw in enumerate(
        array(continuity.get("sidewalk_absences"), "junction_corner_continuity.sidewalk_absences")
    ):
        item = obj(raw, f"junction_corner_continuity.sidewalk_absences[{index}]")
        role = text(item.get("role"), f"sidewalk absence {index}.role")
        if role not in required_continuity_roles or role in absence_roles:
            raise ContractError(f"sidewalk absence {role} is duplicate or does not name a required junction side")
        text(item.get("reason"), f"sidewalk absence {role}.reason")
        text(item.get("raw_artifact"), f"sidewalk absence {role}.raw_artifact")
        absence_roles.add(role)
    required_continuity_roles -= absence_roles

    continuity_roles: set[str] = set()
    continuity_sample_count = 0
    continuity_issue_count = 0
    for index, raw in enumerate(array(continuity.get("runs"), "junction_corner_continuity.runs")):
        item = obj(raw, f"junction_corner_continuity.runs[{index}]")
        run_id = text(item.get("id"), f"junction continuity run {index}.id")
        role = text(item.get("role"), f"junction continuity run {run_id}.role")
        junction_id = text(item.get("junction_id"), f"junction continuity run {run_id}.junction_id")
        if junction_id not in junction_centers:
            errors.append(f"junction continuity run {run_id} references unknown junction {junction_id}")
        if role in continuity_roles:
            raise ContractError(f"duplicate junction continuity role {role}")
        continuity_roles.add(role)
        if role.endswith(":t_opposite_continuous"):
            if role != f"{junction_id}:t_opposite_continuous" or junction_kinds.get(junction_id) != "t":
                errors.append(f"junction continuity run {run_id} has an invalid T-junction opposite-side role")
        else:
            approach_id = text(item.get("approach_id"), f"junction continuity run {run_id}.approach_id")
            if approach_id not in approaches or approaches[approach_id].junction_id != junction_id:
                errors.append(f"junction continuity run {run_id} references the wrong approach/junction pair")
            if role not in {f"{approach_id}:left_return", f"{approach_id}:right_return"}:
                errors.append(f"junction continuity run {run_id} has an invalid approach-side role")
        path = [
            vec2(value, f"junction continuity run {run_id}.path[{point_index}]")
            for point_index, value in enumerate(
                array(item.get("path"), f"junction continuity run {run_id}.path", nonempty=True)
            )
        ]
        if len(path) < 2:
            raise ContractError(f"junction continuity run {run_id}.path needs at least two points")
        clear_width = number(
            item.get("clear_width"), f"junction continuity run {run_id}.clear_width", minimum=1e-6
        )
        if clear_width + 1e-9 < minimum_clear_width:
            errors.append(f"junction continuity run {run_id} clear width is below the project contract")
        text(item.get("raw_artifact"), f"junction continuity run {run_id}.raw_artifact")
        transitions: list[tuple[str, tuple[Vec2, ...], set[str]]] = []
        for transition_index, raw_transition in enumerate(
            array(item.get("transition_contracts"), f"junction continuity run {run_id}.transition_contracts")
        ):
            transition = obj(raw_transition, f"junction continuity run {run_id}.transition_contracts[{transition_index}]")
            transition_id = text(transition.get("id"), f"junction transition {run_id}/{transition_index}.id")
            transition_kind = text(transition.get("kind"), f"junction transition {run_id}/{transition_id}.kind")
            if transition_kind not in {"curb_ramp", "blended_transition", "authored_cutout"}:
                raise ContractError(f"junction transition {run_id}/{transition_id} has unsupported kind")
            transition_allowed = strings(
                transition.get("allowed_top_surface_classes"),
                f"junction transition {run_id}/{transition_id}.allowed_top_surface_classes",
                nonempty=True,
            )
            unknown = sorted(transition_allowed - known_surface_classes)
            if unknown:
                raise ContractError(
                    f"junction transition {run_id}/{transition_id} uses unknown surfaces: {', '.join(unknown)}"
                )
            text(transition.get("raw_artifact"), f"junction transition {run_id}/{transition_id}.raw_artifact")
            transitions.append(
                (
                    transition_id,
                    polygon(transition.get("polygon"), f"junction transition {run_id}/{transition_id}.polygon"),
                    transition_allowed,
                )
            )
        local_issues: list[str] = []
        for point in sample_polyline_band(path, continuity_step, clear_width):
            continuity_sample_count += 1
            classes = surface_classes_at(point, regions)
            matching = [value for value in transitions if point_in_polygon(point, list(value[1]))]
            if len(matching) > 1:
                local_issues.append(f"multiple transition contracts at ({point[0]:.3g},{point[1]:.3g})")
                continue
            if matching:
                _, _, transition_allowed = matching[0]
                if not (classes & transition_allowed) or (classes & forbidden_corner_surfaces) - transition_allowed:
                    local_issues.append(f"transition top surface mismatch at ({point[0]:.3g},{point[1]:.3g})")
            elif not (classes & allowed_corner_surfaces) or classes & forbidden_corner_surfaces:
                local_issues.append(
                    f"unclosed sidewalk/curb return at ({point[0]:.3g},{point[1]:.3g}); "
                    f"surfaces={','.join(sorted(classes)) or 'none'}"
                )
        if local_issues:
            continuity_issue_count += len(local_issues)
            errors.append(
                f"junction continuity run {run_id} has {len(local_issues)} inner-corner/band failure(s): "
                + "; ".join(local_issues[:5])
            )
    if continuity_roles != required_continuity_roles:
        errors.append(
            "junction corner continuity roles do not match declared approaches/T-sides; "
            f"missing={','.join(sorted(required_continuity_roles - continuity_roles)) or 'none'} "
            f"extra={','.join(sorted(continuity_roles - required_continuity_roles)) or 'none'}"
        )

    crosswalks: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(array(graph.get("crosswalks"), "road_graph.crosswalks", nonempty=True)):
        item = obj(raw, f"road_graph.crosswalks[{index}]")
        crosswalk_id = text(item.get("id"), f"crosswalk {index}.id")
        if crosswalk_id in crosswalks:
            raise ContractError(f"duplicate crosswalk {crosswalk_id}")
        junction_id = text(item.get("junction_id"), f"crosswalk {crosswalk_id}.junction_id")
        start = text(item.get("from_sidewalk_node"), f"crosswalk {crosswalk_id}.from_sidewalk_node")
        end = text(item.get("to_sidewalk_node"), f"crosswalk {crosswalk_id}.to_sidewalk_node")
        approach_ids = strings(item.get("approach_ids"), f"crosswalk {crosswalk_id}.approach_ids", nonempty=True)
        shape = polygon(item.get("polygon"), f"crosswalk {crosswalk_id}.polygon")
        if junction_id not in junction_centers:
            errors.append(f"crosswalk {crosswalk_id} references unknown junction {junction_id}")
        if start not in sidewalk_nodes or end not in sidewalk_nodes:
            errors.append(f"crosswalk {crosswalk_id} does not connect two known sidewalk nodes")
        else:
            if sidewalk_degree[start] < 1:
                errors.append(f"crosswalk {crosswalk_id} starts at isolated sidewalk node {start}")
            if sidewalk_degree[end] < 1:
                errors.append(f"crosswalk {crosswalk_id} ends at isolated sidewalk node {end}")
        unknown_approaches = sorted(approach_ids - set(approaches))
        if unknown_approaches:
            errors.append(f"crosswalk {crosswalk_id} references unknown approaches: {', '.join(unknown_approaches)}")
        wrong = [
            point
            for point in grid_samples(shape, sample_step).values()
            if not (surface_classes_at(point, regions) & {"crosswalk", "intersection"})
        ]
        if wrong:
            errors.append(f"crosswalk {crosswalk_id} leaves the intersection/crosswalk surface")
        crosswalks[crosswalk_id] = {
            "junction_id": junction_id,
            "from": start,
            "to": end,
            "approach_ids": approach_ids,
            "center": centroid(shape),
        }

    stop_line_approaches: set[str] = set()
    for index, raw in enumerate(array(graph.get("stop_lines"), "road_graph.stop_lines", nonempty=True)):
        item = obj(raw, f"road_graph.stop_lines[{index}]")
        stop_id = text(item.get("id"), f"stop line {index}.id")
        approach_id = text(item.get("approach_id"), f"stop line {stop_id}.approach_id")
        start = vec2(item.get("start"), f"stop line {stop_id}.start")
        end = vec2(item.get("end"), f"stop line {stop_id}.end")
        if approach_id in stop_line_approaches:
            raise ContractError(f"duplicate stop line for approach {approach_id}")
        stop_line_approaches.add(approach_id)
        approach = approaches.get(approach_id)
        if approach is None:
            errors.append(f"stop line {stop_id} references unknown approach {approach_id}")
            continue
        line_direction = (end[0] - start[0], end[1] - start[1])
        perpendicular_error = abs(90.0 - angle_error_degrees(line_direction, approach.travel_direction))
        tolerance = number(item.get("perpendicular_tolerance_degrees"), f"stop line {stop_id}.perpendicular_tolerance_degrees", minimum=0.0)
        if perpendicular_error > tolerance + 1e-9:
            errors.append(f"stop line {stop_id} is not perpendicular to approach {approach_id}")
        stop_center = ((start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0)
        if approach.junction_id in junction_centers:
            junction_center = junction_centers[approach.junction_id]
            toward = (junction_center[0] - stop_center[0], junction_center[1] - stop_center[1])
            if dot(toward, approach.travel_direction) <= 0.0:
                errors.append(f"stop line {stop_id} lies beyond or faces away from its junction")
            relevant = [value for value in crosswalks.values() if approach_id in value["approach_ids"]]
            if not relevant:
                errors.append(f"approach {approach_id} has no associated crosswalk")
            for crosswalk in relevant:
                crosswalk_center = crosswalk["center"]
                if distance(stop_center, junction_center) + node_tolerance < distance(crosswalk_center, junction_center):
                    errors.append(f"stop line {stop_id} is downstream of crosswalk on approach {approach_id}")
    missing_stop_lines = sorted(set(approaches) - stop_line_approaches)
    if missing_stop_lines:
        errors.append(f"approaches lack stop lines: {', '.join(missing_stop_lines)}")

    for chain_index, raw in enumerate(array(graph.get("lane_divider_chains"), "road_graph.lane_divider_chains", nonempty=True)):
        chain = obj(raw, f"road_graph.lane_divider_chains[{chain_index}]")
        chain_id = text(chain.get("id"), f"lane divider chain {chain_index}.id")
        max_gap = number(chain.get("maximum_gap"), f"lane divider chain {chain_id}.maximum_gap", minimum=0.0)
        segments = array(chain.get("segments"), f"lane divider chain {chain_id}.segments", nonempty=True)
        previous_end: Vec2 | None = None
        for segment_index, raw_segment in enumerate(segments):
            segment = obj(raw_segment, f"lane divider chain {chain_id}.segments[{segment_index}]")
            start = vec2(segment.get("start"), f"lane divider {chain_id}/{segment_index}.start")
            end = vec2(segment.get("end"), f"lane divider {chain_id}/{segment_index}.end")
            if previous_end is not None and distance(previous_end, start) > max_gap + 1e-9:
                errors.append(f"lane divider chain {chain_id} has a disconnected gap")
            for point in sample_segment(start, end, graph_step):
                if not (surface_classes_at(point, regions) & {"travel_lane", "intersection"}):
                    errors.append(f"lane divider chain {chain_id} leaves the carriageway")
                    break
            previous_end = end

    for marking_index, raw in enumerate(array(graph.get("area_markings"), "road_graph.area_markings")):
        marking = obj(raw, f"road_graph.area_markings[{marking_index}]")
        marking_id = text(marking.get("id"), f"area marking {marking_index}.id")
        marking_class = text(marking.get("class"), f"area marking {marking_id}.class")
        shape = polygon(marking.get("polygon"), f"area marking {marking_id}.polygon")
        forbidden = strings(marking.get("forbidden_surface_classes"), f"area marking {marking_id}.forbidden_surface_classes")
        bad = 0
        samples = list(grid_samples(shape, sample_step).values())
        for point in samples:
            if surface_classes_at(point, regions) & forbidden:
                bad += 1
        if bad:
            errors.append(f"{marking_class} marking {marking_id} overlaps forbidden junction/crosswalk surface")

    profiles: dict[str, PlacementProfile] = {}
    for index, raw in enumerate(array(model.get("placement_profiles"), "placement_profiles", nonempty=True)):
        item = obj(raw, f"placement_profiles[{index}]")
        profile_id = text(item.get("id"), f"placement_profiles[{index}].id")
        if profile_id in profiles:
            raise ContractError(f"duplicate placement profile {profile_id}")
        allowed = frozenset(strings(item.get("allowed_surface_classes"), f"placement profile {profile_id}.allowed_surface_classes", nonempty=True))
        forbidden = frozenset(strings(item.get("forbidden_surface_classes"), f"placement profile {profile_id}.forbidden_surface_classes"))
        unknown = sorted((allowed | forbidden) - known_surface_classes)
        if unknown:
            raise ContractError(f"placement profile {profile_id} uses unknown surfaces: {', '.join(unknown)}")
        furniture = boolean(item.get("street_furniture"), f"placement profile {profile_id}.street_furniture")
        profiles[profile_id] = PlacementProfile(
            profile_id,
            allowed,
            forbidden,
            ratio(item.get("minimum_allowed_ratio"), f"placement profile {profile_id}.minimum_allowed_ratio"),
            ratio(item.get("maximum_forbidden_ratio"), f"placement profile {profile_id}.maximum_forbidden_ratio"),
            boolean(item.get("allow_forbidden_with_closure"), f"placement profile {profile_id}.allow_forbidden_with_closure"),
            furniture,
            number(item.get("minimum_curb_setback"), f"placement profile {profile_id}.minimum_curb_setback", minimum=0.0) if furniture else 0.0,
            number(item.get("maximum_curb_setback"), f"placement profile {profile_id}.maximum_curb_setback", minimum=0.0) if furniture else 0.0,
            number(item.get("minimum_junction_clearance"), f"placement profile {profile_id}.minimum_junction_clearance", minimum=0.0) if furniture else 0.0,
            boolean(item.get("approach_required"), f"placement profile {profile_id}.approach_required") if furniture else False,
            number(item.get("maximum_approach_distance"), f"placement profile {profile_id}.maximum_approach_distance", minimum=0.0) if furniture else 0.0,
            text(item.get("orientation_mode"), f"placement profile {profile_id}.orientation_mode") if furniture else "none",
            number(item.get("orientation_tolerance_degrees"), f"placement profile {profile_id}.orientation_tolerance_degrees", minimum=0.0) if furniture else 0.0,
            boolean(item.get("road_detail"), f"placement profile {profile_id}.road_detail"),
            number(item.get("minimum_crosswalk_clearance"), f"placement profile {profile_id}.minimum_crosswalk_clearance", minimum=0.0),
        )
        if furniture and profiles[profile_id].maximum_curb_setback < profiles[profile_id].minimum_curb_setback:
            raise ContractError(f"placement profile {profile_id} curb setback maximum is below minimum")
        if profiles[profile_id].orientation_mode not in {"none", "with_travel", "face_oncoming"}:
            raise ContractError(f"placement profile {profile_id} has unknown orientation_mode")
        if profiles[profile_id].road_detail:
            if "crosswalk" not in profiles[profile_id].forbidden_surface_classes:
                errors.append(f"road-detail profile {profile_id} does not forbid crosswalk surfaces")
            if profiles[profile_id].maximum_forbidden_ratio > 0.0:
                errors.append(f"road-detail profile {profile_id} permits crosswalk overlap")
            if profiles[profile_id].allow_forbidden_with_closure:
                errors.append(f"road-detail profile {profile_id} cannot use a closure to cut crosswalk markings")

    placed_objects: dict[str, PlacedObject] = {}
    object_surface_results: dict[str, tuple[int, int, int]] = {}
    road_detail_count = 0
    for index, raw in enumerate(array(model.get("placed_objects"), "placed_objects", nonempty=True)):
        item = obj(raw, f"placed_objects[{index}]")
        object_id = text(item.get("id"), f"placed_objects[{index}].id")
        if object_id in placed_objects:
            raise ContractError(f"duplicate placed object {object_id}")
        profile_id = text(item.get("profile_id"), f"placed object {object_id}.profile_id")
        profile = profiles.get(profile_id)
        if profile is None:
            raise ContractError(f"placed object {object_id} uses unknown profile {profile_id}")
        shape = polygon(item.get("footprint"), f"placed object {object_id}.footprint")
        anchor = vec2(item.get("anchor"), f"placed object {object_id}.anchor")
        forward = normalize(vec2(item.get("forward"), f"placed object {object_id}.forward"), f"placed object {object_id}.forward")
        approach_id = item.get("approach_id")
        if approach_id is not None:
            approach_id = text(approach_id, f"placed object {object_id}.approach_id")
        closure_id = item.get("closure_id")
        if closure_id is not None:
            closure_id = text(closure_id, f"placed object {object_id}.closure_id")
        zone_id = item.get("zone_id")
        if zone_id is not None:
            zone_id = text(zone_id, f"placed object {object_id}.zone_id")
        object_class = text(item.get("class"), f"placed object {object_id}.class")
        placed_objects[object_id] = PlacedObject(
            object_id,
            object_class,
            text(item.get("source_node"), f"placed object {object_id}.source_node"),
            profile_id,
            shape,
            anchor,
            forward,
            approach_id,
            closure_id,
            zone_id,
        )
        normalized_class = object_class.lower().replace("-", "_")
        protected_road_surfaces = {"travel_lane", "intersection", "crosswalk", "sidewalk_clear"}
        vegetation_class = normalized_class in {
            "tree", "stump", "rock", "bush", "vegetation", "vegetation_tree",
            "vegetation_stump", "vegetation_rock", "vegetation_bush",
        }
        curb_furniture_class = normalized_class in {
            "hydrant", "street_light", "lamp", "lamp_post", "utility_pole",
            "traffic_signal", "traffic_sign", "road_sign", "street_sign",
        }
        if vegetation_class or curb_furniture_class:
            missing_forbidden = protected_road_surfaces - set(profile.forbidden_surface_classes)
            if missing_forbidden:
                errors.append(
                    f"placed object class {object_class} profile {profile_id} does not forbid "
                    f"road/intersection/crosswalk/sidewalk-clear surfaces: {','.join(sorted(missing_forbidden))}"
                )
            if set(profile.allowed_surface_classes) & protected_road_surfaces:
                errors.append(
                    f"placed object class {object_class} profile {profile_id} permits a protected road/pedestrian surface"
                )
            if profile.allow_forbidden_with_closure:
                errors.append(
                    f"placed object class {object_class} profile {profile_id} cannot use a closure exemption"
                )
        if curb_furniture_class and not profile.street_furniture:
            errors.append(
                f"placed object class {object_class} must use a street-furniture placement profile"
            )
        if normalized_class in {"traffic_signal", "traffic_sign", "road_sign", "street_sign"} \
                and not profile.approach_required:
            errors.append(
                f"placed object class {object_class} must require an exact road approach"
            )
        samples = list(grid_samples(shape, sample_step).values())
        allowed_count = 0
        forbidden_count = 0
        missing_count = 0
        for point in samples:
            classes = surface_classes_at(point, regions)
            if not classes:
                missing_count += 1
            if classes & set(profile.allowed_surface_classes):
                allowed_count += 1
            if classes & set(profile.forbidden_surface_classes):
                forbidden_count += 1
        allowed_ratio = allowed_count / max(1, len(samples))
        forbidden_ratio = forbidden_count / max(1, len(samples))
        closure_exemption = bool(closure_id and profile.allow_forbidden_with_closure)
        if allowed_ratio + 1e-12 < profile.minimum_allowed_ratio:
            errors.append(
                f"placed object {object_id} allowed-surface ratio {allowed_ratio:.4f} is below {profile.minimum_allowed_ratio:.4f}"
            )
        if forbidden_ratio > profile.maximum_forbidden_ratio + 1e-12 and not closure_exemption:
            errors.append(
                f"placed object {object_id} forbidden-surface ratio {forbidden_ratio:.4f} exceeds {profile.maximum_forbidden_ratio:.4f}"
            )
            if profile.allow_forbidden_with_closure and not closure_id:
                errors.append(
                    f"placed object {object_id} occupies a closure-controlled surface without an authored incident closure"
                )
        if missing_count:
            errors.append(f"placed object {object_id} has {missing_count} footprint sample(s) outside semantic surfaces")
        object_surface_results[object_id] = (len(samples), forbidden_count, missing_count)

        if profile.road_detail:
            road_detail_count += 1
            crosswalk_regions = [region for region in regions if region.surface_class == "crosswalk"]
            nearest_crosswalk = min(
                (polygon_distance(shape, region.shape) for region in crosswalk_regions),
                default=float("inf"),
            )
            if nearest_crosswalk + 1e-9 < profile.minimum_crosswalk_clearance:
                errors.append(
                    f"road detail {object_id} crosswalk clearance {nearest_crosswalk:.3f} is below profile budget"
                )

        if profile.street_furniture:
            curb_distance = nearest_region_distance(anchor, regions, {"curb"})
            if curb_distance < profile.minimum_curb_setback - 1e-9 or curb_distance > profile.maximum_curb_setback + 1e-9:
                errors.append(
                    f"street furniture {object_id} curb setback {curb_distance:.3f} is outside profile budget"
                )
            junction_distance = min((distance(anchor, value) for value in junction_centers.values()), default=float("inf"))
            if junction_distance + 1e-9 < profile.minimum_junction_clearance:
                errors.append(
                    f"street furniture {object_id} junction clearance {junction_distance:.3f} is below profile budget"
                )
            if profile.approach_required and not approach_id:
                errors.append(f"street furniture {object_id} lacks required approach association")
            if approach_id:
                approach = approaches.get(approach_id)
                if approach is None:
                    errors.append(f"street furniture {object_id} references unknown approach {approach_id}")
                else:
                    approach_segments = [
                        (nodes[lanes[lane_id].start_node], nodes[lanes[lane_id].end_node])
                        for lane_id in approach.inbound_lane_ids
                        if lane_id in lanes and lanes[lane_id].start_node in nodes and lanes[lane_id].end_node in nodes
                    ]
                    if not approach_segments:
                        errors.append(f"street furniture {object_id} approach {approach_id} has no resolved lane segment")
                    else:
                        lane_distance = min(
                            point_segment_distance(anchor, start, end)
                            for start, end in approach_segments
                        )
                        if lane_distance > profile.maximum_approach_distance + 1e-9:
                            errors.append(f"street furniture {object_id} is too far from associated approach {approach_id}")
                    if profile.orientation_mode == "with_travel":
                        error = angle_error_degrees(forward, approach.travel_direction)
                    elif profile.orientation_mode == "face_oncoming":
                        error = angle_error_degrees(forward, (-approach.travel_direction[0], -approach.travel_direction[1]))
                    else:
                        error = 0.0
                    if error > profile.orientation_tolerance_degrees + 1e-9:
                        errors.append(f"street furniture {object_id} orientation does not match approach {approach_id}")
    if len(placed_objects) != expected_objects:
        errors.append(f"placed object manifest has {len(placed_objects)}; expected {expected_objects}")

    resolved_meshes: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(
        array(model.get("resolved_visible_mesh_manifest"), "resolved_visible_mesh_manifest", nonempty=True)
    ):
        item = obj(raw, f"resolved_visible_mesh_manifest[{index}]")
        mesh_id = text(item.get("id"), f"resolved visible mesh {index}.id")
        if mesh_id in resolved_meshes:
            raise ContractError(f"duplicate resolved visible mesh {mesh_id}")
        node_path = text(item.get("node_path"), f"resolved visible mesh {mesh_id}.node_path")
        mesh_resource_id = text(
            item.get("mesh_resource_id"), f"resolved visible mesh {mesh_id}.mesh_resource_id"
        )
        surface_count = integer(
            item.get("surface_count"), f"resolved visible mesh {mesh_id}.surface_count", 1
        )
        surfaces: dict[int, dict[str, str]] = {}
        for surface_entry_index, raw_surface in enumerate(
            array(item.get("surfaces"), f"resolved visible mesh {mesh_id}.surfaces", nonempty=True)
        ):
            surface = obj(
                raw_surface,
                f"resolved visible mesh {mesh_id}.surfaces[{surface_entry_index}]",
            )
            surface_index = integer(
                surface.get("surface_index"),
                f"resolved visible mesh {mesh_id} surface index",
            )
            if surface_index >= surface_count:
                raise ContractError(
                    f"resolved visible mesh {mesh_id} surface {surface_index} is outside surface_count"
                )
            if surface_index in surfaces:
                raise ContractError(f"duplicate resolved surface {mesh_id}/{surface_index}")
            material_source_kind = text(
                surface.get("material_source_kind"),
                f"resolved visible mesh {mesh_id}/{surface_index}.material_source_kind",
            )
            if material_source_kind not in {
                "mesh_surface_material",
                "surface_override_material",
                "node_material_override",
                "missing",
            }:
                raise ContractError(
                    f"resolved visible mesh {mesh_id}/{surface_index} has unknown material source"
                )
            surfaces[surface_index] = {
                "material_id": text(
                    surface.get("effective_material_id"),
                    f"resolved visible mesh {mesh_id}/{surface_index}.effective_material_id",
                ),
                "material_source_kind": material_source_kind,
            }
        if set(surfaces) != set(range(surface_count)):
            raise ContractError(
                f"resolved visible mesh {mesh_id} surface manifest does not cover 0..{surface_count - 1}"
            )
        resolved_meshes[mesh_id] = {
            "node_path": node_path,
            "mesh_resource_id": mesh_resource_id,
            "surface_count": surface_count,
            "surfaces": surfaces,
        }
    if len(resolved_meshes) != expected_visible_meshes:
        errors.append(
            f"resolved visible mesh manifest has {len(resolved_meshes)}; expected {expected_visible_meshes}"
        )

    classifications: dict[str, dict[str, Any]] = {}
    scope_counts: dict[str, int] = {}
    furniture_class_counts: dict[str, int] = {}
    support_class_counts: dict[str, int] = {}
    furniture_meshes_by_object: dict[str, set[str]] = {}
    support_mesh_ids: set[str] = set()
    allowed_scopes = {
        "building",
        "street_furniture",
        "support_structure",
        "road_surface",
        "boundary_structure",
        "other",
    }
    for index, raw in enumerate(
        array(model.get("visible_mesh_classifications"), "visible_mesh_classifications", nonempty=True)
    ):
        item = obj(raw, f"visible_mesh_classifications[{index}]")
        mesh_id = text(item.get("mesh_instance_id"), f"visible mesh classification {index}.mesh_instance_id")
        if mesh_id in classifications:
            raise ContractError(f"duplicate visible mesh classification {mesh_id}")
        if mesh_id not in resolved_meshes:
            errors.append(f"visible mesh classification {mesh_id} is absent from resolved scene traversal")
        scope = text(item.get("semantic_scope"), f"visible mesh classification {mesh_id}.semantic_scope")
        if scope not in allowed_scopes:
            raise ContractError(f"visible mesh classification {mesh_id} has unknown semantic_scope")
        semantic_class = text(
            item.get("semantic_class"), f"visible mesh classification {mesh_id}.semantic_class"
        )
        classification_source_kind = text(
            item.get("classification_source_kind"),
            f"visible mesh classification {mesh_id}.classification_source_kind",
        )
        if classification_source_kind not in {
            "production_node_metadata",
            "production_resource_registry",
            "import_semantic_manifest",
        }:
            errors.append(
                f"visible mesh classification {mesh_id} is adapter-invented rather than production-authored"
            )
        text(
            item.get("classification_source_id"),
            f"visible mesh classification {mesh_id}.classification_source_id",
        )
        object_id_value = item.get("object_id")
        object_id = (
            text(object_id_value, f"visible mesh classification {mesh_id}.object_id")
            if object_id_value is not None
            else None
        )
        if scope == "other":
            text(item.get("exclusion_reason"), f"visible mesh classification {mesh_id}.exclusion_reason")
        elif scope in {"building", "street_furniture", "support_structure", "boundary_structure"} and object_id is None:
            errors.append(f"visible mesh classification {mesh_id} lacks an exact placed object ID")
        elif object_id is not None and object_id not in placed_objects:
            errors.append(f"visible mesh classification {mesh_id} references unknown object {object_id}")
        classifications[mesh_id] = {
            "scope": scope,
            "class": semantic_class,
            "object_id": object_id,
        }
        scope_counts[scope] = scope_counts.get(scope, 0) + 1
        if scope == "street_furniture":
            furniture_class_counts[semantic_class] = furniture_class_counts.get(semantic_class, 0) + 1
            if object_id is not None:
                furniture_meshes_by_object.setdefault(object_id, set()).add(mesh_id)
                placed = placed_objects.get(object_id)
                if placed is not None:
                    profile = profiles[placed.profile_id]
                    if not profile.street_furniture:
                        errors.append(
                            f"visible street furniture mesh {mesh_id} maps to non-furniture object {object_id}"
                        )
                    if placed.object_class != semantic_class:
                        errors.append(
                            f"visible street furniture mesh {mesh_id} class disagrees with object {object_id}"
                        )
        if scope == "support_structure":
            support_mesh_ids.add(mesh_id)
            support_class_counts[semantic_class] = support_class_counts.get(semantic_class, 0) + 1
    if set(classifications) != set(resolved_meshes):
        errors.append(
            "visible mesh classifications do not exactly cover resolved scene traversal; "
            f"missing={','.join(sorted(set(resolved_meshes) - set(classifications))) or 'none'} "
            f"extra={','.join(sorted(set(classifications) - set(resolved_meshes))) or 'none'}"
        )

    expected_scope_counts = {
        key: integer(value, f"contract.expected_visible_mesh_scope_counts.{key}")
        for key, value in obj(
            settings.get("expected_visible_mesh_scope_counts"),
            "contract.expected_visible_mesh_scope_counts",
        ).items()
    }
    if scope_counts != expected_scope_counts:
        errors.append(
            f"visible mesh scope counts {scope_counts} do not match declared counts {expected_scope_counts}"
        )
    expected_furniture_counts = {
        key: integer(value, f"contract.expected_street_furniture_class_counts.{key}")
        for key, value in obj(
            settings.get("expected_street_furniture_class_counts"),
            "contract.expected_street_furniture_class_counts",
        ).items()
    }
    if furniture_class_counts != expected_furniture_counts:
        errors.append(
            "visible street-furniture class inventory is incomplete; "
            f"resolved={furniture_class_counts} expected={expected_furniture_counts}"
        )
    expected_support_counts = {
        key: integer(value, f"contract.expected_support_structure_class_counts.{key}")
        for key, value in obj(
            settings.get("expected_support_structure_class_counts"),
            "contract.expected_support_structure_class_counts",
        ).items()
    }
    if support_class_counts != expected_support_counts:
        errors.append(
            f"visible support-structure class inventory {support_class_counts} does not match {expected_support_counts}"
        )
    for placed in placed_objects.values():
        if profiles[placed.profile_id].street_furniture and placed.object_id not in furniture_meshes_by_object:
            errors.append(
                f"street furniture object {placed.object_id} has no resolved visible mesh classification"
            )

    marking_chains: dict[str, dict[str, Any]] = {}
    marking_mesh_coverage: set[str] = set()
    for index, raw in enumerate(
        array(model.get("resolved_marking_mesh_chains"), "resolved_marking_mesh_chains")
    ):
        item = obj(raw, f"resolved_marking_mesh_chains[{index}]")
        chain_id = text(item.get("id"), f"resolved marking mesh chain {index}.id")
        if chain_id in marking_chains:
            raise ContractError(f"duplicate resolved marking mesh chain {chain_id}")
        if text(
            item.get("source_kind"), f"resolved marking mesh chain {chain_id}.source_kind"
        ) != "resolved_marking_mesh_chain":
            errors.append(f"marking chain {chain_id} is not exporter-owned resolved mesh evidence")
        text(item.get("marking_class"), f"resolved marking mesh chain {chain_id}.marking_class")
        chain_lane_ids = strings(
            item.get("lane_ids"), f"resolved marking mesh chain {chain_id}.lane_ids", nonempty=True
        )
        if not chain_lane_ids <= set(lanes):
            errors.append(f"marking chain {chain_id} references unknown lanes")
        chain_mesh_ids = strings(
            item.get("mesh_instance_ids"),
            f"resolved marking mesh chain {chain_id}.mesh_instance_ids",
            nonempty=True,
        )
        if chain_mesh_ids & marking_mesh_coverage:
            raise ContractError(f"marking chain {chain_id} reuses a mesh owned by another chain")
        marking_mesh_coverage |= chain_mesh_ids
        if not chain_mesh_ids <= set(resolved_meshes):
            errors.append(f"marking chain {chain_id} references missing resolved meshes")
        for mesh_id in sorted(chain_mesh_ids & set(classifications)):
            classification = classifications[mesh_id]
            if classification["scope"] != "road_surface" or classification["class"] != "road_marking":
                errors.append(
                    f"marking chain {chain_id} mesh {mesh_id} is not classified as road_surface/road_marking"
                )
        endpoints: list[Vec2] = []
        resolved_segments: list[tuple[Vec2, Vec2, str]] = []
        for segment_index, raw_segment in enumerate(
            array(item.get("segments"), f"resolved marking mesh chain {chain_id}.segments", nonempty=True)
        ):
            segment = obj(raw_segment, f"resolved marking mesh chain {chain_id}.segments[{segment_index}]")
            mesh_id = text(
                segment.get("mesh_instance_id"),
                f"resolved marking mesh chain {chain_id} segment {segment_index}.mesh_instance_id",
            )
            if mesh_id not in chain_mesh_ids:
                errors.append(f"marking chain {chain_id} segment uses an undeclared mesh {mesh_id}")
            if text(
                segment.get("measurement_source_kind"),
                f"resolved marking mesh chain {chain_id} segment {segment_index}.measurement_source_kind",
            ) != "resolved_mesh_vertices":
                errors.append(f"marking chain {chain_id} segment endpoints are not resolved from mesh vertices")
            surface_index = integer(
                segment.get("surface_index"),
                f"resolved marking mesh chain {chain_id} segment {segment_index}.surface_index",
            )
            start_vertex_index = integer(
                segment.get("start_vertex_index"),
                f"resolved marking mesh chain {chain_id} segment {segment_index}.start_vertex_index",
            )
            end_vertex_index = integer(
                segment.get("end_vertex_index"),
                f"resolved marking mesh chain {chain_id} segment {segment_index}.end_vertex_index",
            )
            if start_vertex_index == end_vertex_index:
                errors.append(f"marking chain {chain_id} segment reuses one mesh vertex as both endpoints")
            if mesh_id in resolved_meshes and surface_index not in resolved_meshes[mesh_id]["surfaces"]:
                errors.append(f"marking chain {chain_id} segment references an invalid mesh surface")
            start = vec2(
                segment.get("start"),
                f"resolved marking mesh chain {chain_id} segment {segment_index}.start",
            )
            end = vec2(
                segment.get("end"),
                f"resolved marking mesh chain {chain_id} segment {segment_index}.end",
            )
            if distance(start, end) <= 1e-9:
                errors.append(f"marking chain {chain_id} has a zero-length resolved segment")
            endpoints.extend((start, end))
            resolved_segments.append((start, end, mesh_id))
        marking_chains[chain_id] = {
            "lane_ids": chain_lane_ids,
            "mesh_ids": chain_mesh_ids,
            "endpoints": endpoints,
            "segments": resolved_segments,
        }
    expected_marking_mesh_ids = {
        mesh_id
        for mesh_id, classification in classifications.items()
        if classification["scope"] == "road_surface" and classification["class"] == "road_marking"
    }
    if marking_mesh_coverage != expected_marking_mesh_ids:
        errors.append(
            "resolved marking mesh chains do not exactly cover road-marking meshes; "
            f"missing={','.join(sorted(expected_marking_mesh_ids - marking_mesh_coverage)) or 'none'} "
            f"extra={','.join(sorted(marking_mesh_coverage - expected_marking_mesh_ids)) or 'none'}"
        )
    if len(marking_chains) != expected_marking_chains:
        errors.append(
            f"resolved marking mesh chain manifest has {len(marking_chains)}; expected {expected_marking_chains}"
        )

    termination_nodes = {
        node_id
        for node_id, kind in node_kinds.items()
        if kind == "boundary"
        and any(lane.start_node == node_id or lane.end_node == node_id for lane in lanes.values())
    }
    termination_records: set[str] = set()
    termination_measurements: list[dict[str, Any]] = []
    road_end_surface_measurements: list[dict[str, Any]] = []
    for index, raw in enumerate(
        array(model.get("lane_boundary_terminations"), "lane_boundary_terminations")
    ):
        item = obj(raw, f"lane_boundary_terminations[{index}]")
        node_id = text(item.get("node_id"), f"lane boundary termination {index}.node_id")
        if node_id in termination_records:
            raise ContractError(f"duplicate lane boundary termination {node_id}")
        termination_records.add(node_id)
        if node_id not in termination_nodes:
            errors.append(f"lane boundary termination {node_id} is not a resolved lane boundary endpoint")
            continue
        associated_lanes = {
            lane_id
            for lane_id, lane in lanes.items()
            if lane.start_node == node_id or lane.end_node == node_id
        }
        declared_lanes = strings(
            item.get("lane_ids"), f"lane boundary termination {node_id}.lane_ids", nonempty=True
        )
        if declared_lanes != associated_lanes:
            errors.append(f"lane boundary termination {node_id} does not own every incident lane")
        termination_kind = text(
            item.get("termination_kind"), f"lane boundary termination {node_id}.termination_kind"
        )
        if termination_kind not in {"continued_offmap", "turn", "cul_de_sac", "physical_closure"}:
            raise ContractError(f"lane boundary termination {node_id} has unsupported kind")
        outward = normalize(
            vec2(
                item.get("outward_direction"),
                f"lane boundary termination {node_id}.outward_direction",
            ),
            f"lane boundary termination {node_id}.outward_direction",
        )
        declared_region_ids = strings(
            item.get("surface_region_ids"),
            f"lane boundary termination {node_id}.surface_region_ids",
            nonempty=True,
        )
        unknown_regions = sorted(declared_region_ids - region_ids)
        if unknown_regions:
            errors.append(
                f"lane boundary termination {node_id} references unknown surfaces: {', '.join(unknown_regions)}"
            )
        geometry = obj(
            item.get("termination_geometry"),
            f"lane boundary termination {node_id}.termination_geometry",
        )
        if text(
            geometry.get("source_kind"),
            f"lane boundary termination {node_id}.termination_geometry.source_kind",
        ) != "resolved_typed_termination_geometry":
            errors.append(f"lane boundary termination {node_id} geometry is adapter-declared")
        profile_kind = text(
            geometry.get("profile_kind"),
            f"lane boundary termination {node_id}.termination_geometry.profile_kind",
        )
        allowed_profiles = {
            "continued_offmap": {"offmap_corridor"},
            "turn": {"turn_connection"},
            "cul_de_sac": {"cul_de_sac_bulb", "cul_de_sac_hammerhead"},
            "physical_closure": {
                "barrier_closure",
                "gate_closure",
                "debris_closure",
                "facade_closure",
                "terrain_closure",
                "vehicle_cordon",
            },
        }
        if profile_kind not in allowed_profiles[termination_kind]:
            errors.append(
                f"lane boundary termination {node_id} geometry profile {profile_kind} "
                f"does not match {termination_kind}"
            )
        cap_mesh_ids = strings(
            geometry.get("mesh_instance_ids"),
            f"lane boundary termination {node_id}.termination_geometry.mesh_instance_ids",
            nonempty=True,
        )
        unknown_caps = sorted(cap_mesh_ids - set(resolved_meshes))
        if unknown_caps:
            errors.append(
                f"lane boundary termination {node_id} references unknown cap meshes: {', '.join(unknown_caps)}"
            )
        raw_cause_ids = strings(
            item.get("visible_cause_object_ids"),
            f"lane boundary termination {node_id}.visible_cause_object_ids",
        )
        unknown_causes = sorted(raw_cause_ids - set(placed_objects))
        if unknown_causes:
            errors.append(
                f"lane boundary termination {node_id} references unknown visible causes: {', '.join(unknown_causes)}"
            )
        geometry_footprint = polygon(
            geometry.get("footprint"),
            f"lane boundary termination {node_id}.termination_geometry.footprint",
        )
        top_surface_classes = strings(
            geometry.get("top_surface_classes"),
            f"lane boundary termination {node_id}.termination_geometry.top_surface_classes",
            nonempty=True,
        )
        travel_lane_overlap_ratio = ratio(
            geometry.get("travel_lane_overlap_ratio"),
            f"lane boundary termination {node_id}.termination_geometry.travel_lane_overlap_ratio",
        )
        marking_chain_ids = strings(
            item.get("marking_chain_ids"),
            f"lane boundary termination {node_id}.marking_chain_ids",
        )
        physical_marking_policy: str | None = None
        relevant_marking_chains = {
            chain_id
            for chain_id, chain in marking_chains.items()
            if chain["lane_ids"] & associated_lanes
        }
        if marking_chain_ids != relevant_marking_chains:
            errors.append(
                f"lane boundary termination {node_id} marking chains do not exactly match incident-lane meshes"
            )
        if not marking_chain_ids:
            text(
                item.get("marking_absence_reason"),
                f"lane boundary termination {node_id}.marking_absence_reason",
            )
        text(item.get("raw_artifact"), f"lane boundary termination {node_id}.raw_artifact")
        endpoint = nodes[node_id]
        for placed in placed_objects.values():
            if placed.object_class == "building" and point_in_polygon(endpoint, list(placed.footprint)):
                errors.append(
                    f"lane boundary endpoint {node_id} lies inside building footprint {placed.object_id}"
                )
        if termination_kind == "continued_offmap":
            continuation = number(
                item.get("minimum_surface_continuation"),
                f"lane boundary termination {node_id}.minimum_surface_continuation",
                minimum=graph_step,
            )
            declared_regions = [region for region in regions if region.region_id in declared_region_ids]
            misses = [
                point
                for point in sample_segment(
                    endpoint,
                    (endpoint[0] + outward[0] * continuation, endpoint[1] + outward[1] * continuation),
                    graph_step,
                )[1:]
                if not any(point_in_polygon(point, list(region.shape)) for region in declared_regions)
            ]
            if misses:
                errors.append(
                    f"lane boundary termination {node_id} has a bare cutoff instead of resolved off-map continuation"
                )
            required_continuation_classes = strings(
                item.get("required_continuation_surface_classes"),
                f"lane boundary termination {node_id}.required_continuation_surface_classes",
                nonempty=True,
            )
            if not {"travel_lane", "sidewalk_clear", "curb"} <= required_continuation_classes:
                errors.append(
                    f"lane boundary termination {node_id} off-map corridor lacks road/sidewalk/curb continuation"
                )
            sampled_continuation_classes: set[str] = set()
            for sample_index, raw_sample in enumerate(
                array(
                    item.get("continuation_surface_samples"),
                    f"lane boundary termination {node_id}.continuation_surface_samples",
                    nonempty=True,
                )
            ):
                sample = obj(
                    raw_sample,
                    f"lane boundary termination {node_id}.continuation_surface_samples[{sample_index}]",
                )
                if text(
                    sample.get("source_kind"),
                    f"lane boundary termination {node_id} continuation sample {sample_index}.source_kind",
                ) != "resolved_render_surface_sample":
                    errors.append(f"lane boundary termination {node_id} has adapter-invented continuation samples")
                sample_class = text(
                    sample.get("surface_class"),
                    f"lane boundary termination {node_id} continuation sample {sample_index}.surface_class",
                )
                sample_point = vec2(
                    sample.get("point"),
                    f"lane boundary termination {node_id} continuation sample {sample_index}.point",
                )
                sample_mesh_id = text(
                    sample.get("mesh_instance_id"),
                    f"lane boundary termination {node_id} continuation sample {sample_index}.mesh_instance_id",
                )
                if sample_mesh_id not in cap_mesh_ids or sample_mesh_id not in resolved_meshes:
                    errors.append(f"lane boundary termination {node_id} continuation sample lacks resolved geometry")
                projected = dot((sample_point[0] - endpoint[0], sample_point[1] - endpoint[1]), outward)
                if projected + 1e-9 < continuation:
                    errors.append(f"lane boundary termination {node_id} continuation sample stops before its budget")
                matching_regions = [
                    region
                    for region in declared_regions
                    if region.surface_class == sample_class
                    and point_in_polygon(sample_point, list(region.shape))
                ]
                if not matching_regions:
                    errors.append(
                        f"lane boundary termination {node_id} continuation sample is not on its declared top surface"
                    )
                sampled_continuation_classes.add(sample_class)
            if sampled_continuation_classes != required_continuation_classes:
                errors.append(
                    f"lane boundary termination {node_id} continuation samples do not exactly cover required classes"
                )
            for building in placed_objects.values():
                if building.object_class == "building" and polygon_distance(
                    building.footprint, geometry_footprint
                ) <= 1e-9:
                    errors.append(
                        f"lane boundary continuation {node_id} intersects building footprint {building.object_id}"
                    )
            minimum_marking_continuation = number(
                item.get("minimum_marking_continuation"),
                f"lane boundary termination {node_id}.minimum_marking_continuation",
                minimum=0.0,
            )
            for chain_id in sorted(marking_chain_ids & set(marking_chains)):
                maximum_projection = max(
                    dot((point[0] - endpoint[0], point[1] - endpoint[1]), outward)
                    for point in marking_chains[chain_id]["endpoints"]
                )
                if maximum_projection + 1e-9 < minimum_marking_continuation:
                    errors.append(
                        f"lane boundary termination {node_id} marking mesh {chain_id} does not continue off-map"
                    )
                termination_measurements.append(
                    {
                        "node_id": node_id,
                        "termination_kind": termination_kind,
                        "profile_kind": profile_kind,
                        "marking_chain_id": chain_id,
                        "measurement": "outward_continuation",
                        "measured_distance": maximum_projection,
                        "minimum_distance": minimum_marking_continuation,
                    }
                )
        elif termination_kind == "turn":
            continuation_lanes = strings(
                item.get("continuation_lane_ids"),
                f"lane boundary termination {node_id}.continuation_lane_ids",
                nonempty=True,
            )
            if not continuation_lanes <= set(lanes):
                errors.append(f"lane boundary termination {node_id} turn references unknown lanes")
        elif termination_kind == "cul_de_sac":
            if not ({"travel_lane", "intersection"} & top_surface_classes):
                errors.append(f"lane boundary termination {node_id} cul-de-sac lacks authored road turnaround")
        elif termination_kind == "physical_closure":
            if not raw_cause_ids:
                errors.append(f"lane boundary termination {node_id} physical closure lacks a visible cause")
            elif all(
                point_polygon_distance(endpoint, placed_objects[cause_id].footprint) > node_tolerance
                for cause_id in raw_cause_ids
                if cause_id in placed_objects
            ):
                errors.append(
                    f"lane boundary termination {node_id} physical closure is detached from its visible cause"
                )
            cause_mesh_ids = {
                mesh_id
                for mesh_id, classification in classifications.items()
                if classification["object_id"] in raw_cause_ids
            }
            if not cap_mesh_ids <= cause_mesh_ids:
                errors.append(
                    f"lane boundary termination {node_id} uses common/non-cause geometry as its physical cap"
                )
            if travel_lane_overlap_ratio > 0.0 and top_surface_classes & {
                "sidewalk_clear",
                "curb",
                "furnishing_zone",
            }:
                errors.append(
                    f"lane boundary termination {node_id} uses pedestrian slab geometry as a road closure"
                )

            road_end_policy = text(
                item.get("road_end_policy"),
                f"lane boundary termination {node_id}.road_end_policy",
            )
            expected_policy_by_profile = {
                "vehicle_cordon": "vehicle_cordon",
                "facade_closure": "facade_end",
                "barrier_closure": "barrier_end",
                "gate_closure": "gate_end",
                "debris_closure": "debris_end",
                "terrain_closure": "terrain_end",
            }
            expected_policy = expected_policy_by_profile.get(profile_kind)
            if road_end_policy != expected_policy:
                errors.append(
                    f"lane boundary termination {node_id} road-end policy {road_end_policy} "
                    f"does not match {profile_kind}; expected {expected_policy}"
                )

            physical_marking_policy = text(
                item.get("marking_policy"),
                f"lane boundary termination {node_id}.marking_policy",
            )
            allowed_marking_policies = {
                "vehicle_cordon": {"stop_before_cause", "continue_under_visible_vehicle_cause"},
                "facade_end": {"stop_before_cause"},
                "barrier_end": {"stop_before_cause"},
                "gate_end": {"stop_before_cause"},
                "debris_end": {"stop_before_cause"},
                "terrain_end": {"stop_before_cause"},
            }
            if physical_marking_policy not in allowed_marking_policies.get(road_end_policy, set()):
                errors.append(
                    f"lane boundary termination {node_id} marking policy {physical_marking_policy} "
                    f"does not match road-end policy {road_end_policy}"
                )

            overlay_mesh_ids = strings(
                item.get("termination_overlay_mesh_ids"),
                f"lane boundary termination {node_id}.termination_overlay_mesh_ids",
            )
            unknown_overlays = sorted(overlay_mesh_ids - set(resolved_meshes))
            if unknown_overlays:
                errors.append(
                    f"lane boundary termination {node_id} references unknown termination overlays: "
                    + ", ".join(unknown_overlays)
                )
            if overlay_mesh_ids:
                errors.append(
                    f"lane boundary termination {node_id} uses surrogate road-end overlay geometry; "
                    "reconstruct the real road, facade, terrain, or visible cause instead"
                )

            relation = obj(
                item.get("road_substrate_relation"),
                f"lane boundary termination {node_id}.road_substrate_relation",
            )
            if text(
                relation.get("source_kind"),
                f"lane boundary termination {node_id}.road_substrate_relation.source_kind",
            ) != "exporter_resolved_topmost_render_mesh_samples":
                errors.append(
                    f"lane boundary termination {node_id} road/substrate relation is adapter-declared"
                )
            ray_top_y = number(
                relation.get("ray_top_y"),
                f"lane boundary termination {node_id}.road_substrate_relation.ray_top_y",
            )
            ray_bottom_y = number(
                relation.get("ray_bottom_y"),
                f"lane boundary termination {node_id}.road_substrate_relation.ray_bottom_y",
            )
            if ray_top_y <= ray_bottom_y:
                raise ContractError(
                    f"lane boundary termination {node_id} topmost render query has inverted Y bounds"
                )
            road_substrate_continues = boolean(
                relation.get("road_substrate_continues"),
                f"lane boundary termination {node_id}.road_substrate_relation.road_substrate_continues",
            )
            expected_continuation = road_end_policy in {
                "vehicle_cordon", "barrier_end", "gate_end", "debris_end"
            }
            if road_substrate_continues != expected_continuation:
                verb = "continue beneath/through the visible closure" if expected_continuation else "stop before the facade/terrain"
                errors.append(
                    f"lane boundary termination {node_id} road substrate must {verb}"
                )
            required_phases = (
                {"before_cause", "between_causes", "beyond_cause"}
                if road_end_policy == "vehicle_cordon" and len(raw_cause_ids) >= 2
                else {"before_cause", "beyond_cause"}
                if road_end_policy == "vehicle_cordon"
                else {"before_cause", "beyond_cause"}
                if expected_continuation
                else {"before_cause", "at_cause"}
            )
            observed_phases: set[str] = set()
            forbidden_surrogate_classes = {
                "closure_patch", "road_end_patch", "surrogate_overlay",
                "surrogate_vehicle_bed", "dark_vehicle_bed", "debug_plane",
            }
            for sample_index, raw_sample in enumerate(
                array(
                    relation.get("samples"),
                    f"lane boundary termination {node_id}.road_substrate_relation.samples",
                    nonempty=True,
                )
            ):
                sample = obj(
                    raw_sample,
                    f"lane boundary termination {node_id} road/substrate sample {sample_index}",
                )
                if text(
                    sample.get("source_kind"),
                    f"lane boundary termination {node_id} road/substrate sample {sample_index}.source_kind",
                ) != "exporter_resolved_topmost_render_mesh_sample":
                    errors.append(
                        f"lane boundary termination {node_id} road/substrate sample {sample_index} is adapter-declared"
                    )
                phase = text(
                    sample.get("phase"),
                    f"lane boundary termination {node_id} road/substrate sample {sample_index}.phase",
                )
                if phase in observed_phases:
                    raise ContractError(
                        f"lane boundary termination {node_id} duplicates road/substrate phase {phase}"
                    )
                observed_phases.add(phase)
                vec2(
                    sample.get("point"),
                    f"lane boundary termination {node_id} road/substrate sample {sample_index}.point",
                )
                sample_surface_class = text(
                    sample.get("surface_class"),
                    f"lane boundary termination {node_id} road/substrate sample {sample_index}.surface_class",
                )
                sample_mesh_id = text(
                    sample.get("mesh_instance_id"),
                    f"lane boundary termination {node_id} road/substrate sample {sample_index}.mesh_instance_id",
                )
                topmost_mesh_id = text(
                    sample.get("topmost_mesh_instance_id"),
                    f"lane boundary termination {node_id} road/substrate sample {sample_index}.topmost_mesh_instance_id",
                )
                covering_mesh_ids = strings(
                    sample.get("covering_mesh_instance_ids"),
                    f"lane boundary termination {node_id} road/substrate sample {sample_index}.covering_mesh_instance_ids",
                )
                coplanar_top_mesh_ids = strings(
                    sample.get("coplanar_top_mesh_instance_ids"),
                    f"lane boundary termination {node_id} road/substrate sample {sample_index}.coplanar_top_mesh_instance_ids",
                    nonempty=True,
                )
                for mesh_id in sorted(
                    {sample_mesh_id, topmost_mesh_id} | covering_mesh_ids | coplanar_top_mesh_ids
                ):
                    if mesh_id not in resolved_meshes:
                        errors.append(
                            f"lane boundary termination {node_id} road/substrate sample {sample_index} "
                            f"references missing resolved mesh {mesh_id}"
                        )
                if topmost_mesh_id not in coplanar_top_mesh_ids:
                    errors.append(
                        f"lane boundary termination {node_id} road/substrate sample {sample_index} "
                        "topmost mesh is absent from its exporter-resolved coplanar set"
                    )
                if len(coplanar_top_mesh_ids) > 1:
                    errors.append(
                        f"lane boundary termination {node_id} road/substrate sample {sample_index} "
                        "has ambiguous coplanar top meshes/z-fighting at the road end"
                    )
                topmost_classification = classifications.get(topmost_mesh_id, {})
                topmost_semantic_class = topmost_classification.get("class")
                covering_classes = {
                    classifications.get(mesh_id, {}).get("class") for mesh_id in covering_mesh_ids
                }
                road_end_surface_measurements.append(
                    {
                        "node_id": node_id,
                        "road_end_policy": road_end_policy,
                        "phase": phase,
                        "surface_class": sample_surface_class,
                        "base_mesh_instance_id": sample_mesh_id,
                        "topmost_mesh_instance_id": topmost_mesh_id,
                        "covering_mesh_instance_ids": sorted(covering_mesh_ids),
                        "coplanar_top_mesh_instance_ids": sorted(coplanar_top_mesh_ids),
                    }
                )
                if topmost_semantic_class in forbidden_surrogate_classes or covering_classes & forbidden_surrogate_classes:
                    errors.append(
                        f"lane boundary termination {node_id} road/substrate sample {sample_index} "
                        "is hidden by a surrogate/dark closure plane"
                    )
                if phase in {"before_cause", "between_causes", "beyond_cause"} and expected_continuation:
                    if sample_surface_class != "travel_lane":
                        errors.append(
                            f"lane boundary termination {node_id} phase {phase} does not preserve road substrate"
                        )
                    base_classification = classifications.get(sample_mesh_id, {})
                    if base_classification.get("scope") != "road_surface" or base_classification.get("class") != "road_surface":
                        errors.append(
                            f"lane boundary termination {node_id} phase {phase} is not resolved from the authored road mesh"
                        )
                    if topmost_mesh_id != sample_mesh_id or covering_mesh_ids:
                        errors.append(
                            f"lane boundary termination {node_id} phase {phase} is covered by ad-hoc termination geometry"
                        )
                if road_end_policy in {"facade_end", "terrain_end"}:
                    if phase == "before_cause":
                        base_classification = classifications.get(sample_mesh_id, {})
                        if sample_surface_class != "travel_lane" \
                                or base_classification.get("scope") != "road_surface" \
                                or base_classification.get("class") != "road_surface" \
                                or topmost_mesh_id != sample_mesh_id or covering_mesh_ids:
                            errors.append(
                                f"lane boundary termination {node_id} lacks unobstructed authored road substrate before its semantic end"
                            )
                    if phase == "at_cause":
                        if sample_surface_class == "travel_lane":
                            errors.append(
                                f"lane boundary termination {node_id} road substrate continues into its facade/terrain"
                            )
                        valid_end_mass = (
                            topmost_classification.get("scope") in {"building", "boundary_structure"}
                            if road_end_policy == "facade_end"
                            else topmost_classification.get("scope") in {"boundary_structure", "other"}
                            and topmost_classification.get("class") in {"terrain", "cliff", "landscape"}
                        )
                        if not valid_end_mass:
                            errors.append(
                                f"lane boundary termination {node_id} semantic end is not the topmost facade/terrain mass"
                            )
            if observed_phases != required_phases:
                errors.append(
                    f"lane boundary termination {node_id} road/substrate phases do not exactly cover "
                    f"{','.join(sorted(required_phases))}"
                )

            if physical_marking_policy == "stop_before_cause":
                for chain_id in sorted(marking_chain_ids & set(marking_chains)):
                    if any(
                        point_in_polygon(point, list(geometry_footprint))
                        for start, end, _ in marking_chains[chain_id]["segments"]
                        for point in sample_segment(start, end, graph_step)
                    ):
                        errors.append(
                            f"lane boundary termination {node_id} marking mesh {chain_id} lies beneath/intersects its closure geometry"
                        )

        if termination_kind == "cul_de_sac" or (
            termination_kind == "physical_closure" and physical_marking_policy == "stop_before_cause"
        ):
            minimum_marking = number(
                item.get("minimum_marking_stop_distance"),
                f"lane boundary termination {node_id}.minimum_marking_stop_distance",
                minimum=0.0,
            )
            maximum_marking = number(
                item.get("maximum_marking_stop_distance"),
                f"lane boundary termination {node_id}.maximum_marking_stop_distance",
                minimum=0.0,
            )
            if maximum_marking < minimum_marking:
                raise ContractError(f"lane boundary termination {node_id} marking budget is inverted")
            for chain_id in sorted(marking_chain_ids & set(marking_chains)):
                projections = [
                    dot((point[0] - endpoint[0], point[1] - endpoint[1]), outward)
                    for point in marking_chains[chain_id]["endpoints"]
                ]
                if any(value > node_tolerance for value in projections):
                    errors.append(
                        f"lane boundary termination {node_id} marking mesh {chain_id} continues through its cap"
                    )
                inside_distances = [-value for value in projections if value <= node_tolerance]
                measured_stop = min(inside_distances) if inside_distances else float("inf")
                if measured_stop < minimum_marking - 1e-9 or measured_stop > maximum_marking + 1e-9:
                    errors.append(
                        f"lane boundary termination {node_id} resolved marking mesh stop is outside its budget"
                    )
                termination_measurements.append(
                    {
                        "node_id": node_id,
                        "termination_kind": termination_kind,
                        "profile_kind": profile_kind,
                        "marking_chain_id": chain_id,
                        "measurement": "inward_stop",
                        "measured_distance": measured_stop,
                        "minimum_distance": minimum_marking,
                        "maximum_distance": maximum_marking,
                    }
                )
    if termination_records != termination_nodes:
        errors.append(
            "lane boundary termination manifest does not exactly cover boundary endpoints; "
            f"missing={','.join(sorted(termination_nodes - termination_records)) or 'none'} "
            f"extra={','.join(sorted(termination_records - termination_nodes)) or 'none'}"
        )
    if len(termination_records) != expected_lane_terminations:
        errors.append(
            f"lane boundary termination manifest has {len(termination_records)}; expected {expected_lane_terminations}"
        )

    support_contacts_seen: set[str] = set()
    support_contact_measurements: list[dict[str, Any]] = []
    support_mesh_coverage: set[str] = set()
    for index, raw in enumerate(array(model.get("support_contacts"), "support_contacts")):
        item = obj(raw, f"support_contacts[{index}]")
        contact_id = text(item.get("id"), f"support contact {index}.id")
        if contact_id in support_contacts_seen:
            raise ContractError(f"duplicate support contact {contact_id}")
        support_contacts_seen.add(contact_id)
        mesh_ids = strings(
            item.get("mesh_instance_ids"), f"support contact {contact_id}.mesh_instance_ids", nonempty=True
        )
        if mesh_ids & support_mesh_coverage:
            raise ContractError(f"support contact {contact_id} reuses an already measured support mesh")
        support_mesh_coverage |= mesh_ids
        if not mesh_ids <= support_mesh_ids:
            errors.append(f"support contact {contact_id} references non-support or missing meshes")
        mode = text(item.get("support_mode"), f"support contact {contact_id}.support_mode")
        if mode not in {"ground_supported", "facade_mounted", "suspended"}:
            raise ContractError(f"support contact {contact_id} has unknown support_mode")
        measurement_source_kind = text(
            item.get("measurement_source_kind"),
            f"support contact {contact_id}.measurement_source_kind",
        )
        expected_measurement_source = (
            "resolved_mesh_vertices_to_render_surface"
            if mode == "ground_supported"
            else "resolved_mesh_vertices_to_mount_mesh"
        )
        if measurement_source_kind != expected_measurement_source:
            errors.append(f"support contact {contact_id} lacks resolved vertex contact provenance")
        allowed_gap = number(
            item.get("maximum_gap"), f"support contact {contact_id}.maximum_gap", minimum=0.0
        )
        if allowed_gap > maximum_support_gap + 1e-12:
            errors.append(f"support contact {contact_id} weakens the project maximum gap")
        text(item.get("raw_artifact"), f"support contact {contact_id}.raw_artifact")
        if mode == "ground_supported":
            lowest_visible_y = number(
                item.get("lowest_visible_y"), f"support contact {contact_id}.lowest_visible_y"
            )
            samples = array(
                item.get("contact_samples"), f"support contact {contact_id}.contact_samples", nonempty=True
            )
            if len(samples) < minimum_support_samples:
                errors.append(f"support contact {contact_id} has too few resolved contact samples")
            support_values: list[float] = []
            resolved_gaps: list[float] = []
            for sample_index, raw_sample in enumerate(samples):
                sample = obj(raw_sample, f"support contact {contact_id}.contact_samples[{sample_index}]")
                support_y = number(sample.get("support_y"), f"support contact {contact_id} sample.support_y")
                ground_y = number(sample.get("ground_y"), f"support contact {contact_id} sample.ground_y")
                measured_gap = number(
                    sample.get("gap"), f"support contact {contact_id} sample.gap", minimum=0.0
                )
                support_values.append(support_y)
                resolved_gap = abs(support_y - ground_y)
                resolved_gaps.append(resolved_gap)
                if abs(resolved_gap - measured_gap) > 1e-6:
                    errors.append(f"support contact {contact_id} sample gap disagrees with resolved heights")
                if measured_gap > allowed_gap + 1e-12:
                    errors.append(f"support contact {contact_id} floats above its render support")
            if support_values and abs(min(support_values) - lowest_visible_y) > 1e-6:
                errors.append(f"support contact {contact_id} lowest visible Y is not measurement-derived")
            support_contact_measurements.append(
                {
                    "id": contact_id,
                    "support_mode": mode,
                    "sample_count": len(samples),
                    "maximum_measured_gap": max(resolved_gaps, default=0.0),
                }
            )
        else:
            mount_ids = strings(
                item.get("mount_mesh_instance_ids"),
                f"support contact {contact_id}.mount_mesh_instance_ids",
                nonempty=True,
            )
            if not mount_ids <= set(resolved_meshes):
                errors.append(f"support contact {contact_id} references missing mount meshes")
            measured_mount_gap = number(
                item.get("measured_mount_gap"),
                f"support contact {contact_id}.measured_mount_gap",
                minimum=0.0,
            )
            samples = array(
                item.get("contact_samples"),
                f"support contact {contact_id}.contact_samples",
                nonempty=True,
            )
            if len(samples) < minimum_support_samples:
                errors.append(f"support contact {contact_id} has too few mount-contact samples")
            resolved_gaps: list[float] = []
            for sample_index, raw_sample in enumerate(samples):
                sample = obj(
                    raw_sample,
                    f"support contact {contact_id}.contact_samples[{sample_index}]",
                )
                support_mesh_id = text(
                    sample.get("support_mesh_instance_id"),
                    f"support contact {contact_id} sample {sample_index}.support_mesh_instance_id",
                )
                mount_mesh_id = text(
                    sample.get("mount_mesh_instance_id"),
                    f"support contact {contact_id} sample {sample_index}.mount_mesh_instance_id",
                )
                if support_mesh_id not in mesh_ids:
                    errors.append(f"support contact {contact_id} sample uses an undeclared support mesh")
                if mount_mesh_id not in mount_ids:
                    errors.append(f"support contact {contact_id} sample uses an undeclared mount mesh")
                integer(
                    sample.get("support_vertex_index"),
                    f"support contact {contact_id} sample {sample_index}.support_vertex_index",
                )
                mount_surface_index = integer(
                    sample.get("mount_surface_index"),
                    f"support contact {contact_id} sample {sample_index}.mount_surface_index",
                )
                integer(
                    sample.get("mount_triangle_index"),
                    f"support contact {contact_id} sample {sample_index}.mount_triangle_index",
                )
                if (
                    mount_mesh_id in resolved_meshes
                    and mount_surface_index not in resolved_meshes[mount_mesh_id]["surfaces"]
                ):
                    errors.append(f"support contact {contact_id} sample references invalid mount surface")
                support_point = vec3(
                    sample.get("support_point"),
                    f"support contact {contact_id} sample {sample_index}.support_point",
                )
                mount_point = vec3(
                    sample.get("mount_point"),
                    f"support contact {contact_id} sample {sample_index}.mount_point",
                )
                declared_gap = number(
                    sample.get("gap"),
                    f"support contact {contact_id} sample {sample_index}.gap",
                    minimum=0.0,
                )
                resolved_gap = distance3(support_point, mount_point)
                resolved_gaps.append(resolved_gap)
                if abs(resolved_gap - declared_gap) > 1e-6:
                    errors.append(f"support contact {contact_id} mount gap is not vertex-derived")
                if resolved_gap > allowed_gap + 1e-12:
                    errors.append(f"support contact {contact_id} is detached from its authored mount")
            if resolved_gaps and abs(max(resolved_gaps) - measured_mount_gap) > 1e-6:
                errors.append(f"support contact {contact_id} measured mount gap is adapter-declared")
            if measured_mount_gap > allowed_gap + 1e-12:
                errors.append(f"support contact {contact_id} is detached from its authored mount")
            support_contact_measurements.append(
                {
                    "id": contact_id,
                    "support_mode": mode,
                    "sample_count": len(samples),
                    "maximum_measured_gap": max(resolved_gaps, default=0.0),
                    "declared_aggregate_gap": measured_mount_gap,
                }
            )
    if support_mesh_coverage != support_mesh_ids:
        errors.append(
            "support contact manifest does not exactly cover every visible canopy/awning/support mesh"
        )
    if len(support_contacts_seen) != expected_support_contacts:
        errors.append(
            f"support contact manifest has {len(support_contacts_seen)}; expected {expected_support_contacts}"
        )

    closures: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(array(model.get("incident_closures"), "incident_closures")):
        item = obj(raw, f"incident_closures[{index}]")
        closure_id = text(item.get("id"), f"incident_closures[{index}].id")
        if closure_id in closures:
            raise ContractError(f"duplicate incident closure {closure_id}")
        blocked_lanes = strings(item.get("blocked_lane_ids"), f"closure {closure_id}.blocked_lane_ids", nonempty=True)
        cue_objects = strings(item.get("visual_cue_object_ids"), f"closure {closure_id}.visual_cue_object_ids", nonempty=True)
        text(item.get("cause"), f"closure {closure_id}.cause")
        text(item.get("raw_artifact"), f"closure {closure_id}.raw_artifact")
        for lane_id in sorted(blocked_lanes):
            if lane_id not in lanes:
                errors.append(f"closure {closure_id} references unknown lane {lane_id}")
            elif lanes[lane_id].status != "closed":
                errors.append(f"closure {closure_id} blocks lane {lane_id} but graph still marks it open")
        unknown_cues = sorted(cue_objects - set(placed_objects))
        if unknown_cues:
            errors.append(f"closure {closure_id} uses unknown visual cue objects: {', '.join(unknown_cues)}")
        paths = array(item.get("alternate_lane_paths"), f"closure {closure_id}.alternate_lane_paths", nonempty=True)
        alternate_from = text(item.get("alternate_from_node"), f"closure {closure_id}.alternate_from_node")
        alternate_to = text(item.get("alternate_to_node"), f"closure {closure_id}.alternate_to_node")
        if alternate_from not in nodes or alternate_to not in nodes:
            errors.append(f"closure {closure_id} alternate route endpoints are missing from the road graph")
        valid_path = False
        for path_index, raw_path in enumerate(paths):
            path = [text(value, f"closure {closure_id}.alternate_lane_paths[{path_index}]") for value in array(raw_path, f"closure {closure_id}.alternate_lane_paths[{path_index}]", nonempty=True)]
            if any(lane_id not in lanes or lanes[lane_id].status != "open" for lane_id in path):
                continue
            contiguous = (
                lanes[path[0]].start_node == alternate_from
                and lanes[path[-1]].end_node == alternate_to
                and all(lanes[first].end_node == lanes[second].start_node for first, second in zip(path, path[1:]))
            )
            valid_path = valid_path or contiguous
        if not valid_path:
            errors.append(f"closure {closure_id} lacks a contiguous open alternate lane path")
        closures[closure_id] = {"blocked_lanes": blocked_lanes, "cue_objects": cue_objects}
    for item in placed_objects.values():
        if item.closure_id is not None:
            closure = closures.get(item.closure_id)
            if closure is None:
                errors.append(f"placed object {item.object_id} references missing closure {item.closure_id}")
            elif item.object_id not in closure["cue_objects"]:
                errors.append(f"placed object {item.object_id} is not a declared visual cue for closure {item.closure_id}")

    resolved_building_source_roles: dict[str, dict[str, dict[str, Any]]] = {}
    for index, raw in enumerate(
        array(
            model.get("resolved_building_source_role_manifest"),
            "resolved_building_source_role_manifest",
            nonempty=True,
        )
    ):
        item = obj(raw, f"resolved_building_source_role_manifest[{index}]")
        building_id = text(
            item.get("object_id"),
            f"resolved building source-role manifest {index}.object_id",
        )
        if building_id in resolved_building_source_roles:
            raise ContractError(f"duplicate resolved building source-role manifest {building_id}")
        if text(
            item.get("source_kind"),
            f"resolved building source-role manifest {building_id}.source_kind",
        ) != "resolved_scene_building_source_roles":
            errors.append(f"resolved building source-role manifest {building_id} is adapter-declared")
        roles: dict[str, dict[str, Any]] = {}
        for role_index, raw_role in enumerate(
            array(
                item.get("roles"),
                f"resolved building source-role manifest {building_id}.roles",
                nonempty=True,
            )
        ):
            role_item = obj(
                raw_role,
                f"resolved building source-role manifest {building_id}.roles[{role_index}]",
            )
            role = text(
                role_item.get("role"),
                f"resolved building source-role manifest {building_id} role {role_index}.role",
            )
            if role in roles:
                raise ContractError(f"duplicate resolved source role {building_id}/{role}")
            source_kind = text(
                role_item.get("source_kind"),
                f"resolved building source-role manifest {building_id}/{role}.source_kind",
            )
            if source_kind not in {"authored_mesh_surface", "source_texture_uv_mask"}:
                errors.append(f"resolved building source role {building_id}/{role} has synthetic provenance")
            mesh_surface_keys = strings(
                role_item.get("mesh_surface_keys"),
                f"resolved building source-role manifest {building_id}/{role}.mesh_surface_keys",
                nonempty=True,
            )
            for mesh_surface_key in sorted(mesh_surface_keys):
                mesh_id, separator, raw_surface_index = mesh_surface_key.rpartition("#")
                if not separator or not raw_surface_index.isdigit():
                    raise ContractError(
                        f"resolved building source role {building_id}/{role} has invalid mesh surface key"
                    )
                surface_index = int(raw_surface_index)
                classification = classifications.get(mesh_id)
                if (
                    mesh_id not in resolved_meshes
                    or surface_index not in resolved_meshes[mesh_id]["surfaces"]
                    or classification is None
                    or classification["scope"] != "building"
                    or classification["object_id"] != building_id
                ):
                    errors.append(
                        f"resolved building source role {building_id}/{role} references an unrelated surface"
                    )
            source_texture_id = ""
            source_uv_mask_id = ""
            uv_channel = -1
            if source_kind == "source_texture_uv_mask":
                source_texture_id = text(
                    role_item.get("source_texture_id"),
                    f"resolved building source-role manifest {building_id}/{role}.source_texture_id",
                )
                source_uv_mask_id = text(
                    role_item.get("source_uv_mask_id"),
                    f"resolved building source-role manifest {building_id}/{role}.source_uv_mask_id",
                )
                uv_channel = integer(
                    role_item.get("uv_channel"),
                    f"resolved building source-role manifest {building_id}/{role}.uv_channel",
                )
            roles[role] = {
                "source_kind": source_kind,
                "mesh_surface_keys": mesh_surface_keys,
                "source_texture_id": source_texture_id,
                "source_uv_mask_id": source_uv_mask_id,
                "uv_channel": uv_channel,
            }
        resolved_building_source_roles[building_id] = roles

    style_profiles: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(array(model.get("building_style_profiles"), "building_style_profiles", nonempty=True)):
        item = obj(raw, f"building_style_profiles[{index}]")
        profile_id = text(item.get("id"), f"building_style_profiles[{index}].id")
        if profile_id in style_profiles:
            raise ContractError(f"duplicate building style profile {profile_id}")
        required_roles = strings(
            item.get("required_visible_roles"),
            f"building style {profile_id}.required_visible_roles",
            nonempty=True,
        )
        role_envelopes: dict[str, dict[str, float | int]] = {}
        for envelope_index, raw_envelope in enumerate(
            array(item.get("rendered_role_envelopes"), f"building style {profile_id}.rendered_role_envelopes", nonempty=True)
        ):
            envelope = obj(raw_envelope, f"building style {profile_id}.rendered_role_envelopes[{envelope_index}]")
            role = text(envelope.get("role"), f"building style {profile_id} rendered envelope role")
            if role in role_envelopes:
                raise ContractError(f"duplicate rendered role envelope {profile_id}/{role}")
            role_envelopes[role] = {
                "minimum_visible_pixels": integer(
                    envelope.get("minimum_visible_pixels"),
                    f"building style {profile_id}/{role}.minimum_visible_pixels",
                    1,
                ),
                "minimum_mean_value": ratio(
                    envelope.get("minimum_mean_value"),
                    f"building style {profile_id}/{role}.minimum_mean_value",
                ),
                "maximum_mean_value": ratio(
                    envelope.get("maximum_mean_value"),
                    f"building style {profile_id}/{role}.maximum_mean_value",
                ),
                "minimum_mean_chroma": ratio(
                    envelope.get("minimum_mean_chroma"),
                    f"building style {profile_id}/{role}.minimum_mean_chroma",
                ),
                "maximum_mean_chroma": ratio(
                    envelope.get("maximum_mean_chroma"),
                    f"building style {profile_id}/{role}.maximum_mean_chroma",
                ),
                "minimum_value_stddev": ratio(
                    envelope.get("minimum_value_stddev"),
                    f"building style {profile_id}/{role}.minimum_value_stddev",
                ),
                "minimum_chroma_stddev": ratio(
                    envelope.get("minimum_chroma_stddev"),
                    f"building style {profile_id}/{role}.minimum_chroma_stddev",
                ),
                "maximum_dominant_color_ratio": ratio(
                    envelope.get("maximum_dominant_color_ratio"),
                    f"building style {profile_id}/{role}.maximum_dominant_color_ratio",
                ),
                "dominant_color_bin_size": integer(
                    envelope.get("dominant_color_bin_size"),
                    f"building style {profile_id}/{role}.dominant_color_bin_size",
                    1,
                ),
            }
            if role_envelopes[role]["dominant_color_bin_size"] > 255:
                raise ContractError(
                    f"building style {profile_id}/{role} dominant_color_bin_size exceeds 255"
                )
            if role_envelopes[role]["maximum_mean_value"] < role_envelopes[role]["minimum_mean_value"]:
                raise ContractError(f"building style {profile_id}/{role} value envelope is inverted")
            if role_envelopes[role]["maximum_mean_chroma"] < role_envelopes[role]["minimum_mean_chroma"]:
                raise ContractError(f"building style {profile_id}/{role} chroma envelope is inverted")
        if set(role_envelopes) != required_roles:
            raise ContractError(
                f"building style {profile_id} rendered envelopes must exactly cover required roles"
            )
        separations: list[tuple[str, str, float]] = []
        separated_roles: set[str] = set()
        for separation_index, raw_separation in enumerate(
            array(item.get("rendered_role_separation"), f"building style {profile_id}.rendered_role_separation", nonempty=True)
        ):
            separation = obj(raw_separation, f"building style {profile_id}.rendered_role_separation[{separation_index}]")
            first_role = text(separation.get("first_role"), f"building style {profile_id} separation first_role")
            second_role = text(separation.get("second_role"), f"building style {profile_id} separation second_role")
            if first_role == second_role or first_role not in required_roles or second_role not in required_roles:
                raise ContractError(f"building style {profile_id} separation references invalid roles")
            minimum_delta = number(
                separation.get("minimum_delta_e"),
                f"building style {profile_id} {first_role}/{second_role}.minimum_delta_e",
                minimum=1e-6,
            )
            separations.append((first_role, second_role, minimum_delta))
            separated_roles |= {first_role, second_role}
        if separated_roles != required_roles:
            raise ContractError(
                f"building style {profile_id} must place every required role in a perceptual separation pair"
            )
        for detail_role in {"openings", "trim"} & required_roles:
            if not any(
                {first_role, second_role} == {"facade", detail_role}
                for first_role, second_role, _minimum_delta in separations
            ):
                raise ContractError(
                    f"building style {profile_id} must directly separate facade from {detail_role}"
                )
        building_color_bin_size = integer(
            item.get("building_color_bin_size"),
            f"building style {profile_id}.building_color_bin_size",
            1,
        )
        if building_color_bin_size > 255:
            raise ContractError(f"building style {profile_id} building_color_bin_size exceeds 255")
        style_profiles[profile_id] = {
            "required_roles": required_roles,
            "forbidden_materials": strings(item.get("forbidden_material_ids"), f"building style {profile_id}.forbidden_material_ids", nonempty=True),
            "allowed_zones": strings(item.get("allowed_zone_ids"), f"building style {profile_id}.allowed_zone_ids", nonempty=True),
            "allowed_story_states": strings(item.get("allowed_story_states"), f"building style {profile_id}.allowed_story_states", nonempty=True),
            "minimum_coverage": ratio(item.get("minimum_materialized_visible_area_ratio"), f"building style {profile_id}.minimum_materialized_visible_area_ratio"),
            "allow_node_material_override": boolean(
                item.get("allow_node_material_override"),
                f"building style {profile_id}.allow_node_material_override",
            ),
            "role_envelopes": role_envelopes,
            "separations": separations,
            "minimum_building_value_stddev": ratio(
                item.get("minimum_building_value_stddev"),
                f"building style {profile_id}.minimum_building_value_stddev",
            ),
            "maximum_building_dominant_color_ratio": ratio(
                item.get("maximum_building_dominant_color_ratio"),
                f"building style {profile_id}.maximum_building_dominant_color_ratio",
            ),
            "building_color_bin_size": building_color_bin_size,
        }

    buildings_seen: set[str] = set()
    building_profiles: dict[str, str] = {}
    building_source_roles: dict[str, dict[str, dict[str, Any]]] = {}
    building_role_surface_keys: dict[tuple[str, str], set[str]] = {}
    for index, raw in enumerate(array(model.get("visible_buildings"), "visible_buildings", nonempty=True)):
        item = obj(raw, f"visible_buildings[{index}]")
        building_id = text(item.get("object_id"), f"visible_buildings[{index}].object_id")
        if building_id in buildings_seen:
            raise ContractError(f"duplicate visible building {building_id}")
        buildings_seen.add(building_id)
        placed = placed_objects.get(building_id)
        if placed is None:
            errors.append(f"visible building {building_id} has no full-footprint placed-object record")
        profile_id = text(item.get("style_profile_id"), f"visible building {building_id}.style_profile_id")
        profile = style_profiles.get(profile_id)
        if profile is None:
            raise ContractError(f"visible building {building_id} uses unknown style profile {profile_id}")
        building_profiles[building_id] = profile_id
        zone_id = text(item.get("zone_id"), f"visible building {building_id}.zone_id")
        story_state = text(item.get("story_state"), f"visible building {building_id}.story_state")
        text(item.get("function"), f"visible building {building_id}.function")
        if zone_id not in profile["allowed_zones"]:
            errors.append(f"visible building {building_id} style profile is invalid for zone {zone_id}")
        if story_state not in profile["allowed_story_states"]:
            errors.append(f"visible building {building_id} story state {story_state} is outside its style profile")
        total_area = number(item.get("visible_surface_area"), f"visible building {building_id}.visible_surface_area", minimum=1e-9)
        building_mesh_ids = {
            mesh_id
            for mesh_id, classification in classifications.items()
            if classification["scope"] == "building" and classification["object_id"] == building_id
        }
        if not building_mesh_ids:
            errors.append(f"visible building {building_id} has no resolved building mesh classification")
        source_role_inventory: dict[str, dict[str, Any]] = {}
        for source_role_index, raw_source_role in enumerate(
            array(
                item.get("source_role_inventory"),
                f"visible building {building_id}.source_role_inventory",
                nonempty=True,
            )
        ):
            source_role = obj(
                raw_source_role,
                f"visible building {building_id}.source_role_inventory[{source_role_index}]",
            )
            source_role_name = text(
                source_role.get("role"),
                f"visible building {building_id} source role {source_role_index}.role",
            )
            if source_role_name in source_role_inventory:
                raise ContractError(f"visible building {building_id} duplicates source role {source_role_name}")
            source_kind = text(
                source_role.get("source_kind"),
                f"visible building {building_id}/{source_role_name}.source_kind",
            )
            if source_kind not in {"authored_mesh_surface", "source_texture_uv_mask"}:
                errors.append(f"visible building {building_id}/{source_role_name} has synthetic source-role provenance")
            mesh_surface_keys = strings(
                source_role.get("mesh_surface_keys"),
                f"visible building {building_id}/{source_role_name}.mesh_surface_keys",
                nonempty=True,
            )
            for mesh_surface_key in sorted(mesh_surface_keys):
                mesh_id, separator, raw_surface_index = mesh_surface_key.rpartition("#")
                if not separator or not raw_surface_index.isdigit():
                    raise ContractError(
                        f"visible building {building_id}/{source_role_name} has invalid mesh surface key"
                    )
                surface_index = int(raw_surface_index)
                if mesh_id not in building_mesh_ids or surface_index not in resolved_meshes[mesh_id]["surfaces"]:
                    errors.append(
                        f"visible building {building_id}/{source_role_name} source role references an unrelated surface"
                    )
            source_texture_id = ""
            source_uv_mask_id = ""
            uv_channel = -1
            if source_kind == "source_texture_uv_mask":
                source_texture_id = text(
                    source_role.get("source_texture_id"),
                    f"visible building {building_id}/{source_role_name}.source_texture_id",
                )
                source_uv_mask_id = text(
                    source_role.get("source_uv_mask_id"),
                    f"visible building {building_id}/{source_role_name}.source_uv_mask_id",
                )
                uv_channel = integer(
                    source_role.get("uv_channel"),
                    f"visible building {building_id}/{source_role_name}.uv_channel",
                )
            source_role_inventory[source_role_name] = {
                "source_kind": source_kind,
                "mesh_surface_keys": mesh_surface_keys,
                "source_texture_id": source_texture_id,
                "source_uv_mask_id": source_uv_mask_id,
                "uv_channel": uv_channel,
            }
        for detail_role in {"openings", "trim"} & set(source_role_inventory):
            source_entry = source_role_inventory[detail_role]
            if source_entry["source_kind"] == "source_texture_uv_mask":
                continue
            if any(
                source_entry["mesh_surface_keys"] & other_entry["mesh_surface_keys"]
                for other_role, other_entry in source_role_inventory.items()
                if other_role != detail_role
            ):
                errors.append(
                    f"visible building {building_id}/{detail_role} is not tied to source texture/UV or a dedicated surface"
                )
        if not {"facade", "roof"} <= set(source_role_inventory):
            errors.append(f"visible building {building_id} source-role inventory lacks facade or roof")
        if set(source_role_inventory) != profile["required_roles"]:
            errors.append(
                f"visible building {building_id} required roles do not exactly match source mesh/atlas roles"
            )
        resolved_source_role_inventory = resolved_building_source_roles.get(building_id)
        if resolved_source_role_inventory is None:
            errors.append(f"visible building {building_id} lacks exporter-owned source-role evidence")
        elif source_role_inventory != resolved_source_role_inventory:
            errors.append(
                f"visible building {building_id} source-role inventory disagrees with exporter-owned scene metadata"
            )
        building_source_roles[building_id] = source_role_inventory
        listed_area = 0.0
        materialized_area = 0.0
        roles: set[str] = set()
        slots = array(item.get("visible_surface_slots"), f"visible building {building_id}.visible_surface_slots", nonempty=True)
        slot_ids: set[str] = set()
        claimed_surface_keys: dict[tuple[str, int], list[dict[str, Any]]] = {}
        for slot_index, raw_slot in enumerate(slots):
            slot = obj(raw_slot, f"visible building {building_id}.visible_surface_slots[{slot_index}]")
            slot_id = text(slot.get("id"), f"visible building {building_id} slot {slot_index}.id")
            if slot_id in slot_ids:
                raise ContractError(f"duplicate visible surface slot {building_id}/{slot_id}")
            slot_ids.add(slot_id)
            role = text(slot.get("role"), f"visible building {building_id} slot {slot_id}.role")
            material_id = text(slot.get("material_id"), f"visible building {building_id} slot {slot_id}.material_id")
            mesh_instance_id = text(
                slot.get("mesh_instance_id"),
                f"visible building {building_id} slot {slot_id}.mesh_instance_id",
            )
            surface_index = integer(
                slot.get("surface_index"),
                f"visible building {building_id} slot {slot_id}.surface_index",
            )
            resolved_mesh = resolved_meshes.get(mesh_instance_id)
            if mesh_instance_id not in building_mesh_ids or resolved_mesh is None:
                errors.append(
                    f"visible building {building_id} slot {slot_id} does not reference its resolved mesh"
                )
                resolved_surface = None
            else:
                resolved_surface = resolved_mesh["surfaces"].get(surface_index)
                if resolved_surface is None:
                    errors.append(
                        f"visible building {building_id} slot {slot_id} references invalid surface index"
                    )
            material_source_kind = text(
                slot.get("material_source_kind"),
                f"visible building {building_id} slot {slot_id}.material_source_kind",
            )
            role_source_kind = text(
                slot.get("role_source_kind"),
                f"visible building {building_id} slot {slot_id}.role_source_kind",
            )
            role_source_id = text(
                slot.get("role_source_id"),
                f"visible building {building_id} slot {slot_id}.role_source_id",
            )
            area_source_kind = text(
                slot.get("area_source_kind"),
                f"visible building {building_id} slot {slot_id}.area_source_kind",
            )
            if role_source_kind not in {"authored_mesh_surface", "authored_surface_profile", "shader_mask"}:
                errors.append(f"visible building {building_id} slot {slot_id} lacks authored role provenance")
            if area_source_kind not in {"resolved_mesh_triangles", "resolved_shader_mask_pixels"}:
                errors.append(f"visible building {building_id} slot {slot_id} has synthetic visible-area provenance")
            subregion_id_value = slot.get("subregion_id")
            subregion_id = (
                text(subregion_id_value, f"visible building {building_id} slot {slot_id}.subregion_id")
                if subregion_id_value is not None
                else ""
            )
            if subregion_id:
                if role_source_kind != "shader_mask" or area_source_kind != "resolved_shader_mask_pixels":
                    errors.append(
                        f"visible building {building_id} slot {slot_id} splits a surface without shader-mask provenance"
                    )
                text(
                    slot.get("shader_mask_id"),
                    f"visible building {building_id} slot {slot_id}.shader_mask_id",
                )
                shader_mask_source_kind = text(
                    slot.get("shader_mask_source_kind"),
                    f"visible building {building_id} slot {slot_id}.shader_mask_source_kind",
                )
                if shader_mask_source_kind not in {"source_texture_uv_mask", "resolved_geometry_mask"}:
                    errors.append(
                        f"visible building {building_id} slot {slot_id} has synthetic shader subregion provenance"
                    )
                if role in {"openings", "trim"} and shader_mask_source_kind != "source_texture_uv_mask":
                    errors.append(
                        f"visible building {building_id} slot {slot_id} does not bind {role} to source texture/UV"
                    )
                if shader_mask_source_kind == "source_texture_uv_mask":
                    source_texture_id = text(
                        slot.get("source_texture_id"),
                        f"visible building {building_id} slot {slot_id}.source_texture_id",
                    )
                    source_uv_mask_id = text(
                        slot.get("source_uv_mask_id"),
                        f"visible building {building_id} slot {slot_id}.source_uv_mask_id",
                    )
                    uv_channel = integer(
                        slot.get("uv_channel"),
                        f"visible building {building_id} slot {slot_id}.uv_channel",
                    )
                    source_inventory = source_role_inventory.get(role)
                    if source_inventory is None or (
                        source_inventory["source_kind"] != "source_texture_uv_mask"
                        or source_inventory["source_texture_id"] != source_texture_id
                        or source_inventory["source_uv_mask_id"] != source_uv_mask_id
                        or source_inventory["uv_channel"] != uv_channel
                    ):
                        errors.append(
                            f"visible building {building_id} slot {slot_id} shader mask disagrees with source-role inventory"
                        )
            surface_key = (mesh_instance_id, surface_index)
            claimed_surface_keys.setdefault(surface_key, []).append(
                {"slot_id": slot_id, "subregion_id": subregion_id, "role_source_kind": role_source_kind}
            )
            if resolved_surface is not None:
                if material_id != resolved_surface["material_id"]:
                    errors.append(
                        f"visible building {building_id} slot {slot_id} material disagrees with resolved surface"
                    )
                if material_source_kind != resolved_surface["material_source_kind"]:
                    errors.append(
                        f"visible building {building_id} slot {slot_id} material source disagrees with resolved surface"
                    )
            if material_source_kind == "node_material_override" and not profile["allow_node_material_override"]:
                errors.append(
                    f"visible building {building_id} slot {slot_id} collapses roles through a node-wide material override"
                )
            area = number(slot.get("visible_area"), f"visible building {building_id} slot {slot_id}.visible_area", minimum=0.0)
            listed_area += area
            roles.add(role)
            if material_id not in profile["forbidden_materials"]:
                materialized_area += area
            rendered_surface_key = f"{mesh_instance_id}#{surface_index}#{subregion_id or 'surface'}"
            building_role_surface_keys.setdefault((building_id, role), set()).add(rendered_surface_key)
            if not role_source_id:
                raise ContractError(f"visible building {building_id} slot {slot_id} has empty role provenance")
        for surface_key, claims in claimed_surface_keys.items():
            if len(claims) > 1:
                if any(not claim["subregion_id"] or claim["role_source_kind"] != "shader_mask" for claim in claims):
                    errors.append(
                        f"visible building {building_id} fabricates multiple semantic slots from surface "
                        f"{surface_key[0]}/{surface_key[1]} without resolved shader masks"
                    )
                subregions = [claim["subregion_id"] for claim in claims]
                named_subregions = [value for value in subregions if value]
                if len(set(named_subregions)) != len(named_subregions):
                    raise ContractError(
                        f"visible building {building_id} duplicates a shader subregion on one mesh surface"
                    )
        expected_surface_keys = {
            (mesh_id, surface_index)
            for mesh_id in building_mesh_ids
            for surface_index in resolved_meshes[mesh_id]["surfaces"]
        }
        if set(claimed_surface_keys) != expected_surface_keys:
            errors.append(
                f"visible building {building_id} slots do not exactly cover resolved mesh surface indices"
            )
        if abs(listed_area - total_area) > max(1e-6, total_area * 0.001):
            errors.append(f"visible building {building_id} surface slots do not account for total visible area")
        coverage = materialized_area / total_area
        if coverage + 1e-12 < profile["minimum_coverage"]:
            errors.append(f"visible building {building_id} materialized visible-area ratio {coverage:.4f} is below profile minimum")
        missing_roles = sorted(profile["required_roles"] - roles)
        if missing_roles:
            errors.append(f"visible building {building_id} lacks required visible roles: {', '.join(missing_roles)}")
    if len(buildings_seen) != expected_buildings:
        errors.append(f"visible building manifest has {len(buildings_seen)}; expected {expected_buildings}")
    if set(resolved_building_source_roles) != buildings_seen:
        errors.append(
            "exporter-owned building source-role manifest does not exactly cover visible buildings; "
            f"missing={','.join(sorted(buildings_seen - set(resolved_building_source_roles))) or 'none'} "
            f"extra={','.join(sorted(set(resolved_building_source_roles) - buildings_seen)) or 'none'}"
        )
    if road_detail_count != expected_road_details:
        errors.append(f"road-detail manifest has {road_detail_count}; expected {expected_road_details}")

    rendered = obj(model.get("rendered_material_evidence"), "rendered_material_evidence")
    if text(rendered.get("source_kind"), "rendered_material_evidence.source_kind") != "target_build_shipping_camera_masked_pixels":
        raise ContractError(
            "rendered_material_evidence.source_kind must be target_build_shipping_camera_masked_pixels"
        )
    required_rendered_buildings = strings(
        rendered.get("required_building_ids"),
        "rendered_material_evidence.required_building_ids",
        nonempty=True,
    )
    if required_rendered_buildings != buildings_seen:
        errors.append("rendered material evidence does not exactly cover every visible building")
    role_stats: dict[tuple[str, str], dict[str, Any]] = {}
    building_pixel_stats: dict[str, dict[str, Any]] = {}
    rendered_role_metrics: list[dict[str, Any]] = []
    rendered_role_separation_metrics: list[dict[str, Any]] = []
    rendered_building_metrics: list[dict[str, Any]] = []
    masked_surface_keys: dict[tuple[str, str], set[str]] = {}
    capture_count = 0
    mask_count = 0
    for capture_index, raw_capture in enumerate(
        array(rendered.get("captures"), "rendered_material_evidence.captures", nonempty=True)
    ):
        capture = obj(raw_capture, f"rendered_material_evidence.captures[{capture_index}]")
        capture_id = text(capture.get("id"), f"rendered material capture {capture_index}.id")
        capture_count += 1
        if text(capture.get("source_kind"), f"rendered material capture {capture_id}.source_kind") != "target_build_shipping_camera":
            errors.append(f"rendered material capture {capture_id} is not target-build shipping-camera evidence")
        if text(capture.get("build_id"), f"rendered material capture {capture_id}.build_id") != build_id:
            errors.append(f"rendered material capture {capture_id} does not match candidate build")
        text(capture.get("camera_node"), f"rendered material capture {capture_id}.camera_node")
        raw_path = resolve_artifact(
            capture.get("raw_artifact"),
            f"rendered material capture {capture_id}.raw_artifact",
            model_directory,
        )
        verify_artifact_hash(
            raw_path,
            capture.get("raw_sha256"),
            f"rendered material capture {capture_id}.raw_sha256",
        )
        try:
            image = Image.open(raw_path).convert("RGB")
        except OSError as exc:
            raise ContractError(f"could not open rendered material capture {capture_id}: {exc}") from exc
        occupied_pixels: dict[str, set[int]] = {}
        for mask_index, raw_mask in enumerate(
            array(capture.get("role_masks"), f"rendered material capture {capture_id}.role_masks", nonempty=True)
        ):
            mask = obj(raw_mask, f"rendered material capture {capture_id}.role_masks[{mask_index}]")
            mask_id = text(mask.get("id"), f"rendered material mask {capture_id}/{mask_index}.id")
            building_id = text(mask.get("building_id"), f"rendered material mask {mask_id}.building_id")
            role = text(mask.get("role"), f"rendered material mask {mask_id}.role")
            if building_id not in buildings_seen:
                errors.append(f"rendered material mask {mask_id} references unknown building {building_id}")
            elif role not in style_profiles[building_profiles[building_id]]["required_roles"]:
                errors.append(f"rendered material mask {mask_id} references undeclared role {role}")
            mask_source_kind = text(
                mask.get("source_kind"), f"rendered material mask {mask_id}.source_kind"
            )
            if mask_source_kind not in {
                "resolved_surface_id_render_pass",
                "source_texture_uv_role_render_pass",
            }:
                errors.append(f"rendered material mask {mask_id} lacks resolved role-render provenance")
            source_role = building_source_roles.get(building_id, {}).get(role)
            if (
                role in {"openings", "trim"}
                and source_role is not None
                and source_role["source_kind"] == "source_texture_uv_mask"
                and mask_source_kind != "source_texture_uv_role_render_pass"
            ):
                errors.append(
                    f"rendered material mask {mask_id} does not prove source texture/UV ownership for {role}"
                )
            surface_keys = strings(
                mask.get("surface_keys"), f"rendered material mask {mask_id}.surface_keys", nonempty=True
            )
            expected_keys = building_role_surface_keys.get((building_id, role), set())
            if not surface_keys <= expected_keys:
                errors.append(f"rendered material mask {mask_id} claims unrelated mesh surfaces")
            masked_surface_keys.setdefault((building_id, role), set()).update(surface_keys)
            mask_path = resolve_artifact(
                mask.get("mask_artifact"),
                f"rendered material mask {mask_id}.mask_artifact",
                model_directory,
            )
            verify_artifact_hash(
                mask_path,
                mask.get("mask_sha256"),
                f"rendered material mask {mask_id}.mask_sha256",
            )
            try:
                mask_image = Image.open(mask_path).convert("L")
            except OSError as exc:
                raise ContractError(f"could not open rendered material mask {mask_id}: {exc}") from exc
            if mask_image.size != image.size:
                raise ContractError(f"rendered material mask {mask_id} size does not match its raw capture")
            selected_indices = {
                pixel_index
                for pixel_index, selected in enumerate(flattened_pixels(mask_image))
                if selected > 127
            }
            if not selected_indices:
                raise ContractError(f"rendered material mask {mask_id} selects no visible pixels")
            prior = occupied_pixels.setdefault(building_id, set())
            if prior & selected_indices:
                errors.append(f"rendered material mask {mask_id} overlaps another role mask for {building_id}")
            prior |= selected_indices
            pixels = flattened_pixels(image)
            stats = role_stats.setdefault(
                (building_id, role),
                {
                    "count": 0,
                    "value": 0.0,
                    "value_squared": 0.0,
                    "chroma": 0.0,
                    "chroma_squared": 0.0,
                    "lab": [0.0, 0.0, 0.0],
                    "color_bins": {},
                },
            )
            building_stats = building_pixel_stats.setdefault(
                building_id,
                {"count": 0, "value": 0.0, "value_squared": 0.0, "color_bins": {}},
            )
            role_bin_size = int(style_profiles[building_profiles[building_id]]["role_envelopes"][role]["dominant_color_bin_size"])
            building_bin_size = int(style_profiles[building_profiles[building_id]]["building_color_bin_size"])
            for pixel_index in selected_indices:
                pixel = pixels[pixel_index]
                value = max(pixel) / 255.0
                chroma = (max(pixel) - min(pixel)) / 255.0
                stats["count"] += 1
                stats["value"] += value
                stats["value_squared"] += value * value
                stats["chroma"] += chroma
                stats["chroma_squared"] += chroma * chroma
                role_bin = tuple(channel // role_bin_size for channel in pixel)
                stats["color_bins"][role_bin] = stats["color_bins"].get(role_bin, 0) + 1
                lab = rgb_to_lab(pixel)
                for component in range(3):
                    stats["lab"][component] += lab[component]
                building_stats["count"] += 1
                building_stats["value"] += value
                building_stats["value_squared"] += value * value
                building_bin = tuple(channel // building_bin_size for channel in pixel)
                building_stats["color_bins"][building_bin] = (
                    building_stats["color_bins"].get(building_bin, 0) + 1
                )
            mask_count += 1
    for building_id in buildings_seen:
        profile = style_profiles[building_profiles[building_id]]
        for role in profile["required_roles"]:
            key = (building_id, role)
            stats = role_stats.get(key)
            if stats is None:
                errors.append(f"visible building {building_id} lacks rendered pixel evidence for {role}")
                continue
            expected_keys = building_role_surface_keys.get(key, set())
            if masked_surface_keys.get(key, set()) != expected_keys:
                errors.append(
                    f"visible building {building_id}/{role} rendered masks do not cover every resolved role surface"
                )
            envelope = profile["role_envelopes"][role]
            count = stats["count"]
            mean_value = stats["value"] / count
            mean_chroma = stats["chroma"] / count
            value_stddev = standard_deviation(stats["value"], stats["value_squared"], count)
            chroma_stddev = standard_deviation(stats["chroma"], stats["chroma_squared"], count)
            dominant_color_ratio = max(stats["color_bins"].values()) / count
            stats["mean_lab"] = tuple(component / count for component in stats["lab"])
            rendered_role_metrics.append(
                {
                    "building_id": building_id,
                    "role": role,
                    "visible_pixels": count,
                    "mean_value": mean_value,
                    "mean_chroma": mean_chroma,
                    "value_stddev": value_stddev,
                    "chroma_stddev": chroma_stddev,
                    "dominant_color_ratio": dominant_color_ratio,
                }
            )
            if count < envelope["minimum_visible_pixels"]:
                errors.append(f"visible building {building_id}/{role} has too few rendered pixels")
            if not envelope["minimum_mean_value"] <= mean_value <= envelope["maximum_mean_value"]:
                errors.append(
                    f"visible building {building_id}/{role} rendered mean value {mean_value:.4f} is outside its profile envelope"
                )
            if not envelope["minimum_mean_chroma"] <= mean_chroma <= envelope["maximum_mean_chroma"]:
                errors.append(
                    f"visible building {building_id}/{role} rendered mean chroma {mean_chroma:.4f} is outside its profile envelope"
                )
            if value_stddev + 1e-12 < envelope["minimum_value_stddev"]:
                errors.append(
                    f"visible building {building_id}/{role} value variation is below its flood-fill threshold"
                )
            if chroma_stddev + 1e-12 < envelope["minimum_chroma_stddev"]:
                errors.append(
                    f"visible building {building_id}/{role} chroma variation is below its flood-fill threshold"
                )
            if dominant_color_ratio > envelope["maximum_dominant_color_ratio"] + 1e-12:
                errors.append(
                    f"visible building {building_id}/{role} dominant-color ratio {dominant_color_ratio:.4f} "
                    "looks like a flat flood fill"
                )
        for first_role, second_role, minimum_delta in profile["separations"]:
            first = role_stats.get((building_id, first_role))
            second = role_stats.get((building_id, second_role))
            if first is None or second is None or "mean_lab" not in first or "mean_lab" not in second:
                continue
            measured_delta = delta_e(first["mean_lab"], second["mean_lab"])
            rendered_role_separation_metrics.append(
                {
                    "building_id": building_id,
                    "first_role": first_role,
                    "second_role": second_role,
                    "measured_delta_e": measured_delta,
                    "minimum_delta_e": minimum_delta,
                }
            )
            if measured_delta + 1e-12 < minimum_delta:
                errors.append(
                    f"visible building {building_id} rendered {first_role}/{second_role} separation "
                    f"DeltaE {measured_delta:.3f} is below {minimum_delta:.3f}"
                )
        building_stats = building_pixel_stats.get(building_id)
        if building_stats is None or building_stats["count"] <= 0:
            errors.append(f"visible building {building_id} lacks a complete rendered building mask")
        else:
            building_value_stddev = standard_deviation(
                building_stats["value"],
                building_stats["value_squared"],
                building_stats["count"],
            )
            building_dominant_ratio = (
                max(building_stats["color_bins"].values()) / building_stats["count"]
            )
            rendered_building_metrics.append(
                {
                    "building_id": building_id,
                    "visible_pixels": building_stats["count"],
                    "value_stddev": building_value_stddev,
                    "dominant_color_ratio": building_dominant_ratio,
                }
            )
            if building_value_stddev + 1e-12 < profile["minimum_building_value_stddev"]:
                errors.append(
                    f"visible building {building_id} whole-mask value variation is below its flood-fill threshold"
                )
            if building_dominant_ratio > profile["maximum_building_dominant_color_ratio"] + 1e-12:
                errors.append(
                    f"visible building {building_id} whole-mask dominant-color ratio "
                    f"{building_dominant_ratio:.4f} looks monochrome"
                )

    raster = obj(model.get("boundary_reachability"), "boundary_reachability")
    width = integer(raster.get("width"), "boundary_reachability.width", 2)
    height = integer(raster.get("height"), "boundary_reachability.height", 2)
    number(raster.get("cell_size"), "boundary_reachability.cell_size", minimum=1e-6)
    vec2(raster.get("origin"), "boundary_reachability.origin")
    starts = unique_cells(raster.get("player_start_cells"), "boundary_reachability.player_start_cells", width, height, nonempty=True)
    outside = unique_cells(raster.get("outside_cells"), "boundary_reachability.outside_cells", width, height)
    nonwalkable = unique_cells(raster.get("nonwalkable_cells"), "boundary_reachability.nonwalkable_cells", width, height)
    visible_blockers = unique_cells(raster.get("visible_blocker_cells"), "boundary_reachability.visible_blocker_cells", width, height, nonempty=True)
    safety_blockers = unique_cells(raster.get("safety_blocker_cells"), "boundary_reachability.safety_blocker_cells", width, height, nonempty=True)
    if (outside | nonwalkable | visible_blockers | safety_blockers) & starts:
        raise ContractError("player_start_cells overlap blocked/outside cells")
    blocked = outside | nonwalkable | visible_blockers | safety_blockers
    reachable: set[tuple[int, int]] = set(starts)
    queue: deque[tuple[int, int]] = deque(starts)
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))
    while queue:
        cell = queue.popleft()
        for dx, dz in directions:
            neighbor = (cell[0] + dx, cell[1] + dz)
            if not (0 <= neighbor[0] < width and 0 <= neighbor[1] < height):
                continue
            if neighbor in blocked or neighbor in reachable:
                continue
            reachable.add(neighbor)
            queue.append(neighbor)
    expected_reachable = integer(raster.get("expected_reachable_cell_count"), "boundary_reachability.expected_reachable_cell_count", 1)
    if len(reachable) != expected_reachable:
        errors.append(f"boundary reachability has {len(reachable)} cells; expected {expected_reachable}")
    safety_contacts = {
        cell
        for cell in reachable
        if any((cell[0] + dx, cell[1] + dz) in safety_blockers for dx, dz in directions)
    }
    max_contacts = integer(raster.get("max_reachable_safety_contact_cells"), "boundary_reachability.max_reachable_safety_contact_cells")
    if len(safety_contacts) > max_contacts:
        errors.append(
            f"visible boundary permits {len(safety_contacts)} reachable pocket/contact cell(s) against the safety wall"
        )
    covered_safety: set[tuple[int, int]] = set()
    for index, raw in enumerate(array(raster.get("visible_boundary_causes"), "boundary_reachability.visible_boundary_causes", nonempty=True)):
        cause = obj(raw, f"visible_boundary_causes[{index}]")
        cause_id = text(cause.get("id"), f"visible boundary cause {index}.id")
        cause_objects = strings(cause.get("object_ids"), f"visible boundary cause {cause_id}.object_ids", nonempty=True)
        unknown_objects = sorted(cause_objects - set(placed_objects))
        if unknown_objects:
            errors.append(f"visible boundary cause {cause_id} references unknown objects: {', '.join(unknown_objects)}")
        cause_visible = unique_cells(cause.get("visible_cells"), f"visible boundary cause {cause_id}.visible_cells", width, height, nonempty=True)
        cause_safety = unique_cells(cause.get("safety_cells"), f"visible boundary cause {cause_id}.safety_cells", width, height, nonempty=True)
        text(cause.get("raw_artifact"), f"visible boundary cause {cause_id}.raw_artifact")
        if not cause_visible <= visible_blockers or not cause_safety <= safety_blockers:
            errors.append(f"visible boundary cause {cause_id} cells do not match the resolved raster")
        max_contact_distance = integer(cause.get("maximum_contact_distance_cells"), f"visible boundary cause {cause_id}.maximum_contact_distance_cells")
        for safety in cause_safety:
            nearest = min(max(abs(safety[0] - value[0]), abs(safety[1] - value[1])) for value in cause_visible)
            if nearest > max_contact_distance:
                errors.append(f"visible boundary cause {cause_id} does not contact/precede safety cell {safety}")
        if covered_safety & cause_safety:
            raise ContractError(f"visible boundary cause {cause_id} duplicates safety cells")
        covered_safety |= cause_safety
    if covered_safety != safety_blockers:
        errors.append("visible boundary causes do not cover every safety-wall cell")

    survey = obj(model.get("road_junction_survey"), "road_junction_survey")
    required_junctions = strings(survey.get("required_junction_ids"), "road_junction_survey.required_junction_ids", nonempty=True)
    required_approaches = strings(survey.get("required_approach_ids"), "road_junction_survey.required_approach_ids", nonempty=True)
    required_regions = strings(survey.get("required_surface_region_ids"), "road_junction_survey.required_surface_region_ids", nonempty=True)
    streetscape_classes = {
        "travel_lane", "parking_lane", "intersection", "crosswalk", "sidewalk_clear",
        "curb", "furnishing_zone", "frontage", "median", "traffic_island",
    }
    resolved_street_regions = {
        region.region_id for region in regions if region.surface_class in streetscape_classes
    }
    if required_junctions != set(junction_centers):
        errors.append("road-junction survey required_junction_ids does not match resolved junction manifest")
    if required_approaches != set(approaches):
        errors.append("road-junction survey required_approach_ids does not match resolved approach manifest")
    if required_regions != resolved_street_regions:
        errors.append("road-junction survey required_surface_region_ids does not match resolved streetscape regions")
    covered_junctions: set[str] = set()
    covered_approaches: set[str] = set()
    covered_regions: set[str] = set()
    captures = array(survey.get("captures"), "road_junction_survey.captures", nonempty=True)
    for index, raw in enumerate(captures):
        capture = obj(raw, f"road_junction_survey.captures[{index}]")
        capture_id = text(capture.get("id"), f"road junction capture {index}.id")
        if text(capture.get("source_kind"), f"road junction capture {capture_id}.source_kind") != "target_build_shipping_camera":
            errors.append(f"road junction capture {capture_id} is not from target_build_shipping_camera")
        if text(capture.get("build_id"), f"road junction capture {capture_id}.build_id") != build_id:
            errors.append(f"road junction capture {capture_id} does not match candidate build {build_id}")
        text(capture.get("camera_node"), f"road junction capture {capture_id}.camera_node")
        text(capture.get("raw_artifact"), f"road junction capture {capture_id}.raw_artifact")
        covered_junctions |= strings(capture.get("covered_junction_ids"), f"road junction capture {capture_id}.covered_junction_ids")
        covered_approaches |= strings(capture.get("covered_approach_ids"), f"road junction capture {capture_id}.covered_approach_ids")
        covered_regions |= strings(capture.get("covered_surface_region_ids"), f"road junction capture {capture_id}.covered_surface_region_ids")
    if covered_junctions != required_junctions:
        errors.append(f"shipping-camera road survey misses junctions: {', '.join(sorted(required_junctions - covered_junctions))}")
    if covered_approaches != required_approaches:
        errors.append(f"shipping-camera road survey misses approaches: {', '.join(sorted(required_approaches - covered_approaches))}")
    if covered_regions != required_regions:
        errors.append(f"shipping-camera road survey misses street regions: {', '.join(sorted(required_regions - covered_regions))}")

    required_states = strings(survey.get("required_state_ids"), "road_junction_survey.required_state_ids", nonempty=True)
    observed_states: set[str] = set()
    for index, raw in enumerate(array(survey.get("candidate_states"), "road_junction_survey.candidate_states", nonempty=True)):
        state = obj(raw, f"road_junction_survey.candidate_states[{index}]")
        state_id = text(state.get("id"), f"candidate state {index}.id")
        if text(state.get("source_kind"), f"candidate state {state_id}.source_kind") != "target_build_shipping_camera":
            errors.append(f"candidate state {state_id} is not a raw shipping-camera artifact")
        if text(state.get("build_id"), f"candidate state {state_id}.build_id") != build_id:
            errors.append(f"candidate state {state_id} does not match build {build_id}")
        text(state.get("raw_artifact"), f"candidate state {state_id}.raw_artifact")
        observed_states.add(state_id)
    if not required_states <= observed_states:
        errors.append(f"road semantics state matrix misses: {', '.join(sorted(required_states - observed_states))}")

    detected = strings(survey.get("detected_defect_classes"), "road_junction_survey.detected_defect_classes")
    resolved: set[str] = set()
    for index, raw in enumerate(array(survey.get("defect_resolutions"), "road_junction_survey.defect_resolutions")):
        item = obj(raw, f"road_junction_survey.defect_resolutions[{index}]")
        defect_class = text(item.get("class"), f"defect resolution {index}.class")
        if defect_class in resolved:
            raise ContractError(f"duplicate defect resolution class {defect_class}")
        resolved.add(defect_class)
        for phase in ("before", "fixed", "rerun"):
            artifact = obj(item.get(phase), f"defect resolution {defect_class}.{phase}")
            text(artifact.get("build_id"), f"defect resolution {defect_class}.{phase}.build_id")
            text(artifact.get("raw_artifact"), f"defect resolution {defect_class}.{phase}.raw_artifact")
        if text(obj(item.get("rerun"), "rerun").get("build_id"), f"defect resolution {defect_class}.rerun.build_id") != build_id:
            errors.append(f"defect resolution {defect_class} rerun does not match candidate build")
    if resolved != detected:
        errors.append("before/fixed/rerun defect-resolution classes do not match detected classes")

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
            "junction_continuity_query": junction_continuity_query,
            "road_detail_query": road_detail_query,
            "visible_mesh_inventory_query": visible_mesh_inventory_query,
            "rendered_material_query": rendered_material_query,
            "road_endpoint_query": road_endpoint_query,
            "support_contact_query": support_contact_query,
        },
        "surface_region_count": len(regions),
        "lane_count": len(lanes),
        "junction_count": len(junction_centers),
        "approach_count": len(approaches),
        "junction_continuity_run_count": len(continuity_roles),
        "junction_continuity_sample_count": continuity_sample_count,
        "junction_continuity_issue_count": continuity_issue_count,
        "placed_object_count": len(placed_objects),
        "road_detail_count": road_detail_count,
        "resolved_visible_mesh_count": len(resolved_meshes),
        "street_furniture_class_counts": furniture_class_counts,
        "support_structure_class_counts": support_class_counts,
        "support_contact_count": len(support_contacts_seen),
        "support_contact_measurements": support_contact_measurements,
        "resolved_marking_mesh_chain_count": len(marking_chains),
        "lane_boundary_termination_count": len(termination_records),
        "lane_boundary_termination_measurements": termination_measurements,
        "road_end_surface_measurements": road_end_surface_measurements,
        "visible_building_count": len(buildings_seen),
        "resolved_building_source_role_count": sum(
            len(roles) for roles in resolved_building_source_roles.values()
        ),
        "rendered_material_capture_count": capture_count,
        "rendered_material_mask_count": mask_count,
        "rendered_role_metrics": rendered_role_metrics,
        "rendered_role_separation_metrics": rendered_role_separation_metrics,
        "rendered_building_metrics": rendered_building_metrics,
        "incident_closure_count": len(closures),
        "reachable_cell_count": len(reachable),
        "reachable_safety_contact_count": len(safety_contacts),
        "survey_capture_count": len(captures),
        "survey_surface_region_count": len(covered_regions),
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
            f"[{marker}] streetscape-semantics id={report['contract_id']} "
            f"junctions={report['junction_count']} objects={report['placed_object_count']} "
            f"meshes={report['resolved_visible_mesh_count']} buildings={report['visible_building_count']} "
            f"terminations={report['lane_boundary_termination_count']} pockets={report['reachable_safety_contact_count']} "
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
