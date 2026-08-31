#!/usr/bin/env python3
"""Smoke tests for deterministic contracts and production workflow helpers."""

from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def run_script(name: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(SCRIPTS / name), *arguments],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
        check=False,
    )


def load_asset_json(name: str) -> dict[str, object]:
    return json.loads((ROOT / "assets" / name).read_text(encoding="utf-8"))


def run_contract(script: str, model: dict[str, object]) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "contract.json"
        path.write_text(json.dumps(model), encoding="utf-8")
        return run_script(script, "--model", str(path), "--summary")


class RepositoryIntegrityTests(unittest.TestCase):
    def test_local_markdown_links_resolve(self) -> None:
        documents = [ROOT / "SKILL.md", ROOT / "README.md", ROOT / "README.ru.md"]
        documents.extend((ROOT / "references").glob("*.md"))
        missing: list[str] = []
        pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
        for document in documents:
            for raw_target in pattern.findall(document.read_text(encoding="utf-8")):
                target = raw_target.strip().split("#", 1)[0]
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                resolved = (document.parent / target).resolve()
                if not resolved.exists():
                    missing.append(f"{document.relative_to(ROOT)} -> {raw_target}")
        self.assertEqual(missing, [], "\n".join(missing))

    def test_all_json_assets_and_eval_files_parse(self) -> None:
        paths = list((ROOT / "assets").glob("*.json"))
        paths.extend((ROOT / "evals").glob("*.json"))
        for path in paths:
            with self.subTest(path=path.name):
                self.assertIsInstance(json.loads(path.read_text(encoding="utf-8")), dict)


class ProgressionGraphTests(unittest.TestCase):
    def test_template_passes(self) -> None:
        completed = run_script(
            "progression_graph_audit.py",
            "--graph",
            str(ROOT / "assets" / "progression-graph.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS]", completed.stdout)

    def test_escape_trap_fails(self) -> None:
        graph = {
            "start": "start",
            "safe_nodes": ["start"],
            "required_nodes": ["pit"],
            "nodes": [
                {"id": "start", "safe": True},
                {"id": "pit", "must_escape": True},
            ],
            "edges": [{"from": "start", "to": "pit"}],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.json"
            path.write_text(json.dumps(graph), encoding="utf-8")
            completed = run_script(
                "progression_graph_audit.py", "--graph", str(path), "--summary"
            )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("must_escape state cannot reach a safe node", completed.stdout)


class IdleEconomyTests(unittest.TestCase):
    def test_template_passes(self) -> None:
        completed = run_script(
            "idle_economy_probe.py",
            "--model",
            str(ROOT / "assets" / "idle-economy.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS]", completed.stdout)

    def test_impossible_milestone_fails(self) -> None:
        model = {
            "duration_seconds": "10",
            "manual_rate": "0",
            "generators": [
                {
                    "id": "helper",
                    "base_cost": "10",
                    "cost_growth": "1.1",
                    "base_rate": "1",
                    "rate_growth": "1",
                }
            ],
            "milestones": [{"seconds": "10", "min_purchases": 1}],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "economy.json"
            path.write_text(json.dumps(model), encoding="utf-8")
            completed = run_script(
                "idle_economy_probe.py", "--model", str(path), "--summary"
            )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("milestone 10s", completed.stdout)


class ProgressionBalanceTests(unittest.TestCase):
    @staticmethod
    def load_template() -> dict[str, object]:
        return json.loads(
            (ROOT / "assets" / "progression-balance.template.json").read_text(
                encoding="utf-8"
            )
        )

    def run_model(self, model: dict[str, object]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "progression-balance.json"
            path.write_text(json.dumps(model), encoding="utf-8")
            return run_script(
                "progression_balance_probe.py", "--model", str(path), "--summary"
            )

    def test_template_passes(self) -> None:
        completed = run_script(
            "progression_balance_probe.py",
            "--model",
            str(ROOT / "assets" / "progression-balance.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS]", completed.stdout)

    def test_missing_required_archetype_fails(self) -> None:
        model = self.load_template()
        model["traces"] = [
            trace for trace in model["traces"] if trace["archetype"] != "expert"
        ]
        completed = self.run_model(model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("missing required archetypes: expert", completed.stdout)

    def test_resource_bankruptcy_fails(self) -> None:
        model = self.load_template()
        model["traces"][0]["checkpoints"][1]["balances"]["coins"] = "-1"
        completed = self.run_model(model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("below floor", completed.stdout)

    def test_declared_dominant_option_fails(self) -> None:
        model = self.load_template()
        model["budgets"]["max_single_option_pick_share"] = "0.60"
        completed = self.run_model(model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("option route_b pick share", completed.stdout)


class DifficultyPacingTests(unittest.TestCase):
    @staticmethod
    def load_template() -> dict[str, object]:
        return load_asset_json("difficulty-pacing-contract.template.json")

    def run_contract(self, contract: dict[str, object]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "difficulty-pacing.json"
            path.write_text(json.dumps(contract), encoding="utf-8")
            return run_script(
                "difficulty_pacing_probe.py", "--contract", str(path), "--summary"
            )

    def test_template_passes(self) -> None:
        completed = run_script(
            "difficulty_pacing_probe.py",
            "--contract",
            str(ROOT / "assets" / "difficulty-pacing-contract.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS]", completed.stdout)

    def test_monotonic_wave_without_relief_fails(self) -> None:
        contract = self.load_template()
        for index, beat in enumerate(contract["beats"]):
            beat["challenge"] = index * 0.5 + 1
        contract["budgets"]["max_consecutive_challenge_rises"] = 10
        completed = self.run_contract(contract)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("requires at least one challenge decrease", completed.stdout)

    def test_puzzle_without_learned_skill_combination_fails(self) -> None:
        contract = self.load_template()
        contract["contract"]["genre_profile"] = "puzzle"
        contract["contract"]["curve_model"] = "puzzle_mastery"
        contract["beats"][3]["uses_skills"] = ["dodge"]
        completed = self.run_contract(contract)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("combine beat using at least two learned skills", completed.stdout)

    def test_competitive_hidden_midmatch_adjustment_fails(self) -> None:
        contract = self.load_template()
        contract["contract"]["genre_profile"] = "competitive_multiplayer"
        contract["contract"]["curve_model"] = "skill_bands"
        contract["adaptation"]["ranked_midmatch_outcome_manipulation"] = True
        completed = self.run_contract(contract)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("requires matchmaking", completed.stdout)
        self.assertIn("ranked mid-match outcome manipulation must be false", completed.stdout)

    def test_extraction_self_selected_routes_can_pass(self) -> None:
        contract = self.load_template()
        contract["contract"]["genre_profile"] = "extraction_survival"
        contract["contract"]["curve_model"] = "self_selected_routes"
        contract["contract"]["required_phases"] = [
            "teach", "choice", "combine", "peak", "recovery", "test"
        ]
        contract["beats"][1]["phase"] = "choice"
        contract["beats"][1]["branch_id"] = "safe_route"
        contract["beats"][3]["branch_id"] = "risky_route"
        completed = self.run_contract(contract)
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS]", completed.stdout)


class NetworkContractTests(unittest.TestCase):
    @staticmethod
    def load_template() -> dict[str, object]:
        return json.loads(
            (ROOT / "assets" / "network-contract.template.json").read_text(
                encoding="utf-8"
            )
        )

    def run_model(self, model: dict[str, object]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "network-contract.json"
            path.write_text(json.dumps(model), encoding="utf-8")
            return run_script("network_contract_probe.py", "--model", str(path), "--summary")

    def test_template_passes(self) -> None:
        completed = run_script(
            "network_contract_probe.py",
            "--model",
            str(ROOT / "assets" / "network-contract.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS]", completed.stdout)

    def test_client_authoritative_rpc_fails(self) -> None:
        model = self.load_template()
        model["rpc_surfaces"][0]["authority"] = "client"
        completed = self.run_model(model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("not server-authoritative", completed.stdout)

    def test_accepted_hostile_request_fails(self) -> None:
        model = self.load_template()
        hostile = next(
            trace for trace in model["traces"] if trace["scenario"] == "hostile_input"
        )
        hostile["invalid_requests_accepted"] = 1
        completed = self.run_model(model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("accepted 1 invalid request(s)", completed.stdout)

    def test_web_target_with_enet_fails(self) -> None:
        model = self.load_template()
        model["architecture"]["target_platforms"].append("web")
        completed = self.run_model(model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("Web target cannot use declared transport enet", completed.stdout)


class ExtractionLoopTests(unittest.TestCase):
    @staticmethod
    def load_template() -> dict[str, object]:
        return json.loads(
            (ROOT / "assets" / "extraction-loop.template.json").read_text(
                encoding="utf-8"
            )
        )

    def run_model(self, model: dict[str, object]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "extraction-loop.json"
            path.write_text(json.dumps(model), encoding="utf-8")
            return run_script("extraction_loop_probe.py", "--model", str(path), "--summary")

    def test_template_passes(self) -> None:
        completed = run_script(
            "extraction_loop_probe.py",
            "--model",
            str(ROOT / "assets" / "extraction-loop.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS]", completed.stdout)

    def test_stash_ledger_mismatch_fails(self) -> None:
        model = self.load_template()
        model["traces"][0]["stash_after"] = "999"
        completed = self.run_model(model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("stash ledger mismatch", completed.stdout)

    def test_death_loot_beyond_secure_capacity_fails(self) -> None:
        model = self.load_template()
        death = next(trace for trace in model["traces"] if trace["scenario"] == "death")
        death["persisted_loot_value"] = "20"
        death["stash_after"] = "93"
        completed = self.run_model(model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("death persists loot beyond secure capacity", completed.stdout)

    def test_duplicate_reconnect_settlement_fails(self) -> None:
        model = self.load_template()
        reconnect = next(
            trace for trace in model["traces"] if trace["scenario"] == "reconnect_settlement"
        )
        reconnect["settlement_applications"] = 2
        completed = self.run_model(model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("settlement applied 2 times", completed.stdout)


class SaveDataContractTests(unittest.TestCase):
    def test_template_passes(self) -> None:
        completed = run_script(
            "save_data_probe.py",
            "--model",
            str(ROOT / "assets" / "save-data-contract.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] save-data", completed.stdout)

    def test_digest_mismatch_fails(self) -> None:
        model = load_asset_json("save-data-contract.template.json")
        model["traces"][1]["actual_digest"] = "wrong-state"
        completed = run_contract("save_data_probe.py", model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("round-trip digest mismatch", completed.stdout)

    def test_missing_supported_migration_fails(self) -> None:
        model = load_asset_json("save-data-contract.template.json")
        model["traces"] = [
            trace
            for trace in model["traces"]
            if not (trace["scenario"] == "migration" and trace["source_version"] == 1)
        ]
        completed = run_contract("save_data_probe.py", model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("missing migration traces from versions: 1", completed.stdout)


class AINavigationContractTests(unittest.TestCase):
    def test_template_passes(self) -> None:
        completed = run_script(
            "ai_navigation_probe.py",
            "--model",
            str(ROOT / "assets" / "ai-navigation-contract.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] ai-navigation", completed.stdout)

    def test_forbidden_information_fails(self) -> None:
        model = load_asset_json("ai-navigation-contract.template.json")
        model["traces"][0]["forbidden_information_read"] = ["raw_player_input"]
        completed = run_contract("ai_navigation_probe.py", model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("reads forbidden information: raw_player_input", completed.stdout)

    def test_unreachable_target_without_recovery_fails(self) -> None:
        model = load_asset_json("ai-navigation-contract.template.json")
        trace = next(
            trace for trace in model["traces"] if trace["scenario"] == "unreachable_target"
        )
        trace["unreachable_handled"] = False
        completed = run_contract("ai_navigation_probe.py", model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("does not handle unreachable target", completed.stdout)


class ProceduralGenerationContractTests(unittest.TestCase):
    def test_template_passes(self) -> None:
        completed = run_script(
            "procedural_generation_probe.py",
            "--model",
            str(ROOT / "assets" / "procedural-generation-contract.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] procedural-generation", completed.stdout)

    def test_same_seed_nondeterminism_fails(self) -> None:
        model = load_asset_json("procedural-generation-contract.template.json")
        model["seed_traces"][1]["layout_hash"] = "changed-layout"
        completed = run_contract("procedural_generation_probe.py", model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("seed 101 is not deterministic", completed.stdout)

    def test_disconnected_seed_fails(self) -> None:
        model = load_asset_json("procedural-generation-contract.template.json")
        model["seed_traces"][2]["start_exit_connected"] = False
        completed = run_contract("procedural_generation_probe.py", model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("has disconnected start and exit", completed.stdout)


class InputAccessibilityContractTests(unittest.TestCase):
    def test_template_passes(self) -> None:
        completed = run_script(
            "input_accessibility_probe.py",
            "--model",
            str(ROOT / "assets" / "input-accessibility-contract.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] input-accessibility", completed.stdout)

    def test_missing_device_binding_fails(self) -> None:
        model = load_asset_json("input-accessibility-contract.template.json")
        model["contract"]["bindings"][0]["devices"] = ["keyboard_mouse"]
        completed = run_contract("input_accessibility_probe.py", model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("critical action move misses devices: gamepad", completed.stdout)

    def test_cross_player_input_leak_fails(self) -> None:
        model = load_asset_json("input-accessibility-contract.template.json")
        trace = next(
            trace for trace in model["traces"] if trace["scenario"] == "local_join_leave"
        )
        trace["cross_player_actions"] = 1
        completed = run_contract("input_accessibility_probe.py", model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("leaks actions across players", completed.stdout)


class LocalizationContractTests(unittest.TestCase):
    def test_template_passes(self) -> None:
        completed = run_script(
            "localization_probe.py",
            "--model",
            str(ROOT / "assets" / "localization-contract.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] localization", completed.stdout)

    def test_overflow_fails(self) -> None:
        model = load_asset_json("localization-contract.template.json")
        model["traces"][1]["overflow_controls"] = 1
        completed = run_contract("localization_probe.py", model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("exceeds overflow budget", completed.stdout)

    def test_stale_runtime_switch_fails(self) -> None:
        model = load_asset_json("localization-contract.template.json")
        trace = next(item for item in model["traces"] if item["scenario"] == "runtime_switch")
        trace["cached_text_invalidated"] = False
        completed = run_contract("localization_probe.py", model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("leaves stale cached text", completed.stdout)


class ReproducibleBuildContractTests(unittest.TestCase):
    def test_template_passes(self) -> None:
        completed = run_script(
            "reproducible_build_probe.py",
            "--model",
            str(ROOT / "assets" / "reproducible-build-contract.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] reproducible-build", completed.stdout)

    def test_warm_checkout_fails(self) -> None:
        model = load_asset_json("reproducible-build-contract.template.json")
        model["builds"][0]["clean_checkout"] = False
        completed = run_contract("reproducible_build_probe.py", model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("not from a clean checkout", completed.stdout)

    def test_artifact_drift_fails(self) -> None:
        model = load_asset_json("reproducible-build-contract.template.json")
        model["builds"][1]["normalized_hash"] = "different"
        completed = run_contract("reproducible_build_probe.py", model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("normalized outputs differ", completed.stdout)


class ReplayContractTests(unittest.TestCase):
    def test_template_passes(self) -> None:
        completed = run_script(
            "replay_probe.py",
            "--model",
            str(ROOT / "assets" / "replay-contract.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] replay", completed.stdout)

    def test_digest_divergence_fails(self) -> None:
        model = load_asset_json("replay-contract.template.json")
        model["traces"][0]["actual_digest"] = "different"
        completed = run_contract("replay_probe.py", model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("state digest diverges", completed.stdout)

    def test_colliding_ghost_fails(self) -> None:
        model = load_asset_json("replay-contract.template.json")
        trace = next(item for item in model["traces"] if item["scenario"] == "ghost_isolation")
        trace["ghost_collision_events"] = 1
        completed = run_contract("replay_probe.py", model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("ghost affects collision", completed.stdout)


class LiveOpsContractTests(unittest.TestCase):
    def test_template_passes(self) -> None:
        completed = run_script(
            "liveops_probe.py",
            "--model",
            str(ROOT / "assets" / "liveops-contract.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] liveops", completed.stdout)

    def test_forbidden_telemetry_field_fails(self) -> None:
        model = load_asset_json("liveops-contract.template.json")
        model["traces"][0]["forbidden_fields_sent"] = ["payment_token"]
        completed = run_contract("liveops_probe.py", model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("sends forbidden fields", completed.stdout)

    def test_non_idempotent_retry_fails(self) -> None:
        model = load_asset_json("liveops-contract.template.json")
        trace = next(item for item in model["traces"] if item["scenario"] == "duplicate_retry")
        trace["idempotent_event_ids"] = False
        completed = run_contract("liveops_probe.py", model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("retry is not idempotent", completed.stdout)


class ProductionModifierContractTests(unittest.TestCase):
    CONTRACTS = {
        "crash": ("crash_resilience_probe.py", "crash-resilience-contract.template.json"),
        "commerce": ("commerce_entitlement_probe.py", "commerce-entitlement-contract.template.json"),
        "account": ("account_cloud_probe.py", "account-cloud-contract.template.json"),
        "safety": ("online_safety_probe.py", "online-safety-contract.template.json"),
        "upgrade": ("upgrade_compatibility_probe.py", "upgrade-compatibility-contract.template.json"),
        "fault": ("fault_injection_probe.py", "fault-injection-contract.template.json"),
        "desktop": ("desktop_hardware_probe.py", "desktop-hardware-contract.template.json"),
        "assistive": ("assistive_accessibility_probe.py", "assistive-accessibility-contract.template.json"),
    }

    def test_all_templates_pass(self) -> None:
        for label, (script, template) in self.CONTRACTS.items():
            with self.subTest(contract=label):
                completed = run_script(
                    script, "--model", str(ROOT / "assets" / template), "--summary"
                )
                self.assertEqual(completed.returncode, 0, completed.stdout)
                self.assertIn("[PASS]", completed.stdout)

    def test_each_contract_rejects_an_invariant_failure(self) -> None:
        mutations = {
            "crash": (0, "recovered", False, "does not prove recovered"),
            "commerce": (1, "grant_count", 2, "not exactly-once"),
            "account": (0, "silent_overwrites", 1, "non-zero silent_overwrites"),
            "safety": (0, "client_can_ban", True, "sanction authority"),
            "upgrade": (0, "data_loss_records", 1, "loses records"),
            "fault": (0, "hangs", 1, "non-zero hangs"),
            "desktop": (0, "minimum_observed_fps", 1, "below FPS budget"),
            "assistive": (0, "focus_traps", 1, "non-zero focus_traps"),
        }
        for label, (script, template) in self.CONTRACTS.items():
            with self.subTest(contract=label):
                model = load_asset_json(template)
                index, key, value, message = mutations[label]
                model["traces"][index][key] = value
                completed = run_contract(script, model)
                self.assertEqual(completed.returncode, 1, completed.stdout)
                self.assertIn(message, completed.stdout)

    def test_each_contract_rejects_missing_required_coverage(self) -> None:
        for label, (script, template) in self.CONTRACTS.items():
            with self.subTest(contract=label):
                model = load_asset_json(template)
                missing = model["contract"]["required_scenarios"][-1]
                model["traces"] = [
                    trace for trace in model["traces"] if trace["scenario"] != missing
                ]
                completed = run_contract(script, model)
                self.assertEqual(completed.returncode, 1, completed.stdout)
                self.assertIn(missing, completed.stdout)


class ForwardEvaluationAuditTests(unittest.TestCase):
    def run_matrix(self, model: dict[str, object]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "matrix.json"
            path.write_text(json.dumps(model), encoding="utf-8")
            return run_script("forward_eval_audit.py", "--matrix", str(path), "--summary")

    def valid_matrix(self) -> dict[str, object]:
        base = {
            "brief_path": "briefs/scenario.md",
            "godot_version": "4.7.2-stable",
            "composite_case": "new-shooter-action-complete+localized-release-complete",
            "contracts": ["shooter"],
            "builder_context": "isolated builder task",
            "reviewer_context": "separate raw reviewer task",
            "first_pass_verdict": "pass",
            "user_found_defects": [],
            "expected_gate_for_each_defect": {},
            "false_positive_burden": "none observed in isolated control case",
            "token_cost": 1000,
            "elapsed_minutes": 10,
            "result_artifacts": ["reports/raw.mp4"],
        }
        positive = {**base, "id": "shooter-positive", "positive_fixture": True, "negative_fixture": False}
        negative = {
            **base,
            "id": "shooter-negative",
            "first_pass_verdict": "fail",
            "positive_fixture": False,
            "negative_fixture": True,
            "user_found_defects": ["missing recoil"],
            "expected_gate_for_each_defect": {"missing recoil": "shooter_combat_playtest"},
        }
        positive_two = {**positive, "id": "shooter-positive-2"}
        negative_two = {**negative, "id": "shooter-negative-2"}
        return {
            "schema_version": 1,
            "skill_commit": "abcdef1234567890",
            "required_contracts": ["shooter"],
            "scenarios": [positive, negative, positive_two, negative_two],
        }

    def test_positive_and_negative_coverage_passes(self) -> None:
        completed = self.run_matrix(self.valid_matrix())
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] forward-eval", completed.stdout)

    def test_missing_negative_fixture_fails(self) -> None:
        model = self.valid_matrix()
        model["scenarios"] = model["scenarios"][:1]
        completed = self.run_matrix(model)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("lacks a negative fixture", completed.stdout)

    def test_art_direction_selection_has_isolated_positive_and_negative_fixtures(self) -> None:
        completed = run_script(
            "forward_eval_audit.py",
            "--matrix",
            str(ROOT / "tests" / "fixtures" / "art-direction-forward-eval.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] forward-eval", completed.stdout)

    def test_ui_onboarding_and_progression_have_positive_and_negative_fixtures(self) -> None:
        completed = run_script(
            "forward_eval_audit.py",
            "--matrix",
            str(ROOT / "tests" / "fixtures" / "ui-onboarding-progression-forward-eval.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] forward-eval", completed.stdout)

    def test_product_craft_and_closure_have_positive_and_negative_fixtures(self) -> None:
        completed = run_script(
            "forward_eval_audit.py",
            "--matrix",
            str(ROOT / "tests" / "fixtures" / "product-craft-closure-forward-eval.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] forward-eval", completed.stdout)

    def test_high_angle_district_and_camera_have_positive_and_negative_fixtures(self) -> None:
        completed = run_script(
            "forward_eval_audit.py",
            "--matrix",
            str(ROOT / "tests" / "fixtures" / "high-angle-district-forward-eval.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] forward-eval", completed.stdout)

    def test_environment_integrity_template_passes(self) -> None:
        completed = run_script(
            "environment_integrity_audit.py",
            "--model",
            str(ROOT / "assets" / "environment-integrity-contract.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] environment-integrity", completed.stdout)

    def test_environment_integrity_rejects_visual_fail_after_collision_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "environment-integrity.json"
            completed = run_script(
                "environment_integrity_audit.py",
                "--model",
                str(ROOT / "tests" / "fixtures" / "environment-integrity-negative.json"),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(
            report["prior_structural_checks"],
            {
                "collision_coverage": "164/164",
                "boundary_coverage": "180/180",
                "collision_alignment_pass": True,
            },
        )
        errors = "\n".join(report["errors"])
        self.assertIn("unintentional transformed-volume overlap", errors)
        self.assertIn("semantic surface ownership failed", errors)
        self.assertIn("render-ground coverage/seam failure", errors)
        self.assertIn("vertical clearance", errors)

    def test_environment_coverage_template_passes(self) -> None:
        completed = run_script(
            "environment_coverage_audit.py",
            "--model",
            str(ROOT / "assets" / "environment-coverage-contract.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] environment-coverage", completed.stdout)

    def test_environment_coverage_rejects_curated_pass_whole_map_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "environment-coverage.json"
            completed = run_script(
                "environment_coverage_audit.py",
                "--model",
                str(ROOT / "tests" / "fixtures" / "environment-coverage-negative.json"),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(report["survey_uncovered_cell_count"], 5)
        self.assertGreater(report["invisible_blocked_sample_count"], 0)
        errors = "\n".join(report["errors"])
        self.assertIn("mixes semantic families", errors)
        self.assertIn("fallback exposure ratio", errors)
        self.assertIn("shipping-camera tiled survey", errors)
        self.assertIn("visible-shell overlap ratio", errors)
        self.assertIn("production occluder aliases miss collision roots", errors)
        self.assertIn("surface/object pair", errors)

    def test_environment_coverage_requires_every_observed_adjacency_rule(self) -> None:
        source = json.loads(
            (ROOT / "assets" / "environment-coverage-contract.template.json").read_text(
                encoding="utf-8"
            )
        )
        source["surface_adjacency_rules"] = source["surface_adjacency_rules"][:1]
        with tempfile.TemporaryDirectory() as directory:
            model_path = Path(directory) / "missing-adjacency.json"
            model_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "environment_coverage_audit.py",
                "--model",
                str(model_path),
                "--summary",
            )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("lacks an authored transition/cause rule", completed.stdout)

    def test_streetscape_semantics_template_passes(self) -> None:
        completed = run_script(
            "streetscape_semantics_audit.py",
            "--model",
            str(ROOT / "assets" / "streetscape-semantics-contract.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] streetscape-semantics", completed.stdout)

    def test_streetscape_semantics_rejects_old_geometry_pass_candidate(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "streetscape-semantics-old-clinic-negative.json"
        source = json.loads(fixture.read_text(encoding="utf-8"))
        self.assertEqual(
            source["prior_geometry_gates"],
            {
                "resolved_scene_provenance": "pass",
                "environment_integrity_audit": "pass",
                "environment_coverage_audit": "pass",
            },
        )
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "streetscape.json"
            completed = run_script(
                "streetscape_semantics_audit.py",
                "--model",
                str(fixture),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(completed.returncode, 1, completed.stdout)
        errors = "\n".join(report["errors"])
        self.assertIn("does not connect two known sidewalk nodes", errors)
        self.assertIn("disconnected gap", errors)
        self.assertIn("road-building forbidden-surface ratio", errors)
        self.assertIn("hydrant-in-lane forbidden-surface ratio", errors)
        self.assertIn("misoriented-signal orientation", errors)
        self.assertIn("without an authored incident closure", errors)
        self.assertIn("materialized visible-area ratio", errors)
        self.assertIn("reachable pocket/contact", errors)
        self.assertIn("shipping-camera road survey misses junctions", errors)

    def test_resolved_scene_provenance_template_passes(self) -> None:
        completed = run_script(
            "resolved_scene_provenance_audit.py",
            "--manifest",
            str(ROOT / "assets" / "resolved-scene-provenance.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] resolved-scene-provenance", completed.stdout)

    def test_resolved_scene_provenance_links_environment_and_streetscape_contracts(self) -> None:
        completed = run_script(
            "resolved_scene_provenance_audit.py",
            "--manifest",
            str(ROOT / "assets" / "resolved-scene-provenance.template.json"),
            "--evidence-contract",
            str(ROOT / "assets" / "environment-integrity-contract.template.json"),
            "--evidence-contract",
            str(ROOT / "assets" / "environment-coverage-contract.template.json"),
            "--evidence-contract",
            str(ROOT / "assets" / "streetscape-semantics-contract.template.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] resolved-scene-provenance", completed.stdout)

    def test_resolved_scene_provenance_rejects_mismatched_evidence_contract(self) -> None:
        contract = load_asset_json("environment-integrity-contract.template.json")
        contract["scene_provenance"]["dependency_closure_digest"] = "f" * 64
        with tempfile.TemporaryDirectory() as directory:
            contract_path = Path(directory) / "mismatched-contract.json"
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            completed = run_script(
                "resolved_scene_provenance_audit.py",
                "--manifest",
                str(ROOT / "assets" / "resolved-scene-provenance.template.json"),
                "--evidence-contract",
                str(contract_path),
                "--summary",
            )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("dependency_closure_digest does not match", completed.stdout)

    def test_resolved_scene_provenance_rejects_root_only_digest(self) -> None:
        completed = run_script(
            "resolved_scene_provenance_audit.py",
            "--manifest",
            str(
                ROOT
                / "tests"
                / "fixtures"
                / "resolved-scene-provenance-root-only-negative.json"
            ),
            "--summary",
        )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("root-file-only digest is invalid", completed.stdout)
        self.assertIn("dependency closure entries are missing", completed.stdout)

    def test_nested_dependency_mutation_changes_closure_with_same_root_hash(self) -> None:
        baseline_path = (
            ROOT / "tests" / "fixtures" / "resolved-scene-provenance-v18.json"
        )
        candidate_path = (
            ROOT / "tests" / "fixtures" / "resolved-scene-provenance-v19.json"
        )
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "provenance-comparison.json"
            completed = run_script(
                "resolved_scene_provenance_audit.py",
                "--manifest",
                str(candidate_path),
                "--baseline",
                str(baseline_path),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(completed.returncode, 0, completed.stdout)
        comparison = report["baseline_comparison"]
        self.assertTrue(comparison["root_scene_sha256_same"])
        self.assertFalse(comparison["dependency_closure_digest_same"])
        self.assertTrue(comparison["candidate_content_changed_beyond_root"])

    def test_nested_dependency_mutation_rejects_stale_closure_digest(self) -> None:
        completed = run_script(
            "resolved_scene_provenance_audit.py",
            "--manifest",
            str(
                ROOT
                / "tests"
                / "fixtures"
                / "resolved-scene-provenance-v19-stale-negative.json"
            ),
            "--baseline",
            str(ROOT / "tests" / "fixtures" / "resolved-scene-provenance-v18.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("closure_digest mismatch", completed.stdout)

    def test_project_verification_detects_dependency_file_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            files = {
                "project.godot": "[application]\nconfig/name=\"Fixture\"\n",
                "export_presets.cfg": "[preset.0]\nname=\"Windows Desktop\"\n",
                "root.tscn": "[gd_scene format=3]\n[node name=\"Root\" type=\"Node\"]\n",
                "nested.tres": "[gd_resource type=\"Resource\" format=3]\n[resource]\n",
                "exporter.gd": "extends SceneTree\n",
            }
            for relative, content in files.items():
                (project / relative).write_text(content, encoding="utf-8")

            def record(relative: str, kind: str, role: str | None = None) -> dict[str, object]:
                path = project / relative
                item: dict[str, object] = {
                    "path": f"res://{relative}",
                    "bytes": path.stat().st_size,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
                item["role" if role else "kind"] = role or kind
                return item

            manifest = {
                "schema_version": 1,
                "manifest_id": "filesystem-verification-fixture",
                "build_id": "fixture-v1",
                "source_kind": "resolved_target_scene",
                "root_scene": "res://root.tscn",
                "engine_version": "4.x",
                "export_preset_selector": "Windows Desktop",
                "dependency_discovery": {
                    "method": "godot_resource_loader_recursive",
                    "direct_dependencies": ["res://nested.tres"],
                    "recursive_dependencies": ["res://nested.tres"],
                    "runtime_dependency_paths": [],
                    "declared_dependency_count": 1,
                },
                "entries": [
                    record("nested.tres", "resource"),
                    record("root.tscn", "root_scene"),
                ],
                "toolchain_inputs": [
                    record("export_presets.cfg", "", "export_presets"),
                    record("exporter.gd", "", "exporter_script"),
                    record("project.godot", "", "project_settings"),
                ],
                "closure_digest": "0" * 64,
            }
            manifest_path = project / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            digest_run = run_script(
                "resolved_scene_provenance_audit.py",
                "--manifest",
                str(manifest_path),
                "--print-computed-digest",
            )
            manifest["closure_digest"] = digest_run.stdout.splitlines()[0]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            passing = run_script(
                "resolved_scene_provenance_audit.py",
                "--manifest",
                str(manifest_path),
                "--project",
                str(project),
                "--summary",
            )
            (project / "nested.tres").write_text("mutated nested dependency", encoding="utf-8")
            failing = run_script(
                "resolved_scene_provenance_audit.py",
                "--manifest",
                str(manifest_path),
                "--project",
                str(project),
                "--summary",
            )
        self.assertEqual(passing.returncode, 0, passing.stdout)
        self.assertEqual(failing.returncode, 1, failing.stdout)
        self.assertIn("file SHA-256 mismatch for res://nested.tres", failing.stdout)

    def test_environment_audits_reject_legacy_root_scene_revision(self) -> None:
        for asset_name, script_name in (
            ("environment-integrity-contract.template.json", "environment_integrity_audit.py"),
            ("environment-coverage-contract.template.json", "environment_coverage_audit.py"),
            ("streetscape-semantics-contract.template.json", "streetscape_semantics_audit.py"),
        ):
            model = load_asset_json(asset_name)
            provenance = model["scene_provenance"]
            provenance.clear()
            provenance.update(
                {
                    "source_kind": "resolved_target_scene",
                    "scene_path": "res://scenes/world/example_district.tscn",
                    "scene_revision": "root-file-sha256-only",
                    "exporter": "res://tests/legacy_exporter.gd",
                }
            )
            completed = run_contract(script_name, model)
            self.assertEqual(completed.returncode, 2, completed.stdout)
            self.assertIn("root-file provenance", completed.stdout)


class GenreRubricTests(unittest.TestCase):
    def test_rubric_case_and_score_cap_references_are_closed(self) -> None:
        rubric = json.loads((ROOT / "evals" / "rubric.json").read_text(encoding="utf-8"))
        cases = {item["id"] for item in rubric["cases"]}
        gates = {item["id"] for item in rubric["blocking_gates"]}
        for gate in rubric["blocking_gates"]:
            self.assertTrue(set(gate.get("cases", [])) <= cases, gate["id"])
        for cap in rubric["score_caps"]:
            self.assertIn(cap["gate"], gates)

    def test_new_cases_prepare_their_conditional_gates(self) -> None:
        expected = {
            "new-2d-fighting-complete": "fighting_simulation_evidence",
            "new-2d-metroidvania-complete": "metroidvania_progression_evidence",
            "new-idle-clicker-complete": "idle_economy_evidence",
            "new-quest-driven-complete": "quest_transaction_evidence",
            "new-progression-heavy-complete": "progression_balance_model_evidence",
            "difficulty-pacing-complete": "difficulty_pacing_evidence",
            "new-networked-multiplayer-complete": "network_contract_evidence",
            "new-extraction-complete": "extraction_loop_evidence",
            "new-online-extraction-complete": "network_contract_evidence",
            "new-mmo-production-slice": "online_service_readiness_evidence",
            "new-procedural-roguelike-complete": "procedural_generation_evidence",
            "new-strategy-simulation-complete": "strategy_simulation_evidence",
            "new-vehicle-racing-complete": "vehicle_racing_evidence",
            "new-shooter-action-complete": "shooter_combat_evidence",
            "new-narrative-complete": "narrative_flow_evidence",
            "new-local-multiplayer-complete": "local_multiplayer_input_evidence",
            "multi-platform-store-release": "platform_release_evidence",
            "modding-ugc-production-slice": "modding_ugc_evidence",
            "localized-release-complete": "localization_contract_evidence",
            "reproducible-release-pipeline": "reproducible_build_evidence",
            "replay-ghost-spectator-complete": "replay_contract_evidence",
            "large-world-streaming-complete": "large_world_streaming_evidence",
            "mobile-native-release": "mobile_native_evidence",
            "liveops-production-slice": "liveops_contract_evidence",
            "xr-production-slice": "xr_runtime_evidence",
            "console-release-readiness": "console_release_evidence",
            "runtime-authoring-tools-complete": "runtime_authoring_evidence",
            "crash-resilience-production": "crash_resilience_evidence",
            "commerce-entitlement-production": "commerce_entitlement_evidence",
            "account-cloud-cross-progression": "account_cloud_evidence",
            "online-safety-production": "online_safety_evidence",
            "upgrade-compatibility-release": "upgrade_compatibility_evidence",
            "fault-injection-hardening": "fault_injection_evidence",
            "desktop-hardware-release": "desktop_hardware_evidence",
            "assistive-accessibility-release": "assistive_accessibility_evidence",
            "new-2-5d-complete": "production_art_integrity_evidence",
            "new-isometric-fixed-camera-complete": "isometric_vertical_slice_art_review",
            "high-angle-3d-district-complete": "high_angle_3d_district_composition_evidence",
            "ui-reference-integration": "reference_parity_evidence",
        }
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            for case_id, gate_id in expected.items():
                output = temp / f"{case_id}.json"
                completed = run_script(
                    "evidence_helper.py",
                    "--rubric",
                    str(ROOT / "evals" / "rubric.json"),
                    "--case",
                    case_id,
                    "--output",
                    str(output),
                )
                self.assertEqual(completed.returncode, 0, completed.stdout)
                evidence = json.loads(output.read_text(encoding="utf-8"))
                self.assertIn(gate_id, evidence["gates"])

    def test_high_angle_district_scaffold_instantiates_builder_gate_and_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            completed = run_script(
                "evidence_helper.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "new-extraction-complete+high-angle-3d-district-complete",
                "--output",
                str(temp / "evidence.json"),
                "--high-angle-district-review-output",
                str(temp / "high-angle-district-review.md"),
                "--environment-integrity-review-output",
                str(temp / "environment-integrity-review.md"),
                "--streetscape-semantics-review-output",
                str(temp / "streetscape-semantics-review.md"),
                "--resolved-scene-provenance-output",
                str(temp / "resolved-scene-provenance.json"),
            )
            evidence = json.loads((temp / "evidence.json").read_text(encoding="utf-8"))
            review = (temp / "high-angle-district-review.md").read_text(encoding="utf-8")
            integrity_review = (temp / "environment-integrity-review.md").read_text(encoding="utf-8")
            streetscape_review = (temp / "streetscape-semantics-review.md").read_text(encoding="utf-8")
            provenance = json.loads(
                (temp / "resolved-scene-provenance.json").read_text(encoding="utf-8")
            )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(
            evidence["gates"]["high_angle_3d_district_composition_evidence"]["reviewer"]["role"],
            "builder",
        )
        self.assertIn("Fixed/High-angle 3D District Review", review)
        self.assertEqual(
            evidence["gates"]["high_angle_environment_integrity_evidence"]["reviewer"]["role"],
            "builder",
        )
        self.assertIn("High-angle 3D Environment Integrity Review", integrity_review)
        self.assertEqual(
            evidence["gates"]["high_angle_streetscape_semantics_evidence"]["reviewer"]["role"],
            "builder",
        )
        self.assertIn("High-angle Road and Streetscape Semantics Review", streetscape_review)
        self.assertEqual(provenance["source_kind"], "resolved_target_scene")
        self.assertGreater(len(provenance["entries"]), 1)

    def test_progression_scaffold_instantiates_model_and_human_gates_and_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            completed = run_script(
                "evidence_helper.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "new-progression-heavy-complete",
                "--output",
                str(temp / "evidence.json"),
                "--progression-balance-review-output",
                str(temp / "progression-review.md"),
            )
            evidence = json.loads((temp / "evidence.json").read_text(encoding="utf-8"))
            review = (temp / "progression-review.md").read_text(encoding="utf-8")
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(
            evidence["gates"]["progression_balance_model_evidence"]["reviewer"]["role"],
            "builder",
        )
        self.assertEqual(
            evidence["gates"]["progression_pacing_playtest"]["reviewer"]["role"],
            "human",
        )
        self.assertEqual(
            evidence["gates"]["progression_visual_comprehension_review"]["reviewer"]["role"],
            "independent",
        )
        self.assertIn("Progression and Balance Review", review)
        self.assertIn("Player-facing visual comprehension matrix", review)

    def test_difficulty_scaffold_instantiates_builder_and_human_gates_and_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            completed = run_script(
                "evidence_helper.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "difficulty-pacing-complete",
                "--output",
                str(temp / "evidence.json"),
                "--difficulty-pacing-review-output",
                str(temp / "difficulty-review.md"),
            )
            evidence = json.loads((temp / "evidence.json").read_text(encoding="utf-8"))
            review = (temp / "difficulty-review.md").read_text(encoding="utf-8")
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(
            evidence["gates"]["difficulty_pacing_evidence"]["reviewer"]["role"],
            "builder",
        )
        self.assertEqual(
            evidence["gates"]["difficulty_pacing_playtest"]["reviewer"]["role"],
            "human",
        )
        self.assertIn("Difficulty and Pacing Review", review)

    def test_online_scaffolds_instantiate_owners_and_reviews(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            completed = run_script(
                "evidence_helper.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "new-mmo-production-slice",
                "--output",
                str(temp / "evidence.json"),
                "--network-review-output",
                str(temp / "network-review.md"),
                "--online-service-review-output",
                str(temp / "service-review.md"),
            )
            evidence = json.loads((temp / "evidence.json").read_text(encoding="utf-8"))
            network_review = (temp / "network-review.md").read_text(encoding="utf-8")
            service_review = (temp / "service-review.md").read_text(encoding="utf-8")
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(
            evidence["gates"]["network_contract_evidence"]["reviewer"]["role"],
            "builder",
        )
        self.assertEqual(
            evidence["gates"]["network_multipeer_playtest"]["reviewer"]["role"],
            "human",
        )
        self.assertEqual(
            evidence["gates"]["online_service_architecture_review"]["reviewer"]["role"],
            "independent",
        )
        self.assertIn("Networked Multiplayer Review", network_review)
        self.assertIn("Online Service Readiness", service_review)

    def test_extraction_scaffold_instantiates_loop_and_human_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            completed = run_script(
                "evidence_helper.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "new-extraction-complete",
                "--output",
                str(temp / "evidence.json"),
                "--extraction-review-output",
                str(temp / "extraction-review.md"),
            )
            evidence = json.loads((temp / "evidence.json").read_text(encoding="utf-8"))
            review = (temp / "extraction-review.md").read_text(encoding="utf-8")
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(
            evidence["gates"]["extraction_loop_evidence"]["reviewer"]["role"],
            "builder",
        )
        self.assertEqual(
            evidence["gates"]["extraction_risk_pacing_playtest"]["reviewer"]["role"],
            "human",
        )
        self.assertIn("Extraction Loop Review", review)

    def test_2_5d_scaffold_instantiates_art_menu_hud_motion_and_run_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            completed = run_script(
                "evidence_helper.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "new-2-5d-complete",
                "--output",
                str(temp / "evidence.json"),
                "--menu-review-output",
                str(temp / "menu-review.md"),
                "--cross-surface-craft-review-output",
                str(temp / "cross-surface-review.md"),
                "--review-profile-reset-output",
                str(temp / "review-profile.md"),
                "--product-owner-slice-output",
                str(temp / "owner-slice.md"),
                "--hud-review-output",
                str(temp / "hud-review.md"),
                "--art-direction-selection-output",
                str(temp / "art-direction-selection.md"),
                "--project-status-output",
                str(temp / "project-run-state.md"),
                "--production-art-review-output",
                str(temp / "production-art-review.md"),
                "--motion-review-output",
                str(temp / "motion-review.md"),
            )
            evidence = json.loads((temp / "evidence.json").read_text(encoding="utf-8"))
            menu = (temp / "menu-review.md").read_text(encoding="utf-8")
            cross_surface = (temp / "cross-surface-review.md").read_text(encoding="utf-8")
            review_profile = (temp / "review-profile.md").read_text(encoding="utf-8")
            owner_slice = (temp / "owner-slice.md").read_text(encoding="utf-8")
            hud = (temp / "hud-review.md").read_text(encoding="utf-8")
            direction = (temp / "art-direction-selection.md").read_text(encoding="utf-8")
            run_state = (temp / "project-run-state.md").read_text(encoding="utf-8")
            art = (temp / "production-art-review.md").read_text(encoding="utf-8")
            motion = (temp / "motion-review.md").read_text(encoding="utf-8")
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("menu_identity_craft_review", evidence["gates"])
        self.assertIn("production_art_integrity_evidence", evidence["gates"])
        self.assertIn("gameplay_hud_glanceability_review", evidence["gates"])
        self.assertIn("art_direction_selection_evidence", evidence["gates"])
        self.assertIn("cross_surface_production_craft_review", evidence["gates"])
        self.assertIn("critical_action_comprehension_review", evidence["gates"])
        self.assertIn("cross_family_art_coherence_review", evidence["gates"])
        self.assertIn("product_owner_slice_approval", evidence["gates"])
        self.assertEqual(
            evidence["gates"]["product_owner_slice_approval"]["reviewer"]["role"],
            "product_owner",
        )
        self.assertEqual(evidence["project_disposition"], {"status": "active"})
        self.assertIn("Menu Identity Craft Review", menu)
        self.assertIn("Cross-surface Production Craft Review", cross_surface)
        self.assertIn("Actual Review-modality Profile Reset", review_profile)
        self.assertIn("Product-owner Slice Decision", owner_slice)
        self.assertIn("Gameplay HUD Glanceability Review", hud)
        self.assertIn("Art Direction Selection Contract", direction)
        self.assertIn("Project Run State", run_state)
        self.assertIn("Production Art State Review", art)
        self.assertIn("Production Character Motion Contract", motion)

    def test_capture_manifest_includes_watched_delivery_proof_contract(self) -> None:
        manifest = json.loads(
            (ROOT / "assets" / "capture-manifest.template.json").read_text(encoding="utf-8")
        )
        proof = manifest["delivery_proof"]
        self.assertIn("not watched or played", proof["required_when"])
        self.assertIsNone(proof["builder_watched_back_entire_recording"])
        self.assertEqual(proof["result"], "not_tested")

    def test_extended_review_templates_are_scaffolded(self) -> None:
        flags = {
            "--save-review-output": ("save.md", "Save Data Integrity Review"),
            "--ai-review-output": ("ai.md", "AI and Navigation Review"),
            "--procedural-review-output": ("procedural.md", "Procedural Generation Review"),
            "--input-accessibility-review-output": (
                "input.md",
                "Input and Accessibility Review",
            ),
            "--strategy-review-output": ("strategy.md", "Strategy and Simulation Review"),
            "--vehicle-review-output": ("vehicle.md", "Vehicle and Racing Review"),
            "--shooter-review-output": ("shooter.md", "Shooter and Action Combat Review"),
            "--narrative-review-output": ("narrative.md", "Narrative and Cinematic Review"),
            "--platform-release-output": ("platform.md", "Platform and Store Release Matrix"),
            "--modding-review-output": ("modding.md", "Modding and UGC Review"),
            "--localization-review-output": (
                "localization.md",
                "Localization and Globalization Review",
            ),
            "--reproducible-build-review-output": (
                "reproducible.md",
                "Reproducible Build and Dependency Review",
            ),
            "--replay-review-output": ("replay.md", "Replay, Ghost, and Spectator Review"),
            "--large-world-review-output": ("large-world.md", "Large-world and Streaming Review"),
            "--mobile-native-review-output": ("mobile.md", "Mobile-native Production Review"),
            "--liveops-review-output": ("liveops.md", "LiveOps, Telemetry, and Privacy Review"),
            "--xr-console-review-output": ("xr-console.md", "XR and Console Review"),
            "--runtime-authoring-review-output": (
                "runtime-authoring.md",
                "Runtime Authoring Tool Review",
            ),
            "--crash-review-output": ("crash.md", "Crash Resilience and Diagnostics Review"),
            "--commerce-review-output": ("commerce.md", "Commerce and Entitlement Review"),
            "--account-cloud-review-output": ("account.md", "Account, Cloud, and Cross-progression Review"),
            "--online-safety-review-output": ("safety.md", "Online Safety and Anti-abuse Review"),
            "--upgrade-review-output": ("upgrade.md", "Upgrade Compatibility Review"),
            "--fault-review-output": ("fault.md", "Fault Injection and Fuzzing Review"),
            "--desktop-review-output": ("desktop.md", "Desktop Hardware and Display Review"),
            "--assistive-review-output": ("assistive.md", "Assistive Accessibility Review"),
            "--difficulty-pacing-review-output": (
                "difficulty.md",
                "Difficulty and Pacing Review",
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            arguments = [
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "new-procedural-roguelike-complete",
                "--output",
                str(temp / "evidence.json"),
            ]
            for flag, (name, _) in flags.items():
                arguments.extend([flag, str(temp / name)])
            completed = run_script("evidence_helper.py", *arguments)
            rendered = {
                name: (temp / name).read_text(encoding="utf-8")
                for name, _ in flags.values()
            }
        self.assertEqual(completed.returncode, 0, completed.stdout)
        for name, heading in flags.values():
            self.assertIn(heading, rendered[name])

    def test_hybrid_case_unions_gates_and_uses_maximum_score_floors(self) -> None:
        selector = (
            "new-shooter-action-complete+new-extraction-complete+"
            "localized-release-complete+fault-injection-hardening+difficulty-pacing-complete"
        )
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            evidence_path = temp / "evidence.json"
            plan_path = temp / "plan.json"
            prepared = run_script(
                "evidence_helper.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                selector,
                "--output",
                str(evidence_path),
            )
            planned = run_script(
                "rubric_case_plan.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                selector,
                "--json-output",
                str(plan_path),
                "--summary",
            )
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(prepared.returncode, 0, prepared.stdout)
        self.assertEqual(planned.returncode, 0, planned.stdout)
        self.assertIn("shooter_combat_evidence", evidence["gates"])
        self.assertIn("extraction_loop_evidence", evidence["gates"])
        self.assertIn("localization_contract_evidence", evidence["gates"])
        self.assertIn("fault_injection_evidence", evidence["gates"])
        self.assertIn("difficulty_pacing_evidence", evidence["gates"])
        self.assertEqual(plan["minimum_scores"]["playability_and_ux"], 3)
        self.assertEqual(len(plan["component_cases"]), 5)

    def test_device_human_gates_cap_unverified_scores(self) -> None:
        expected = {
            "mobile-native-release": ("mobile_device_playtest", 1),
            "xr-production-slice": ("xr_comfort_playtest", 1),
            "desktop-hardware-release": ("desktop_hardware_playtest", 2),
            "assistive-accessibility-release": ("assistive_accessibility_playtest", 1),
        }
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            for case_id, (human_gate, expected_cap) in expected.items():
                evidence_path = temp / f"{case_id}-evidence.json"
                scorecard_path = temp / f"{case_id}-scorecard.json"
                prepared = run_script(
                    "evidence_helper.py",
                    "--rubric",
                    str(ROOT / "evals" / "rubric.json"),
                    "--case",
                    case_id,
                    "--output",
                    str(evidence_path),
                )
                self.assertEqual(prepared.returncode, 0, prepared.stdout)
                evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
                for score in evidence["scores"].values():
                    score["score"] = 4
                    score["evidence"] = ["fixture: submitted maximum before unresolved caps"]
                evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
                scored = run_script(
                    "eval_scorecard.py",
                    "--rubric",
                    str(ROOT / "evals" / "rubric.json"),
                    "--case",
                    case_id,
                    "--evidence",
                    str(evidence_path),
                    "--json-output",
                    str(scorecard_path),
                    "--summary",
                )
                self.assertEqual(scored.returncode, 1, scored.stdout)
                report = json.loads(scorecard_path.read_text(encoding="utf-8"))
                self.assertEqual(report["verdict"], "blocked")
                self.assertTrue(
                    any(
                        item["gate"] == human_gate
                        and item["dimension"] == "playability_and_ux"
                        and item["after"] == expected_cap
                        for item in report["score_caps_applied"]
                    ),
                    report["score_caps_applied"],
                )


@unittest.skipUnless(importlib.util.find_spec("PIL"), "Pillow is not installed")
class ImageCompareTests(unittest.TestCase):
    def test_identical_capture_passes_zero_thresholds(self) -> None:
        source = ROOT / "tests" / "fixtures" / "valid_project" / "assets" / "sheet.png"
        with tempfile.TemporaryDirectory() as directory:
            completed = run_script(
                "image_compare.py",
                "--reference",
                str(source),
                "--actual",
                str(source),
                "--output-dir",
                directory,
                "--max-mean-error",
                "0",
                "--max-changed-ratio",
                "0",
                "--summary",
            )
            artifacts = {path.name for path in Path(directory).glob("*.png")}
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS]", completed.stdout)
        self.assertEqual(
            artifacts,
            {"side_by_side.png", "overlay_50.png", "diff_absolute.png", "diff_emphasized.png"},
        )

    def test_changed_capture_can_fail_gate(self) -> None:
        from PIL import Image

        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            reference = temp / "reference.png"
            actual = temp / "actual.png"
            Image.new("RGBA", (4, 4), (0, 0, 0, 255)).save(reference)
            Image.new("RGBA", (4, 4), (255, 255, 255, 255)).save(actual)
            completed = run_script(
                "image_compare.py",
                "--reference",
                str(reference),
                "--actual",
                str(actual),
                "--output-dir",
                str(temp / "artifacts"),
                "--max-changed-ratio",
                "0.1",
                "--summary",
            )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("[FAIL]", completed.stdout)


@unittest.skipUnless(importlib.util.find_spec("PIL"), "Pillow is not installed")
class IsometricReadabilityTests(unittest.TestCase):
    @staticmethod
    def make_capture(directory: Path, background: int, hero: int) -> tuple[Path, Path]:
        from PIL import Image, ImageDraw

        screenshot = directory / "frame.png"
        mask = directory / "hero-mask.png"
        frame_image = Image.new("RGB", (100, 100), (background, background, background))
        ImageDraw.Draw(frame_image).rectangle((40, 30, 59, 69), fill=(hero, hero, hero))
        frame_image.save(screenshot)
        mask_image = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        ImageDraw.Draw(mask_image).rectangle((40, 30, 59, 69), fill=(255, 255, 255, 255))
        mask_image.save(mask)
        return screenshot, mask

    def test_high_separation_same_frame_mask_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            screenshot, mask = self.make_capture(temp, background=20, hero=245)
            completed = run_script(
                "isometric_readability_audit.py",
                "--screenshot",
                str(screenshot),
                "--mask",
                str(mask),
                "--require-thresholds",
                "--min-mean-luminance-delta",
                "0.5",
                "--min-edge-luminance-delta",
                "0.5",
                "--min-bbox-height-ratio",
                "0.3",
                "--summary",
            )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("status=pass", completed.stdout)

    def test_white_on_white_character_fails_declared_budget(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            screenshot, mask = self.make_capture(temp, background=240, hero=250)
            completed = run_script(
                "isometric_readability_audit.py",
                "--screenshot",
                str(screenshot),
                "--mask",
                str(mask),
                "--require-thresholds",
                "--min-mean-luminance-delta",
                "0.2",
                "--min-edge-luminance-delta",
                "0.2",
                "--min-bbox-height-ratio",
                "0.3",
                "--summary",
            )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("status=fail", completed.stdout)


if __name__ == "__main__":
    unittest.main()
