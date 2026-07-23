---
name: spine-original-art-blink
description: Create a high-fidelity blink-only Spine animation from one original illustration while preserving every non-eye pixel. Use for Spine or Live2D-style eye animation, open/half/closed eyelid states, fixing blink offsets or color seams, avoiding body slicing and ghosting, importing a minimal Spine project, and performing native frame-by-frame pixel QA before any breathing, hair, limb, clothing, or accessory animation begins.
---

# Spine Original-Art Blink

Build and approve blinking as an isolated first milestone. Keep the complete
original character intact and change only the two eye regions.

## Required reading

Read [references/workflow.md](references/workflow.md) completely before taking
task actions. It contains the tool routing, every production step, the Spine
commands, and the acceptance checklist.

Use [references/blink-config.example.json](references/blink-config.example.json)
when preparing the eye-state build configuration.

## Non-negotiable constraints

- Preserve the original illustration as the source of truth.
- Keep `character_open.png` byte-identical to the original file.
- Use full-canvas, identically aligned open, half, and closed states.
- Change pixels only inside explicitly approved eye boxes.
- Do not slice, transform, key, or animate the body, hair, limbs, clothing, or
  accessories during this milestone.
- Do not resize an eye patch to make it fit. Correct the source box or redraw
  the eye state instead.
- Never use an AI-generated full character as the replacement illustration.
  Use generated output only as a local eyelid reference after visual review.
- Import a minimal Spine skeleton: one root bone, one slot, three attachments,
  one attachment timeline, and no root transform timeline.
- Export native Spine frames and prove that every non-eye pixel is fixed.
- Stop after blink acceptance. Do not infer permission to begin idle motion.

## Production workflow

1. Audit and archive prior attempts without deleting the approved original.
2. Record source dimensions, color mode, alpha, and SHA-256.
3. Inspect the face at original resolution and define exact left/right eye
   boxes and feather polygons.
4. Prepare an approved half-closed source for each eye.
5. Create or draw a closed-eye reference. If image generation is used, request
   a precise eye-only edit and reject changes outside the eyes.
6. Create a build config from the bundled example.
7. Run `scripts/build_eye_states.py`.
8. Inspect the three full-canvas states and the generated QA report.
9. Run `scripts/build_spine_blink_json.py`.
10. Import the JSON into Spine with the CLI, open the project, and inspect the
    `blink_only` animation in the Spine UI.
11. Export PNG frames from Spine at the intended FPS.
12. Run `scripts/validate_blink_export.py`.
13. Inspect the native contact sheet and animated preview.
14. Retain only the approved project, its exact source chain, and QA artifacts.

## Script usage

Use a Python environment with Pillow. If the default Python lacks Pillow, load
the workspace dependencies and use the bundled Python executable.

Build the three aligned character states:

```bash
python3 scripts/build_eye_states.py \
  --original /path/original.png \
  --closed-reference /path/closed-reference.png \
  --config /path/blink-config.json \
  --output-dir /path/images-blink-only
```

Build the Spine import JSON:

```bash
python3 scripts/build_spine_blink_json.py \
  --images-dir /path/images-blink-only \
  --output /path/character-blink-only.json \
  --skeleton-name character-blink-only \
  --fps 30 --duration 3.2 \
  --open-start 34 --half-in 35 --closed-in 37 \
  --half-out 39 --open-out 41
```

Import and inspect:

```bash
"/Applications/Spine.app/Contents/MacOS/Spine" \
  -i /path/character-blink-only.json \
  -o /path/character-blink-only.spine -r

open -a "/Applications/Spine.app" /path/character-blink-only.spine

"/Applications/Spine.app/Contents/MacOS/Spine" \
  -i /path/character-blink-only.spine
```

Export native PNG frames:

```bash
mkdir -p /path/native-frames

"/Applications/Spine.app/Contents/MacOS/Spine" \
  -i /path/character-blink-only.spine \
  -o /path/native-frames \
  -e /path/export-png.json
```

Keep the JSON, image directory, project, and native-frame directory under a
normal workspace folder on macOS. Do not run the Spine image pipeline from
`/tmp` or `/private/tmp`; Spine can create zero-byte PNGs there even when the
project structure is valid.

Validate the native frames:

```bash
python3 scripts/validate_blink_export.py \
  --frames-dir /path/native-frames \
  --report /path/qa-report.json \
  --contact /path/native-contact.png \
  --preview /path/blink.webp \
  --fps 30 --duration 3.2 \
  --open-start 34 --half-in 35 --closed-in 37 \
  --half-out 39 --open-out 41 \
  --allowed-eye-box X1 Y1 X2 Y2
```

## Acceptance gates

Require all of the following:

- Open output hash equals the original hash.
- All three states have identical dimensions, alpha handling, scale, and
  placement.
- Open-to-half and half-to-closed difference boxes are inside the approved eye
  region.
- All native frames are identical outside the approved eye region.
- Repeated states are pixel-identical.
- The end frame loops to the open state without a jump.
- Frame order is open → half → closed → half → open.
- Spine reports one bone, one slot, three attachments, and one animation.
- The root bone has no animation timeline.
- Visual review shows no rectangle, color seam, duplicate edge, offset eyelid,
  face drift, or antialias halo.

If any gate fails, fix the eye source or alignment and repeat from state
generation. Do not compensate by moving the whole attachment in Spine.

## Cleanup and handoff

Resolve cleanup targets with a read-only inventory. Move superseded files to a
uniquely named recoverable Trash folder unless the user explicitly requests
permanent deletion. Retain:

- untouched original;
- approved half-eye sources and closed-eye reference;
- build config and scripts;
- open, half, and closed full-canvas PNGs;
- Spine import JSON and `.spine` project;
- export settings;
- native frames, contact sheet, preview, and QA report.

Report exact paths, animation name, frame schedule, QA status, and Trash
location. State explicitly that later body animation has not started.
