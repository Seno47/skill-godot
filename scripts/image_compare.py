#!/usr/bin/env python3
"""Create deterministic screenshot parity artifacts and bounded pixel metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare same-size reference/runtime images and create overlay/diff artifacts."
    )
    parser.add_argument("--reference", required=True, help="Approved reference image.")
    parser.add_argument("--actual", required=True, help="Runtime capture to compare.")
    parser.add_argument("--output-dir", required=True, help="Directory for comparison PNGs.")
    parser.add_argument(
        "--pixel-threshold",
        type=int,
        default=8,
        help="A pixel counts as changed when any compared channel exceeds this 0-255 value.",
    )
    parser.add_argument(
        "--max-mean-error",
        type=float,
        help="Optional failure threshold for normalized mean absolute channel error (0..1).",
    )
    parser.add_argument(
        "--max-changed-ratio",
        type=float,
        help="Optional failure threshold for changed pixels (0..1).",
    )
    parser.add_argument(
        "--ignore-alpha", action="store_true", help="Compare RGB only while preserving alpha in artifacts."
    )
    parser.add_argument("--json-output", help="Write full metrics as JSON.")
    parser.add_argument("--summary", action="store_true", help="Print a compact result line.")
    args = parser.parse_args()
    if not 0 <= args.pixel_threshold <= 255:
        parser.error("--pixel-threshold must be between 0 and 255")
    for name in ("max_mean_error", "max_changed_ratio"):
        value = getattr(args, name)
        if value is not None and not 0 <= value <= 1:
            parser.error(f"--{name.replace('_', '-')} must be between 0 and 1")
    return args


def resolved_file(value: str, label: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise ValueError(f"{label} does not exist or is not a file: {path}")
    return path


def write_json(path_value: str | None, report: dict[str, Any]) -> None:
    if not path_value:
        return
    path = Path(path_value).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    try:
        from PIL import Image, ImageChops, ImageDraw
    except ImportError:
        print("[ERROR] image_compare.py requires Pillow: install the 'Pillow' Python package.")
        return 2

    try:
        reference_path = resolved_file(args.reference, "Reference")
        actual_path = resolved_file(args.actual, "Actual image")
        output_dir = Path(args.output_dir).expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        with Image.open(reference_path) as source:
            reference = source.convert("RGBA")
        with Image.open(actual_path) as source:
            actual = source.convert("RGBA")
        if reference.size != actual.size:
            raise ValueError(
                "Images must use identical capture dimensions; "
                f"reference={reference.size[0]}x{reference.size[1]} "
                f"actual={actual.size[0]}x{actual.size[1]}"
            )

        compare_reference = reference.convert("RGB") if args.ignore_alpha else reference
        compare_actual = actual.convert("RGB") if args.ignore_alpha else actual
        difference = ImageChops.difference(compare_reference, compare_actual)
        width, height = reference.size
        pixel_count = width * height
        channel_count = len(difference.getbands())
        histogram = difference.histogram()
        absolute_error = 0
        max_error = 0
        for channel in range(channel_count):
            channel_histogram = histogram[channel * 256 : (channel + 1) * 256]
            absolute_error += sum(value * count for value, count in enumerate(channel_histogram))
            for value in range(255, -1, -1):
                if channel_histogram[value]:
                    max_error = max(max_error, value)
                    break
        mean_error = absolute_error / (pixel_count * channel_count * 255) if pixel_count else 0.0
        pixels = (
            difference.get_flattened_data()
            if hasattr(difference, "get_flattened_data")
            else difference.getdata()
        )
        changed_pixels = sum(1 for pixel in pixels if max(pixel) > args.pixel_threshold)
        changed_ratio = changed_pixels / pixel_count if pixel_count else 0.0

        overlay_path = output_dir / "overlay_50.png"
        diff_path = output_dir / "diff_absolute.png"
        emphasized_path = output_dir / "diff_emphasized.png"
        side_by_side_path = output_dir / "side_by_side.png"
        Image.blend(reference, actual, 0.5).save(overlay_path)
        difference.save(diff_path)
        difference.point(lambda value: min(255, value * 4)).save(emphasized_path)

        gap = 16
        side_by_side = Image.new("RGBA", (width * 2 + gap, height), (24, 24, 24, 255))
        side_by_side.paste(reference, (0, 0))
        side_by_side.paste(actual, (width + gap, 0))
        ImageDraw.Draw(side_by_side).rectangle((width, 0, width + gap - 1, height), fill=(24, 24, 24, 255))
        side_by_side.save(side_by_side_path)

        failures: list[str] = []
        if args.max_mean_error is not None and mean_error > args.max_mean_error:
            failures.append(
                f"mean_error {mean_error:.6f} exceeds {args.max_mean_error:.6f}"
            )
        if args.max_changed_ratio is not None and changed_ratio > args.max_changed_ratio:
            failures.append(
                f"changed_ratio {changed_ratio:.6f} exceeds {args.max_changed_ratio:.6f}"
            )
        report: dict[str, Any] = {
            "reference": str(reference_path),
            "actual": str(actual_path),
            "width": width,
            "height": height,
            "compared_channels": list(difference.getbands()),
            "ignore_alpha": args.ignore_alpha,
            "pixel_threshold": args.pixel_threshold,
            "mean_absolute_channel_error": mean_error,
            "changed_pixels": changed_pixels,
            "changed_pixel_ratio": changed_ratio,
            "max_channel_error": max_error,
            "thresholds": {
                "max_mean_error": args.max_mean_error,
                "max_changed_ratio": args.max_changed_ratio,
            },
            "artifacts": {
                "side_by_side": str(side_by_side_path),
                "overlay_50": str(overlay_path),
                "diff_absolute": str(diff_path),
                "diff_emphasized": str(emphasized_path),
            },
            "failures": failures,
            "passed": not failures,
            "interpretation": (
                "Pixel metrics are diagnostic. Review named regions and raw captures; "
                "renderer/font/animation differences can affect the score."
            ),
        }
        write_json(args.json_output, report)
        status = "PASS" if not failures else "FAIL"
        if args.summary or failures:
            print(
                f"[{status}] size={width}x{height} mean_error={mean_error:.6f} "
                f"changed_ratio={changed_ratio:.6f} max_error={max_error} artifacts={output_dir}"
            )
            for failure in failures:
                print(f"[ERROR] {failure}")
        elif not args.json_output:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if not failures else 1
    except (OSError, ValueError) as error:
        print(f"[ERROR] {error}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
