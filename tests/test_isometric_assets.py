#!/usr/bin/env python3
"""Engine-backed smoke tests for reusable isometric Godot assets."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ROOT / "assets" / "godot-components"
PROBES = ROOT / "assets" / "godot-tests"


def find_godot() -> str | None:
    configured = os.environ.get("GODOT_BIN")
    if configured and Path(configured).is_file():
        return configured
    for name in ("godot4", "godot"):
        discovered = shutil.which(name)
        if discovered:
            return discovered
    return None


def run_godot(godot: str, project: Path, script: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(project),
            "--script",
            script,
            "--",
            *arguments,
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
class IsometricAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.godot = find_godot()
        assert cls.godot is not None

    def test_projection_component_and_probe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.godot").write_text(
                'config_version=5\n\n[application]\nconfig/name="Isometric Projection Test"\n',
                encoding="utf-8",
            )
            shutil.copy2(COMPONENTS / "isometric_projection.gd", project)
            shutil.copy2(PROBES / "isometric_projection_probe.gd", project)
            (project / "projection.tres").write_text(
                '[gd_resource type="Resource" script_class="IsometricProjection" load_steps=2 format=3]\n\n'
                '[ext_resource type="Script" path="res://isometric_projection.gd" id="1_projection"]\n\n'
                '[resource]\n'
                'script = ExtResource("1_projection")\n'
                'tile_size = Vector2(128, 64)\n'
                'elevation_step = 32.0\n'
                'origin = Vector2(17, -9)\n',
                encoding="utf-8",
            )
            completed = run_godot(
                self.godot,
                project,
                "res://isometric_projection_probe.gd",
                "projection=res://projection.tres",
                "cells=0:0:0;1:0:0;0:1:0;-2:3:0;4:-1:2",
            )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] Isometric projection round-trip passed", completed.stdout)

    def test_navigation_probe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.godot").write_text(
                'config_version=5\n\n[application]\nconfig/name="Isometric Navigation Test"\n',
                encoding="utf-8",
            )
            shutil.copy2(PROBES / "isometric_navigation_probe.gd", project)
            (project / "navigation_adapter.gd").write_text(
                'extends Node\n\n'
                'func find_cell_path(start: Vector3i, goal: Vector3i) -> Array[Vector3i]:\n'
                '\tvar path: Array[Vector3i] = [start]\n'
                '\tvar current := start\n'
                '\twhile current.x != goal.x:\n'
                '\t\tcurrent.x += 1 if goal.x > current.x else -1\n'
                '\t\tpath.append(current)\n'
                '\twhile current.y != goal.y:\n'
                '\t\tcurrent.y += 1 if goal.y > current.y else -1\n'
                '\t\tpath.append(current)\n'
                '\twhile current.z != goal.z:\n'
                '\t\tcurrent.z += 1 if goal.z > current.z else -1\n'
                '\t\tpath.append(current)\n'
                '\treturn path\n\n'
                'func is_cell_walkable(_cell: Vector3i) -> bool:\n'
                '\treturn true\n',
                encoding="utf-8",
            )
            (project / "fixture.tscn").write_text(
                '[gd_scene load_steps=2 format=3]\n\n'
                '[ext_resource type="Script" path="res://navigation_adapter.gd" id="1_adapter"]\n\n'
                '[node name="Fixture" type="Node"]\n\n'
                '[node name="NavigationAdapter" type="Node" parent="."]\n'
                'script = ExtResource("1_adapter")\n',
                encoding="utf-8",
            )
            completed = run_godot(
                self.godot,
                project,
                "res://isometric_navigation_probe.gd",
                "scene=res://fixture.tscn",
                "adapter=NavigationAdapter",
                "routes=0:0:0>3:2:0;3:2:0>4:2:1",
                "require_height_change=true",
            )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("[PASS] Isometric navigation passed", completed.stdout)


if __name__ == "__main__":
    unittest.main()
