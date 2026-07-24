#!/usr/bin/env python3
"""Build review-only v1 eyebrow-linked blink states from approved eye states."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from statistics import median
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFilter


SEQUENCE = (
    (34, "open"),
    (35, "half"),
    (36, "half"),
    (37, "closed"),
    (38, "closed"),
    (39, "half"),
    (40, "half"),
    (41, "open"),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def effective_difference(first: Image.Image, second: Image.Image) -> Image.Image:
    channels = ImageChops.difference(first.convert("RGBA"), second.convert("RGBA")).split()
    result = channels[0]
    for channel in channels[1:]:
        result = ImageChops.lighter(result, channel)
    return result


def outside_boxes_identical(
    first: Image.Image,
    second: Image.Image,
    boxes: list[tuple[int, int, int, int]],
) -> bool:
    difference = effective_difference(first, second)
    for box in boxes:
        difference.paste(0, box)
    return difference.getbbox() is None


def changed_pixels(first: Image.Image, second: Image.Image) -> int:
    difference = effective_difference(first, second)
    values = (
        difference.get_flattened_data()
        if hasattr(difference, "get_flattened_data")
        else difference.getdata()
    )
    return sum(1 for value in values if value)


def resolve_config_path(config_path: Path, value: str) -> Path:
    candidate = Path(value).expanduser()
    return candidate if candidate.is_absolute() else (config_path.parent / candidate).resolve()


def color_shift(
    base_patch: Image.Image,
    generated_patch: Image.Image,
    raw_mask: Image.Image,
) -> tuple[int, int, int]:
    base_pixels = base_patch.convert("RGB").load()
    generated_pixels = generated_patch.convert("RGB").load()
    mask_pixels = raw_mask.load()
    samples: list[list[int]] = [[], [], []]
    for y in range(base_patch.height):
        for x in range(base_patch.width):
            if mask_pixels[x, y]:
                continue
            base_rgb = base_pixels[x, y]
            generated_rgb = generated_pixels[x, y]
            if min(base_rgb) < 105 or min(generated_rgb) < 105:
                continue
            for channel in range(3):
                delta = base_rgb[channel] - generated_rgb[channel]
                if abs(delta) <= 80:
                    samples[channel].append(delta)
    return tuple(round(median(values)) if values else 0 for values in samples)


def shifted_patch(image: Image.Image, shift: tuple[int, int, int]) -> Image.Image:
    output = image.convert("RGBA")
    pixels = output.load()
    for y in range(output.height):
        for x in range(output.width):
            red, green, blue, alpha = pixels[x, y]
            pixels[x, y] = (
                max(0, min(255, red + shift[0])),
                max(0, min(255, green + shift[1])),
                max(0, min(255, blue + shift[2])),
                alpha,
            )
    return output


def apply_regions(
    base: Image.Image,
    generated: Image.Image,
    regions: list[dict[str, Any]],
    feather_radius: float,
) -> Image.Image:
    if base.size != generated.size:
        raise ValueError(f"Canvas mismatch: {base.size} != {generated.size}")
    output = base.copy().convert("RGBA")
    for region in regions:
        box = tuple(int(value) for value in region["box"])
        base_patch = base.crop(box).convert("RGBA")
        generated_patch = generated.crop(box).convert("RGBA")
        raw_mask = Image.new("L", base_patch.size, 0)
        polygon = [tuple(int(value) for value in point) for point in region["polygon"]]
        ImageDraw.Draw(raw_mask).polygon(polygon, fill=255)
        shift = color_shift(base_patch, generated_patch, raw_mask)
        corrected = shifted_patch(generated_patch, shift)
        corrected.putalpha(base_patch.getchannel("A"))
        feathered = raw_mask.filter(ImageFilter.GaussianBlur(feather_radius))
        composite = Image.composite(corrected, base_patch, feathered)
        output.paste(composite, (box[0], box[1]))
    return output


def checkerboard(size: tuple[int, int]) -> Image.Image:
    image = Image.new("RGBA", size, (180, 180, 180, 255))
    draw = ImageDraw.Draw(image)
    tile = 32
    for y in range(0, size[1], tile):
        for x in range(0, size[0], tile):
            if (x // tile + y // tile) % 2:
                draw.rectangle(
                    (x, y, x + tile - 1, y + tile - 1),
                    fill=(138, 138, 138, 255),
                )
    return image


def review_crop(
    config: dict[str, Any],
    regions: list[dict[str, Any]],
    canvas_size: tuple[int, int],
) -> tuple[int, int, int, int]:
    if config.get("review_crop"):
        return tuple(int(value) for value in config["review_crop"])
    boxes = [tuple(int(value) for value in region["box"]) for region in regions]
    left = max(0, min(box[0] for box in boxes) - 90)
    top = max(0, min(box[1] for box in boxes) - 90)
    right = min(canvas_size[0], max(box[2] for box in boxes) + 90)
    bottom = min(canvas_size[1], max(box[3] for box in boxes) + 140)
    return left, top, right, bottom


def build_contact(
    states: dict[str, Image.Image],
    crop_box: tuple[int, int, int, int],
    output: Path,
) -> None:
    scale = 2
    padding = 14
    label_height = 26
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
    for position, (frame, state) in enumerate(SEQUENCE):
        column = position % 4
        row = position // 4
        x = padding + column * (cell_width + padding)
        y = padding + row * (cell_height + label_height + padding)
        crop = states[state].crop(crop_box).resize(
            (cell_width, cell_height),
            Image.Resampling.NEAREST,
        )
        background = checkerboard(crop.size)
        background.alpha_composite(crop)
        canvas.paste(background.convert("RGB"), (x, y + label_height))
        draw.text((x, y), f"frame {frame}  {state} + brow v1", fill=(242, 242, 242))
    canvas.save(output)


def build_preview(
    states: dict[str, Image.Image],
    crop_box: tuple[int, int, int, int],
    output: Path,
) -> None:
    durations = [850, 75, 75, 90, 90, 75, 75, 850]
    frames = []
    for _, state in SEQUENCE:
        crop = states[state].crop(crop_box)
        frame = checkerboard((crop.width * 2, crop.height * 2))
        frame.alpha_composite(
            crop.resize(frame.size, Image.Resampling.NEAREST),
        )
        frames.append(frame)
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        lossless=True,
        quality=100,
        method=6,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--open", required=True, type=Path)
    parser.add_argument("--half", required=True, type=Path)
    parser.add_argument("--closed", required=True, type=Path)
    parser.add_argument("--half-reference", required=True, type=Path)
    parser.add_argument("--closed-reference", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    paths = {
        name: value.expanduser().resolve()
        for name, value in {
            "open": args.open,
            "half": args.half,
            "closed": args.closed,
            "half_reference": args.half_reference,
            "closed_reference": args.closed_reference,
            "config": args.config,
        }.items()
    }
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    config: dict[str, Any] = json.loads(paths["config"].read_text(encoding="utf-8"))
    regions = config["brow_regions"]
    boxes = [tuple(int(value) for value in region["box"]) for region in regions]
    feather_radius = float(config.get("feather_radius", 1.0))

    open_image = Image.open(paths["open"]).convert("RGBA")
    half_base = Image.open(paths["half"]).convert("RGBA")
    closed_base = Image.open(paths["closed"]).convert("RGBA")
    half_reference = Image.open(paths["half_reference"]).convert("RGBA")
    closed_reference = Image.open(paths["closed_reference"]).convert("RGBA")
    sizes = {
        image.size
        for image in (
            open_image,
            half_base,
            closed_base,
            half_reference,
            closed_reference,
        )
    }
    if len(sizes) != 1:
        raise ValueError(f"All inputs must share one canvas size: {sorted(sizes)}")

    half = apply_regions(half_base, half_reference, regions, feather_radius)
    closed = apply_regions(closed_base, closed_reference, regions, feather_radius)
    open_output = output_dir / "candidate_open.png"
    half_output = output_dir / "candidate_half_brow.png"
    closed_output = output_dir / "candidate_closed_brow.png"
    shutil.copyfile(paths["open"], open_output)
    half.save(half_output)
    closed.save(closed_output)

    crop_box = review_crop(config, regions, open_image.size)
    states = {"open": open_image, "half": half, "closed": closed}
    build_contact(states, crop_box, output_dir / "eyebrow-blink-review-contact.png")
    build_preview(states, crop_box, output_dir / "eyebrow-blink-review-loop.webp")

    report = {
        "status": "review_only",
        "formal_project_modified": False,
        "skill_modified": False,
        "method": "v1 full-reference color match with feathered brow-region composite",
        "dimensions": list(open_image.size),
        "open_byte_identical_to_source": sha256(paths["open"]) == sha256(open_output),
        "brow_regions": [
            {"name": str(region["name"]), "box": list(box)}
            for region, box in zip(regions, boxes)
        ],
        "half_vs_approved_half": {
            "changed_pixels": changed_pixels(half_base, half),
            "changed_outside_brow_regions": not outside_boxes_identical(
                half_base, half, boxes
            ),
            "diff_bbox": effective_difference(half_base, half).getbbox(),
        },
        "closed_vs_approved_closed": {
            "changed_pixels": changed_pixels(closed_base, closed),
            "changed_outside_brow_regions": not outside_boxes_identical(
                closed_base, closed, boxes
            ),
            "diff_bbox": effective_difference(closed_base, closed).getbbox(),
        },
        "review_crop": list(crop_box),
    }
    report_path = output_dir / "eyebrow-blink-review-qa.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if (
        not report["open_byte_identical_to_source"]
        or report["half_vs_approved_half"]["changed_outside_brow_regions"]
        or report["closed_vs_approved_closed"]["changed_outside_brow_regions"]
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
