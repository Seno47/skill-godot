#!/usr/bin/env python3
"""Dependency-free smoke tests for the skill's deterministic Godot auditors."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "valid_project"
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


def load_script_module(name: str):
    path = SCRIPTS / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AuditorSmokeTests(unittest.TestCase):
    def assert_passes(self, completed: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS]", completed.stdout)

    def assert_fails(self, completed: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("[FAIL]", completed.stdout)

    def test_valid_fixture(self) -> None:
        self.assert_passes(
            run_script("scene_graph_audit.py", "--project", str(FIXTURE), "--summary")
        )
        self.assert_passes(
            run_script(
                "gltf_audit.py",
                "--project",
                str(FIXTURE),
                "--asset",
                "res://assets/empty.gltf",
                "--summary",
            )
        )
        self.assert_passes(
            run_script(
                "sprite_audit.py",
                "--project",
                str(FIXTURE),
                "--image",
                "res://assets/sheet.png",
                "--sheet",
                "res://assets/sheet.png=2x1",
                "--alpha-padding",
                "0",
                "--summary",
            )
        )

    def test_capture_command_dry_run(self) -> None:
        completed = run_script(
            "godot_capture.py",
            "--project",
            str(FIXTURE),
            "--mode",
            "capture",
            "--scene",
            "res://main.tscn",
            "--output",
            "reports/capture.avi",
            "--dry-run",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("--write-movie", completed.stdout)
        self.assertIn("--quit-after", completed.stdout)
        self.assertIn("--import", completed.stdout)
        self.assertIn("can create a large AVI", completed.stdout)

    def test_capture_classifies_forced_quit_leak_noise(self) -> None:
        module = load_script_module("godot_capture.py")
        completed = module.execute(
            [
                sys.executable,
                "-c",
                "print('WARNING: ObjectDB instances leaked at exit (run with --verbose for details).')",
            ],
            timeout=10,
            name="run",
            forced_quit=True,
        )
        self.assertFalse(completed["failed"])
        self.assertEqual(len(completed["forced_quit_diagnostic_lines"]), 1)
        self.assertEqual(completed["engine_error_lines"], [])

    def test_capture_script_command_dry_run(self) -> None:
        completed = run_script(
            "godot_capture.py",
            "--project",
            str(FIXTURE),
            "--mode",
            "run",
            "--headless",
            "--script",
            "res://tests/touch_scroll_probe.gd",
            "--user-arg",
            "scene=res://main.tscn",
            "--user-arg",
            "target=Scroll",
            "--dry-run",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("--script res://tests/touch_scroll_probe.gd", completed.stdout)
        self.assertIn("scene=res://main.tscn", completed.stdout)

    def test_third_person_probe_command_dry_run(self) -> None:
        completed = run_script(
            "godot_capture.py",
            "--project",
            str(FIXTURE),
            "--mode",
            "run",
            "--script",
            "res://tests/third_person_controller_probe.gd",
            "--user-arg",
            "scene=res://tests/third_person_controller_fixture.tscn",
            "--user-arg",
            "player=Player",
            "--user-arg",
            "yaw_pivot=Player/CameraRig/Yaw",
            "--user-arg",
            "pitch_pivot=Player/CameraRig/Yaw/Pitch",
            "--user-arg",
            "camera=Player/CameraRig/Yaw/Pitch/SpringArm3D/Camera3D",
            "--user-arg",
            "yaw_degrees=45;90",
            "--dry-run",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("--script res://tests/third_person_controller_probe.gd", completed.stdout)
        self.assertIn("yaw_degrees=45;90", completed.stdout)

    def test_third_person_visibility_probe_command_dry_run(self) -> None:
        completed = run_script(
            "godot_capture.py",
            "--project",
            str(FIXTURE),
            "--mode",
            "run",
            "--script",
            "res://tests/third_person_visibility_probe.gd",
            "--user-arg",
            "scene=res://tests/third_person_visibility_fixture.tscn",
            "--user-arg",
            "adapter=OcclusionProbeAdapter",
            "--user-arg",
            "desired_camera=DesiredCamera",
            "--user-arg",
            "sample_points=Player/VisibilityPoints/Feet;Player/VisibilityPoints/Torso;Player/VisibilityPoints/Head",
            "--user-arg",
            "cases=single:1:cutaway;multi:2:cutaway;open_hole:0:clear;restored:0:clear",
            "--dry-run",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("--script res://tests/third_person_visibility_probe.gd", completed.stdout)
        self.assertIn("multi:2:cutaway", completed.stdout)
        self.assertIn("open_hole:0:clear", completed.stdout)

    def test_third_person_hud_mouse_probe_command_dry_run(self) -> None:
        completed = run_script(
            "godot_capture.py",
            "--project",
            str(FIXTURE),
            "--mode",
            "run",
            "--script",
            "res://tests/third_person_hud_mouse_probe.gd",
            "--user-arg",
            "scene=res://tests/third_person_production_hud_fixture.tscn",
            "--user-arg",
            "yaw_pivot=Player/CameraRig/Yaw",
            "--user-arg",
            "pitch_pivot=Player/CameraRig/Yaw/Pitch",
            "--user-arg",
            "hud_root=HUD/FullScreenRoot",
            "--user-arg",
            "mouse_delta=30:20",
            "--dry-run",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("--script res://tests/third_person_hud_mouse_probe.gd", completed.stdout)
        self.assertIn("hud_root=HUD/FullScreenRoot", completed.stdout)

    def test_project_snapshot(self) -> None:
        completed = run_script("project_snapshot.py", "--project", str(FIXTURE), "--no-git")
        self.assertEqual(completed.returncode, 0, completed.stdout)
        report = json.loads(completed.stdout)
        self.assertEqual(report["project"]["main_scene"], "res://main.tscn")
        self.assertEqual(report["scenes"][0]["node_count"], 2)

    def test_eval_scorecard(self) -> None:
        completed = run_script(
            "eval_scorecard.py",
            "--rubric",
            str(ROOT / "evals" / "rubric.json"),
            "--case",
            "existing-project-feature",
            "--evidence",
            str(ROOT / "tests" / "fixtures" / "eval_evidence.json"),
            "--summary",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("verdict=pass", completed.stdout)
        self.assertIn("score=100.00/100", completed.stdout)

    def test_evidence_helper_migrates_new_gates_and_instantiates_manifest(self) -> None:
        source = json.loads((ROOT / "tests" / "fixtures" / "eval_evidence.json").read_text(encoding="utf-8"))
        source["case_id"] = "constrained-mobile-web"
        for gate_id in (
            "interactive_onboarding",
            "clean_shipping_state",
            "semantic_identity_review",
            "independent_ux_review",
            "human_audio_listening",
            "content_duration_evidence",
            "responsive_layout_evidence",
            "input_modality_ui_evidence",
        ):
            del source["gates"][gate_id]
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            old_path = temp / "old.json"
            output_path = temp / "migrated.json"
            manifest_path = temp / "captures.json"
            review_path = temp / "review.md"
            checklist_path = temp / "yandex-checklist.md"
            old_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "evidence_helper.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "constrained-mobile-web",
                "--from-existing",
                str(old_path),
                "--output",
                str(output_path),
                "--capture-manifest-output",
                str(manifest_path),
                "--review-output",
                str(review_path),
                "--yandex-checklist-output",
                str(checklist_path),
            )
            self.assert_passes(completed)
            migrated = json.loads(output_path.read_text(encoding="utf-8"))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            review_text = review_path.read_text(encoding="utf-8")
            checklist_text = checklist_path.read_text(encoding="utf-8")
            scored = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "constrained-mobile-web",
                "--evidence",
                str(output_path),
                "--summary",
            )
        self.assertEqual(migrated["gates"]["interactive_onboarding"]["status"], "not_tested")
        self.assertEqual(migrated["gates"]["semantic_identity_review"]["status"], "not_tested")
        self.assertEqual(migrated["gates"]["human_audio_listening"]["status"], "not_tested")
        self.assertEqual(migrated["gates"]["content_duration_evidence"]["status"], "not_tested")
        self.assertEqual(migrated["gates"]["engine_clean"]["status"], "pass")
        self.assertEqual(
            [(item["width"], item["height"]) for item in manifest["viewport_matrix"]],
            [(336, 629), (760, 701), (844, 390), (1280, 720)],
        )
        self.assertIn("Independent UX Review", review_text)
        self.assertIn("Yandex Games Release Checklist", checklist_text)
        self.assertEqual(scored.returncode, 1, scored.stdout)
        self.assertIn("verdict=blocked", scored.stdout)

    def test_eval_blocking_gate_overrides_score(self) -> None:
        source = json.loads((ROOT / "tests" / "fixtures" / "eval_evidence.json").read_text(encoding="utf-8"))
        source["gates"]["engine_clean"] = {
            "status": "not_tested",
            "evidence": ["fixture: Godot unavailable"],
        }
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "evidence.json"
            evidence_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "existing-project-feature",
                "--evidence",
                str(evidence_path),
                "--summary",
            )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("verdict=blocked", completed.stdout)

    def test_eval_complete_slice_requires_independent_ux_review(self) -> None:
        source = json.loads((ROOT / "tests" / "fixtures" / "eval_evidence.json").read_text(encoding="utf-8"))
        source["case_id"] = "constrained-mobile-web"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: licensed audio and export listening review"],
        }
        source["gates"]["independent_ux_review"] = {
            "status": "not_tested",
            "evidence": ["fixture: only the building agent reviewed screenshots"],
        }
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "evidence.json"
            evidence_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "constrained-mobile-web",
                "--evidence",
                str(evidence_path),
                "--summary",
            )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("verdict=blocked", completed.stdout)
        self.assertIn("blocking_gates=1", completed.stdout)

    def test_eval_unverified_independent_review_caps_submitted_scores(self) -> None:
        source = json.loads((ROOT / "tests" / "fixtures" / "eval_evidence.json").read_text(encoding="utf-8"))
        source["case_id"] = "constrained-mobile-web"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: independent target-build listening"],
        }
        source["gates"]["independent_ux_review"] = {
            "status": "not_tested",
            "evidence": ["fixture: builder self-review only"],
        }
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            evidence_path = temp / "evidence.json"
            report_path = temp / "scorecard.json"
            evidence_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "constrained-mobile-web",
                "--evidence",
                str(evidence_path),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertGreater(report["submitted_score_100"], report["score_100"])
        self.assertTrue(
            any(cap["gate"] == "independent_ux_review" for cap in report["score_caps_applied"])
        )
        self.assertEqual(report["verdict"], "blocked")

    def test_eval_complete_slice_requires_semantic_identity_review(self) -> None:
        source = json.loads((ROOT / "tests" / "fixtures" / "eval_evidence.json").read_text(encoding="utf-8"))
        source["case_id"] = "constrained-mobile-web"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: licensed audio and independent target-build listening"],
        }
        source["gates"]["semantic_identity_review"] = {
            "status": "not_tested",
            "evidence": ["fixture: palette reviewed, but no blind final-size reading of the app/menu mark"],
        }
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "evidence.json"
            evidence_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "constrained-mobile-web",
                "--evidence",
                str(evidence_path),
                "--summary",
            )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("verdict=blocked", completed.stdout)
        self.assertIn("blocking_gates=1", completed.stdout)

    def test_eval_mobile_web_requires_input_modality_ui_evidence(self) -> None:
        source = json.loads((ROOT / "tests" / "fixtures" / "eval_evidence.json").read_text(encoding="utf-8"))
        source["case_id"] = "constrained-mobile-web"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: licensed audio and export listening review"],
        }
        source["gates"]["input_modality_ui_evidence"] = {
            "status": "not_tested",
            "evidence": ["fixture: ScrollContainer exists but no touch drag or modality-specific entry trace"],
        }
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "evidence.json"
            evidence_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "constrained-mobile-web",
                "--evidence",
                str(evidence_path),
                "--summary",
            )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("verdict=blocked", completed.stdout)
        self.assertIn("blocking_gates=1", completed.stdout)

    def test_eval_complete_slice_rejects_missing_case_gate(self) -> None:
        source = json.loads((ROOT / "tests" / "fixtures" / "eval_evidence.json").read_text(encoding="utf-8"))
        source["case_id"] = "constrained-mobile-web"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: licensed audio and export listening review"],
        }
        del source["gates"]["interactive_onboarding"]
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "evidence.json"
            evidence_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "constrained-mobile-web",
                "--evidence",
                str(evidence_path),
                "--summary",
            )
        self.assertEqual(completed.returncode, 2, completed.stdout)
        self.assertIn("Missing gate evidence: interactive_onboarding", completed.stdout)

    def test_eval_existing_feature_ignores_complete_game_gates(self) -> None:
        source = json.loads((ROOT / "tests" / "fixtures" / "eval_evidence.json").read_text(encoding="utf-8"))
        source["gates"]["interactive_onboarding"] = {
            "status": "not_tested",
            "evidence": ["fixture: unrelated focused feature"],
        }
        source["gates"]["independent_ux_review"] = {
            "status": "not_tested",
            "evidence": ["fixture: unrelated focused feature"],
        }
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "evidence.json"
            evidence_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "existing-project-feature",
                "--evidence",
                str(evidence_path),
                "--summary",
            )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("verdict=pass", completed.stdout)
        self.assertIn("blocking_gates=0", completed.stdout)

    def test_eval_complete_slice_requires_solid_audio(self) -> None:
        source = json.loads((ROOT / "tests" / "fixtures" / "eval_evidence.json").read_text(encoding="utf-8"))
        source["case_id"] = "constrained-mobile-web"
        source["scores"]["audio_direction_quality"] = {
            "score": 2,
            "evidence": ["fixture: generic placeholder audio remained"],
        }
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "evidence.json"
            evidence_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "constrained-mobile-web",
                "--evidence",
                str(evidence_path),
                "--summary",
            )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("verdict=blocked", completed.stdout)
        self.assertIn("quality_floor_failures=1", completed.stdout)

    def test_eval_complete_slice_requires_human_audio_listening(self) -> None:
        source = json.loads((ROOT / "tests" / "fixtures" / "eval_evidence.json").read_text(encoding="utf-8"))
        source["case_id"] = "constrained-mobile-web"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: structural audio checks and builder review only"],
        }
        source["gates"]["human_audio_listening"] = {
            "status": "not_tested",
            "evidence": ["fixture: no independent human listened to the target build"],
        }
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "evidence.json"
            evidence_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "constrained-mobile-web",
                "--evidence",
                str(evidence_path),
                "--summary",
            )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("verdict=blocked", completed.stdout)
        self.assertIn("blocking_gates=1", completed.stdout)

    def test_eval_third_person_case_requires_control_and_visibility(self) -> None:
        source = json.loads((ROOT / "tests" / "fixtures" / "eval_evidence.json").read_text(encoding="utf-8"))
        source["case_id"] = "new-3d-third-person-complete"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: human listening signoff"],
        }
        source["scores"]["asset_pipeline"] = {
            "score": 3,
            "evidence": ["fixture: licensed 3D asset manifest"],
        }
        source["scores"]["performance_and_size"] = {
            "score": 3,
            "evidence": ["fixture: desktop target profile and build audit"],
        }
        source["gates"]["third_person_control_contract"] = {
            "status": "not_tested",
            "evidence": ["fixture: movement tested only at spawn yaw"],
        }
        source["gates"]["gameplay_visibility_evidence"] = {
            "status": "not_tested",
            "evidence": ["fixture: no start-camera HUD/emissive route review"],
        }
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "evidence.json"
            evidence_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "new-3d-third-person-complete",
                "--evidence",
                str(evidence_path),
                "--summary",
            )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("verdict=blocked", completed.stdout)
        self.assertIn("blocking_gates=2", completed.stdout)

    def test_eval_third_person_case_accepts_complete_evidence(self) -> None:
        source = json.loads((ROOT / "tests" / "fixtures" / "eval_evidence.json").read_text(encoding="utf-8"))
        source["case_id"] = "new-3d-third-person-complete"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: independent human target-build listening signoff"],
        }
        source["scores"]["asset_pipeline"] = {
            "score": 3,
            "evidence": ["fixture: licensed 3D asset manifest"],
        }
        source["scores"]["performance_and_size"] = {
            "score": 3,
            "evidence": ["fixture: desktop target profile and build audit"],
        }
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "evidence.json"
            evidence_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "new-3d-third-person-complete",
                "--evidence",
                str(evidence_path),
                "--summary",
            )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("verdict=pass", completed.stdout)
        self.assertIn("blocking_gates=0", completed.stdout)

    def test_eval_isometric_case_caps_missing_art_onboarding_and_readability(self) -> None:
        source = json.loads((ROOT / "tests" / "fixtures" / "eval_evidence.json").read_text(encoding="utf-8"))
        source["case_id"] = "new-isometric-fixed-camera-complete"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: independent target-build listening"],
        }
        source["scores"]["asset_pipeline"] = {
            "score": 4,
            "evidence": ["fixture: imported asset manifest"],
        }
        for gate_id in (
            "isometric_vertical_slice_art_review",
            "isometric_character_readability_evidence",
            "isometric_onboarding_state_machine",
            "isometric_visual_composition_evidence",
        ):
            source["gates"][gate_id] = {
                "status": "not_tested",
                "evidence": [f"fixture: {gate_id} was inferred from structure only"],
            }
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            evidence_path = temp / "evidence.json"
            report_path = temp / "scorecard.json"
            evidence_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "new-isometric-fixed-camera-complete",
                "--evidence",
                str(evidence_path),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(report["blocking_gate_count"], 4)
        self.assertGreater(report["submitted_score_100"], report["score_100"])
        self.assertLessEqual(
            next(item["score"] for item in report["dimensions"] if item["id"] == "visual_coherence"),
            1,
        )
        self.assertEqual(report["verdict"], "blocked")

    def test_eval_isometric_case_accepts_complete_evidence(self) -> None:
        source = json.loads((ROOT / "tests" / "fixtures" / "eval_evidence.json").read_text(encoding="utf-8"))
        source["case_id"] = "new-isometric-fixed-camera-complete"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: independent target-build listening"],
        }
        source["scores"]["asset_pipeline"] = {
            "score": 3,
            "evidence": ["fixture: production art manifest and gameplay-size review"],
        }
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "evidence.json"
            evidence_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "new-isometric-fixed-camera-complete",
                "--evidence",
                str(evidence_path),
                "--summary",
            )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("verdict=pass", completed.stdout)
        self.assertIn("blocking_gates=0", completed.stdout)

    def test_eval_complete_slice_accepts_solid_audio(self) -> None:
        source = json.loads((ROOT / "tests" / "fixtures" / "eval_evidence.json").read_text(encoding="utf-8"))
        source["case_id"] = "constrained-mobile-web"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: licensed audio, gameplay listening review, and export check"],
        }
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "evidence.json"
            evidence_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "constrained-mobile-web",
                "--evidence",
                str(evidence_path),
                "--summary",
            )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("verdict=pass", completed.stdout)
        self.assertIn("quality_floor_failures=0", completed.stdout)

    def test_scene_errors_are_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.godot").write_text("config_version=5\n", encoding="utf-8")
            (project / "bad.tscn").write_text(
                "[gd_scene format=3]\n\n"
                "[node name=\"Root\" type=\"Node\"]\n"
                "script = ExtResource(\"missing\")\n\n"
                "[node name=\"Child\" type=\"Node\" parent=\"Missing\"]\n",
                encoding="utf-8",
            )
            self.assert_fails(
                run_script("scene_graph_audit.py", "--project", str(project), "--summary")
            )

    def test_texture_rect_expand_without_aspect_mode_warns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.godot").write_text("config_version=5\n", encoding="utf-8")
            (project / "icon.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"/>',
                encoding="utf-8",
            )
            (project / "bad-icon.tscn").write_text(
                '[gd_scene load_steps=2 format=3]\n\n'
                '[ext_resource type="Texture2D" path="res://icon.svg" id="1_icon"]\n\n'
                '[node name="Root" type="Control"]\n\n'
                '[node name="Icon" type="TextureRect" parent="."]\n'
                'texture = ExtResource("1_icon")\n'
                'expand_mode = 1\n',
                encoding="utf-8",
            )
            completed = run_script(
                "scene_graph_audit.py",
                "--project",
                str(project),
                "--summary",
                "--fail-on-warnings",
            )
        self.assert_fails(completed)
        self.assertIn("stretch_mode is default SCALE", completed.stdout)

    def test_texture_rect_keep_aspect_mode_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.godot").write_text("config_version=5\n", encoding="utf-8")
            (project / "icon.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"/>',
                encoding="utf-8",
            )
            (project / "good-icon.tscn").write_text(
                '[gd_scene load_steps=2 format=3]\n\n'
                '[ext_resource type="Texture2D" path="res://icon.svg" id="1_icon"]\n\n'
                '[node name="Root" type="Control"]\n\n'
                '[node name="Icon" type="TextureRect" parent="."]\n'
                'texture = ExtResource("1_icon")\n'
                'expand_mode = 1\n'
                'stretch_mode = 5\n',
                encoding="utf-8",
            )
            completed = run_script(
                "scene_graph_audit.py",
                "--project",
                str(project),
                "--summary",
                "--fail-on-warnings",
            )
        self.assert_passes(completed)

    def test_focus_stylebox_expand_inside_scroll_warns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.godot").write_text("config_version=5\n", encoding="utf-8")
            (project / "settings.tscn").write_text(
                '[gd_scene load_steps=2 format=3]\n\n'
                '[sub_resource type="StyleBoxFlat" id="StyleBoxFocus"]\n'
                'border_width_left = 2\n'
                'expand_margin_left = 4.0\n'
                'expand_margin_right = 4.0\n\n'
                '[node name="Root" type="Control"]\n\n'
                '[node name="Scroll" type="ScrollContainer" parent="."]\n\n'
                '[node name="Language" type="OptionButton" parent="Scroll"]\n'
                'theme_override_styles/focus = SubResource("StyleBoxFocus")\n',
                encoding="utf-8",
            )
            completed = run_script(
                "scene_graph_audit.py",
                "--project",
                str(project),
                "--summary",
                "--fail-on-warnings",
            )
        self.assert_fails(completed)
        self.assertIn("expands outside its rect", completed.stdout)
        self.assertIn("ScrollContainer", completed.stdout)

    def test_focus_stylebox_without_expand_inside_scroll_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.godot").write_text("config_version=5\n", encoding="utf-8")
            (project / "settings.tscn").write_text(
                '[gd_scene load_steps=2 format=3]\n\n'
                '[sub_resource type="StyleBoxFlat" id="StyleBoxFocus"]\n'
                'border_width_left = 2\n\n'
                '[node name="Root" type="Control"]\n\n'
                '[node name="Scroll" type="ScrollContainer" parent="."]\n\n'
                '[node name="Language" type="OptionButton" parent="Scroll"]\n'
                'theme_override_styles/focus = SubResource("StyleBoxFocus")\n',
                encoding="utf-8",
            )
            completed = run_script(
                "scene_graph_audit.py",
                "--project",
                str(project),
                "--summary",
                "--fail-on-warnings",
            )
        self.assert_passes(completed)

    def test_builtin_button_icon_with_centered_text_warns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.godot").write_text("config_version=5\n", encoding="utf-8")
            (project / "play.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"/>',
                encoding="utf-8",
            )
            (project / "menu.tscn").write_text(
                '[gd_scene load_steps=2 format=3]\n\n'
                '[ext_resource type="Texture2D" path="res://play.svg" id="1_icon"]\n\n'
                '[node name="Play" type="Button"]\n'
                'text = "Play"\n'
                'icon = ExtResource("1_icon")\n',
                encoding="utf-8",
            )
            completed = run_script(
                "scene_graph_audit.py",
                "--project",
                str(project),
                "--summary",
                "--fail-on-warnings",
            )
        self.assert_fails(completed)
        self.assertIn("localized icon-plus-label group", completed.stdout)

    def test_scene_authored_compound_button_shell_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.godot").write_text("config_version=5\n", encoding="utf-8")
            (project / "menu.tscn").write_text(
                '[gd_scene format=3]\n\n'
                '[node name="Play" type="Button"]\n\n'
                '[node name="Center" type="CenterContainer" parent="."]\n'
                'mouse_filter = 2\n\n'
                '[node name="Row" type="HBoxContainer" parent="Center"]\n'
                'mouse_filter = 2\n\n'
                '[node name="Label" type="Label" parent="Center/Row"]\n'
                'mouse_filter = 2\n'
                'text = "Play"\n',
                encoding="utf-8",
            )
            completed = run_script(
                "scene_graph_audit.py",
                "--project",
                str(project),
                "--summary",
                "--fail-on-warnings",
            )
        self.assert_passes(completed)

    def test_gltf_errors_are_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "bad.gltf").write_text(
                json.dumps(
                    {
                        "asset": {"version": "1.0"},
                        "scene": 2,
                        "scenes": [{"nodes": [4]}],
                        "nodes": [{}],
                    }
                ),
                encoding="utf-8",
            )
            self.assert_fails(
                run_script(
                    "gltf_audit.py",
                    "--project",
                    str(project),
                    "--asset",
                    str(project / "bad.gltf"),
                    "--summary",
                )
            )

    def test_corrupt_embedded_gltf_buffer_is_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            asset = project / "bad-buffer.gltf"
            asset.write_text(
                json.dumps(
                    {
                        "asset": {"version": "2.0"},
                        "scene": 0,
                        "scenes": [{"nodes": [0]}],
                        "nodes": [{}],
                        "buffers": [
                            {
                                "byteLength": 4,
                                "uri": "data:application/octet-stream;base64,%%%"
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            self.assert_fails(
                run_script(
                    "gltf_audit.py",
                    "--project",
                    str(project),
                    "--asset",
                    str(asset),
                    "--summary",
                )
            )


if __name__ == "__main__":
    unittest.main()
