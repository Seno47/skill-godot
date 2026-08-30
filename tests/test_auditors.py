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


def load_eval_evidence() -> dict:
    source = json.loads(
        (ROOT / "tests" / "fixtures" / "eval_evidence.json").read_text(encoding="utf-8")
    )
    rubric = json.loads((ROOT / "evals" / "rubric.json").read_text(encoding="utf-8"))
    owner_default = rubric.get("acceptance_owner_default", "builder")
    owners = {
        item["id"]: item.get("acceptance_owner", owner_default)
        for item in rubric["blocking_gates"]
    }
    for gate_id, gate in source["gates"].items():
        gate.setdefault(
            "reviewer",
            {
                "role": owners.get(gate_id, owner_default),
                "context": f"fixture {owners.get(gate_id, owner_default)} acceptance context",
            },
        )
    source.setdefault("run_metadata", {})["artifact_root"] = str(
        ROOT / "tests" / "fixtures"
    )
    return source


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

    def test_capture_delivery_proof_derives_deterministic_frame_count(self) -> None:
        completed = run_script(
            "godot_capture.py",
            "--project",
            str(FIXTURE),
            "--mode",
            "capture",
            "--scene",
            "res://main.tscn",
            "--proof-seconds",
            "15",
            "--fixed-fps",
            "30",
            "--output",
            "reports/proof.avi",
            "--dry-run",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("--quit-after 450", completed.stdout)
        self.assertIn("Delivery proof=15s frames=450 fixed_fps=30", completed.stdout)
        self.assertIn("watch the entire recording", completed.stdout)

    def test_capture_delivery_proof_rejects_manual_frames(self) -> None:
        completed = run_script(
            "godot_capture.py",
            "--project",
            str(FIXTURE),
            "--mode",
            "capture",
            "--proof-seconds",
            "15",
            "--frames",
            "450",
            "--output",
            "reports/proof.avi",
            "--dry-run",
        )
        self.assertEqual(completed.returncode, 2, completed.stdout)
        self.assertIn("mutually exclusive", completed.stdout)

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

    def test_asset_manifest_records_gameplay_use_cost_and_resumable_job(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            project = temp / "project"
            project.mkdir()
            (project / "project.godot").write_text("[application]\n", encoding="utf-8")
            job_record = project / "work" / "hero.provider.json"
            job_record.parent.mkdir()
            job_record.write_text('{"task_id":"fixture-1"}\n', encoding="utf-8")
            manifest = temp / "assets.json"
            initialized = run_script("asset_manifest.py", "init", "--manifest", str(manifest))
            added = run_script(
                "asset_manifest.py",
                "add",
                "--manifest",
                str(manifest),
                "--id",
                "hero",
                "--kind",
                "character-model",
                "--source-type",
                "generated",
                "--status",
                "accepted",
                "--tool",
                "fixture-generator 1.0",
                "--cost-cents",
                "37",
                "--job-record",
                "work/hero.provider.json",
                "--gameplay-use",
                "1.8m tall at the production camera",
            )
            validated = run_script(
                "asset_manifest.py",
                "validate",
                "--manifest",
                str(manifest),
                "--project",
                str(project),
            )
            record = json.loads(manifest.read_text(encoding="utf-8"))["assets"][0]
        self.assertEqual(initialized.returncode, 0, initialized.stdout)
        self.assertIn("[OK] Created", initialized.stdout)
        self.assertEqual(added.returncode, 0, added.stdout)
        self.assert_passes(validated)
        self.assertEqual(record["origin"]["cost_cents"], 37)
        self.assertEqual(record["origin"]["job_record"], "work/hero.provider.json")
        self.assertEqual(
            record["usage"]["gameplay_use"],
            "1.8m tall at the production camera",
        )

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

    def test_eval_scorecard_reports_publication_certified_responsibility(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "scorecard.json"
            completed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "existing-project-feature",
                "--evidence",
                str(ROOT / "tests" / "fixtures" / "eval_evidence.json"),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("responsibility=publication_certified", completed.stdout)
        self.assertEqual(report["responsibility_status"], "publication_certified")
        self.assertEqual(report["builder_completion_status"], "complete")
        self.assertEqual(report["publication_status"], "certified")

    def test_eval_scorecard_reports_ready_when_only_external_review_is_pending(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "constrained-mobile-web"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: licensed audio and builder-owned runtime checks"],
        }
        source["gates"]["independent_ux_review"] = {
            "status": "not_tested",
            "evidence": ["fixture: independent review is external to the builder run"],
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
        self.assertIn("verdict=blocked", completed.stdout)
        self.assertIn("responsibility=ready_for_human_test", completed.stdout)
        self.assertEqual(report["builder_owned_unresolved_gate_count"], 0)
        self.assertEqual(report["external_pending_gates"], ["independent_ux_review"])
        self.assertEqual(report["builder_completion_status"], "complete")
        self.assertEqual(report["publication_status"], "not_certified")

    def test_eval_scorecard_keeps_missing_builder_gate_as_builder_work(self) -> None:
        source = load_eval_evidence()
        source["gates"]["engine_clean"] = {
            "status": "not_tested",
            "evidence": ["fixture: builder did not run the available engine check"],
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
                "existing-project-feature",
                "--evidence",
                str(evidence_path),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("responsibility=builder_work_remaining", completed.stdout)
        self.assertEqual(report["builder_owned_unresolved_gates"], ["engine_clean"])
        self.assertEqual(report["builder_completion_status"], "incomplete")

    def test_eval_scorecard_returns_failed_external_review_to_builder(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "constrained-mobile-web"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: licensed audio and target-build checks"],
        }
        source["gates"]["independent_ux_review"] = {
            "status": "fail",
            "evidence": ["fixture: reviewer found an actionable clipped control"],
            "reviewer": {
                "role": "independent",
                "context": "separate fixture reviewer context",
            },
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
        self.assertIn("responsibility=builder_work_remaining", completed.stdout)
        self.assertEqual(report["external_failed_gates"], ["independent_ux_review"])
        self.assertEqual(report["builder_completion_status"], "incomplete")

    def test_cross_surface_pass_fails_without_pause_or_runtime_modal_artifact(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "constrained-mobile-web"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: licensed target-build audio"],
        }
        gate = source["gates"]["cross_surface_production_craft_review"]
        gate["artifacts"] = [
            item
            for item in gate["artifacts"]
            if "pause_or_runtime_modal" not in item.get("states", [])
        ]
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
        cross_surface = next(
            item for item in report["gates"] if item["id"] == "cross_surface_production_craft_review"
        )
        self.assertEqual(cross_surface["status"], "fail")
        self.assertTrue(
            any("pause_or_runtime_modal" in item for item in cross_surface["validation_failures"])
        )
        self.assertEqual(report["responsibility_status"], "builder_work_remaining")

    def test_product_owner_rejection_is_builder_work_until_explicit_closure(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "new-progression-heavy-complete"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: licensed target-build audio"],
        }
        source["scores"]["asset_pipeline"] = {
            "score": 4,
            "evidence": ["fixture: production asset pipeline"],
        }
        source["scores"]["performance_and_size"] = {
            "score": 4,
            "evidence": ["fixture: target budget"],
        }
        source["gates"]["product_owner_slice_approval"] = {
            "status": "fail",
            "evidence": ["fixture: owner rejected the core concept after the representative slice"],
            "reviewer": {
                "role": "product_owner",
                "context": "fixture product owner rejection",
            },
        }
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            active_path = temp / "active.json"
            active_report = temp / "active-scorecard.json"
            active_path.write_text(json.dumps(source), encoding="utf-8")
            active = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "new-progression-heavy-complete",
                "--evidence",
                str(active_path),
                "--json-output",
                str(active_report),
                "--summary",
            )
            active_data = json.loads(active_report.read_text(encoding="utf-8"))

            closed_source = json.loads(json.dumps(source))
            closed_source["project_disposition"] = {
                "status": "user_closed",
                "decision_owner": "user",
                "context": "fixture user explicitly closed the disliked project",
                "reason": "core concept did not appeal to the product owner",
                "continue_authorized": False,
            }
            closed_path = temp / "closed.json"
            closed_report = temp / "closed-scorecard.json"
            closed_path.write_text(json.dumps(closed_source), encoding="utf-8")
            closed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "new-progression-heavy-complete",
                "--evidence",
                str(closed_path),
                "--json-output",
                str(closed_report),
                "--summary",
            )
            closed_data = json.loads(closed_report.read_text(encoding="utf-8"))

        self.assertEqual(active.returncode, 1, active.stdout)
        self.assertEqual(active_data["responsibility_status"], "builder_work_remaining")
        self.assertEqual(closed.returncode, 1, closed.stdout)
        self.assertIn("verdict=closed", closed.stdout)
        self.assertIn("responsibility=project_closed_user_rejected", closed.stdout)
        self.assertEqual(closed_data["responsibility_status"], "project_closed_user_rejected")
        self.assertEqual(closed_data["builder_completion_status"], "closed")
        self.assertEqual(closed_data["publication_status"], "not_certified")
        self.assertEqual(closed_data["project_disposition"]["status"], "user_closed")

    def test_account_cloud_acceptance_splits_builder_and_provider_owners(self) -> None:
        rubric = json.loads((ROOT / "evals" / "rubric.json").read_text(encoding="utf-8"))
        owner_default = rubric["acceptance_owner_default"]
        gates = {item["id"]: item for item in rubric["blocking_gates"]}
        self.assertEqual(
            gates["account_cloud_evidence"].get("acceptance_owner", owner_default),
            "builder",
        )
        self.assertEqual(
            gates["account_cloud_provider_evidence"]["acceptance_owner"],
            "provider",
        )

    def test_account_cloud_provider_boundary_allows_ready_but_client_gap_does_not(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "account-cloud-cross-progression"
        source["gates"]["account_cloud_evidence"] = {
            "status": "pass",
            "evidence": ["fixture: production client resolver and provider-response matrix"],
            "reviewer": {"role": "builder", "context": "isolated client-contract builder"},
            "artifacts": [
                {"path": "evidence-artifacts/report.md", "kind": "report", "states": ["client_contract"]},
                {"path": "evidence-artifacts/review.md", "kind": "report", "states": ["redaction"]},
                {"path": "evidence-artifacts/trace-a.json", "kind": "trace", "states": ["guest_link_conflict"]},
                {"path": "evidence-artifacts/trace-b.json", "kind": "trace", "states": ["multi_device_offline"]},
                {"path": "evidence-artifacts/trace-c.json", "kind": "trace", "states": ["switch_signout"]},
                {"path": "evidence-artifacts/trace-d.json", "kind": "trace", "states": ["outage_delete"]},
                {"path": "evidence-artifacts/trace-e.json", "kind": "trace", "states": ["guest_link_conflict"]},
                {"path": "evidence-artifacts/progression-trace-a.json", "kind": "trace", "states": ["multi_device_offline"]},
                {"path": "evidence-artifacts/build.zip", "kind": "build", "states": ["target_build"]},
            ],
        }
        source["gates"]["account_cloud_provider_evidence"] = {
            "status": "not_tested",
            "evidence": ["fixture: no authorized target-provider account in this run"],
            "reviewer": {"role": "provider", "context": "provider access unavailable"},
        }
        source["gates"]["account_conflict_ux_review"] = {
            "status": "pass",
            "evidence": ["fixture: separate conflict and account-switch UX review"],
            "reviewer": {"role": "independent", "context": "isolated account UX reviewer"},
            "artifacts": [
                {"path": "evidence-artifacts/review.md", "kind": "review", "states": ["conflict_choice", "account_switch_or_outage"]},
                {"path": "evidence-artifacts/quiet.png", "kind": "image", "states": ["conflict_choice"]},
                {"path": "evidence-artifacts/dense.png", "kind": "image", "states": ["account_switch_or_outage"]},
                {"path": "evidence-artifacts/report.md", "kind": "report", "states": ["ux_inventory"]},
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            ready_evidence = temp / "ready.json"
            ready_report = temp / "ready-scorecard.json"
            ready_evidence.write_text(json.dumps(source), encoding="utf-8")
            ready = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "account-cloud-cross-progression",
                "--evidence",
                str(ready_evidence),
                "--json-output",
                str(ready_report),
                "--summary",
            )
            ready_data = json.loads(ready_report.read_text(encoding="utf-8"))

            incomplete_source = json.loads(json.dumps(source))
            incomplete_source["gates"]["account_cloud_evidence"] = {
                "status": "not_tested",
                "evidence": ["fixture: available client resolver matrix was not run"],
            }
            incomplete_evidence = temp / "incomplete.json"
            incomplete_report = temp / "incomplete-scorecard.json"
            incomplete_evidence.write_text(json.dumps(incomplete_source), encoding="utf-8")
            incomplete = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "account-cloud-cross-progression",
                "--evidence",
                str(incomplete_evidence),
                "--json-output",
                str(incomplete_report),
                "--summary",
            )
            incomplete_data = json.loads(incomplete_report.read_text(encoding="utf-8"))

        self.assertEqual(ready.returncode, 1, ready.stdout)
        self.assertIn("responsibility=ready_for_human_test", ready.stdout)
        self.assertEqual(ready_data["builder_owned_unresolved_gate_count"], 0)
        self.assertEqual(
            ready_data["external_pending_gates"],
            ["account_cloud_provider_evidence"],
        )
        self.assertEqual(ready_data["builder_completion_status"], "complete")

        self.assertEqual(incomplete.returncode, 1, incomplete.stdout)
        self.assertIn("responsibility=builder_work_remaining", incomplete.stdout)
        self.assertEqual(
            incomplete_data["builder_owned_unresolved_gates"],
            ["account_cloud_evidence"],
        )
        self.assertEqual(incomplete_data["builder_completion_status"], "incomplete")

    def test_external_audio_floor_defers_at_cap_but_not_below_cap(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "constrained-mobile-web"
        source["scores"]["audio_direction_quality"] = {
            "score": 2,
            "evidence": ["fixture: builder verified coverage, provenance, integration and runtime behavior"],
        }
        source["gates"]["human_audio_listening"] = {
            "status": "not_tested",
            "evidence": ["fixture: representative listening requires an external human"],
            "reviewer": {"role": "human", "context": "human listener unavailable"},
        }
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            ready_evidence = temp / "audio-ready.json"
            ready_report = temp / "audio-ready-scorecard.json"
            ready_evidence.write_text(json.dumps(source), encoding="utf-8")
            ready = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "constrained-mobile-web",
                "--evidence",
                str(ready_evidence),
                "--json-output",
                str(ready_report),
                "--summary",
            )
            ready_data = json.loads(ready_report.read_text(encoding="utf-8"))

            weak_source = json.loads(json.dumps(source))
            weak_source["scores"]["audio_direction_quality"]["score"] = 1
            weak_evidence = temp / "audio-weak.json"
            weak_report = temp / "audio-weak-scorecard.json"
            weak_evidence.write_text(json.dumps(weak_source), encoding="utf-8")
            weak = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "constrained-mobile-web",
                "--evidence",
                str(weak_evidence),
                "--json-output",
                str(weak_report),
                "--summary",
            )
            weak_data = json.loads(weak_report.read_text(encoding="utf-8"))

        self.assertEqual(ready.returncode, 1, ready.stdout)
        self.assertIn("responsibility=ready_for_human_test", ready.stdout)
        self.assertEqual(ready_data["submitted_quality_floor_failure_count"], 1)
        self.assertEqual(ready_data["builder_quality_floor_failure_count"], 0)
        self.assertEqual(ready_data["external_deferred_quality_floor_count"], 1)
        deferred = ready_data["external_deferred_quality_floors"][0]
        self.assertEqual(deferred["id"], "audio_direction_quality")
        self.assertEqual(deferred["pre_external_floor"], 2.0)
        self.assertEqual(deferred["pending_external_gates"], ["human_audio_listening"])

        self.assertEqual(weak.returncode, 1, weak.stdout)
        self.assertIn("responsibility=builder_work_remaining", weak.stdout)
        self.assertEqual(weak_data["builder_quality_floor_failure_count"], 1)
        self.assertEqual(weak_data["external_deferred_quality_floor_count"], 0)

    def test_evidence_helper_migrates_account_provider_gate_without_promoting_mock(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "account-cloud-cross-progression"
        source["gates"]["account_cloud_evidence"] = {
            "status": "pass",
            "evidence": ["fixture: legacy client and mock-provider contract"],
            "reviewer": {"role": "builder", "context": "legacy isolated builder"},
        }
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            old_path = temp / "old-account-evidence.json"
            migrated_path = temp / "migrated-account-evidence.json"
            old_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "evidence_helper.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "account-cloud-cross-progression",
                "--from-existing",
                str(old_path),
                "--output",
                str(migrated_path),
            )
            migrated = json.loads(migrated_path.read_text(encoding="utf-8"))
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(migrated["gates"]["account_cloud_evidence"]["status"], "pass")
        provider_gate = migrated["gates"]["account_cloud_provider_evidence"]
        self.assertEqual(provider_gate["status"], "not_tested")
        self.assertEqual(provider_gate["reviewer"]["role"], "provider")

    def test_evidence_helper_migrates_new_gates_and_instantiates_manifest(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "constrained-mobile-web"
        for gate_id in (
            "interactive_onboarding",
            "clean_shipping_state",
            "semantic_identity_review",
            "independent_ux_review",
            "human_audio_listening",
            "content_duration_evidence",
            "gameplay_hud_glanceability_review",
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
        self.assertEqual(
            migrated["gates"]["gameplay_hud_glanceability_review"]["status"],
            "not_tested",
        )
        self.assertEqual(
            migrated["gates"]["gameplay_hud_glanceability_review"]["reviewer"]["role"],
            "independent",
        )
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
        source = load_eval_evidence()
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
        source = load_eval_evidence()
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
        source = load_eval_evidence()
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
        source = load_eval_evidence()
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

    def test_eval_complete_slice_rejects_incomplete_art_direction_selection(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "constrained-mobile-web"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: licensed audio and independent target-build listening"],
        }
        source["gates"]["art_direction_selection_evidence"]["artifacts"] = [
            item
            for item in source["gates"]["art_direction_selection_evidence"]["artifacts"]
            if "representative_composition" not in item["states"]
        ]
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "evidence.json"
            report_path = Path(directory) / "report.json"
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
        self.assertIn("blocking_gates=1", completed.stdout)
        gate = next(
            item for item in report["gates"] if item["id"] == "art_direction_selection_evidence"
        )
        self.assertEqual(gate["status"], "fail")
        self.assertTrue(
            any("representative_composition" in issue for issue in gate["validation_failures"])
        )

    def test_eval_complete_slice_requires_tutorial_discovery_artifact(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "constrained-mobile-web"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: licensed audio and independent target-build listening"],
        }
        for artifact in source["gates"]["interactive_onboarding"]["artifacts"]:
            artifact["states"] = [
                state for state in artifact["states"] if state != "tutorial_discovery"
            ]
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "evidence.json"
            report_path = Path(directory) / "report.json"
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
        gate = next(item for item in report["gates"] if item["id"] == "interactive_onboarding")
        self.assertEqual(gate["status"], "fail")
        self.assertTrue(any("tutorial_discovery" in issue for issue in gate["validation_failures"]))

    def test_progression_visual_comprehension_rejects_missing_locked_late_state(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "new-progression-heavy-complete"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: licensed audio and independent target-build listening"],
        }
        source["gates"]["progression_visual_comprehension_review"]["artifacts"] = [
            item
            for item in source["gates"]["progression_visual_comprehension_review"]["artifacts"]
            if "progression_locked_late" not in item["states"]
        ]
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "evidence.json"
            report_path = Path(directory) / "report.json"
            evidence_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "new-progression-heavy-complete",
                "--evidence",
                str(evidence_path),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(completed.returncode, 1, completed.stdout)
        gate = next(
            item
            for item in report["gates"]
            if item["id"] == "progression_visual_comprehension_review"
        )
        self.assertEqual(gate["status"], "fail")
        self.assertTrue(
            any("progression_locked_late" in issue for issue in gate["validation_failures"])
        )

    def test_eval_mobile_web_requires_input_modality_ui_evidence(self) -> None:
        source = load_eval_evidence()
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
        source = load_eval_evidence()
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
        source = load_eval_evidence()
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
        source = load_eval_evidence()
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
        source = load_eval_evidence()
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
        source = load_eval_evidence()
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

    def test_eval_production_character_motion_is_builder_owned_and_blocking(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "new-isometric-fixed-camera-complete"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: human target-build listening"],
        }
        source["scores"]["asset_pipeline"] = {
            "score": 4,
            "evidence": ["fixture: imported production character and animation library"],
        }
        source["gates"]["production_character_motion_evidence"] = {
            "status": "not_tested",
            "evidence": ["fixture: clips exist but no production pose or target-build motion proof"],
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
        motion_gate = next(
            item for item in report["gates"] if item["id"] == "production_character_motion_evidence"
        )
        scores = {item["id"]: item for item in report["dimensions"]}
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(report["blocking_gate_count"], 1)
        self.assertEqual(motion_gate["acceptance_owner"], "builder")
        self.assertEqual(scores["visual_coherence"]["score"], 1)
        self.assertEqual(scores["playability_and_ux"]["score"], 2)
        self.assertEqual(scores["asset_pipeline"]["score"], 2)
        self.assertEqual(report["verdict"], "blocked")

    def test_eval_progression_case_blocks_model_and_human_pacing_claims(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "new-progression-heavy-complete"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: human target-build listening"],
        }
        source["scores"]["asset_pipeline"] = {
            "score": 3,
            "evidence": ["fixture: production asset manifest"],
        }
        for gate_id in (
            "progression_balance_model_evidence",
            "progression_pacing_playtest",
        ):
            source["gates"][gate_id]["status"] = "not_tested"
            source["gates"][gate_id]["evidence"] = [
                f"fixture: {gate_id} was inferred from one optimal autoplay"
            ]
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
                "new-progression-heavy-complete",
                "--evidence",
                str(evidence_path),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        scores = {item["id"]: item for item in report["dimensions"]}
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(report["blocking_gate_count"], 2)
        self.assertEqual(scores["gameplay_correctness"]["score"], 1)
        self.assertEqual(scores["playability_and_ux"]["score"], 1)
        self.assertEqual(scores["technical_quality"]["score"], 2)
        self.assertEqual(scores["evidence_and_reproducibility"]["score"], 2)
        self.assertEqual(report["verdict"], "blocked")

    def test_eval_online_extraction_cannot_bypass_network_and_loop_gates(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "new-online-extraction-complete"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: human target-build listening"],
        }
        source["scores"]["performance_and_size"] = {
            "score": 4,
            "evidence": ["fixture: submitted network performance claim"],
        }
        for gate_id in (
            "network_contract_evidence",
            "network_multipeer_playtest",
            "extraction_loop_evidence",
            "extraction_risk_pacing_playtest",
        ):
            source["gates"][gate_id] = {
                "status": "not_tested",
                "evidence": [f"fixture: {gate_id} deliberately absent"],
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
                "new-online-extraction-complete",
                "--evidence",
                str(evidence_path),
                "--json-output",
                str(report_path),
                "--summary",
            )
            self.assertTrue(report_path.exists(), completed.stdout)
            report = json.loads(report_path.read_text(encoding="utf-8"))
        blocking = {item["id"] for item in report["gates"] if item["status"] != "pass"}
        caps = {item["gate"] for item in report["score_caps_applied"]}
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertTrue(
            {
                "network_contract_evidence",
                "network_multipeer_playtest",
                "extraction_loop_evidence",
                "extraction_risk_pacing_playtest",
            }.issubset(blocking)
        )
        self.assertIn("network_contract_evidence", caps)
        self.assertIn("network_multipeer_playtest", caps)
        self.assertEqual(report["verdict"], "blocked")

    def test_eval_mmo_slice_cannot_bypass_service_readiness(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "new-mmo-production-slice"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: human target-build listening"],
        }
        source["scores"]["performance_and_size"] = {
            "score": 4,
            "evidence": ["fixture: submitted service capacity claim"],
        }
        for gate_id in (
            "network_contract_evidence",
            "network_multipeer_playtest",
            "online_service_readiness_evidence",
            "online_service_architecture_review",
        ):
            source["gates"][gate_id] = {
                "status": "not_tested",
                "evidence": [f"fixture: {gate_id} deliberately absent"],
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
                "new-mmo-production-slice",
                "--evidence",
                str(evidence_path),
                "--json-output",
                str(report_path),
                "--summary",
            )
            self.assertTrue(report_path.exists(), completed.stdout)
            report = json.loads(report_path.read_text(encoding="utf-8"))
        gates = {item["id"]: item for item in report["gates"]}
        scores = {item["id"]: item for item in report["dimensions"]}
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(gates["online_service_readiness_evidence"]["status"], "not_tested")
        self.assertEqual(gates["online_service_architecture_review"]["status"], "not_tested")
        self.assertEqual(scores["technical_quality"]["score"], 1)
        self.assertEqual(scores["performance_and_size"]["score"], 1)
        self.assertEqual(scores["intent_and_scope"]["score"], 2)
        self.assertEqual(report["verdict"], "blocked")

    def test_eval_procedural_case_cannot_bypass_generation_ai_and_human_gates(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "new-procedural-roguelike-complete"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: human target-build listening"],
        }
        source["scores"]["performance_and_size"] = {
            "score": 4,
            "evidence": ["fixture: submitted procedural capacity claim"],
        }
        missing = (
            "progression_balance_model_evidence",
            "progression_pacing_playtest",
            "ai_navigation_evidence",
            "ai_behavior_readability_review",
            "procedural_generation_evidence",
            "procedural_variety_playtest",
        )
        for gate_id in missing:
            source["gates"][gate_id] = {
                "status": "not_tested",
                "evidence": [f"fixture: {gate_id} deliberately absent"],
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
                "new-procedural-roguelike-complete",
                "--evidence",
                str(evidence_path),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        blocking = {item["id"] for item in report["gates"] if item["status"] != "pass"}
        caps = {item["gate"] for item in report["score_caps_applied"]}
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertTrue(set(missing).issubset(blocking))
        self.assertTrue(
            {
                "progression_balance_model_evidence",
                "ai_navigation_evidence",
                "ai_behavior_readability_review",
            }.issubset(caps)
        )
        self.assertEqual(report["verdict"], "blocked")

    def test_eval_platform_release_requires_exact_candidate_matrix(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "multi-platform-store-release"
        source["scores"]["performance_and_size"] = {
            "score": 4,
            "evidence": ["fixture: submitted package performance claim"],
        }
        source["gates"]["platform_release_evidence"] = {
            "status": "not_tested",
            "evidence": ["fixture: exports exist without install/update matrix"],
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
                "multi-platform-store-release",
                "--evidence",
                str(evidence_path),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        scores = {item["id"]: item for item in report["dimensions"]}
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(scores["technical_quality"]["score"], 1)
        self.assertEqual(scores["performance_and_size"]["score"], 1)
        self.assertEqual(scores["evidence_and_reproducibility"]["score"], 1)
        self.assertEqual(report["verdict"], "blocked")

    def test_eval_modding_slice_requires_loader_and_security_review(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "modding-ugc-production-slice"
        for gate_id in ("modding_ugc_evidence", "modding_security_review"):
            source["gates"][gate_id] = {
                "status": "not_tested",
                "evidence": [f"fixture: {gate_id} deliberately absent"],
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
                "modding-ugc-production-slice",
                "--evidence",
                str(evidence_path),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        gates = {item["id"]: item for item in report["gates"]}
        scores = {item["id"]: item for item in report["dimensions"]}
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(gates["modding_ugc_evidence"]["status"], "not_tested")
        self.assertEqual(gates["modding_security_review"]["status"], "not_tested")
        self.assertEqual(scores["technical_quality"]["score"], 1)
        self.assertEqual(scores["intent_and_scope"]["score"], 2)
        self.assertEqual(report["verdict"], "blocked")

    def test_eval_pass_rejects_missing_raw_motion_artifact(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "new-2-5d-complete"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: human target-build listening"],
        }
        source["scores"]["asset_pipeline"] = {
            "score": 3,
            "evidence": ["fixture: production asset integration"],
        }
        source["gates"]["production_character_motion_evidence"]["artifacts"][0]["path"] = (
            "evidence-artifacts/missing-motion.avi"
        )
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
                "new-2-5d-complete",
                "--evidence",
                str(evidence_path),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        motion = next(
            item for item in report["gates"] if item["id"] == "production_character_motion_evidence"
        )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(motion["submitted_status"], "pass")
        self.assertEqual(motion["status"], "fail")
        self.assertTrue(any("missing" in item for item in motion["validation_failures"]))

    def test_eval_independent_gate_cannot_be_self_awarded(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "new-2-5d-complete"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: human target-build listening"],
        }
        source["scores"]["asset_pipeline"] = {
            "score": 3,
            "evidence": ["fixture: production asset integration"],
        }
        source["gates"]["menu_identity_craft_review"]["reviewer"] = {
            "role": "builder",
            "context": "same context that authored the menu",
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
                "new-2-5d-complete",
                "--evidence",
                str(evidence_path),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        menu = next(item for item in report["gates"] if item["id"] == "menu_identity_craft_review")
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(menu["status"], "fail")
        self.assertTrue(any("reviewer.role=independent" in item for item in menu["validation_failures"]))

    def test_eval_2_5d_complete_requires_dense_and_vfx_art_states(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "new-2-5d-complete"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: human target-build listening"],
        }
        source["scores"]["asset_pipeline"] = {
            "score": 3,
            "evidence": ["fixture: production asset integration"],
        }
        source["gates"]["production_art_integrity_evidence"]["artifacts"] = [
            item
            for item in source["gates"]["production_art_integrity_evidence"]["artifacts"]
            if "dense_interaction" not in item.get("states", [])
            and "vfx_peak" not in item.get("states", [])
        ]
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
                "new-2-5d-complete",
                "--evidence",
                str(evidence_path),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        art = next(
            item for item in report["gates"] if item["id"] == "production_art_integrity_evidence"
        )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(art["status"], "fail")
        self.assertTrue(any("dense_interaction" in item for item in art["validation_failures"]))
        self.assertTrue(any("vfx_peak" in item for item in art["validation_failures"]))

    def test_eval_complete_game_requires_all_hud_glanceability_states(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "new-2-5d-complete"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: human target-build listening"],
        }
        source["scores"]["asset_pipeline"] = {
            "score": 3,
            "evidence": ["fixture: production asset integration"],
        }
        source["gates"]["gameplay_hud_glanceability_review"]["artifacts"] = [
            item
            for item in source["gates"]["gameplay_hud_glanceability_review"]["artifacts"]
            if "hud_dense" not in item.get("states", [])
            and "hud_vfx_peak" not in item.get("states", [])
        ]
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
                "new-2-5d-complete",
                "--evidence",
                str(evidence_path),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        hud = next(
            item for item in report["gates"] if item["id"] == "gameplay_hud_glanceability_review"
        )
        scores = {item["id"]: item for item in report["dimensions"]}
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(hud["submitted_status"], "pass")
        self.assertEqual(hud["status"], "fail")
        self.assertTrue(any("hud_dense" in item for item in hud["validation_failures"]))
        self.assertTrue(any("hud_vfx_peak" in item for item in hud["validation_failures"]))
        self.assertEqual(scores["playability_and_ux"]["score"], 1)
        self.assertEqual(scores["visual_coherence"]["score"], 2)

    def test_eval_2_5d_complete_accepts_concrete_artifacts_and_owners(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "new-2-5d-complete"
        source["scores"]["audio_direction_quality"] = {
            "score": 3,
            "evidence": ["fixture: human target-build listening"],
        }
        source["scores"]["asset_pipeline"] = {
            "score": 3,
            "evidence": ["fixture: production asset integration"],
        }
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "evidence.json"
            evidence_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "new-2-5d-complete",
                "--evidence",
                str(evidence_path),
                "--summary",
            )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("verdict=pass", completed.stdout)
        self.assertIn("blocking_gates=0", completed.stdout)

    def test_evidence_helper_labels_character_motion_as_builder_owned(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "new-isometric-fixed-camera-complete"
        del source["gates"]["production_character_motion_evidence"]
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            old_path = temp / "old.json"
            output_path = temp / "migrated.json"
            old_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "evidence_helper.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "new-isometric-fixed-camera-complete",
                "--from-existing",
                str(old_path),
                "--output",
                str(output_path),
            )
            migrated = json.loads(output_path.read_text(encoding="utf-8"))
        self.assert_passes(completed)
        motion = migrated["gates"]["production_character_motion_evidence"]
        self.assertEqual(motion["status"], "not_tested")
        self.assertIn("[builder-owned]", motion["evidence"][0])
        self.assertEqual(motion["reviewer"]["role"], "builder")
        self.assertIn("UNRESOLVED", motion["reviewer"]["context"])
        self.assertEqual(motion["artifacts"], [])

    def test_eval_third_person_case_accepts_complete_evidence(self) -> None:
        source = load_eval_evidence()
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
        source = load_eval_evidence()
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
        source = load_eval_evidence()
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

    def test_eval_high_angle_district_modifier_fails_closed_without_visual_and_motion_packet(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "high-angle-3d-district-complete"
        source["scores"]["asset_pipeline"] = {
            "score": 4,
            "evidence": ["fixture: imported modular district kit"],
        }
        source["gates"]["high_angle_3d_district_composition_evidence"] = {
            "status": "not_tested",
            "evidence": ["fixture: collision navmesh prop counts and one still only"],
            "reviewer": {"role": "builder", "context": "fixture builder context"},
            "artifacts": [],
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
                "high-angle-3d-district-complete",
                "--evidence",
                str(evidence_path),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        gate = next(
            item
            for item in report["gates"]
            if item["id"] == "high_angle_3d_district_composition_evidence"
        )
        scores = {item["id"]: item for item in report["dimensions"]}
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(gate["status"], "not_tested")
        self.assertEqual(report["blocking_gate_count"], 1)
        self.assertEqual(scores["visual_coherence"]["score"], 1)
        self.assertEqual(scores["scene_resource_authorship"]["score"], 2)
        self.assertEqual(scores["playability_and_ux"]["score"], 2)
        self.assertEqual(scores["asset_pipeline"]["score"], 2)
        self.assertEqual(report["verdict"], "blocked")

    def test_eval_high_angle_district_material_direction_states_fail_closed(self) -> None:
        artifacts = [
            {
                "path": "evidence-artifacts/report.md",
                "kind": "report",
                "states": [
                    "district_boundary_zone_and_camera_contract",
                    "architectural_palette_and_material_contract",
                ],
            },
            {"path": "evidence-artifacts/menu.png", "kind": "image", "states": ["entry_and_landmark"]},
            {"path": "evidence-artifacts/normal.png", "kind": "image", "states": ["typical_block"]},
            {"path": "evidence-artifacts/quiet.png", "kind": "image", "states": ["boundary_contact"]},
            {"path": "evidence-artifacts/icon.png", "kind": "image", "states": ["opening_negative"]},
            {"path": "evidence-artifacts/dense.png", "kind": "image", "states": ["view_corridor_termination"]},
            {"path": "evidence-artifacts/vfx.png", "kind": "image", "states": ["dense_interaction"]},
            {"path": "evidence-artifacts/result.png", "kind": "image", "states": ["objective_or_extraction"]},
            {"path": "evidence-artifacts/menu-interaction.png", "kind": "image", "states": ["overview_and_repetition_overlay"]},
            {"path": "evidence-artifacts/material-same-zone.png", "kind": "image", "states": ["same_zone_palette_cluster"]},
            {"path": "evidence-artifacts/material-cross-zone.png", "kind": "image", "states": ["cross_zone_palette_transition"]},
            {"path": "evidence-artifacts/material-detail.png", "kind": "image", "states": ["texture_preserving_material_detail"]},
            {
                "path": "evidence-artifacts/motion.avi",
                "kind": "video",
                "states": ["dense_interaction", "objective_or_extraction", "camera_motion_and_restoration"],
            },
        ]

        def run_with(candidate_artifacts: list[dict]) -> tuple[subprocess.CompletedProcess[str], dict]:
            source = load_eval_evidence()
            source["case_id"] = "high-angle-3d-district-complete"
            source["scores"]["asset_pipeline"] = {
                "score": 4,
                "evidence": ["fixture: semantic architectural material profiles and target-build raw states"],
            }
            source["gates"]["high_angle_3d_district_composition_evidence"] = {
                "status": "pass",
                "evidence": ["fixture: complete district composition camera and semantic material packet"],
                "reviewer": {"role": "builder", "context": "fixture builder district review"},
                "artifacts": candidate_artifacts,
            }
            with tempfile.TemporaryDirectory() as directory:
                evidence_path = Path(directory) / "evidence.json"
                report_path = Path(directory) / "scorecard.json"
                evidence_path.write_text(json.dumps(source), encoding="utf-8")
                completed = run_script(
                    "eval_scorecard.py",
                    "--rubric",
                    str(ROOT / "evals" / "rubric.json"),
                    "--case",
                    "high-angle-3d-district-complete",
                    "--evidence",
                    str(evidence_path),
                    "--json-output",
                    str(report_path),
                    "--summary",
                )
                report = json.loads(report_path.read_text(encoding="utf-8"))
            return completed, report

        completed, report = run_with(artifacts)
        gate = next(item for item in report["gates"] if item["id"] == "high_angle_3d_district_composition_evidence")
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertEqual(gate["status"], "pass")
        self.assertEqual(gate["validation_failures"], [])

        missing_same_zone = [
            {**item, "states": [state for state in item["states"] if state != "same_zone_palette_cluster"]}
            for item in artifacts
        ]
        completed, report = run_with(missing_same_zone)
        gate = next(item for item in report["gates"] if item["id"] == "high_angle_3d_district_composition_evidence")
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(gate["status"], "fail")
        self.assertTrue(
            any("same_zone_palette_cluster" in failure for failure in gate["validation_failures"]),
            gate["validation_failures"],
        )

    def test_eval_high_angle_environment_integrity_fails_closed_without_render_ground_state(self) -> None:
        source = load_eval_evidence()
        source["case_id"] = "high-angle-3d-district-complete"
        gate_evidence = source["gates"]["high_angle_environment_integrity_evidence"]
        for artifact in gate_evidence["artifacts"]:
            artifact["states"] = [
                state
                for state in artifact["states"]
                if state != "render_ground_coverage_and_seams"
            ]
        source["gates"]["high_angle_3d_district_composition_evidence"] = {
            "status": "pass",
            "evidence": ["fixture: valid district composition packet"],
            "reviewer": {"role": "builder", "context": "fixture builder district review"},
            "artifacts": [
                {"path": "evidence-artifacts/report.md", "kind": "report", "states": ["district_boundary_zone_and_camera_contract", "architectural_palette_and_material_contract"]},
                {"path": "evidence-artifacts/menu.png", "kind": "image", "states": ["entry_and_landmark"]},
                {"path": "evidence-artifacts/normal.png", "kind": "image", "states": ["typical_block"]},
                {"path": "evidence-artifacts/quiet.png", "kind": "image", "states": ["boundary_contact"]},
                {"path": "evidence-artifacts/icon.png", "kind": "image", "states": ["opening_negative"]},
                {"path": "evidence-artifacts/dense.png", "kind": "image", "states": ["view_corridor_termination"]},
                {"path": "evidence-artifacts/vfx.png", "kind": "image", "states": ["dense_interaction"]},
                {"path": "evidence-artifacts/result.png", "kind": "image", "states": ["objective_or_extraction"]},
                {"path": "evidence-artifacts/menu-interaction.png", "kind": "image", "states": ["overview_and_repetition_overlay"]},
                {"path": "evidence-artifacts/material-same-zone.png", "kind": "image", "states": ["same_zone_palette_cluster"]},
                {"path": "evidence-artifacts/material-cross-zone.png", "kind": "image", "states": ["cross_zone_palette_transition"]},
                {"path": "evidence-artifacts/material-detail.png", "kind": "image", "states": ["texture_preserving_material_detail"]},
                {"path": "evidence-artifacts/motion.avi", "kind": "video", "states": ["dense_interaction", "objective_or_extraction", "camera_motion_and_restoration"]}
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            evidence_path = Path(directory) / "evidence.json"
            report_path = Path(directory) / "scorecard.json"
            evidence_path.write_text(json.dumps(source), encoding="utf-8")
            completed = run_script(
                "eval_scorecard.py",
                "--rubric",
                str(ROOT / "evals" / "rubric.json"),
                "--case",
                "high-angle-3d-district-complete",
                "--evidence",
                str(evidence_path),
                "--json-output",
                str(report_path),
                "--summary",
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        gate = next(
            item
            for item in report["gates"]
            if item["id"] == "high_angle_environment_integrity_evidence"
        )
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertEqual(gate["status"], "fail")
        self.assertTrue(
            any("render_ground_coverage_and_seams" in failure for failure in gate["validation_failures"]),
            gate["validation_failures"],
        )

    def test_eval_complete_slice_accepts_solid_audio(self) -> None:
        source = load_eval_evidence()
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


@unittest.skipUnless(importlib.util.find_spec("PIL"), "Pillow is not installed")
class IconOpticalAuditTests(unittest.TestCase):
    def test_optical_audit_passes_balanced_family_and_fails_shifted_icon(self) -> None:
        from PIL import Image, ImageDraw

        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            centered_a = temp / "centered-a.png"
            centered_b = temp / "centered-b.png"
            shifted = temp / "shifted.png"
            for path, bounds in (
                (centered_a, (8, 8, 24, 24)),
                (centered_b, (7, 7, 25, 25)),
                (shifted, (0, 8, 16, 24)),
            ):
                image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
                ImageDraw.Draw(image).ellipse(bounds, fill=(255, 255, 255, 255))
                image.save(path)

            passing = run_script(
                "icon_optical_audit.py",
                "--image",
                str(centered_a),
                "--image",
                str(centered_b),
                "--max-center-offset-ratio",
                "0.05",
                "--max-weight-ratio",
                "1.5",
                "--summary",
            )
            failing = run_script(
                "icon_optical_audit.py",
                "--image",
                str(centered_a),
                "--image",
                str(shifted),
                "--max-center-offset-ratio",
                "0.1",
                "--summary",
            )
        self.assertEqual(passing.returncode, 0, passing.stdout)
        self.assertIn("[PASS]", passing.stdout)
        self.assertEqual(failing.returncode, 1, failing.stdout)
        self.assertIn("[FAIL]", failing.stdout)


if __name__ == "__main__":
    unittest.main()
