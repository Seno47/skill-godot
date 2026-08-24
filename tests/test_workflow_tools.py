#!/usr/bin/env python3
"""Smoke tests for parity, progression, and idle-economy workflow helpers."""

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


class GenreRubricTests(unittest.TestCase):
    def test_new_cases_prepare_their_conditional_gates(self) -> None:
        expected = {
            "new-2d-fighting-complete": "fighting_simulation_evidence",
            "new-2d-metroidvania-complete": "metroidvania_progression_evidence",
            "new-idle-clicker-complete": "idle_economy_evidence",
            "new-quest-driven-complete": "quest_transaction_evidence",
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
