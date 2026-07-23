#!/usr/bin/env python3
"""Build aligned open, half, and closed full-canvas blink states."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFilter


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


def color_match(
    generated: Image.Image,
    target: Image.Image,
    region: Image.Image,
    ring_size: int,
) -> Image.Image:
    ring = ImageChops.subtract(region.filter(ImageFilter.MaxFilter(ring_size)), region)
    generated_pixels = generated.convert("RGB").load()
    target_pixels = target.convert("RGB").load()
    ring_pixels = ring.load()
    samples: list[tuple[int, int, int]] = []
    for y in range(target.height):
        for x in range(target.width):
            if not ring_pixels[x, y]:
                continue
            generated_pixel = generated_pixels[x, y]
            target_pixel = target_pixels[x, y]
            if min(generated_pixel) < 105 or min(target_pixel) < 105:
                continue
            samples.append(
                tuple(target_pixel[channel] - generated_pixel[channel] for channel in range(3))
            )

    shifts = [0, 0, 0]
    for channel in range(3):
        if samples:
            values = sorted(sample[channel] for sample in samples)
            shifts[channel] = values[len(values) // 2]

    output = generated.convert("RGBA")
    pixels = output.load()
    for y in range(output.height):
        for x in range(output.width):
            red, green, blue, alpha = pixels[x, y]
            pixels[x, y] = (
                max(0, min(255, red + shifts[0])),
                max(0, min(255, green + shifts[1])),
                max(0, min(255, blue + shifts[2])),
                alpha,
            )
    return output


def resolve_config_path(config_path: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (config_path.parent / path).resolve()


def load_patch(
    source_path: Path,
    source_box: list[int] | None,
    target_box: tuple[int, int, int, int],
) -> Image.Image:
    source = Image.open(source_path).convert("RGBA")
    expected = (target_box[2] - target_box[0], target_box[3] - target_box[1])
    if source_box is not None:
        patch = source.crop(tuple(source_box))
    elif source.size == expected:
        patch = source
    elif source.width >= target_box[2] and source.height >= target_box[3]:
        patch = source.crop(target_box)
    else:
        raise ValueError(
            f"{source_path}: provide source_box; source {source.size}, expected patch {expected}"
        )
    if patch.size != expected:
        raise ValueError(f"{source_path}: patch {patch.size} != target {expected}")
    return patch


def outside_boxes_identical(
    first: Image.Image,
    second: Image.Image,
    boxes: list[tuple[int, int, int, int]],
) -> bool:
    difference = effective_difference(first, second)
    for box in boxes:
        difference.paste(0, box)
    return difference.getbbox() is None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--closed-reference", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    original_path = args.original.expanduser().resolve()
    reference_path = args.closed_reference.expanduser().resolve()
    config_path = args.config.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    config: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))

    original = Image.open(original_path).convert("RGBA")
    reference = Image.open(reference_path).convert("RGBA")
    output_dir.mkdir(parents=True, exist_ok=True)

    states = {
        "half": original.copy(),
        "closed": original.copy(),
    }
    target_boxes: list[tuple[int, int, int, int]] = []
    feather_radius = float(config.get("feather_radius", 0.8))
    ring_size = int(config.get("color_match_ring", 7))
    if ring_size < 3 or ring_size % 2 == 0:
        raise ValueError("color_match_ring must be an odd integer >= 3")

    for eye in config["eyes"]:
        name = str(eye["name"])
        target_box = tuple(int(value) for value in eye["target_box"])
        if len(target_box) != 4:
            raise ValueError(f"{name}: target_box must contain four integers")
        target_boxes.append(target_box)

        half_path = resolve_config_path(config_path, eye["half_source"])
        half_patch = load_patch(half_path, eye.get("half_source_box"), target_box)
        closed_patch = load_patch(
            reference_path,
            eye.get("closed_source_box"),
            target_box,
        )

        region = Image.new("L", half_patch.size, 0)
        polygon = [tuple(int(value) for value in point) for point in eye["mask_polygon"]]
        ImageDraw.Draw(region).polygon(polygon, fill=255)
        matched = color_match(closed_patch, half_patch, region, ring_size)
        feathered = region.filter(ImageFilter.GaussianBlur(feather_radius))
        corrected_closed = Image.composite(matched, half_patch, feathered)

        destination = (target_box[0], target_box[1])
        states["half"].alpha_composite(half_patch, destination)
        states["closed"].alpha_composite(corrected_closed, destination)
        half_patch.save(output_dir / f"eye_{name}_half.png")
        corrected_closed.save(output_dir / f"eye_{name}_closed.png")

    open_output = output_dir / "character_open.png"
    half_output = output_dir / "character_half.png"
    closed_output = output_dir / "character_closed.png"
    shutil.copyfile(original_path, open_output)
    states["half"].save(half_output)
    states["closed"].save(closed_output)

    open_image = Image.open(open_output).convert("RGBA")
    report = {
        "status": "passed",
        "mode": "original full illustration; eye-local changes only",
        "dimensions": list(original.size),
        "original_sha256": sha256(original_path),
        "open_sha256": sha256(open_output),
        "open_byte_identical_to_original": sha256(original_path) == sha256(open_output),
        "half_changes_eye_local_only": outside_boxes_identical(
            open_image, states["half"], target_boxes
        ),
        "closed_changes_eye_local_only": outside_boxes_identical(
            open_image, states["closed"], target_boxes
        ),
        "open_to_half_diff_bbox": effective_difference(
            open_image, states["half"]
        ).getbbox(),
        "half_to_closed_diff_bbox": effective_difference(
            states["half"], states["closed"]
        ).getbbox(),
        "target_boxes": [list(box) for box in target_boxes],
    }
    required = (
        report["open_byte_identical_to_original"],
        report["half_changes_eye_local_only"],
        report["closed_changes_eye_local_only"],
    )
    if not all(required):
        report["status"] = "failed"
    report_path = output_dir / "eye-state-qa.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
