#!/usr/bin/env python3
"""Audit road, junction, facade, furniture, closure, and visible-boundary semantics."""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass
import json
from math import acos, ceil, degrees, hypot
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
    return obj(data, "model root")


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
    if model.get("schema_version") != 1:
        raise ContractError("schema_version must be 1")
    contract_id = text(model.get("contract_id"), "contract_id")
    build_id = text(model.get("build_id"), "build_id")
    raw_provenance = obj(model.get("scene_provenance"), "scene_provenance")
    try:
        provenance = validate_scene_provenance_reference(raw_provenance)
    except ProvenanceError as exc:
        raise ContractError(str(exc)) from exc
    text(raw_provenance.get("streetscape_query"), "scene_provenance.streetscape_query")
    text(raw_provenance.get("visible_surface_query"), "scene_provenance.visible_surface_query")

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
    for index, raw in enumerate(array(graph.get("junctions"), "road_graph.junctions", nonempty=True)):
        item = obj(raw, f"road_graph.junctions[{index}]")
        junction_id = text(item.get("id"), f"road_graph.junctions[{index}].id")
        if junction_id in junction_centers:
            raise ContractError(f"duplicate junction {junction_id}")
        center = vec2(item.get("center"), f"junction {junction_id}.center")
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
        )
        if furniture and profiles[profile_id].maximum_curb_setback < profiles[profile_id].minimum_curb_setback:
            raise ContractError(f"placement profile {profile_id} curb setback maximum is below minimum")
        if profiles[profile_id].orientation_mode not in {"none", "with_travel", "face_oncoming"}:
            raise ContractError(f"placement profile {profile_id} has unknown orientation_mode")

    placed_objects: dict[str, PlacedObject] = {}
    object_surface_results: dict[str, tuple[int, int, int]] = {}
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
        placed_objects[object_id] = PlacedObject(
            object_id,
            text(item.get("class"), f"placed object {object_id}.class"),
            text(item.get("source_node"), f"placed object {object_id}.source_node"),
            profile_id,
            shape,
            anchor,
            forward,
            approach_id,
            closure_id,
            zone_id,
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

    style_profiles: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(array(model.get("building_style_profiles"), "building_style_profiles", nonempty=True)):
        item = obj(raw, f"building_style_profiles[{index}]")
        profile_id = text(item.get("id"), f"building_style_profiles[{index}].id")
        if profile_id in style_profiles:
            raise ContractError(f"duplicate building style profile {profile_id}")
        style_profiles[profile_id] = {
            "required_roles": strings(item.get("required_visible_roles"), f"building style {profile_id}.required_visible_roles", nonempty=True),
            "forbidden_materials": strings(item.get("forbidden_material_ids"), f"building style {profile_id}.forbidden_material_ids", nonempty=True),
            "allowed_zones": strings(item.get("allowed_zone_ids"), f"building style {profile_id}.allowed_zone_ids", nonempty=True),
            "allowed_story_states": strings(item.get("allowed_story_states"), f"building style {profile_id}.allowed_story_states", nonempty=True),
            "minimum_coverage": ratio(item.get("minimum_materialized_visible_area_ratio"), f"building style {profile_id}.minimum_materialized_visible_area_ratio"),
        }

    buildings_seen: set[str] = set()
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
        zone_id = text(item.get("zone_id"), f"visible building {building_id}.zone_id")
        story_state = text(item.get("story_state"), f"visible building {building_id}.story_state")
        text(item.get("function"), f"visible building {building_id}.function")
        if zone_id not in profile["allowed_zones"]:
            errors.append(f"visible building {building_id} style profile is invalid for zone {zone_id}")
        if story_state not in profile["allowed_story_states"]:
            errors.append(f"visible building {building_id} story state {story_state} is outside its style profile")
        total_area = number(item.get("visible_surface_area"), f"visible building {building_id}.visible_surface_area", minimum=1e-9)
        listed_area = 0.0
        materialized_area = 0.0
        roles: set[str] = set()
        slots = array(item.get("visible_surface_slots"), f"visible building {building_id}.visible_surface_slots", nonempty=True)
        slot_ids: set[str] = set()
        for slot_index, raw_slot in enumerate(slots):
            slot = obj(raw_slot, f"visible building {building_id}.visible_surface_slots[{slot_index}]")
            slot_id = text(slot.get("id"), f"visible building {building_id} slot {slot_index}.id")
            if slot_id in slot_ids:
                raise ContractError(f"duplicate visible surface slot {building_id}/{slot_id}")
            slot_ids.add(slot_id)
            role = text(slot.get("role"), f"visible building {building_id} slot {slot_id}.role")
            material_id = text(slot.get("material_id"), f"visible building {building_id} slot {slot_id}.material_id")
            source_kind = text(slot.get("source_kind"), f"visible building {building_id} slot {slot_id}.source_kind")
            if source_kind not in {"mesh_surface_material", "surface_override_material"}:
                errors.append(f"visible building {building_id} slot {slot_id} lacks resolved mesh material provenance")
            area = number(slot.get("visible_area"), f"visible building {building_id} slot {slot_id}.visible_area", minimum=0.0)
            listed_area += area
            roles.add(role)
            if material_id not in profile["forbidden_materials"]:
                materialized_area += area
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
        },
        "surface_region_count": len(regions),
        "lane_count": len(lanes),
        "junction_count": len(junction_centers),
        "approach_count": len(approaches),
        "placed_object_count": len(placed_objects),
        "visible_building_count": len(buildings_seen),
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
            f"buildings={report['visible_building_count']} pockets={report['reachable_safety_contact_count']} "
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
