#!/usr/bin/env python3
"""Measure visible alpha bounds, optical centers, padding, and family weight for final-size icon crops."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any


class OpticalAuditError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Audit transparent final-size raster icon crops. Metrics support, but do not replace, "
            "independent optical/family review."
        )
    )
    parser.add_argument("--image", action="append", required=True, help="PNG/WebP icon crop; repeat per family member.")
    parser.add_argument("--alpha-threshold", type=int, default=8, help="Visible alpha threshold 0-255.")
    parser.add_argument(
        "--max-center-offset-ratio",
        type=float,
        help="Optional maximum alpha-centroid distance from canvas center, normalized by half-diagonal.",
    )
    parser.add_argument(
        "--max-weight-ratio",
        type=float,
        help="Optional maximum largest/smallest alpha-weight ratio across the family.",
    )
    parser.add_argument("--json-output", help="Write complete JSON report.")
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args()


def inspect_image(path: Path, threshold: int) -> dict[str, Any]:
    try:
        from PIL import Image
    except ImportError as exc:
        raise OpticalAuditError("Pillow is required for icon_optical_audit.py") from exc

    if not path.is_file():
        raise OpticalAuditError(f"image not found: {path}")
    try:
        image = Image.open(path).convert("RGBA")
    except Exception as exc:  # Pillow exposes format-specific exceptions.
        raise OpticalAuditError(f"could not read image {path}: {exc}") from exc

    width, height = image.size
    if width <= 0 or height <= 0:
        raise OpticalAuditError(f"image has invalid dimensions: {path}")

    visible: list[tuple[int, int, int]] = []
    for y in range(height):
        for x in range(width):
            alpha = image.getpixel((x, y))[3]
            if alpha > threshold:
                visible.append((x, y, alpha))
    if not visible:
        raise OpticalAuditError(f"image has no pixels above alpha threshold {threshold}: {path}")

    xs = [item[0] for item in visible]
    ys = [item[1] for item in visible]
    left, top, right_inclusive, bottom_inclusive = min(xs), min(ys), max(xs), max(ys)
    right, bottom = right_inclusive + 1, bottom_inclusive + 1
    alpha_weight = sum(item[2] / 255.0 for item in visible)
    centroid_x = sum((x + 0.5) * alpha for x, _, alpha in visible) / sum(alpha for _, _, alpha in visible)
    centroid_y = sum((y + 0.5) * alpha for _, y, alpha in visible) / sum(alpha for _, _, alpha in visible)
    canvas_center_x, canvas_center_y = width / 2.0, height / 2.0
    offset_pixels = math.hypot(centroid_x - canvas_center_x, centroid_y - canvas_center_y)
    half_diagonal = math.hypot(width / 2.0, height / 2.0)
    return {
        "path": str(path),
        "canvas": {"width": width, "height": height},
        "visible_bounds": {"left": left, "top": top, "right": right, "bottom": bottom},
        "padding": {"left": left, "top": top, "right": width - right, "bottom": height - bottom},
        "alpha_centroid": {"x": round(centroid_x, 4), "y": round(centroid_y, 4)},
        "center_offset_pixels": round(offset_pixels, 4),
        "center_offset_ratio": round(offset_pixels / half_diagonal, 6),
        "visible_bbox_area_ratio": round(((right - left) * (bottom - top)) / (width * height), 6),
        "alpha_weight": round(alpha_weight, 4),
        "alpha_weight_ratio_to_canvas": round(alpha_weight / (width * height), 6),
    }


def main() -> int:
    args = parse_args()
    try:
        if not 0 <= args.alpha_threshold <= 254:
            raise OpticalAuditError("--alpha-threshold must be between 0 and 254")
        if args.max_center_offset_ratio is not None and args.max_center_offset_ratio < 0:
            raise OpticalAuditError("--max-center-offset-ratio must be non-negative")
        if args.max_weight_ratio is not None and args.max_weight_ratio < 1:
            raise OpticalAuditError("--max-weight-ratio must be at least 1")

        items = [inspect_image(Path(value).expanduser().resolve(), args.alpha_threshold) for value in args.image]
        weights = [item["alpha_weight_ratio_to_canvas"] for item in items]
        smallest = min(weights)
        family_weight_ratio = max(weights) / smallest if smallest > 0 else math.inf
        failures: list[str] = []
        if args.max_center_offset_ratio is not None:
            for item in items:
                if item["center_offset_ratio"] > args.max_center_offset_ratio:
                    failures.append(
                        f"center offset {item['center_offset_ratio']} exceeds {args.max_center_offset_ratio}: {item['path']}"
                    )
        if args.max_weight_ratio is not None and family_weight_ratio > args.max_weight_ratio:
            failures.append(
                f"family alpha-weight ratio {family_weight_ratio:.6f} exceeds {args.max_weight_ratio}"
            )

        report = {
            "schema_version": 1,
            "alpha_threshold": args.alpha_threshold,
            "family_weight_ratio": round(family_weight_ratio, 6),
            "thresholds": {
                "max_center_offset_ratio": args.max_center_offset_ratio,
                "max_weight_ratio": args.max_weight_ratio,
            },
            "items": items,
            "failures": failures,
            "result": "fail" if failures else "pass",
            "limitations": [
                "Alpha area is a repeatable proxy, not a complete measure of perceived optical weight.",
                "Baseline, filtering/halo, semantic recognition, and neighboring-family coherence still require raw final-size review.",
            ],
        }
        if args.json_output:
            output = Path(args.json_output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(
            f"[{'FAIL' if failures else 'PASS'}] icons={len(items)} "
            f"family_weight_ratio={family_weight_ratio:.4f} failures={len(failures)}"
        )
        if not args.summary:
            for item in items:
                print(
                    f"[ICON] {item['path']} center_offset={item['center_offset_ratio']:.6f} "
                    f"alpha_weight={item['alpha_weight_ratio_to_canvas']:.6f} padding={item['padding']}"
                )
            for failure in failures:
                print(f"[FAILURE] {failure}")
        return 1 if failures else 0
    except OpticalAuditError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
