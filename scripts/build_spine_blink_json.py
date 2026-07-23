#!/usr/bin/env python3
"""Create a minimal Spine JSON containing only an attachment-based blink."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from PIL import Image


STATES = ("character_open", "character_half", "character_closed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--images-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--skeleton-name", required=True)
    parser.add_argument("--spine-version", default="4.3.23")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--duration", type=float, default=3.2)
    parser.add_argument("--open-start", type=int, default=34)
    parser.add_argument("--half-in", type=int, default=35)
    parser.add_argument("--closed-in", type=int, default=37)
    parser.add_argument("--half-out", type=int, default=39)
    parser.add_argument("--open-out", type=int, default=41)
    return parser.parse_args()


def attachment(name: str, width: int, height: int) -> dict[str, object]:
    return {
        "path": name,
        "y": height / 2,
        "width": width,
        "height": height,
    }


def attachment_key(frame: int, fps: int, name: str) -> dict[str, object]:
    key: dict[str, object] = {"name": name}
    if frame:
        key["time"] = frame / fps
    return key


def main() -> None:
    args = parse_args()
    images_dir = args.images_dir.expanduser().resolve()
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.stem != args.skeleton_name:
        raise ValueError(
            "Spine uses the import JSON filename as the skeleton name; "
            f"output stem {output.stem!r} must equal --skeleton-name {args.skeleton_name!r}"
        )

    paths = [images_dir / f"{state}.png" for state in STATES]
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)
    dimensions = [Image.open(path).size for path in paths]
    if len(set(dimensions)) != 1:
        raise ValueError(f"State dimensions differ: {dimensions}")
    width, height = dimensions[0]

    frames = [
        0,
        args.open_start,
        args.half_in,
        args.closed_in,
        args.half_out,
        args.open_out,
        round(args.duration * args.fps),
    ]
    if frames != sorted(frames) or len(set(frames)) != len(frames):
        raise ValueError(f"Frames must be strictly increasing: {frames}")

    images_path = os.path.relpath(images_dir, output.parent).replace(os.sep, "/")
    blink = [
        (0, "character_open"),
        (args.open_start, "character_open"),
        (args.half_in, "character_half"),
        (args.closed_in, "character_closed"),
        (args.half_out, "character_half"),
        (args.open_out, "character_open"),
        (round(args.duration * args.fps), "character_open"),
    ]
    data = {
        "skeleton": {
            "hash": f"{args.skeleton_name}-blink-only",
            "spine": args.spine_version,
            "x": -width / 2,
            "width": width,
            "height": height,
            "images": f"./{images_path}/",
        },
        "bones": [{"name": "root", "color": "ffffffff"}],
        "slots": [{"name": "character", "bone": "root", "attachment": "character_open"}],
        "skins": [
            {
                "name": "default",
                "attachments": {
                    "character": {
                        state: attachment(state, width, height) for state in STATES
                    }
                },
            }
        ],
        "animations": {
            "blink_only": {
                "slots": {
                    "character": {
                        "attachment": [
                            attachment_key(frame, args.fps, state) for frame, state in blink
                        ]
                    }
                }
            }
        },
    }
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
