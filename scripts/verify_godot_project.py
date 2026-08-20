#!/usr/bin/env python3
"""Static and optional engine smoke checks for a Godot project."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Iterable


IGNORED_DIRECTORIES = {
    ".git",
    ".godot",
    ".import",
    ".mono",
    "bin",
    "obj",
}

TEXT_EXTENSIONS = {
    ".cfg",
    ".cs",
    ".gd",
    ".gdextension",
    ".gdshader",
    ".godot",
    ".tres",
    ".tscn",
}

QUOTED_RES_PATH = re.compile(r"(?P<quote>['\"])(?P<path>res://.*?)(?P=quote)")
FEATURES_PATTERN = re.compile(r"config/features\s*=\s*PackedStringArray\((.*?)\)")
QUOTED_VALUE = re.compile(r'"([^"]+)"')
PROJECT_NAME_PATTERN = re.compile(r'^config/name\s*=\s*"([^"]*)"', re.MULTILINE)
MAIN_SCENE_PATTERN = re.compile(r'^run/main_scene\s*=\s*"([^"]*)"', re.MULTILINE)

NODE_CLASS_NAMES = (
    "Node",
    "Node2D",
    "Node3D",
    "Control",
    "CanvasLayer",
    "CharacterBody2D",
    "CharacterBody3D",
    "RigidBody2D",
    "RigidBody3D",
    "StaticBody2D",
    "StaticBody3D",
    "Area2D",
    "Area3D",
    "Sprite2D",
    "AnimatedSprite2D",
    "MeshInstance3D",
    "Camera2D",
    "Camera3D",
    "CollisionShape2D",
    "CollisionShape3D",
    "AnimationPlayer",
    "AnimationTree",
    "Label",
    "Button",
    "Panel",
    "TextureRect",
    "ColorRect",
    "VBoxContainer",
    "HBoxContainer",
    "GridContainer",
    "MarginContainer",
)
NODE_NEW_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(name) for name in NODE_CLASS_NAMES) + r")\.new\s*\("
)

ENGINE_FAILURE_PATTERN = re.compile(
    r"SCRIPT ERROR:|Parse Error:|Failed to load script|Failed loading resource|"
    r"Cannot load resource file|Error while parsing",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Godot resource paths and scene-first warning signs, with optional "
            "Godot import/runtime smoke tests."
        )
    )
    parser.add_argument(
        "--project",
        default=".",
        help="Project directory or path to project.godot (default: current directory).",
    )
    parser.add_argument(
        "--godot",
        help="Godot editor binary. Otherwise use GODOT_BIN or a binary on PATH.",
    )
    parser.add_argument(
        "--engine",
        action="store_true",
        help="Run a headless Godot import check after static checks.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run a bounded headless smoke test after import. Implies --engine.",
    )
    parser.add_argument(
        "--scene",
        help="Specific scene for --run, preferably res://path/to/scene.tscn.",
    )
    parser.add_argument(
        "--frames",
        type=int,
        default=5,
        help="Number of engine iterations for --run (default: 5).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout in seconds for each Godot command (default: 120).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print successful Godot command output and skipped dynamic references.",
    )
    args = parser.parse_args()
    if args.frames < 1:
        parser.error("--frames must be at least 1")
    if args.timeout < 1:
        parser.error("--timeout must be at least 1")
    if args.scene and not args.run:
        parser.error("--scene requires --run")
    if args.run:
        args.engine = True
    return args


def find_project_root(value: str) -> Path:
    candidate = Path(value).expanduser().resolve()
    if candidate.is_file():
        if candidate.name != "project.godot":
            raise ValueError(f"Expected project.godot, got file: {candidate}")
        return candidate.parent
    if not candidate.is_dir():
        raise ValueError(f"Project path does not exist: {candidate}")
    if not (candidate / "project.godot").is_file():
        raise ValueError(f"project.godot not found in: {candidate}")
    return candidate


def iter_source_files(root: Path) -> Iterable[Path]:
    for current, directories, files in os.walk(root):
        directories[:] = [name for name in directories if name not in IGNORED_DIRECTORIES]
        current_path = Path(current)
        for name in files:
            path = current_path / name
            if path.name == "project.godot" or path.suffix.lower() in TEXT_EXTENSIONS:
                yield path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def normalize_resource_reference(reference: str) -> str | None:
    value = reference.split("::", 1)[0]
    if any(marker in value for marker in ("%", "{", "}")):
        return None
    return value


def scan_project(root: Path, verbose: bool) -> tuple[list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    counts = {"scenes": 0, "resources": 0, "gdscript": 0, "csharp": 0, "shaders": 0}
    missing_seen: set[tuple[str, str]] = set()

    for path in iter_source_files(root):
        suffix = path.suffix.lower()
        if suffix == ".tscn":
            counts["scenes"] += 1
        elif suffix == ".tres":
            counts["resources"] += 1
        elif suffix == ".gd":
            counts["gdscript"] += 1
        elif suffix == ".cs":
            counts["csharp"] += 1
        elif suffix == ".gdshader":
            counts["shaders"] += 1

        content = read_text(path)
        relative_source = path.relative_to(root).as_posix()
        for match in QUOTED_RES_PATH.finditer(content):
            reference = match.group("path")
            normalized = normalize_resource_reference(reference)
            if normalized is None:
                if verbose:
                    warnings.append(
                        f"Skipped dynamic resource path in {relative_source}: {reference}"
                    )
                continue
            relative_target = normalized.removeprefix("res://")
            target = (root / Path(relative_target.replace("/", os.sep))).resolve()
            if not is_within(target, root):
                errors.append(
                    f"Resource path escapes the project in {relative_source}: {reference}"
                )
                continue
            if not target.exists():
                key = (relative_source, normalized)
                if key not in missing_seen:
                    missing_seen.add(key)
                    errors.append(
                        f"Missing resource referenced by {relative_source}: {normalized}"
                    )

        if suffix == ".gd":
            constructions = len(NODE_NEW_PATTERN.findall(content))
            lower_path = relative_source.lower()
            editor_context = (
                "@tool" in content
                or "extends EditorScript" in content
                or "extends EditorPlugin" in content
                or any(part in lower_path for part in ("editor", "tool", "generator"))
            )
            if constructions >= 6 and not editor_context:
                warnings.append(
                    f"Review scene-first design in {relative_source}: "
                    f"{constructions} native node constructions found"
                )

    if counts["scenes"] == 0 and (counts["gdscript"] or counts["csharp"]):
        warnings.append("Scripts exist but no .tscn scenes were found")

    return errors, warnings, counts


def project_metadata(project_file: Path) -> tuple[str, list[str], str | None]:
    content = read_text(project_file)
    name_match = PROJECT_NAME_PATTERN.search(content)
    features_match = FEATURES_PATTERN.search(content)
    main_match = MAIN_SCENE_PATTERN.search(content)
    name = name_match.group(1) if name_match else project_file.parent.name
    features = QUOTED_VALUE.findall(features_match.group(1)) if features_match else []
    main_scene = main_match.group(1) if main_match else None
    return name, features, main_scene


def discover_godot(explicit: str | None) -> str | None:
    candidates: list[str] = []
    if explicit:
        candidates.append(explicit)
    environment_value = os.environ.get("GODOT_BIN")
    if environment_value:
        candidates.append(environment_value)
    candidates.extend(("godot", "godot4", "godot-mono", "godot_mono"))

    for candidate in candidates:
        expanded = str(Path(candidate).expanduser())
        if Path(expanded).is_file():
            return str(Path(expanded).resolve())
        discovered = shutil.which(candidate)
        if discovered:
            return discovered

    if os.name == "nt":
        portable_candidates: list[Path] = []
        for folder_name in ("Desktop", "Downloads"):
            folder = Path.home() / folder_name
            if folder.is_dir():
                portable_candidates.extend(folder.glob("Godot*.exe"))
        if portable_candidates:
            return str(sorted(portable_candidates, key=lambda path: path.name, reverse=True)[0].resolve())

    macos_binary = Path("/Applications/Godot.app/Contents/MacOS/Godot")
    if macos_binary.is_file():
        return str(macos_binary)
    return None


def run_command(command: list[str], timeout: int) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        partial = exc.stdout or ""
        if isinstance(partial, bytes):
            partial = partial.decode(errors="replace")
        return 124, f"Command timed out after {timeout}s\n{partial}"
    except OSError as exc:
        return 127, f"Could not start command: {exc}"
    return completed.returncode, completed.stdout


def compact_output(output: str, limit: int = 120) -> str:
    lines = output.rstrip().splitlines()
    if len(lines) <= limit:
        return "\n".join(lines)
    omitted = len(lines) - limit
    return f"... {omitted} earlier lines omitted ...\n" + "\n".join(lines[-limit:])


def engine_check(
    root: Path,
    godot: str,
    run_game: bool,
    scene: str | None,
    frames: int,
    timeout: int,
    verbose: bool,
    main_scene: str | None,
) -> list[str]:
    errors: list[str] = []

    version_code, version_output = run_command([godot, "--version"], timeout)
    if version_code != 0:
        return [f"Godot version check failed ({version_code}): {compact_output(version_output)}"]
    print(f"[OK] Godot: {version_output.strip() or godot}")

    import_command = [godot, "--headless", "--path", str(root), "--import"]
    import_code, import_output = run_command(import_command, timeout)
    import_failed = import_code != 0 or bool(ENGINE_FAILURE_PATTERN.search(import_output))
    if import_failed:
        errors.append(
            f"Godot import check failed ({import_code}):\n{compact_output(import_output)}"
        )
    else:
        print("[OK] Godot import check")
        if verbose and import_output.strip():
            print(compact_output(import_output))

    if not run_game or import_failed:
        return errors

    if scene is None and not main_scene:
        return errors + ["Cannot run smoke test: project has no main scene and --scene was not given"]

    run_command_line = [
        godot,
        "--headless",
        "--path",
        str(root),
        "--quit-after",
        str(frames),
    ]
    if scene:
        run_command_line.extend(("--scene", scene))
    run_code, run_output = run_command(run_command_line, timeout)
    run_failed = run_code != 0 or bool(ENGINE_FAILURE_PATTERN.search(run_output))
    if run_failed:
        errors.append(
            f"Godot runtime smoke test failed ({run_code}):\n{compact_output(run_output)}"
        )
    else:
        tested = scene or main_scene or "main scene"
        print(f"[OK] Runtime smoke test: {tested} ({frames} iterations)")
        if verbose and run_output.strip():
            print(compact_output(run_output))
    return errors


def main() -> int:
    args = parse_args()
    try:
        root = find_project_root(args.project)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    project_file = root / "project.godot"
    name, features, main_scene = project_metadata(project_file)
    print(f"[OK] Project: {name} ({root})")
    if features:
        print(f"[INFO] Features: {', '.join(features)}")
    print(f"[INFO] Main scene: {main_scene or 'not configured'}")

    errors, warnings, counts = scan_project(root, args.verbose)
    print(
        "[INFO] Sources: "
        f"{counts['scenes']} scenes, {counts['resources']} resources, "
        f"{counts['gdscript']} GDScript, {counts['csharp']} C#, "
        f"{counts['shaders']} shaders"
    )

    for warning in warnings:
        print(f"[WARN] {warning}")

    if args.engine:
        godot = discover_godot(args.godot)
        if godot is None:
            errors.append(
                "Godot editor binary not found; pass --godot or set GODOT_BIN"
            )
        else:
            errors.extend(
                engine_check(
                    root=root,
                    godot=godot,
                    run_game=args.run,
                    scene=args.scene,
                    frames=args.frames,
                    timeout=args.timeout,
                    verbose=args.verbose,
                    main_scene=main_scene,
                )
            )

    sys.stdout.flush()
    for error in errors:
        print(f"[ERROR] {error}", file=sys.stderr)

    if errors:
        print(f"[FAIL] {len(errors)} error(s), {len(warnings)} warning(s)", file=sys.stderr)
        return 1

    print(f"[PASS] 0 errors, {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
