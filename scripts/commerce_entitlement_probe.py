#!/usr/bin/env python3
"""Audit purchase delivery, entitlement, restore, and revocation evidence."""

from contract_probe_utils import (
    ContractError, array, boolean, cli_main, contract_header, finish_report, integer, obj,
    require_coverage, require_target_pass, require_true, strings, text, trace_header,
)


def audit(model):
    contract_id, _, contract = contract_header(model)
    required = strings(contract.get("required_scenarios"), "required_scenarios", nonempty=True)
    authority = text(contract.get("verification_authority"), "verification_authority")
    durable = boolean(contract.get("durable_online_currency"), "durable_online_currency")
    if durable and authority != "secure_backend":
        raise ContractError("durable online currency requires secure_backend verification")
    if boolean(contract.get("secrets_embedded"), "secrets_embedded"):
        raise ContractError("commerce client embeds secrets")
    products = array(contract.get("products"), "products", nonempty=True)
    product_ids = set()
    for index, product in enumerate(products):
        item = obj(product, f"products[{index}]")
        product_id = text(item.get("id"), f"products[{index}].id")
        product_type = text(item.get("type"), f"products[{index}].type")
        if product_id in product_ids:
            raise ContractError(f"duplicate product ID {product_id}")
        product_ids.add(product_id)
        if product_type not in {"consumable", "non_consumable", "subscription"}:
            raise ContractError(f"product {product_id} has unsupported type {product_type}")
    traces = array(model.get("traces"), "traces", nonempty=True)
    errors, seen_ids, observed = [], set(), set()
    no_grant = {"pending", "canceled", "offline", "account_mismatch", "server_timeout"}
    for index, raw in enumerate(traces):
        trace, trace_id, scenario = trace_header(raw, index, seen_ids)
        observed.add(scenario)
        require_target_pass(trace, trace_id, errors)
        for key in ("server_or_platform_verified", "ledger_balanced", "safe_state"):
            require_true(trace, key, trace_id, errors)
        if integer(trace.get("secrets_exposed"), f"trace {trace_id}.secrets_exposed"):
            errors.append(f"trace {trace_id} exposes commerce secrets")
        grants = array(trace.get("grants"), f"trace {trace_id}.grants")
        expected = array(trace.get("expected_grants"), f"trace {trace_id}.expected_grants")
        if grants != expected:
            errors.append(f"trace {trace_id} grant ledger differs from expectation")
        if scenario in no_grant and grants:
            errors.append(f"trace {trace_id} grants during {scenario}")
        if scenario == "duplicate_delivery" and integer(trace.get("grant_count"), f"trace {trace_id}.grant_count") != 1:
            errors.append(f"trace {trace_id} is not exactly-once")
        if scenario in {"purchase_success", "duplicate_delivery", "acknowledge_retry"}:
            require_true(trace, "acknowledged_or_consumed", trace_id, errors)
            require_true(trace, "transaction_id_stable", trace_id, errors)
        if scenario == "refund_revoke":
            require_true(trace, "entitlement_removed", trace_id, errors)
        if scenario == "restore":
            require_true(trace, "entitlement_restored", trace_id, errors)
        if scenario == "account_mismatch" and boolean(trace.get("account_match"), f"trace {trace_id}.account_match"):
            errors.append(f"trace {trace_id} did not block account mismatch")
    require_coverage(required, observed, "commerce scenarios", errors)
    return finish_report(contract_id, traces, errors, product_count=len(products), scenario_count=len(observed))


if __name__ == "__main__":
    raise SystemExit(cli_main("commerce entitlement", audit))
