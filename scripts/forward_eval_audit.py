#!/usr/bin/env python3
"""Audit a populated blind forward-evaluation matrix for contract and fixture coverage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import re
import subprocess
from typing import Any
from evidence_integrity import check_hash, resolve, concrete, decode_media, observations_present, finite_number


class MatrixError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit skill-godot forward-eval coverage.")
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--mode", choices=("coverage", "execution"), default="coverage")
    parser.add_argument("--skill-repo", help="Git checkout containing the evaluated immutable commit (execution mode)")
    return parser.parse_args()


def read_json(value: str) -> dict[str, Any]:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise MatrixError(f"matrix not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MatrixError(f"could not read matrix {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise MatrixError("matrix root must be an object")
    return data


def string_list(value: Any, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise MatrixError(f"{label} must be an array of non-empty strings")
    result = [item.strip() for item in value]
    if not allow_empty and not result:
        raise MatrixError(f"{label} must not be empty")
    if len(result) != len(set(result)):
        raise MatrixError(f"{label} must not contain duplicates")
    return result


def audit(data: dict[str, Any], mode: str = "coverage", root: Path | None = None, skill_repo: Path | None = None) -> tuple[list[str], list[str], int]:
    errors: list[str] = []
    warnings: list[str] = []
    if data.get("schema_version") not in {1, 2}:
        errors.append("schema_version must be 1 or 2")
    if mode == "coverage":
        warnings.append("Declaration coverage only: no executed task, media review or artistic improvement is established.")
    elif data.get("schema_version") != 2:
        errors.append("execution mode requires schema_version=2 with bound observed runs")
    commit = data.get("skill_commit")
    if not isinstance(commit, str) or len(commit.strip()) < 7 or "replace" in commit.lower():
        errors.append("skill_commit must name the tested immutable revision")
    if mode == "execution" and (not isinstance(commit, str) or not re.fullmatch(r'[0-9a-f]{40}', commit)):
        errors.append("execution requires a full immutable Git commit SHA")
    elif mode == 'execution':
        try:
            subprocess.run(['git','-C',str(skill_repo or Path(__file__).resolve().parents[1]),'cat-file','-e',commit+'^{commit}'], capture_output=True, check=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            errors.append('skill commit does not resolve in --skill-repo; a plausible SHA is not provenance')
    if data.get('scope', 'canonical') not in {'canonical', 'focused'}:
        errors.append('scope must be canonical or focused')
    try:
        required = string_list(data.get("required_contracts"), "required_contracts")
    except MatrixError as exc:
        errors.append(str(exc))
        required = []
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        return errors + ["scenarios must be a non-empty array"], warnings, 0

    seen_ids: set[str] = set()
    coverage: dict[str, dict[str, bool]] = {
        contract: {"positive": False, "negative": False} for contract in required
    }
    for index, item in enumerate(scenarios):
        label = f"scenarios[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        scenario_id = item.get("id")
        if not isinstance(scenario_id, str) or not scenario_id.strip() or "replace" in scenario_id:
            errors.append(f"{label}.id must be a concrete ID")
        elif scenario_id in seen_ids:
            errors.append(f"duplicate scenario ID: {scenario_id}")
        else:
            seen_ids.add(scenario_id)
        for field in ("brief_path", "godot_version", "composite_case", "builder_context", "reviewer_context"):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip() or "replace" in value.lower():
                errors.append(f"{label}.{field} must be concrete")
        if item.get("builder_context") == item.get("reviewer_context"):
            errors.append(f"{label} builder and reviewer contexts must be distinct")
        if item.get("first_pass_verdict") not in {"pass", "fail", "blocked"}:
            errors.append(f"{label}.first_pass_verdict must be pass, fail, or blocked")
        try:
            contracts = string_list(item.get("contracts"), f"{label}.contracts")
        except MatrixError as exc:
            errors.append(str(exc))
            contracts = []
        unknown = sorted(set(contracts) - set(required))
        if unknown:
            errors.append(f"{label} names unknown contracts: {', '.join(unknown)}")
        positive = item.get("positive_fixture") is True
        negative = item.get("negative_fixture") is True
        if positive and negative:
            errors.append(f"{label} cannot be both positive and negative")
        if not positive and not negative:
            errors.append(f"{label} must contribute a positive or negative fixture")
        for contract in set(contracts) & set(required):
            coverage[contract]["positive"] |= positive
            coverage[contract]["negative"] |= negative
        defects = item.get("user_found_defects")
        mapping = item.get("expected_gate_for_each_defect")
        if not isinstance(defects, list) or any(not isinstance(value, str) for value in defects):
            errors.append(f"{label}.user_found_defects must be an array of strings")
        if not isinstance(mapping, dict):
            errors.append(f"{label}.expected_gate_for_each_defect must be an object")
        elif isinstance(defects, list):
            unmapped = [value for value in defects if value not in mapping]
            if unmapped:
                errors.append(f"{label} has defects without expected gates: {', '.join(unmapped)}")
        artifacts = item.get("result_artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            errors.append(f"{label}.result_artifacts must cite at least one raw result")
        false_positive = item.get("false_positive_burden")
        if not isinstance(false_positive, str) or not false_positive.strip() or false_positive == "unmeasured":
            errors.append(f"{label}.false_positive_burden must be measured or explicitly observed")
        for field in ("token_cost", "elapsed_minutes"):
            value = item.get(field)
            if not finite_number(value) or value < 0:
                errors.append(f"{label}.{field} must be a non-negative number")

        if mode == "execution":
            try:
                artifact_root = root or Path.cwd()
                check_hash(resolve(artifact_root, item.get('brief_path')), item.get('brief_sha256'))
                expected = item.get('expected_verdict')
                if expected not in {'pass', 'fail', 'blocked'} or expected != item.get('first_pass_verdict'):
                    raise MatrixError('expected and observed verdicts disagree or are missing')
                if (positive and expected != 'pass') or (negative and expected == 'pass'):
                    raise MatrixError('calibration polarity disagrees with expected verdict')
                ref = item.get('execution_receipt', {})
                path = resolve(artifact_root, ref.get('path'))
                check_hash(path, ref.get('sha256'))
                receipt = json.loads(path.read_text(encoding='utf-8-sig'))
                if receipt.get('skill_commit') != commit or receipt.get('scenario_id') != scenario_id or receipt.get('observed_verdict') != expected:
                    raise MatrixError('execution receipt is stale or contradicts the scenario')
                if receipt.get('builder_context') != item['builder_context'] or receipt.get('reviewer_context') != item['reviewer_context'] or not concrete(receipt.get('source_message')):
                    raise MatrixError('execution receipt lacks matching context/response provenance')
                if not observations_present(receipt.get('observations')):
                    raise MatrixError('execution receipt lacks observations')
                hashes = item.get('artifact_sha256', {})
                observed = receipt.get('artifact_sha256', {})
                for name in item.get('result_artifacts', []):
                    result_path = resolve(artifact_root, name)
                    actual = check_hash(result_path, hashes.get(name))
                    if observed.get(name) != actual:
                        raise MatrixError('receipt did not observe the exact result artifact')
                    suffix = result_path.suffix.lower()
                    if suffix in {'.png', '.jpg', '.jpeg', '.webp'}:
                        decode_media(result_path, 'image')
                    elif suffix in {'.avi', '.mp4', '.webm', '.mov', '.mkv'}:
                        decode_media(result_path, 'video')
            except Exception as exc:
                errors.append(f'{label}: execution evidence invalid: {exc}')

    for contract, states in coverage.items():
        if not states["positive"]:
            errors.append(f"contract {contract} lacks a positive fixture")
        if not states["negative"]:
            errors.append(f"contract {contract} lacks a negative fixture")
    hybrid_count = sum(
        isinstance(item, dict) and "+" in str(item.get("composite_case", ""))
        for item in scenarios
    )
    if data.get('scope', 'canonical') == 'canonical' and hybrid_count < 4:
        errors.append(f"only {hybrid_count} hybrid scenario(s); canonical matrix requires at least 4")
    return errors, warnings, len(scenarios)


def main() -> int:
    args = parse_args()
    try:
        errors, warnings, count = audit(read_json(args.matrix), args.mode, Path(args.matrix).resolve().parent, Path(args.skill_repo) if args.skill_repo else None)
        for message in errors:
            print(f"[ERROR] {message}")
        for message in warnings:
            print(f"[WARN] {message}")
        status = ("COVERAGE" if args.mode == 'coverage' else "EXECUTION_VALIDATED") if not errors else "FAIL"
        print(f"[{status}] forward-eval mode={args.mode} scenarios={count} errors={len(errors)} warnings={len(warnings)}")
        return 0 if not errors else 1
    except MatrixError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
