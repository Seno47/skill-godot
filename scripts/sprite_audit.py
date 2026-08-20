#!/usr/bin/env python3
"""Audit raster dimensions, transparency, and sprite-sheet frame stability."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import struct
import sys
import zlib
from typing import Any, Iterable
import xml.etree.ElementTree as ET


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
IGNORED_DIRECTORIES = {".git", ".godot", ".import", ".mono", "bin", "obj"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit PNG/SVG dimensions and PNG sprite-sheet alpha alignment."
    )
    parser.add_argument("--project", default=".", help="Project directory used to resolve res:// paths.")
    parser.add_argument("--image", action="append", help="Image path to inspect (repeatable).")
    parser.add_argument(
        "--sheet",
        action="append",
        help="Sprite sheet specification PATH=COLSxROWS (repeatable).",
    )
    parser.add_argument("--alpha-padding", type=int, default=1, help="Recommended transparent border in pixels.")
    parser.add_argument(
        "--max-anchor-drift",
        type=float,
        default=2.0,
        help="Maximum center/bottom alpha-anchor drift across frames in pixels.",
    )
    parser.add_argument("--json-output", help="Write the full JSON report.")
    parser.add_argument("--summary", action="store_true", help="Print bounded diagnostics.")
    parser.add_argument("--max-details", type=int, default=60)
    parser.add_argument("--fail-on-warnings", action="store_true")
    args = parser.parse_args()
    if args.alpha_padding < 0 or args.max_anchor_drift < 0 or args.max_details < 0:
        parser.error("padding, drift, and detail limits must be non-negative")
    return args


def find_root(value: str) -> Path:
    root = Path(value).expanduser().resolve()
    if root.is_file():
        root = root.parent
    if not root.is_dir():
        raise ValueError(f"Project directory does not exist: {root}")
    return root


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_path(root: Path, value: str) -> Path:
    if value.startswith("res://"):
        path = root / value.removeprefix("res://").replace("/", os.sep)
    else:
        candidate = Path(value).expanduser()
        path = candidate if candidate.is_absolute() else root / candidate
    return path.resolve()


def iter_images(root: Path) -> Iterable[Path]:
    for current, directories, files in os.walk(root):
        directories[:] = [name for name in directories if name not in IGNORED_DIRECTORIES]
        for name in files:
            if Path(name).suffix.lower() in {".png", ".svg"}:
                yield Path(current) / name


def png_chunks(data: bytes) -> Iterable[tuple[bytes, bytes]]:
    offset = len(PNG_SIGNATURE)
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        start = offset + 8
        end = start + length
        if end + 4 > len(data):
            raise ValueError("truncated PNG chunk")
        yield kind, data[start:end]
        offset = end + 4
        if kind == b"IEND":
            return


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else b if pb <= pc else c


def unfilter_rows(raw: bytes, width: int, height: int, bytes_per_pixel: int) -> list[bytes]:
    stride = width * bytes_per_pixel
    expected = height * (stride + 1)
    if len(raw) != expected:
        raise ValueError(f"unexpected decompressed length {len(raw)}; expected {expected}")
    rows: list[bytes] = []
    offset = 0
    previous = bytearray(stride)
    for _ in range(height):
        filter_type = raw[offset]
        source = raw[offset + 1 : offset + 1 + stride]
        offset += stride + 1
        result = bytearray(stride)
        for index, value in enumerate(source):
            left = result[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            up = previous[index]
            upper_left = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            if filter_type == 0:
                decoded = value
            elif filter_type == 1:
                decoded = value + left
            elif filter_type == 2:
                decoded = value + up
            elif filter_type == 3:
                decoded = value + ((left + up) // 2)
            elif filter_type == 4:
                decoded = value + paeth(left, up, upper_left)
            else:
                raise ValueError(f"unsupported PNG filter {filter_type}")
            result[index] = decoded & 0xFF
        rows.append(bytes(result))
        previous = result
    return rows


def decode_png(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError("invalid PNG signature")
    width = height = bit_depth = color_type = interlace = None
    compressed: list[bytes] = []
    palette: list[tuple[int, int, int]] = []
    transparency = b""
    for kind, payload in png_chunks(data):
        if kind == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", payload)
        elif kind == b"IDAT":
            compressed.append(payload)
        elif kind == b"PLTE":
            palette = [tuple(payload[i : i + 3]) for i in range(0, len(payload), 3)]
        elif kind == b"tRNS":
            transparency = payload
    if None in {width, height, bit_depth, color_type, interlace}:
        raise ValueError("PNG is missing IHDR")
    result: dict[str, Any] = {
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "alpha": None,
    }
    if bit_depth != 8 or interlace != 0:
        result["pixel_limitation"] = "alpha analysis supports only non-interlaced 8-bit PNG"
        return result
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}.get(color_type)
    if channels is None:
        result["pixel_limitation"] = f"unsupported PNG color type {color_type}"
        return result
    rows = unfilter_rows(zlib.decompress(b"".join(compressed)), width, height, channels)
    alpha: list[list[int]] = []
    for row in rows:
        alpha_row: list[int] = []
        for x in range(width):
            pixel = row[x * channels : (x + 1) * channels]
            if color_type == 6:
                value = pixel[3]
            elif color_type == 4:
                value = pixel[1]
            elif color_type == 3:
                index = pixel[0]
                value = transparency[index] if index < len(transparency) else 255
            elif color_type == 0 and len(transparency) >= 2:
                value = 0 if pixel[0] == struct.unpack(">H", transparency[:2])[0] else 255
            elif color_type == 2 and len(transparency) >= 6:
                transparent_rgb = tuple(struct.unpack(">HHH", transparency[:6]))
                value = 0 if tuple(pixel) == transparent_rgb else 255
            else:
                value = 255
            alpha_row.append(value)
        alpha.append(alpha_row)
    result["alpha"] = alpha
    return result


def svg_dimensions(path: Path) -> tuple[float, float]:
    root = ET.parse(path).getroot()

    def number(value: str | None) -> float | None:
        if value is None:
            return None
        match = re.match(r"^\s*([0-9]*\.?[0-9]+)", value)
        return float(match.group(1)) if match else None

    width, height = number(root.get("width")), number(root.get("height"))
    if width is not None and height is not None:
        return width, height
    view_box = root.get("viewBox")
    if view_box:
        values = [float(value) for value in re.split(r"[ ,]+", view_box.strip())]
        if len(values) == 4:
            return values[2], values[3]
    raise ValueError("SVG has neither usable width/height nor viewBox")


def alpha_bbox(alpha: list[list[int]], x0: int, y0: int, width: int, height: int) -> tuple[int, int, int, int] | None:
    points = [
        (x, y)
        for y in range(y0, y0 + height)
        for x in range(x0, x0 + width)
        if alpha[y][x] > 0
    ]
    if not points:
        return None
    xs, ys = zip(*points)
    return min(xs) - x0, min(ys) - y0, max(xs) - x0, max(ys) - y0


def issue(level: str, path: str, message: str) -> dict[str, str]:
    return {"level": level, "path": path, "message": message}


def inspect_image(root: Path, path: Path, padding: int) -> dict[str, Any]:
    label = path.relative_to(root).as_posix() if is_within(path, root) else str(path)
    result: dict[str, Any] = {"path": label, "diagnostics": []}
    try:
        if path.suffix.lower() == ".png":
            decoded = decode_png(path)
            result.update({key: value for key, value in decoded.items() if key != "alpha"})
            alpha = decoded.get("alpha")
            if decoded.get("pixel_limitation"):
                result["diagnostics"].append(issue("warning", label, decoded["pixel_limitation"]))
            if alpha is not None:
                bbox = alpha_bbox(alpha, 0, 0, decoded["width"], decoded["height"])
                result["alpha_bbox"] = bbox
                if bbox is None:
                    result["diagnostics"].append(issue("warning", label, "image is fully transparent"))
                else:
                    left, top, right, bottom = bbox
                    margins = [left, top, decoded["width"] - 1 - right, decoded["height"] - 1 - bottom]
                    result["alpha_margins"] = margins
                    if min(margins) < padding:
                        result["diagnostics"].append(
                            issue("warning", label, f"opaque pixels violate requested {padding}px transparent padding")
                        )
        elif path.suffix.lower() == ".svg":
            width, height = svg_dimensions(path)
            result.update({"width": width, "height": height})
            result["diagnostics"].append(issue("warning", label, "SVG alpha/pixel edges require rendered inspection"))
        else:
            raise ValueError("supported formats are PNG and SVG")
    except (OSError, ValueError, ET.ParseError, zlib.error) as exc:
        result["diagnostics"].append(issue("error", label, str(exc)))
    return result


def parse_sheet_spec(root: Path, value: str) -> tuple[Path, int, int]:
    if "=" not in value:
        raise ValueError(f"Invalid sheet spec (expected PATH=COLSxROWS): {value}")
    path_value, grid = value.rsplit("=", 1)
    match = re.fullmatch(r"(\d+)[xX](\d+)", grid)
    if not match:
        raise ValueError(f"Invalid sheet grid: {grid}")
    columns, rows = int(match.group(1)), int(match.group(2))
    if columns < 1 or rows < 1:
        raise ValueError("sheet grid values must be positive")
    return resolve_path(root, path_value), columns, rows


def inspect_sheet(root: Path, path: Path, columns: int, rows: int, drift_limit: float) -> dict[str, Any]:
    label = path.relative_to(root).as_posix() if is_within(path, root) else str(path)
    result: dict[str, Any] = {"path": label, "columns": columns, "rows": rows, "diagnostics": []}
    if path.suffix.lower() != ".png":
        result["diagnostics"].append(issue("error", label, "sprite-sheet frame analysis requires PNG"))
        return result
    try:
        decoded = decode_png(path)
    except (OSError, ValueError, zlib.error) as exc:
        result["diagnostics"].append(issue("error", label, str(exc)))
        return result
    width, height, alpha = decoded["width"], decoded["height"], decoded.get("alpha")
    result.update({"width": width, "height": height})
    if width % columns or height % rows:
        result["diagnostics"].append(
            issue("error", label, f"{width}x{height} is not divisible by {columns}x{rows}")
        )
        return result
    cell_width, cell_height = width // columns, height // rows
    result["cell_width"], result["cell_height"] = cell_width, cell_height
    if alpha is None:
        result["diagnostics"].append(issue("warning", label, decoded.get("pixel_limitation", "alpha unavailable")))
        return result
    frames: list[dict[str, Any]] = []
    anchors: list[tuple[float, float]] = []
    for row in range(rows):
        for column in range(columns):
            index = row * columns + column
            bbox = alpha_bbox(alpha, column * cell_width, row * cell_height, cell_width, cell_height)
            frame = {"index": index, "column": column, "row": row, "alpha_bbox": bbox}
            if bbox is None:
                result["diagnostics"].append(issue("error", label, f"frame {index} is fully transparent"))
            else:
                left, _, right, bottom = bbox
                anchor = ((left + right) / 2.0, float(bottom))
                frame["anchor"] = anchor
                anchors.append(anchor)
            frames.append(frame)
    result["frames"] = frames
    if len(anchors) >= 2:
        x_drift = max(value[0] for value in anchors) - min(value[0] for value in anchors)
        bottom_drift = max(value[1] for value in anchors) - min(value[1] for value in anchors)
        result["anchor_drift"] = {"center_x": x_drift, "bottom": bottom_drift}
        if x_drift > drift_limit or bottom_drift > drift_limit:
            result["diagnostics"].append(
                issue(
                    "warning",
                    label,
                    f"frame alpha anchors drift by x={x_drift:.1f}px, bottom={bottom_drift:.1f}px (limit {drift_limit:.1f}px)",
                )
            )
    return result


def main() -> int:
    args = parse_args()
    try:
        root = find_root(args.project)
        sheet_specs = [parse_sheet_spec(root, value) for value in (args.sheet or [])]
        paths = [resolve_path(root, value) for value in (args.image or [])]
        if not paths and not sheet_specs:
            paths = sorted(iter_images(root))
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    missing = [str(path) for path in paths + [spec[0] for spec in sheet_specs] if not path.is_file()]
    if missing:
        print(f"[ERROR] Missing image(s): {', '.join(missing)}", file=sys.stderr)
        return 2
    images = [inspect_image(root, path, args.alpha_padding) for path in paths]
    sheets = [inspect_sheet(root, path, columns, rows, args.max_anchor_drift) for path, columns, rows in sheet_specs]
    diagnostics = [item for result in images + sheets for item in result["diagnostics"]]
    errors = sum(item["level"] == "error" for item in diagnostics)
    warnings = sum(item["level"] == "warning" for item in diagnostics)
    report = {
        "project": str(root),
        "image_count": len(images),
        "sheet_count": len(sheets),
        "error_count": errors,
        "warning_count": warnings,
        "images": images,
        "sheets": sheets,
        "limitations": [
            "Anchor drift is an alpha-bounds heuristic, not a substitute for animation review.",
            "Palette, silhouette identity, timing, cross-cell contamination, and visual consistency still require contact-sheet and motion inspection.",
        ],
    }
    if args.json_output:
        output = Path(args.json_output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[INFO] {len(images)} image(s), {len(sheets)} sheet(s), {errors} error(s), {warnings} warning(s)")
    shown = diagnostics[: args.max_details] if args.summary else diagnostics
    for item in shown:
        print(f"[{item['level'].upper()}] {item['path']}: {item['message']}")
    if len(shown) < len(diagnostics):
        print(f"[INFO] {len(diagnostics) - len(shown)} additional diagnostic(s) omitted; use --json-output")
    failed = errors > 0 or (args.fail_on_warnings and warnings > 0)
    print("[FAIL] Sprite audit failed" if failed else "[PASS] Sprite audit passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
