#!/usr/bin/env python3
"""Validate Godot MJPEG AVI captures and build a model-visible watchback packet."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import struct
import sys
from typing import Any, BinaryIO, Iterator


class WatchbackError(RuntimeError):
    pass


@dataclass(frozen=True)
class Chunk:
    fourcc: bytes
    offset: int
    size: int
    parents: tuple[bytes, ...]


@dataclass(frozen=True)
class StreamHeader:
    index: int
    stream_type: str
    handler: str
    scale: int
    rate: int
    length: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate every JPEG frame in a Godot MJPEG AVI and extract ordered contact sheets "
            "without ffmpeg, OpenCV, or imageio. Pillow is required for JPEG validation/layout."
        )
    )
    parser.add_argument("--input", required=True, help="Godot --write-movie MJPEG AVI capture.")
    parser.add_argument("--output-dir", required=True, help="Directory for frames, sheets, and report.")
    sampling = parser.add_mutually_exclusive_group()
    sampling.add_argument("--sample-count", type=int, help="Uniform frames to extract, including endpoints.")
    sampling.add_argument(
        "--sample-fps",
        type=float,
        help="Uniform visual sampling rate. Defaults to 2 FPS when no sampling option is supplied.",
    )
    sampling.add_argument(
        "--all-frames",
        action="store_true",
        help="Put every decoded video frame in the visual packet for frame-by-frame review.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=120,
        help="Safety bound for extracted frames; raise explicitly when using --all-frames (default: 120).",
    )
    parser.add_argument("--columns", type=int, default=5, help="Contact-sheet columns (default: 5).")
    parser.add_argument("--rows", type=int, default=4, help="Contact-sheet rows per page (default: 4).")
    parser.add_argument("--thumb-width", type=int, default=320, help="Thumbnail width (default: 320).")
    parser.add_argument(
        "--expected-duration-seconds",
        type=float,
        help="Fail when decoded duration differs by more than --duration-tolerance-seconds.",
    )
    parser.add_argument(
        "--duration-tolerance-seconds",
        type=float,
        default=0.1,
        help="Allowed expected-duration drift (default: 0.1 seconds).",
    )
    parser.add_argument(
        "--require-temporal-change",
        action="store_true",
        help="Fail when every encoded video frame is byte-identical.",
    )
    parser.add_argument(
        "--max-identical-run-seconds",
        type=float,
        help="Fail when an exact consecutive duplicate run exceeds this duration.",
    )
    parser.add_argument("--prefix", help="Artifact prefix; defaults to the AVI stem.")
    parser.add_argument("--json-output", help="Report path; defaults inside --output-dir.")
    parser.add_argument("--summary", action="store_true", help="Print a compact result.")
    args = parser.parse_args()
    for name in ("sample_count", "max_samples", "columns", "rows", "thumb_width"):
        value = getattr(args, name)
        if value is not None and value < 1:
            parser.error(f"--{name.replace('_', '-')} must be positive")
    for name in (
        "sample_fps",
        "expected_duration_seconds",
        "duration_tolerance_seconds",
        "max_identical_run_seconds",
    ):
        value = getattr(args, name)
        if value is not None and value <= 0:
            parser.error(f"--{name.replace('_', '-')} must be positive")
    return args


def decode_fourcc(value: bytes) -> str:
    return value.decode("ascii", errors="replace")


def read_exact(handle: BinaryIO, size: int, label: str) -> bytes:
    data = handle.read(size)
    if len(data) != size:
        raise WatchbackError(f"truncated {label}: wanted {size} bytes, found {len(data)}")
    return data


def walk_chunks(
    handle: BinaryIO,
    start: int,
    end: int,
    parents: tuple[bytes, ...] = (),
) -> Iterator[Chunk]:
    position = start
    while position + 8 <= end:
        handle.seek(position)
        fourcc = read_exact(handle, 4, "chunk id")
        size = struct.unpack("<I", read_exact(handle, 4, "chunk size"))[0]
        data_start = position + 8
        data_end = data_start + size
        if data_end > end:
            raise WatchbackError(
                f"chunk {decode_fourcc(fourcc)!r} at {position} exceeds its parent boundary"
            )
        if fourcc in {b"LIST", b"RIFF"}:
            if size < 4:
                raise WatchbackError(f"container {decode_fourcc(fourcc)!r} at {position} is too small")
            handle.seek(data_start)
            list_type = read_exact(handle, 4, "container type")
            yield from walk_chunks(handle, data_start + 4, data_end, parents + (list_type,))
        else:
            yield Chunk(fourcc=fourcc, offset=data_start, size=size, parents=parents)
        next_position = data_end + (size & 1)
        if next_position <= position:
            raise WatchbackError(f"non-advancing RIFF chunk at {position}")
        position = next_position
    if position != end and end - position > 1:
        raise WatchbackError(f"{end - position} trailing byte(s) inside RIFF container")


def parse_stream_header(index: int, payload: bytes) -> StreamHeader:
    if len(payload) < 36:
        raise WatchbackError(f"stream header {index} is only {len(payload)} bytes")
    return StreamHeader(
        index=index,
        stream_type=decode_fourcc(payload[0:4]),
        handler=decode_fourcc(payload[4:8]).rstrip("\x00 "),
        scale=struct.unpack_from("<I", payload, 20)[0],
        rate=struct.unpack_from("<I", payload, 24)[0],
        length=struct.unpack_from("<I", payload, 32)[0],
    )


def jpeg_payload(payload: bytes, frame_index: int) -> tuple[bytes, int, int]:
    start = payload.find(b"\xff\xd8")
    end = payload.rfind(b"\xff\xd9")
    if start < 0 or end < start:
        raise WatchbackError(f"video frame {frame_index} is not a complete JPEG image")
    return payload[start : end + 2], start, len(payload) - (end + 2)


def uniform_indices(frame_count: int, requested: int) -> list[int]:
    count = min(frame_count, requested)
    if count <= 1:
        return [0]
    return sorted({round(step * (frame_count - 1) / (count - 1)) for step in range(count)})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    prefix = args.prefix or input_path.stem
    json_path = (
        Path(args.json_output).expanduser().resolve()
        if args.json_output
        else output_dir / f"{prefix}-watchback.json"
    )
    errors: list[str] = []
    warnings: list[str] = []
    report: dict[str, Any] = {
        "schema_version": 1,
        "input": str(input_path),
        "result": "fail",
        "errors": errors,
        "warnings": warnings,
        "limitations": [
            "This validates the visual MJPEG stream only; embedded audio is not decoded or listened to.",
            "Uniform contact sheets do not prove normal-speed smoothness or reveal every between-sample defect.",
            "Use normal-speed playback when available; otherwise use --all-frames and inspect every sheet in order for full visual frame coverage.",
        ],
    }
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        errors.append("Pillow is required: install the 'Pillow' Python package")
        output_dir.mkdir(parents=True, exist_ok=True)
        write_json(json_path, report)
        print(f"[ERROR] {errors[-1]}")
        print("[FAIL] MJPEG AVI watchback failed")
        return 2

    try:
        if not input_path.is_file():
            raise WatchbackError(f"input AVI does not exist: {input_path}")
        output_dir.mkdir(parents=True, exist_ok=True)
        file_size = input_path.stat().st_size
        if file_size < 12:
            raise WatchbackError("input is too small to be a RIFF AVI")

        main_header: dict[str, int] | None = None
        open_dml_total_frames: int | None = None
        streams: list[StreamHeader] = []
        frame_chunks: list[Chunk] = []
        riff_declared_size = 0
        riff_end = 0
        with input_path.open("rb") as handle:
            if read_exact(handle, 4, "RIFF signature") != b"RIFF":
                raise WatchbackError("input is not a little-endian RIFF file")
            riff_declared_size = struct.unpack("<I", read_exact(handle, 4, "RIFF size"))[0]
            if read_exact(handle, 4, "RIFF form") != b"AVI ":
                raise WatchbackError("RIFF form is not AVI")
            riff_end = 8 + riff_declared_size
            if riff_end > file_size:
                raise WatchbackError(
                    f"RIFF declares {riff_end} bytes but the file contains only {file_size}"
                )
            if file_size - riff_end > 1:
                warnings.append(
                    f"RIFF size is short by {file_size - riff_end} byte(s); "
                    "parsing the complete file and requiring valid top-level chunks"
                )
                riff_end = file_size

            for chunk in walk_chunks(handle, 12, riff_end):
                if chunk.fourcc == b"avih":
                    handle.seek(chunk.offset)
                    payload = read_exact(handle, chunk.size, "AVI main header")
                    if len(payload) < 40:
                        raise WatchbackError("AVI main header is shorter than 40 bytes")
                    main_header = {
                        "microseconds_per_frame": struct.unpack_from("<I", payload, 0)[0],
                        "total_frames": struct.unpack_from("<I", payload, 16)[0],
                        "stream_count": struct.unpack_from("<I", payload, 24)[0],
                        "width": struct.unpack_from("<I", payload, 32)[0],
                        "height": struct.unpack_from("<I", payload, 36)[0],
                    }
                elif chunk.fourcc == b"dmlh" and chunk.size >= 4:
                    handle.seek(chunk.offset)
                    open_dml_total_frames = struct.unpack("<I", read_exact(handle, 4, "dmlh"))[0]
                elif chunk.fourcc == b"strh":
                    handle.seek(chunk.offset)
                    streams.append(
                        parse_stream_header(
                            len(streams), read_exact(handle, chunk.size, f"stream header {len(streams)}")
                        )
                    )
                elif b"movi" in chunk.parents and len(chunk.fourcc) == 4:
                    if chunk.fourcc[2:4] in {b"dc", b"db"}:
                        frame_chunks.append(chunk)

        if main_header is None:
            raise WatchbackError("AVI main header (avih) was not found")
        video_streams = [stream for stream in streams if stream.stream_type == "vids"]
        if len(video_streams) != 1:
            raise WatchbackError(f"expected one video stream, found {len(video_streams)}")
        video = video_streams[0]
        if video.handler.upper() not in {"MJPG", "JPEG"}:
            raise WatchbackError(
                f"unsupported video codec {video.handler!r}; this reader accepts Godot MJPEG AVI only"
            )
        if video.scale <= 0 or video.rate <= 0:
            raise WatchbackError("video stream has an invalid rate/scale")
        fps = video.rate / video.scale
        expected_chunk_prefix = f"{video.index:02d}".encode("ascii")
        video_chunks = [chunk for chunk in frame_chunks if chunk.fourcc[:2] == expected_chunk_prefix]
        if not video_chunks:
            raise WatchbackError(
                f"no {expected_chunk_prefix.decode()}dc/db MJPEG frames were found inside LIST movi"
            )

        declared_counts = {
            "avih": main_header["total_frames"],
            "video_strh": video.length,
            "dmlh": open_dml_total_frames,
        }
        actual_count = len(video_chunks)
        for source, count in declared_counts.items():
            if count not in {None, 0, actual_count}:
                errors.append(f"{source} declares {count} frames but movi contains {actual_count}")
        duration_seconds = actual_count / fps
        header_fps = (
            1_000_000 / main_header["microseconds_per_frame"]
            if main_header["microseconds_per_frame"] > 0
            else None
        )
        if header_fps is not None and abs(header_fps - fps) > max(0.01, fps * 0.001):
            errors.append(f"avih FPS {header_fps:.6f} disagrees with video stream FPS {fps:.6f}")
        if args.expected_duration_seconds is not None:
            drift = abs(duration_seconds - args.expected_duration_seconds)
            if drift > args.duration_tolerance_seconds:
                errors.append(
                    f"duration {duration_seconds:.6f}s differs from expected "
                    f"{args.expected_duration_seconds:.6f}s by {drift:.6f}s"
                )

        if args.all_frames:
            desired_samples = actual_count
            sampling_mode = "all_frames"
        elif args.sample_count is not None:
            desired_samples = args.sample_count
            sampling_mode = "uniform_count"
        else:
            sample_fps = args.sample_fps if args.sample_fps is not None else 2.0
            desired_samples = max(2, math.ceil(duration_seconds * sample_fps) + 1)
            sampling_mode = "uniform_fps"
        desired_samples = min(desired_samples, actual_count)
        if desired_samples > args.max_samples:
            raise WatchbackError(
                f"requested {desired_samples} samples exceeds --max-samples {args.max_samples}; "
                "raise the bound explicitly after checking output cost"
            )
        sample_indices = uniform_indices(actual_count, desired_samples)
        sample_set = set(sample_indices)
        frame_artifacts: list[dict[str, Any]] = []
        frame_artifact_paths: dict[int, Path] = {}
        payload_digests: list[str] = []
        leading_bytes = 0
        trailing_bytes = 0
        decoded_size: tuple[int, int] | None = None

        with input_path.open("rb") as handle:
            for frame_index, chunk in enumerate(video_chunks):
                handle.seek(chunk.offset)
                payload = read_exact(handle, chunk.size, f"video frame {frame_index}")
                jpeg, leading, trailing = jpeg_payload(payload, frame_index)
                leading_bytes += leading
                trailing_bytes += trailing
                payload_digests.append(hashlib.sha256(jpeg).hexdigest())
                try:
                    with Image.open(BytesIO(jpeg)) as image:
                        current_size = image.size
                        image.verify()
                except Exception as exc:
                    raise WatchbackError(f"JPEG decode failed for frame {frame_index}: {exc}") from exc
                if decoded_size is None:
                    decoded_size = current_size
                elif current_size != decoded_size:
                    raise WatchbackError(
                        f"frame {frame_index} size {current_size} differs from {decoded_size}"
                    )
                if current_size != (main_header["width"], main_header["height"]):
                    raise WatchbackError(
                        f"frame {frame_index} size {current_size} disagrees with avih "
                        f"{main_header['width']}x{main_header['height']}"
                    )
                if frame_index in sample_set:
                    artifact = output_dir / f"{prefix}-frame-{frame_index:06d}-t{frame_index / fps:09.3f}.jpg"
                    artifact.write_bytes(jpeg)
                    frame_artifact_paths[frame_index] = artifact
                    frame_artifacts.append(
                        {
                            "frame_index": frame_index,
                            "time_seconds": round(frame_index / fps, 6),
                            "path": str(artifact),
                            "sha256": hashlib.sha256(jpeg).hexdigest(),
                        }
                    )

        unique_payloads = len(set(payload_digests))
        longest_run = 1
        current_run = 1
        for previous, current in zip(payload_digests, payload_digests[1:]):
            if current == previous:
                current_run += 1
                longest_run = max(longest_run, current_run)
            else:
                current_run = 1
        longest_run_seconds = longest_run / fps
        if args.require_temporal_change and unique_payloads < 2:
            errors.append("all encoded video frames are byte-identical")
        if (
            args.max_identical_run_seconds is not None
            and longest_run_seconds > args.max_identical_run_seconds
        ):
            errors.append(
                f"longest exact-identical run is {longest_run_seconds:.6f}s, exceeding "
                f"{args.max_identical_run_seconds:.6f}s"
            )
        if leading_bytes or trailing_bytes:
            warnings.append(
                f"trimmed {leading_bytes} leading and {trailing_bytes} trailing byte(s) around JPEG payloads"
            )

        assert decoded_size is not None
        capacity = args.columns * args.rows
        thumb_height = max(1, round(args.thumb_width * decoded_size[1] / decoded_size[0]))
        label_height = 24
        sheet_artifacts: list[str] = []
        resampling = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
        for page_number, page_start in enumerate(range(0, len(sample_indices), capacity), start=1):
            page = sample_indices[page_start : page_start + capacity]
            rows_used = math.ceil(len(page) / args.columns)
            sheet = Image.new(
                "RGB",
                (args.columns * args.thumb_width, rows_used * (thumb_height + label_height)),
                (20, 23, 27),
            )
            draw = ImageDraw.Draw(sheet)
            for cell_index, frame_index in enumerate(page):
                column = cell_index % args.columns
                row = cell_index // args.columns
                x = column * args.thumb_width
                y = row * (thumb_height + label_height)
                with Image.open(frame_artifact_paths[frame_index]) as image:
                    thumbnail = image.convert("RGB").resize(
                        (args.thumb_width, thumb_height), resampling
                    )
                sheet.paste(thumbnail, (x, y))
                draw.text(
                    (x + 6, y + thumb_height + 5),
                    f"f={frame_index:06d}  t={frame_index / fps:08.3f}s",
                    fill=(235, 238, 242),
                )
            sheet_path = output_dir / f"{prefix}-contact-sheet-{page_number:03d}.png"
            sheet.save(sheet_path)
            sheet_artifacts.append(str(sheet_path))

        report.update(
            {
                "input_size_bytes": file_size,
                "input_sha256": sha256_file(input_path),
                "container": {
                    "kind": "RIFF AVI",
                    "declared_size_bytes": riff_declared_size + 8,
                    "video_codec": video.handler,
                    "video_stream_index": video.index,
                    "audio_stream_count": sum(1 for stream in streams if stream.stream_type == "auds"),
                },
                "video": {
                    "width": decoded_size[0],
                    "height": decoded_size[1],
                    "fps": round(fps, 9),
                    "frame_count": actual_count,
                    "declared_frame_counts": declared_counts,
                    "duration_seconds": round(duration_seconds, 9),
                    "all_mjpeg_frames_verified": True,
                    "unique_encoded_frame_count": unique_payloads,
                    "longest_exact_identical_run_frames": longest_run,
                    "longest_exact_identical_run_seconds": round(longest_run_seconds, 9),
                },
                "sampling": {
                    "mode": sampling_mode,
                    "sample_count": len(sample_indices),
                    "sample_indices": sample_indices,
                    "covers_first_frame": sample_indices[0] == 0,
                    "covers_last_frame": sample_indices[-1] == actual_count - 1,
                    "all_frames_in_visual_packet": len(sample_indices) == actual_count,
                    "frame_artifacts": frame_artifacts,
                    "contact_sheets": sheet_artifacts,
                },
            }
        )
        report["result"] = "pass" if not errors else "fail"
    except (OSError, WatchbackError, struct.error, ValueError) as exc:
        errors.append(str(exc))

    write_json(json_path, report)
    if args.summary:
        video_summary = report.get("video", {})
        sampling_summary = report.get("sampling", {})
        print(
            f"[INFO] frames={video_summary.get('frame_count', 0)} "
            f"fps={video_summary.get('fps', 0)} duration={video_summary.get('duration_seconds', 0)}s "
            f"samples={sampling_summary.get('sample_count', 0)} "
            f"sheets={len(sampling_summary.get('contact_sheets', []))}"
        )
    for message in warnings:
        print(f"[WARN] {message}")
    for message in errors:
        print(f"[ERROR] {message}")
    passed = not errors and report.get("result") == "pass"
    print("[PASS] MJPEG AVI watchback packet passed" if passed else "[FAIL] MJPEG AVI watchback failed")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
