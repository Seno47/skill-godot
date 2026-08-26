#!/usr/bin/env python3
"""Smoke tests for deterministic contracts and production workflow helpers."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
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
            "new-2-5d-complete": "production_art_integrity_evidence",
            "new-isometric-fixed-camera-complete": "isometric_vertical_slice_art_review",
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
        self.assertIn("Progression and Balance Review", review)

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
                "--hud-review-output",
                str(temp / "hud-review.md"),
                "--project-status-output",
                str(temp / "project-run-state.md"),
                "--production-art-review-output",
                str(temp / "production-art-review.md"),
                "--motion-review-output",
                str(temp / "motion-review.md"),
            )
            evidence = json.loads((temp / "evidence.json").read_text(encoding="utf-8"))
            menu = (temp / "menu-review.md").read_text(encoding="utf-8")
            hud = (temp / "hud-review.md").read_text(encoding="utf-8")
            run_state = (temp / "project-run-state.md").read_text(encoding="utf-8")
            art = (temp / "production-art-review.md").read_text(encoding="utf-8")
            motion = (temp / "motion-review.md").read_text(encoding="utf-8")
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("menu_identity_craft_review", evidence["gates"])
        self.assertIn("production_art_integrity_evidence", evidence["gates"])
        self.assertIn("gameplay_hud_glanceability_review", evidence["gates"])
        self.assertIn("Menu Identity Craft Review", menu)
        self.assertIn("Gameplay HUD Glanceability Review", hud)
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
