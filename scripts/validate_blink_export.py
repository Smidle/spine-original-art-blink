#!/usr/bin/env python3
"""Validate native Spine PNG frames for a blink-only project."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frames-dir", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--contact", required=True, type=Path)
    parser.add_argument("--preview", required=True, type=Path)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--duration", type=float, default=3.2)
    parser.add_argument("--open-start", type=int, default=34)
    parser.add_argument("--half-in", type=int, default=35)
    parser.add_argument("--closed-in", type=int, default=37)
    parser.add_argument("--half-out", type=int, default=39)
    parser.add_argument("--open-out", type=int, default=41)
    parser.add_argument("--allowed-eye-box", type=int, nargs=4)
    parser.add_argument(
        "--allowed-box",
        type=int,
        nargs=4,
        action="append",
        help="Repeat for each approved eye or eyebrow change region.",
    )
    parser.add_argument("--contact-crop", type=int, nargs=4)
    return parser.parse_args()


def effective_difference(first: Image.Image, second: Image.Image) -> Image.Image:
    channels = ImageChops.difference(first.convert("RGBA"), second.convert("RGBA")).split()
    result = channels[0]
    for channel in channels[1:]:
        result = ImageChops.lighter(result, channel)
    return result


def pixel_identical(first: Image.Image, second: Image.Image) -> bool:
    return effective_difference(first, second).getbbox() is None


def outside_boxes_identical(
    first: Image.Image,
    second: Image.Image,
    boxes: list[tuple[int, int, int, int]],
) -> bool:
    difference = effective_difference(first, second)
    for box in boxes:
        difference.paste(0, box)
    return difference.getbbox() is None


def frame_index(path: Path) -> int:
    match = re.search(r"(\d+)$", path.stem)
    if not match:
        raise ValueError(f"Frame filename has no trailing number: {path.name}")
    return int(match.group(1))


def checkerboard(size: tuple[int, int]) -> Image.Image:
    checker = Image.new("RGBA", size, (180, 180, 180, 255))
    draw = ImageDraw.Draw(checker)
    tile = 32
    for y in range(0, size[1], tile):
        for x in range(0, size[0], tile):
            if (x // tile + y // tile) % 2:
                draw.rectangle((x, y, x + tile - 1, y + tile - 1), fill=(138, 138, 138, 255))
    return checker


def build_contact(
    frames: dict[int, Image.Image],
    indices: list[int],
    crop_box: tuple[int, int, int, int],
    output: Path,
) -> None:
    scale = 2
    padding = 14
    label_height = 24
    cell_width = (crop_box[2] - crop_box[0]) * scale
    cell_height = (crop_box[3] - crop_box[1]) * scale
    canvas = Image.new(
        "RGB",
        (
            cell_width * 4 + padding * 5,
            (cell_height + label_height) * 2 + padding * 3,
        ),
        (18, 20, 26),
    )
    draw = ImageDraw.Draw(canvas)
    for position, index in enumerate(indices):
        column = position % 4
        row = position // 4
        x = padding + column * (cell_width + padding)
        y = padding + row * (cell_height + label_height + padding)
        crop = frames[index].crop(crop_box).resize(
            (cell_width, cell_height),
            Image.Resampling.NEAREST,
        )
        checker = checkerboard(crop.size)
        checker.alpha_composite(crop)
        canvas.paste(checker.convert("RGB"), (x, y + label_height))
        draw.text((x, y), f"frame {index}", fill=(242, 242, 242))
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)


def build_preview(frames: list[Image.Image], fps: int, output: Path) -> None:
    width, height = frames[0].size
    target_height = min(height, 768)
    target_width = round(width * target_height / height)
    resized = [
        frame.resize((target_width, target_height), Image.Resampling.LANCZOS)
        for frame in frames
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    resized[0].save(
        output,
        save_all=True,
        append_images=resized[1:],
        duration=round(1000 / fps),
        loop=0,
        lossless=True,
        quality=100,
        method=6,
    )


def main() -> None:
    args = parse_args()
    frame_dir = args.frames_dir.expanduser().resolve()
    paths = sorted(frame_dir.glob("*.png"), key=frame_index)
    expected_count = round(args.duration * args.fps) + 1
    if len(paths) != expected_count:
        raise ValueError(f"Expected {expected_count} frames, found {len(paths)}")

    indexed_paths = {frame_index(path): path for path in paths}
    expected_indices = list(range(expected_count))
    if sorted(indexed_paths) != expected_indices:
        raise ValueError("Frame indices are not contiguous from 0")
    frames = {index: Image.open(path).convert("RGBA") for index, path in indexed_paths.items()}
    dimensions = sorted({image.size for image in frames.values()})
    if len(dimensions) != 1:
        raise ValueError(f"Frame dimensions differ: {dimensions}")

    allowed_boxes = [
        tuple(box) for box in (args.allowed_box or [])
    ]
    if args.allowed_eye_box:
        allowed_boxes.append(tuple(args.allowed_eye_box))
    if not allowed_boxes:
        raise ValueError("Provide --allowed-eye-box or at least one --allowed-box")
    last = expected_count - 1
    repeated_checks = {
        "open_0_equals_open_start": pixel_identical(frames[0], frames[args.open_start]),
        "half_in_pair": pixel_identical(frames[args.half_in], frames[args.half_in + 1]),
        "closed_pair": pixel_identical(frames[args.closed_in], frames[args.closed_in + 1]),
        "half_out_pair": pixel_identical(frames[args.half_out], frames[args.half_out + 1]),
        "open_start_equals_open_out": pixel_identical(
            frames[args.open_start], frames[args.open_out]
        ),
        "open_out_equals_last": pixel_identical(frames[args.open_out], frames[last]),
    }
    transitions = {
        "open_to_half": outside_boxes_identical(
            frames[args.open_start], frames[args.half_in], allowed_boxes
        ),
        "half_to_closed": outside_boxes_identical(
            frames[args.half_in], frames[args.closed_in], allowed_boxes
        ),
        "closed_to_half": outside_boxes_identical(
            frames[args.closed_in + 1], frames[args.half_out], allowed_boxes
        ),
        "half_to_open": outside_boxes_identical(
            frames[args.half_out + 1], frames[args.open_out], allowed_boxes
        ),
    }
    every_frame_fixed_outside_allowed_regions = all(
        outside_boxes_identical(frames[0], frames[index], allowed_boxes)
        for index in expected_indices
    )
    report = {
        "status": "passed",
        "frames": expected_count,
        "dimensions": list(dimensions[0]),
        "fps": args.fps,
        "duration_seconds": args.duration,
        "animation": "blink_only",
        "allowed_change_boxes": [list(box) for box in allowed_boxes],
        "repeated_state_pixel_identity": repeated_checks,
        "transitions_change_only_allowed_regions": transitions,
        "every_frame_fixed_outside_allowed_regions": (
            every_frame_fixed_outside_allowed_regions
        ),
        "diff_bboxes": {
            "open_to_half": effective_difference(
                frames[args.open_start], frames[args.half_in]
            ).getbbox(),
            "half_to_closed": effective_difference(
                frames[args.half_in], frames[args.closed_in]
            ).getbbox(),
        },
    }
    if (
        not all(repeated_checks.values())
        or not all(transitions.values())
        or not every_frame_fixed_outside_allowed_regions
    ):
        report["status"] = "failed"

    report_path = args.report.expanduser().resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.contact_crop:
        crop_box = tuple(args.contact_crop)
    else:
        width, height = dimensions[0]
        allowed_box = (
            min(box[0] for box in allowed_boxes),
            min(box[1] for box in allowed_boxes),
            max(box[2] for box in allowed_boxes),
            max(box[3] for box in allowed_boxes),
        )
        margin_x = max(40, (allowed_box[2] - allowed_box[0]) * 2)
        margin_y = max(40, (allowed_box[3] - allowed_box[1]) * 2)
        crop_box = (
            max(0, allowed_box[0] - margin_x),
            max(0, allowed_box[1] - margin_y),
            min(width, allowed_box[2] + margin_x),
            min(height, allowed_box[3] + margin_y),
        )
    indices = list(range(args.open_start, args.open_out + 1))
    if len(indices) != 8:
        raise ValueError("Contact sheet expects exactly eight frames from open-start to open-out")
    build_contact(
        frames,
        indices,
        crop_box,
        args.contact.expanduser().resolve(),
    )
    build_preview(
        [frames[index] for index in expected_indices],
        args.fps,
        args.preview.expanduser().resolve(),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
