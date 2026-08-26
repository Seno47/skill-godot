#!/usr/bin/env python3
"""Audit a project-declared multiplayer authority and runtime trace contract."""

from __future__ import annotations

import argparse
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys
from typing import Any


ALLOWED_CHECKS = {
    "authority_security",
    "lifecycle",
    "state_convergence",
    "impaired_network",
    "reconnect",
    "dedicated_server",
    "persistence_transactions",
    "interest_management",
    "scale_capacity",
    "browser_transport",
}
WEB_TRANSPORTS = {"websocket", "webrtc", "custom_web"}
TRANSFER_MODES = {"reliable", "unreliable", "unreliable_ordered"}


class ContractError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit declared multiplayer authority, impairment, lifecycle, and capacity traces."
    )
    parser.add_argument("--model", required=True, help="Network contract JSON.")
    parser.add_argument("--json-output", help="Optional JSON report path.")
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args()


def obj(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    return value


def text_value(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{label} must be a non-empty string")
    return value.strip()


def text_list(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ContractError(f"{label} must be an array of non-empty strings")
    if not allow_empty and not value:
        raise ContractError(f"{label} must not be empty")
    if len(value) != len(set(value)):
        raise ContractError(f"{label} must not contain duplicates")
    return value


def decimal_value(value: Any, label: str, *, minimum: Decimal | None = Decimal(0)) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ContractError(f"{label} must be a finite decimal string or number")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ContractError(f"{label} is not a decimal") from exc
    if not result.is_finite() or (minimum is not None and result < minimum):
        raise ContractError(f"{label} must be finite and >= {minimum}")
    return result


def int_value(value: Any, label: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContractError(f"{label} must be an integer >= {minimum}")
    return value


def bool_value(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise ContractError(f"{label} must be a boolean")
    return value


def main() -> int:
    args = parse_args()
    model_path = Path(args.model).expanduser().resolve()
    try:
        if not model_path.is_file():
            raise ContractError(f"model not found: {model_path}")
        model = json.loads(model_path.read_text(encoding="utf-8-sig"))
        if not isinstance(model, dict) or model.get("schema_version") != 1:
            raise ContractError("model root must be an object with schema_version 1")
        contract_id = text_value(model.get("contract_id"), "contract_id")
        build_id = text_value(model.get("build_id"), "build_id")
        architecture = obj(model.get("architecture"), "architecture")
        topology = text_value(architecture.get("topology"), "architecture.topology")
        transport = text_value(architecture.get("transport"), "architecture.transport").lower()
        platforms = text_list(architecture.get("target_platforms"), "architecture.target_platforms")
        text_value(architecture.get("authentication"), "architecture.authentication")
        required_checks = set(
            text_list(architecture.get("required_checks"), "architecture.required_checks")
        )
        unknown_checks = sorted(required_checks - ALLOWED_CHECKS)
        if unknown_checks:
            raise ContractError(f"unknown required checks: {', '.join(unknown_checks)}")
        required_scenarios = text_list(
            architecture.get("required_scenarios"), "architecture.required_scenarios"
        )

        budgets = obj(model.get("budgets"), "budgets")
        errors: list[str] = []

        rpc_surfaces = model.get("rpc_surfaces")
        if not isinstance(rpc_surfaces, list):
            raise ContractError("rpc_surfaces must be an array")
        rpc_ids: set[str] = set()
        for index, raw in enumerate(rpc_surfaces):
            rpc = obj(raw, f"rpc_surfaces[{index}]")
            rpc_id = text_value(rpc.get("id"), f"rpc_surfaces[{index}].id")
            if rpc_id in rpc_ids:
                raise ContractError(f"duplicate RPC surface ID: {rpc_id}")
            rpc_ids.add(rpc_id)
            direction = text_value(rpc.get("direction"), f"rpc {rpc_id}.direction")
            authority = text_value(rpc.get("authority"), f"rpc {rpc_id}.authority")
            transfer_mode = text_value(
                rpc.get("transfer_mode"), f"rpc {rpc_id}.transfer_mode"
            )
            if transfer_mode not in TRANSFER_MODES:
                errors.append(f"rpc {rpc_id} has unknown transfer mode {transfer_mode}")
            int_value(rpc.get("channel"), f"rpc {rpc_id}.channel")
            if direction == "client_to_server":
                if authority != "server":
                    errors.append(f"client RPC {rpc_id} is not server-authoritative")
                validations = text_list(rpc.get("validates"), f"rpc {rpc_id}.validates")
                if "authenticated" not in validations or "rate_limit" not in validations:
                    errors.append(
                        f"client RPC {rpc_id} must validate authenticated state and rate_limit"
                    )
                decimal_value(
                    rpc.get("max_calls_per_second"),
                    f"rpc {rpc_id}.max_calls_per_second",
                    minimum=Decimal("0.000001"),
                )
            elif direction != "server_to_client":
                errors.append(f"rpc {rpc_id} has unsupported direction {direction}")

        if "authority_security" in required_checks and not rpc_surfaces:
            errors.append("authority_security requires at least one declared RPC surface")

        streams = model.get("replication_streams")
        if not isinstance(streams, list):
            raise ContractError("replication_streams must be an array")
        stream_ids: set[str] = set()
        for index, raw in enumerate(streams):
            stream = obj(raw, f"replication_streams[{index}]")
            stream_id = text_value(stream.get("id"), f"replication_streams[{index}].id")
            if stream_id in stream_ids:
                raise ContractError(f"duplicate replication stream ID: {stream_id}")
            stream_ids.add(stream_id)
            authority = text_value(stream.get("authority"), f"stream {stream_id}.authority")
            transfer_mode = text_value(
                stream.get("transfer_mode"), f"stream {stream_id}.transfer_mode"
            )
            if authority != "server":
                errors.append(f"replication stream {stream_id} is not server-authoritative")
            if transfer_mode not in TRANSFER_MODES:
                errors.append(f"stream {stream_id} has unknown transfer mode {transfer_mode}")
            int_value(stream.get("channel"), f"stream {stream_id}.channel")
            high_frequency = bool_value(
                stream.get("high_frequency"), f"stream {stream_id}.high_frequency"
            )
            interest_filtered = bool_value(
                stream.get("interest_filtered"), f"stream {stream_id}.interest_filtered"
            )
            if high_frequency and transfer_mode == "reliable":
                errors.append(f"high-frequency stream {stream_id} uses reliable transfer")
            if "interest_management" in required_checks and high_frequency and not interest_filtered:
                errors.append(f"high-frequency stream {stream_id} is not interest-filtered")

        traces = model.get("traces")
        if not isinstance(traces, list) or not traces:
            raise ContractError("traces must be a non-empty array")
        trace_ids: set[str] = set()
        scenario_traces: dict[str, list[dict[str, Any]]] = {}
        hostile_invalid_total = 0
        hostile_accepted_total = 0
        max_observed_clients = 0
        for index, raw in enumerate(traces):
            trace = obj(raw, f"traces[{index}]")
            trace_id = text_value(trace.get("id"), f"traces[{index}].id")
            if trace_id in trace_ids:
                raise ContractError(f"duplicate trace ID: {trace_id}")
            trace_ids.add(trace_id)
            scenario = text_value(trace.get("scenario"), f"trace {trace_id}.scenario")
            text_value(trace.get("source"), f"trace {trace_id}.source")
            clients = int_value(trace.get("clients"), f"trace {trace_id}.clients", minimum=1)
            max_observed_clients = max(max_observed_clients, clients)
            result = text_value(trace.get("result"), f"trace {trace_id}.result")
            if result != "pass":
                errors.append(f"trace {trace_id} result is {result}, not pass")
            scenario_traces.setdefault(scenario, []).append(trace)

            invalid = int_value(
                trace.get("invalid_requests", 0), f"trace {trace_id}.invalid_requests"
            )
            accepted = int_value(
                trace.get("invalid_requests_accepted", 0),
                f"trace {trace_id}.invalid_requests_accepted",
            )
            hostile_invalid_total += invalid
            hostile_accepted_total += accepted
            if accepted:
                errors.append(f"trace {trace_id} accepted {accepted} invalid request(s)")
            duplicate_commits = int_value(
                trace.get("duplicate_commits", 0), f"trace {trace_id}.duplicate_commits"
            )
            unauthorized = int_value(
                trace.get("unauthorized_mutations", 0),
                f"trace {trace_id}.unauthorized_mutations",
            )
            if duplicate_commits:
                errors.append(f"trace {trace_id} recorded duplicate durable commits")
            if unauthorized:
                errors.append(f"trace {trace_id} recorded unauthorized mutations")

            if "state_convergence" in required_checks:
                if not bool_value(
                    trace.get("state_converged"), f"trace {trace_id}.state_converged"
                ):
                    errors.append(f"trace {trace_id} did not converge")
                desyncs = int_value(
                    trace.get("desync_count"), f"trace {trace_id}.desync_count"
                )
                max_desyncs = int_value(
                    budgets.get("max_desync_count"), "budgets.max_desync_count"
                )
                if desyncs > max_desyncs:
                    errors.append(
                        f"trace {trace_id} desync count {desyncs} exceeds {max_desyncs}"
                    )

        missing_scenarios = sorted(set(required_scenarios) - set(scenario_traces))
        if missing_scenarios:
            errors.append(f"missing required scenarios: {', '.join(missing_scenarios)}")
        if "authority_security" in required_checks:
            if hostile_invalid_total <= 0:
                errors.append("authority_security has no rejected hostile/invalid request evidence")
            if hostile_accepted_total:
                errors.append("authority_security accepted hostile/invalid requests")

        if "impaired_network" in required_checks:
            impairment = obj(model.get("impairment_profile"), "impairment_profile")
            minimum_latency = decimal_value(
                impairment.get("minimum_latency_ms"), "impairment_profile.minimum_latency_ms"
            )
            minimum_jitter = decimal_value(
                impairment.get("minimum_jitter_ms"), "impairment_profile.minimum_jitter_ms"
            )
            minimum_loss = decimal_value(
                impairment.get("minimum_packet_loss_percent"),
                "impairment_profile.minimum_packet_loss_percent",
            )
            impaired = scenario_traces.get("impaired_network", [])
            if not impaired:
                errors.append("impaired_network check lacks impaired_network trace")
            max_error = decimal_value(budgets.get("max_state_error"), "budgets.max_state_error")
            max_reconciliation = decimal_value(
                budgets.get("max_reconciliation_ms"), "budgets.max_reconciliation_ms"
            )
            for trace in impaired:
                trace_id = trace["id"]
                if decimal_value(trace.get("latency_ms"), f"trace {trace_id}.latency_ms") < minimum_latency:
                    errors.append(f"trace {trace_id} latency does not reach declared impairment")
                if decimal_value(trace.get("jitter_ms"), f"trace {trace_id}.jitter_ms") < minimum_jitter:
                    errors.append(f"trace {trace_id} jitter does not reach declared impairment")
                if decimal_value(
                    trace.get("packet_loss_percent"), f"trace {trace_id}.packet_loss_percent"
                ) < minimum_loss:
                    errors.append(f"trace {trace_id} packet loss does not reach declared impairment")
                if decimal_value(
                    trace.get("max_state_error"), f"trace {trace_id}.max_state_error"
                ) > max_error:
                    errors.append(f"trace {trace_id} state error exceeds budget {max_error}")
                if decimal_value(
                    trace.get("max_reconciliation_ms"),
                    f"trace {trace_id}.max_reconciliation_ms",
                ) > max_reconciliation:
                    errors.append(
                        f"trace {trace_id} reconciliation exceeds budget {max_reconciliation}ms"
                    )

        if "reconnect" in required_checks:
            reconnect_budget = decimal_value(
                budgets.get("max_reconnect_seconds"), "budgets.max_reconnect_seconds"
            )
            reconnect_traces = scenario_traces.get("disconnect_reconnect", [])
            if not reconnect_traces:
                errors.append("reconnect check lacks disconnect_reconnect trace")
            for trace in reconnect_traces:
                trace_id = trace["id"]
                if decimal_value(
                    trace.get("reconnect_seconds"), f"trace {trace_id}.reconnect_seconds"
                ) > reconnect_budget:
                    errors.append(f"trace {trace_id} reconnect exceeds {reconnect_budget}s")
                if bool_value(trace.get("data_loss"), f"trace {trace_id}.data_loss"):
                    errors.append(f"trace {trace_id} lost state during reconnect")

        if "dedicated_server" in required_checks:
            if topology != "dedicated_authoritative":
                errors.append("dedicated_server check requires dedicated_authoritative topology")
            server_traces = scenario_traces.get("server_boot_shutdown", [])
            if not server_traces:
                errors.append("dedicated_server check lacks server_boot_shutdown trace")
            for trace in server_traces:
                trace_id = trace["id"]
                if not bool_value(trace.get("headless_export"), f"trace {trace_id}.headless_export"):
                    errors.append(f"trace {trace_id} did not use a headless/dedicated export")
                if bool_value(trace.get("server_is_player"), f"trace {trace_id}.server_is_player"):
                    errors.append(f"trace {trace_id} treats the dedicated server as a player")

        if "persistence_transactions" in required_checks:
            transaction_traces = scenario_traces.get("persistence_transaction", [])
            if not transaction_traces:
                errors.append("persistence_transactions lacks persistence_transaction trace")
            for trace in transaction_traces:
                trace_id = trace["id"]
                attempts = int_value(
                    trace.get("transaction_attempts"), f"trace {trace_id}.transaction_attempts"
                )
                commits = int_value(
                    trace.get("transaction_commits"), f"trace {trace_id}.transaction_commits"
                )
                if attempts < 2 or commits != 1:
                    errors.append(
                        f"trace {trace_id} must prove retry attempts >= 2 with exactly one commit"
                    )
                if bool_value(trace.get("data_loss"), f"trace {trace_id}.data_loss"):
                    errors.append(f"trace {trace_id} lost a durable transaction")

        if "scale_capacity" in required_checks:
            target_clients = int_value(
                budgets.get("target_concurrent_clients"),
                "budgets.target_concurrent_clients",
                minimum=1,
            )
            tick_budget = decimal_value(
                budgets.get("max_server_tick_p95_ms"), "budgets.max_server_tick_p95_ms"
            )
            bandwidth_budget = decimal_value(
                budgets.get("max_bandwidth_bytes_per_second_per_client"),
                "budgets.max_bandwidth_bytes_per_second_per_client",
            )
            capacity_traces = scenario_traces.get("capacity", [])
            if max_observed_clients < target_clients or not capacity_traces:
                errors.append(f"capacity evidence does not reach {target_clients} clients")
            for trace in capacity_traces:
                trace_id = trace["id"]
                if decimal_value(
                    trace.get("server_tick_p95_ms"), f"trace {trace_id}.server_tick_p95_ms"
                ) > tick_budget:
                    errors.append(f"trace {trace_id} server tick exceeds {tick_budget}ms")
                if decimal_value(
                    trace.get("bandwidth_bytes_per_second_per_client"),
                    f"trace {trace_id}.bandwidth_bytes_per_second_per_client",
                ) > bandwidth_budget:
                    errors.append(f"trace {trace_id} bandwidth exceeds {bandwidth_budget} B/s/client")

        if "interest_management" in required_checks:
            entity_budget = int_value(
                budgets.get("max_replicated_entities_per_client"),
                "budgets.max_replicated_entities_per_client",
                minimum=1,
            )
            for trace in scenario_traces.get("capacity", []):
                trace_id = trace["id"]
                replicated = int_value(
                    trace.get("replicated_entities_per_client"),
                    f"trace {trace_id}.replicated_entities_per_client",
                )
                if replicated > entity_budget:
                    errors.append(
                        f"trace {trace_id} replicated entities {replicated} exceeds {entity_budget}"
                    )

        web_target = any(item.lower() in {"web", "html5", "browser"} for item in platforms)
        if web_target or "browser_transport" in required_checks:
            if transport not in WEB_TRANSPORTS:
                errors.append(f"Web target cannot use declared transport {transport}")
            if transport == "webrtc":
                signaling = text_value(
                    architecture.get("signaling_service"), "architecture.signaling_service"
                )
                if signaling == "not_applicable":
                    errors.append("WebRTC target requires a signaling service contract")

        report = {
            "status": "pass" if not errors else "fail",
            "contract_id": contract_id,
            "build_id": build_id,
            "topology": topology,
            "transport": transport,
            "trace_count": len(traces),
            "required_checks": sorted(required_checks),
            "observed_scenarios": sorted(scenario_traces),
            "max_observed_clients": max_observed_clients,
            "errors": errors,
        }
        if args.json_output:
            output = Path(args.json_output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        label = "PASS" if not errors else "FAIL"
        print(
            f"[{label}] network-contract id={contract_id} traces={len(traces)} "
            f"clients={max_observed_clients} errors={len(errors)}"
        )
        for error in errors:
            print(f"[ERROR] {error}")
        if not args.summary and not errors:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if not errors else 1
    except (OSError, json.JSONDecodeError, ContractError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
