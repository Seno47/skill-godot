#!/usr/bin/env python3
"""Measure fixed-camera player silhouette and local background separation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

from PIL import Image, ImageChops, ImageFilter


class AuditError(RuntimeError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Measure a hero-only mask against the exact same rendered gameplay frame. "
            "Thresholds are project-owned; use --require-thresholds for completion evidence."
        )
    )
    parser.add_argument("--screenshot", required=True, help="Raw gameplay screenshot.")
    parser.add_argument("--mask", required=True, help="Hero-only mask from the same camera and frame.")
    parser.add_argument("--mask-channel", choices=["auto", "alpha", "luma"], default="auto")
    parser.add_argument("--mask-threshold", type=int, default=127)
    parser.add_argument("--ring-radius", type=int, default=4, help="Local background ring radius in pixels.")
    parser.add_argument("--min-mean-luminance-delta", type=float)
    parser.add_argument("--min-edge-luminance-delta", type=float)
    parser.add_argument("--min-mean-contrast-ratio", type=float)
    parser.add_argument("--min-edge-contrast-ratio", type=float)
    parser.add_argument("--min-bbox-height-ratio", type=float)
    parser.add_argument("--min-area-ratio", type=float)
    parser.add_argument("--require-thresholds", action="store_true")
    parser.add_argument("--json-output")
    parser.add_argument("--summary", action="store_true")
    return parser.parse_args()


def resolve_file(value: str, label: str) -> Path:
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise AuditError(f"{label} not found: {path}")
    return path


def srgb_to_linear(value: int) -> float:
    channel = value / 255.0
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(pixel: tuple[int, int, int]) -> float:
    red, green, blue = (srgb_to_linear(channel) for channel in pixel)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def masked_luminance(image: Image.Image, mask: Image.Image, label: str) -> tuple[float, int]:
    total = 0.0
    count = 0
    for pixel, selected in zip(image.getdata(), mask.getdata()):
        if selected:
            total += relative_luminance(pixel)
            count += 1
    if count == 0:
        raise AuditError(f"{label} contains no selected pixels")
    return total / count, count


def contrast_ratio(first: float, second: float) -> float:
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


def make_mask(image: Image.Image, channel: str, threshold: int) -> tuple[Image.Image, str]:
    if not 0 <= threshold <= 255:
        raise AuditError("--mask-threshold must be between 0 and 255")
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    alpha_min, alpha_max = alpha.getextrema()
    resolved = channel
    if channel == "auto":
        resolved = "alpha" if alpha_min < 255 else "luma"
    source = alpha if resolved == "alpha" else rgba.convert("L")
    binary = source.point(lambda value: 255 if value > threshold else 0, mode="L")
    if binary.getbbox() is None:
        raise AuditError(f"Resolved {resolved} mask is empty; check channel and threshold")
    return binary, resolved


def validate_ratio(value: float | None, label: str) -> None:
    if value is not None and not 0.0 <= value <= 1.0:
        raise AuditError(f"{label} must be between 0 and 1")


def main() -> int:
    args = parse_args()
    try:
        if args.ring_radius < 1 or args.ring_radius > 49:
            raise AuditError("--ring-radius must be between 1 and 49")
        validate_ratio(args.min_mean_luminance_delta, "--min-mean-luminance-delta")
        validate_ratio(args.min_edge_luminance_delta, "--min-edge-luminance-delta")
        validate_ratio(args.min_bbox_height_ratio, "--min-bbox-height-ratio")
        validate_ratio(args.min_area_ratio, "--min-area-ratio")
        for value, label in (
            (args.min_mean_contrast_ratio, "--min-mean-contrast-ratio"),
            (args.min_edge_contrast_ratio, "--min-edge-contrast-ratio"),
        ):
            if value is not None and value < 1.0:
                raise AuditError(f"{label} must be at least 1")

        threshold_groups = {
            "mean separation": [args.min_mean_luminance_delta, args.min_mean_contrast_ratio],
            "edge separation": [args.min_edge_luminance_delta, args.min_edge_contrast_ratio],
            "screen size": [args.min_bbox_height_ratio, args.min_area_ratio],
        }
        missing_groups = [label for label, values in threshold_groups.items() if not any(v is not None for v in values)]
        if args.require_thresholds and missing_groups:
            raise AuditError(
                "--require-thresholds needs at least one threshold for each group: "
                + ", ".join(missing_groups)
            )

        screenshot_path = resolve_file(args.screenshot, "screenshot")
        mask_path = resolve_file(args.mask, "mask")
        screenshot = Image.open(screenshot_path).convert("RGB")
        mask_source = Image.open(mask_path)
        if mask_source.size != screenshot.size:
            raise AuditError(
                f"mask size {mask_source.size} does not match screenshot size {screenshot.size}"
            )
        hero_mask, resolved_channel = make_mask(mask_source, args.mask_channel, args.mask_threshold)

        kernel = args.ring_radius * 2 + 1
        expanded = hero_mask.filter(ImageFilter.MaxFilter(kernel))
        background_ring = ImageChops.subtract(expanded, hero_mask)
        contracted = hero_mask.filter(ImageFilter.MinFilter(kernel))
        hero_edge = ImageChops.subtract(hero_mask, contracted)
        if background_ring.getbbox() is None:
            raise AuditError("No local background ring remains; the hero mask is too large or touches every edge")
        if hero_edge.getbbox() is None:
            hero_edge = hero_mask

        hero_luma, hero_pixels = masked_luminance(screenshot, hero_mask, "hero mask")
        background_luma, background_pixels = masked_luminance(screenshot, background_ring, "background ring")
        hero_edge_luma, hero_edge_pixels = masked_luminance(screenshot, hero_edge, "hero edge")
        background_edge_luma, background_edge_pixels = masked_luminance(
            screenshot, background_ring, "background edge"
        )

        bbox = hero_mask.getbbox()
        assert bbox is not None
        width, height = screenshot.size
        bbox_width = bbox[2] - bbox[0]
        bbox_height = bbox[3] - bbox[1]
        metrics = {
            "hero_pixel_count": hero_pixels,
            "background_ring_pixel_count": background_pixels,
            "hero_edge_pixel_count": hero_edge_pixels,
            "background_edge_pixel_count": background_edge_pixels,
            "hero_bbox": list(bbox),
            "bbox_width_ratio": round(bbox_width / width, 6),
            "bbox_height_ratio": round(bbox_height / height, 6),
            "area_ratio": round(hero_pixels / (width * height), 6),
            "hero_mean_luminance": round(hero_luma, 6),
            "background_mean_luminance": round(background_luma, 6),
            "mean_luminance_delta": round(abs(hero_luma - background_luma), 6),
            "mean_contrast_ratio": round(contrast_ratio(hero_luma, background_luma), 6),
            "hero_edge_mean_luminance": round(hero_edge_luma, 6),
            "background_edge_mean_luminance": round(background_edge_luma, 6),
            "edge_luminance_delta": round(abs(hero_edge_luma - background_edge_luma), 6),
            "edge_contrast_ratio": round(contrast_ratio(hero_edge_luma, background_edge_luma), 6),
        }
        threshold_map = {
            "mean_luminance_delta": args.min_mean_luminance_delta,
            "edge_luminance_delta": args.min_edge_luminance_delta,
            "mean_contrast_ratio": args.min_mean_contrast_ratio,
            "edge_contrast_ratio": args.min_edge_contrast_ratio,
            "bbox_height_ratio": args.min_bbox_height_ratio,
            "area_ratio": args.min_area_ratio,
        }
        checks: list[dict[str, Any]] = []
        for metric, minimum in threshold_map.items():
            if minimum is None:
                continue
            actual = float(metrics[metric])
            checks.append({"metric": metric, "actual": actual, "minimum": minimum, "pass": actual >= minimum})

        passed = bool(checks) and all(check["pass"] for check in checks)
        mode = "thresholded" if checks else "diagnostic_only"
        report = {
            "schema_version": 1,
            "status": "pass" if passed else ("fail" if checks else "measured"),
            "mode": mode,
            "screenshot": str(screenshot_path),
            "mask": str(mask_path),
            "mask_channel": resolved_channel,
            "image_size": [width, height],
            "ring_radius": args.ring_radius,
            "metrics": metrics,
            "checks": checks,
            "limitations": [
                "The audit measures one declared frame and cannot judge animation, route composition, occlusion, or art quality.",
                "A passing report requires project-owned thresholds plus independent raw-screenshot review."
            ],
        }
        if args.json_output:
            output = Path(args.json_output).expanduser().resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(
            f"[ISOMETRIC READABILITY] status={report['status']} mode={mode} "
            f"mean_delta={metrics['mean_luminance_delta']:.4f} "
            f"edge_delta={metrics['edge_luminance_delta']:.4f} "
            f"bbox_height={metrics['bbox_height_ratio']:.4f} area={metrics['area_ratio']:.4f}"
        )
        if not args.summary:
            for check in checks:
                label = "PASS" if check["pass"] else "FAIL"
                print(f"[{label}] {check['metric']}={check['actual']:.6f} minimum={check['minimum']}")
        return 0 if passed or not checks else 1
    except (AuditError, OSError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
