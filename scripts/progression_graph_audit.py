#!/usr/bin/env python3
"""Audit a bounded flag/state progression graph for reachability and escape traps."""

from __future__ import annotations

import argparse
from collections import defaultdict, deque
import json
from pathlib import Path
import sys
from typing import Any, Iterable


State = tuple[str, frozenset[str]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit a quest/metroidvania progression graph expressed as JSON."
    )
    parser.add_argument("--graph", required=True, help="Progression graph JSON file.")
    parser.add_argument("--max-states", type=int, default=100000, help="Bounded state-space limit.")
    parser.add_argument("--json-output", help="Write the full report as JSON.")
    parser.add_argument("--summary", action="store_true", help="Print bounded diagnostics.")
    parser.add_argument("--max-details", type=int, default=60)
    parser.add_argument("--fail-on-warnings", action="store_true")
    args = parser.parse_args()
    if args.max_states <= 0 or args.max_details < 0:
        parser.error("state/detail limits must be positive/non-negative")
    return args


def string_set(value: Any, path: str, errors: list[str]) -> set[str]:
    if value is None:
        return set()
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        errors.append(f"{path} must be an array of non-empty strings")
        return set()
    return set(value)


def conditions_hold(item: dict[str, Any], flags: frozenset[str]) -> bool:
    requires = set(item.get("requires", [])) | set(item.get("consumes", []))
    blocks = set(item.get("blocks", []))
    return requires.issubset(flags) and flags.isdisjoint(blocks)


def enter_node(node: dict[str, Any], flags: frozenset[str]) -> frozenset[str] | None:
    if not conditions_hold(node, flags):
        return None
    return frozenset(set(flags) | set(node.get("grants", [])))


def transition(edge: dict[str, Any], target: dict[str, Any], flags: frozenset[str]) -> frozenset[str] | None:
    if not conditions_hold(edge, flags):
        return None
    changed = set(flags)
    changed.difference_update(edge.get("consumes", []))
    changed.update(edge.get("grants", []))
    return enter_node(target, frozenset(changed))


def normalized_graph(raw: Any) -> tuple[dict[str, Any], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(raw, dict):
        return {}, ["graph root must be an object"], []
    start = raw.get("start")
    if not isinstance(start, str) or not start:
        errors.append("start must be a non-empty node ID")
    raw_nodes = raw.get("nodes")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        errors.append("nodes must be a non-empty array")
        raw_nodes = []
    nodes: dict[str, dict[str, Any]] = {}
    allowed_lists = ("requires", "blocks", "grants")
    for index, item in enumerate(raw_nodes):
        if not isinstance(item, dict):
            errors.append(f"nodes[{index}] must be an object")
            continue
        node_id = item.get("id")
        if not isinstance(node_id, str) or not node_id:
            errors.append(f"nodes[{index}].id must be a non-empty string")
            continue
        if node_id in nodes:
            errors.append(f"duplicate node ID: {node_id}")
            continue
        node = dict(item)
        for field in allowed_lists:
            node[field] = sorted(string_set(item.get(field), f"nodes[{index}].{field}", errors))
        if set(node["requires"]) & set(node["blocks"]):
            errors.append(f"node {node_id} both requires and blocks the same flag")
        for field in ("safe", "terminal", "must_escape"):
            if field in item and not isinstance(item[field], bool):
                errors.append(f"nodes[{index}].{field} must be boolean")
            node[field] = bool(item.get(field, False))
        nodes[node_id] = node

    raw_edges = raw.get("edges", [])
    if not isinstance(raw_edges, list):
        errors.append("edges must be an array")
        raw_edges = []
    edges: list[dict[str, Any]] = []
    edge_ids: set[str] = set()
    for index, item in enumerate(raw_edges):
        if not isinstance(item, dict):
            errors.append(f"edges[{index}] must be an object")
            continue
        source, target = item.get("from"), item.get("to")
        if not isinstance(source, str) or not isinstance(target, str) or not source or not target:
            errors.append(f"edges[{index}] requires non-empty from/to IDs")
            continue
        edge_id = item.get("id", f"{source}->{target}#{index}")
        if not isinstance(edge_id, str) or not edge_id:
            errors.append(f"edges[{index}].id must be a non-empty string")
            continue
        if edge_id in edge_ids:
            errors.append(f"duplicate edge ID: {edge_id}")
            continue
        edge_ids.add(edge_id)
        edge = dict(item)
        edge["id"], edge["from"], edge["to"] = edge_id, source, target
        for field in ("requires", "blocks", "grants", "consumes"):
            edge[field] = sorted(string_set(item.get(field), f"edges[{index}].{field}", errors))
        if set(edge["requires"]) & set(edge["blocks"]):
            errors.append(f"edge {edge_id} both requires and blocks the same flag")
        if source not in nodes:
            errors.append(f"edge {edge_id} references missing source node {source}")
        if target not in nodes:
            errors.append(f"edge {edge_id} references missing target node {target}")
        edges.append(edge)

    safe_nodes = string_set(raw.get("safe_nodes"), "safe_nodes", errors)
    for node_id in safe_nodes:
        if node_id not in nodes:
            errors.append(f"safe_nodes references missing node {node_id}")
        else:
            nodes[node_id]["safe"] = True
    required_nodes = string_set(raw.get("required_nodes"), "required_nodes", errors)
    required_flags = string_set(raw.get("required_flags"), "required_flags", errors)
    for node_id in required_nodes:
        if node_id not in nodes:
            errors.append(f"required_nodes references missing node {node_id}")
    initial_flags = string_set(raw.get("initial_flags"), "initial_flags", errors)
    if not required_nodes and not required_flags:
        warnings.append("no required_nodes or required_flags declared; only structural reachability is audited")
    if not any(node.get("safe") for node in nodes.values()):
        warnings.append("no safe node declared; must_escape checks cannot pass")
    return {
        "start": start,
        "nodes": nodes,
        "edges": edges,
        "initial_flags": initial_flags,
        "required_nodes": required_nodes,
        "required_flags": required_flags,
    }, errors, warnings


def sample_states(states: Iterable[State], limit: int = 40) -> list[dict[str, Any]]:
    ordered = sorted(states, key=lambda state: (state[0], sorted(state[1])))
    return [{"node": node, "flags": sorted(flags)} for node, flags in ordered[:limit]]


def audit(graph: dict[str, Any], max_states: int) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = graph["nodes"]
    outgoing: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for edge in graph["edges"]:
        outgoing[edge["from"]].append(edge)
    start_id = graph["start"]
    start_flags = enter_node(nodes[start_id], frozenset(graph["initial_flags"]))
    if start_flags is None:
        return {
            "errors": ["start node prerequisites are not satisfied by initial_flags"],
            "warnings": [],
            "states": set(),
            "adjacency": {},
            "traversed_edges": set(),
        }
    start: State = (start_id, start_flags)
    queue: deque[State] = deque([start])
    states: set[State] = {start}
    adjacency: dict[State, set[State]] = defaultdict(set)
    traversed_edges: set[str] = set()
    errors: list[str] = []
    warnings: list[str] = []
    capped = False
    while queue:
        state = queue.popleft()
        node_id, flags = state
        for edge in outgoing.get(node_id, []):
            target = nodes[edge["to"]]
            next_flags = transition(edge, target, flags)
            if next_flags is None:
                continue
            next_state: State = (edge["to"], next_flags)
            adjacency[state].add(next_state)
            traversed_edges.add(edge["id"])
            if next_state in states:
                continue
            if len(states) >= max_states:
                errors.append(f"state-space exceeded --max-states={max_states}")
                capped = True
                queue.clear()
                break
            states.add(next_state)
            queue.append(next_state)
        if capped:
            break

    reachable_nodes = {node for node, _ in states}
    reachable_flags = set().union(*(set(flags) for _, flags in states)) if states else set()
    for node_id in sorted(graph["required_nodes"] - reachable_nodes):
        errors.append(f"required node is unreachable: {node_id}")
    for flag in sorted(graph["required_flags"] - reachable_flags):
        errors.append(f"required flag is never acquired: {flag}")

    reverse: dict[State, set[State]] = defaultdict(set)
    for source, targets in adjacency.items():
        for target in targets:
            reverse[target].add(source)
    safe_states = {state for state in states if nodes[state[0]].get("safe")}
    can_reach_safe = set(safe_states)
    reverse_queue: deque[State] = deque(safe_states)
    while reverse_queue:
        state = reverse_queue.popleft()
        for previous in reverse.get(state, set()):
            if previous not in can_reach_safe:
                can_reach_safe.add(previous)
                reverse_queue.append(previous)
    trapped_states = {
        state
        for state in states
        if nodes[state[0]].get("must_escape") and state not in can_reach_safe
    }
    for state in sample_states(trapped_states, 20):
        errors.append(
            f"must_escape state cannot reach a safe node: {state['node']} flags={state['flags']}"
        )

    for state in states:
        node_id, flags = state
        node = nodes[node_id]
        if not adjacency.get(state) and not node.get("safe") and not node.get("terminal"):
            warnings.append(f"reachable dead end: {node_id} flags={sorted(flags)}")
    for node_id in sorted(set(nodes) - reachable_nodes):
        warnings.append(f"node is unreachable in the modeled state space: {node_id}")
    for edge in graph["edges"]:
        if edge["id"] not in traversed_edges:
            warnings.append(f"edge is never traversable: {edge['id']}")
    return {
        "errors": errors,
        "warnings": warnings,
        "states": states,
        "adjacency": adjacency,
        "traversed_edges": traversed_edges,
        "reachable_nodes": reachable_nodes,
        "reachable_flags": reachable_flags,
        "trapped_states": trapped_states,
    }


def main() -> int:
    args = parse_args()
    try:
        graph_path = Path(args.graph).expanduser().resolve()
        raw = json.loads(graph_path.read_text(encoding="utf-8"))
        graph, errors, warnings = normalized_graph(raw)
        if not errors:
            result = audit(graph, args.max_states)
            errors.extend(result["errors"])
            warnings.extend(result["warnings"])
        else:
            result = {
                "states": set(),
                "traversed_edges": set(),
                "reachable_nodes": set(),
                "reachable_flags": set(),
                "trapped_states": set(),
            }
        report = {
            "graph": str(graph_path),
            "node_count": len(graph.get("nodes", {})),
            "edge_count": len(graph.get("edges", [])),
            "reachable_state_count": len(result.get("states", set())),
            "reachable_nodes": sorted(result.get("reachable_nodes", set())),
            "reachable_flags": sorted(result.get("reachable_flags", set())),
            "traversed_edges": sorted(result.get("traversed_edges", set())),
            "trapped_state_samples": sample_states(result.get("trapped_states", set()), 40),
            "state_samples": sample_states(result.get("states", set()), 40),
            "errors": errors,
            "warnings": sorted(set(warnings)),
        }
        report["passed"] = not errors and not (args.fail_on_warnings and report["warnings"])
        if args.json_output:
            output = Path(args.json_output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        status = "PASS" if report["passed"] else "FAIL"
        if args.summary or not args.json_output or not report["passed"]:
            print(
                f"[{status}] nodes={report['node_count']} edges={report['edge_count']} "
                f"states={report['reachable_state_count']} errors={len(errors)} "
                f"warnings={len(report['warnings'])}"
            )
            details = [*(f"[ERROR] {item}" for item in errors), *(f"[WARN] {item}" for item in report["warnings"])]
            for detail in details[: args.max_details]:
                print(detail)
            if len(details) > args.max_details:
                print(f"[INFO] {len(details) - args.max_details} additional diagnostics omitted")
        return 0 if report["passed"] else 1
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        print(f"[ERROR] {error}")
        return 2


if __name__ == "__main__":
    sys.exit(main())

