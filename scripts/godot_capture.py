#!/usr/bin/env python3
"""Run bounded Godot import/play/capture checks and emit a compact report."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time
from typing import Any


FAILURE_PATTERN = re.compile(
    r"SCRIPT ERROR:|Parse Error:|Failed to load script|Failed loading resource|"
    r"Cannot load resource file|Error while parsing|E \d+:\d+:\d+\.\d+",
    re.IGNORECASE,
)

FORCED_QUIT_DIAGNOSTIC_PATTERN = re.compile(
    r"ObjectDB instances leaked at exit|Resources still in use at exit|"
    r"Orphan StringName|orphan nodes? detected|leaked instance(?:s)? at exit",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a deterministic bounded Godot import, runtime smoke test, or movie capture."
    )
    parser.add_argument("--project", default=".", help="Project directory or project.godot path.")
    parser.add_argument("--godot", help="Godot binary; otherwise GODOT_BIN or PATH discovery is used.")
    parser.add_argument("--mode", choices=("import", "run", "capture"), default="run")
    parser.add_argument("--scene", help="Scene to run, preferably res://path/to/scene.tscn.")
    parser.add_argument("--script", help="Project-owned res:// SceneTree script to run (run mode only).")
    parser.add_argument("--frames", type=int, help="Iterations before automatic quit (default: 120).")
    parser.add_argument("--fixed-fps", type=int, default=30, help="Capture simulation FPS.")
    parser.add_argument(
        "--proof-seconds",
        type=float,
        help=(
            "Capture a 15-20 second deterministic delivery proof; derives --frames from "
            "--fixed-fps and cannot be combined with --frames."
        ),
    )
    parser.add_argument("--output", help="Capture output (.avi or .png sequence path). Required for capture.")
    parser.add_argument("--log-file", help="Godot log path.")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--headless", action="store_true", help="Use headless mode for import/run.")
    parser.add_argument(
        "--skip-import",
        action="store_true",
        help="Skip the default import preflight before run/capture (use only when already proven current).",
    )
    parser.add_argument(
        "--user-arg",
        action="append",
        default=[],
        help="Project argument passed after -- (repeatable); use a project-owned test driver to consume it.",
    )
    parser.add_argument("--json-output", help="Write a machine-readable run report.")
    parser.add_argument("--summary", action="store_true", help="Print only the tail of engine output.")
    parser.add_argument("--max-lines", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true", help="Validate and print the command without launching Godot.")
    args = parser.parse_args()
    if args.proof_seconds is not None:
        if args.mode != "capture":
            parser.error("--proof-seconds requires --mode capture")
        if args.frames is not None:
            parser.error("--proof-seconds and --frames are mutually exclusive")
        if not 15 <= args.proof_seconds <= 20:
            parser.error("--proof-seconds must be between 15 and 20 seconds")
        args.frames = round(args.proof_seconds * args.fixed_fps)
    elif args.frames is None:
        args.frames = 120
    if args.frames < 1 or args.fixed_fps < 1 or args.timeout < 1 or args.max_lines < 0:
        parser.error("frames, FPS, timeout, and line limit must be positive (max-lines may be zero)")
    if args.mode == "capture" and not args.output:
        parser.error("--output is required for --mode capture")
    if args.mode == "capture" and args.headless:
        parser.error("capture requires rendering; do not combine --mode capture with --headless")
    if args.scene and args.script:
        parser.error("--scene and --script are mutually exclusive")
    if args.script and args.mode != "run":
        parser.error("--script is supported only in run mode")
    return args


def find_root(value: str) -> Path:
    candidate = Path(value).expanduser().resolve()
    if candidate.is_file():
        if candidate.name != "project.godot":
            raise ValueError(f"Expected project.godot, got: {candidate}")
        candidate = candidate.parent
    if not candidate.is_dir() or not (candidate / "project.godot").is_file():
        raise ValueError(f"Godot project not found: {candidate}")
    return candidate


def discover_godot(explicit: str | None) -> str | None:
    candidates = [explicit, os.environ.get("GODOT_BIN"), "godot", "godot4", "godot-mono", "godot_mono"]
    for candidate in filter(None, candidates):
        expanded = Path(str(candidate)).expanduser()
        if expanded.is_file():
            return str(expanded.resolve())
        found = shutil.which(str(candidate))
        if found:
            return found
    if os.name == "nt":
        portable_candidates: list[Path] = []
        for folder_name in ("Desktop", "Downloads"):
            folder = Path.home() / folder_name
            if folder.is_dir():
                portable_candidates.extend(folder.glob("Godot*.exe"))
        if portable_candidates:
            return str(sorted(portable_candidates, key=lambda path: path.name, reverse=True)[0].resolve())
    macos = Path("/Applications/Godot.app/Contents/MacOS/Godot")
    return str(macos) if macos.is_file() else None


def resolve_output(root: Path, value: str | None) -> Path | None:
    if value is None:
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def build_command(args: argparse.Namespace, root: Path, godot: str) -> tuple[list[str], Path | None, Path | None]:
    capture_output = resolve_output(root, args.output)
    log_file = resolve_output(root, args.log_file)
    command = [godot]
    if args.headless or args.mode == "import":
        command.append("--headless")
    command.extend(("--path", str(root)))
    if log_file:
        command.extend(("--log-file", str(log_file)))
    if args.mode == "import":
        command.append("--import")
    else:
        if args.script:
            command.extend(("--script", args.script))
        elif args.scene:
            command.extend(("--scene", args.scene))
        command.extend(("--quit-after", str(args.frames)))
        if args.mode == "capture":
            command.extend(("--write-movie", str(capture_output), "--fixed-fps", str(args.fixed_fps)))
    if args.user_arg:
        command.append("--")
        command.extend(args.user_arg)
    return command, capture_output, log_file


def import_command(root: Path, godot: str) -> list[str]:
    return [godot, "--headless", "--path", str(root), "--import"]


def compact_output(output: str, max_lines: int) -> tuple[str, int]:
    lines = output.rstrip().splitlines()
    if max_lines == 0:
        return "", len(lines)
    if len(lines) <= max_lines:
        return "\n".join(lines), 0
    return "\n".join(lines[-max_lines:]), len(lines) - max_lines


def execute(
    command: list[str],
    timeout: int,
    name: str,
    scan_engine_errors: bool = True,
    forced_quit: bool = False,
) -> dict[str, Any]:
    started = time.monotonic()
    timed_out = False
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
        exit_code = completed.returncode
        output = completed.stdout
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = 124
        partial = exc.stdout or ""
        output = partial.decode(errors="replace") if isinstance(partial, bytes) else partial
        output += f"\nTimed out after {timeout}s"
    except OSError as exc:
        exit_code = 127
        output = f"Could not start command: {exc}"
    output_lines = output.splitlines()
    forced_quit_diagnostics = (
        [line for line in output_lines if FORCED_QUIT_DIAGNOSTIC_PATTERN.search(line)]
        if forced_quit
        else []
    )
    engine_errors = []
    if scan_engine_errors:
        engine_errors = [
            line
            for line in output_lines
            if FAILURE_PATTERN.search(line)
            and not (forced_quit and FORCED_QUIT_DIAGNOSTIC_PATTERN.search(line))
        ]
    return {
        "name": name,
        "command": command,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "duration_seconds": round(time.monotonic() - started, 3),
        "engine_error_lines": engine_errors,
        "forced_quit_diagnostic_lines": forced_quit_diagnostics,
        "stdout": output,
        "failed": exit_code != 0 or bool(engine_errors),
    }


def main() -> int:
    args = parse_args()
    try:
        root = find_root(args.project)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    godot = discover_godot(args.godot)
    if godot is None:
        if not args.dry_run:
            print("[ERROR] Godot binary not found; pass --godot or set GODOT_BIN", file=sys.stderr)
            return 2
        godot = args.godot or "godot"
    command, capture_output, log_file = build_command(args, root, godot)
    commands = [[godot, "--version"]]
    if args.mode != "import" and not args.skip_import:
        commands.append(import_command(root, godot))
    commands.append(command)
    if args.dry_run:
        for dry_command in commands:
            print(f"[DRY-RUN] {shlex.join(dry_command)}")
        if args.mode == "capture":
            print("[WARN] --write-movie can create a large AVI or image sequence; use run mode for profiling.")
            if args.proof_seconds is not None:
                print(
                    f"[INFO] Delivery proof={args.proof_seconds:g}s frames={args.frames} "
                    f"fixed_fps={args.fixed_fps}; watch the entire recording before handoff."
                )
        return 0
    if capture_output:
        capture_output.parent.mkdir(parents=True, exist_ok=True)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    phases: list[dict[str, Any]] = []
    version_phase = execute(commands[0], args.timeout, "version", scan_engine_errors=False)
    phases.append(version_phase)
    if not version_phase["failed"]:
        next_index = 1
        if args.mode != "import" and not args.skip_import:
            preflight = execute(commands[next_index], args.timeout, "import")
            phases.append(preflight)
            next_index += 1
        else:
            preflight = None
        if preflight is None or not preflight["failed"]:
            phases.append(
                execute(
                    commands[next_index],
                    args.timeout,
                    args.mode,
                    forced_quit=args.mode in {"run", "capture"},
                )
            )
    failed = any(phase["failed"] for phase in phases)
    engine_errors = [line for phase in phases for line in phase["engine_error_lines"]]
    forced_quit_diagnostics = [
        line for phase in phases for line in phase["forced_quit_diagnostic_lines"]
    ]
    capture_exists = capture_output.exists() if capture_output else None
    if args.mode == "capture" and not capture_exists:
        failed = True
        engine_errors.append("Capture output was not created")
    report: dict[str, Any] = {
        "project": str(root),
        "mode": args.mode,
        "scene": args.scene,
        "script": args.script,
        "frames": None if args.mode == "import" else args.frames,
        "fixed_fps": args.fixed_fps if args.mode == "capture" else None,
        "proof_seconds": args.proof_seconds if args.mode == "capture" else None,
        "pre_import": args.mode != "import" and not args.skip_import,
        "phases": phases,
        "exit_code": next((phase["exit_code"] for phase in phases if phase["failed"]), 0),
        "timed_out": any(phase["timed_out"] for phase in phases),
        "duration_seconds": round(sum(phase["duration_seconds"] for phase in phases), 3),
        "engine_error_lines": engine_errors,
        "forced_quit_diagnostic_lines": forced_quit_diagnostics,
        "forced_quit_diagnostics_blocking": False if forced_quit_diagnostics else None,
        "capture_output": str(capture_output) if capture_output else None,
        "capture_exists": capture_exists,
        "log_file": str(log_file) if log_file else None,
        "limitations": [
            "This runner does not synthesize input. Use --user-arg with a project-owned deterministic test driver or a UI automation layer.",
            "A successful bounded run proves startup stability for the exercised state, not playability or visual quality.",
            "Forced-quit ObjectDB/resource/orphan diagnostics are retained separately and need a normal-exit reproduction before they can be dismissed as runner-only noise.",
            "Movie capture can create large files and adds overhead; use run mode for performance profiling unless a recording is required.",
            "A delivery proof must be watched back in full; file creation alone does not prove useful framing, motion, input progression, or absence of dead time.",
        ],
    }
    if args.json_output:
        json_path = resolve_output(root, args.json_output)
        assert json_path is not None
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    for phase in phases:
        print(
            f"[INFO] Phase={phase['name']} exit={phase['exit_code']} "
            f"duration={phase['duration_seconds']:.2f}s command={shlex.join(phase['command'])}"
        )
        phase_output = phase["stdout"]
        line_limit = args.max_lines if args.summary else max(len(phase_output.splitlines()), 1)
        shown, omitted = compact_output(phase_output, line_limit)
        if shown:
            print(shown)
        if omitted:
            print(f"[INFO] {omitted} earlier {phase['name']} line(s) omitted; use --json-output or --log-file")
        if phase["forced_quit_diagnostic_lines"]:
            print(
                f"[DIAGNOSTIC] {len(phase['forced_quit_diagnostic_lines'])} forced-quit shutdown "
                "line(s) retained as non-blocking; reproduce with a normal project-owned exit before dismissal"
            )
    print("[FAIL] Godot run/capture failed" if failed else "[PASS] Godot run/capture passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
