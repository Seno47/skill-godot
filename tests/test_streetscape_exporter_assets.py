#!/usr/bin/env python3
"""Engine-backed regression tests for the streetscape evidence exporter."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXPORTER = ROOT / "assets" / "godot-tests" / "streetscape_semantics_exporter.gd"


def find_godot() -> str | None:
    configured = os.environ.get("GODOT_BIN")
    if configured and Path(configured).is_file():
        return configured
    for name in ("godot4", "godot"):
        discovered = shutil.which(name)
        if discovered:
            return discovered
    return None


@unittest.skipUnless(find_godot(), "Set GODOT_BIN or place Godot 4 on PATH")
class StreetscapeExporterAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.godot = find_godot()
        assert cls.godot is not None

    def test_plane_mesh_and_box_mesh_triangle_collection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "project.godot").write_text(
                'config_version=5\n\n'
                '[application]\nconfig/name="Streetscape PrimitiveMesh Regression"\n\n'
                '[rendering]\nrenderer/rendering_method="gl_compatibility"\n',
                encoding="utf-8",
            )
            shutil.copy2(EXPORTER, project / EXPORTER.name)
            completed = subprocess.run(
                [
                    self.godot,
                    "--headless",
                    "--path",
                    str(project),
                    "--script",
                    f"res://{EXPORTER.name}",
                    "--",
                    "--self-test-primitive-mesh",
                    "true",
                ],
                cwd=project,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="replace",
                check=False,
                timeout=30,
            )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn(
            "[PASS] streetscape-primitive-mesh-regression PlaneMesh=2 BoxMesh=12",
            completed.stdout,
        )


if __name__ == "__main__":
    unittest.main()
