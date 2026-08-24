#!/usr/bin/env python3
"""Engine-backed regression tests for third-person production-HUD mouse routing."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "assets" / "godot-tests" / "third_person_hud_mouse_probe.gd"


def find_godot() -> str | None:
    configured = os.environ.get("GODOT_BIN")
    if configured and Path(configured).is_file():
        return configured
    for name in ("godot4", "godot"):
        discovered = shutil.which(name)
        if discovered:
            return discovered
    return None


def run_probe(godot: str, project: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(project),
            "--script",
            "res://third_person_hud_mouse_probe.gd",
            "--",
            "scene=res://fixture.tscn",
            "yaw_pivot=Yaw",
            "pitch_pivot=Yaw/Pitch",
            "hud_root=HUD/FullScreenRoot",
            "mouse_delta=30:20",
        ],
        cwd=project,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
        check=False,
        timeout=30,
    )


@unittest.skipUnless(find_godot(), "Set GODOT_BIN or place Godot 4 on PATH")
class ThirdPersonHudMouseProbeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.godot = find_godot()
        assert cls.godot is not None

    def _make_fixture(self, directory: str, callback: str) -> Path:
        project = Path(directory)
        (project / "project.godot").write_text(
            'config_version=5\n\n'
            '[application]\nconfig/name="HUD Mouse Routing Test"\n\n'
            '[display]\nwindow/size/viewport_width=640\nwindow/size/viewport_height=360\n',
            encoding="utf-8",
        )
        shutil.copy2(PROBE, project)
        (project / "controller.gd").write_text(
            'extends Node3D\n\n'
            '@onready var pitch: Node3D = $Pitch\n\n'
            f'func {callback}(event: InputEvent) -> void:\n'
            '\tif event is InputEventMouseMotion:\n'
            '\t\trotation.y -= event.relative.x * 0.01\n'
            '\t\tpitch.rotation.x -= event.relative.y * 0.01\n',
            encoding="utf-8",
        )
        (project / "hud.gd").write_text(
            'extends Control\n\n'
            'func _gui_input(event: InputEvent) -> void:\n'
            '\tif event is InputEventMouseMotion:\n'
            '\t\taccept_event()\n',
            encoding="utf-8",
        )
        (project / "fixture.tscn").write_text(
            '[gd_scene load_steps=3 format=3]\n\n'
            '[ext_resource type="Script" path="res://controller.gd" id="1_controller"]\n'
            '[ext_resource type="Script" path="res://hud.gd" id="2_hud"]\n\n'
            '[node name="Fixture" type="Node"]\n\n'
            '[node name="Yaw" type="Node3D" parent="."]\n'
            'script = ExtResource("1_controller")\n\n'
            '[node name="Pitch" type="Node3D" parent="Yaw"]\n\n'
            '[node name="HUD" type="CanvasLayer" parent="."]\n\n'
            '[node name="FullScreenRoot" type="Control" parent="HUD"]\n'
            'layout_mode = 3\n'
            'anchors_preset = 15\n'
            'anchor_right = 1.0\n'
            'anchor_bottom = 1.0\n'
            'grow_horizontal = 2\n'
            'grow_vertical = 2\n'
            'mouse_filter = 0\n'
            'script = ExtResource("2_hud")\n',
            encoding="utf-8",
        )
        return project

    def test_input_stage_look_survives_consuming_fullscreen_hud(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self._make_fixture(directory, "_input")
            completed = run_probe(self.godot, project)
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] Production-HUD mouse routing passed", completed.stdout)

    def test_unhandled_look_is_blocked_by_consuming_fullscreen_hud(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = self._make_fixture(directory, "_unhandled_input")
            completed = run_probe(self.godot, project)
        self.assertEqual(completed.returncode, 1, completed.stdout)
        self.assertIn("GUI may consume motion before _unhandled_input", completed.stdout)


if __name__ == "__main__":
    unittest.main()
