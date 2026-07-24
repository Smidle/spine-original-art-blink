---
name: spine-original-art-blink
description: Create a high-fidelity eye-and-eyebrow blink-only Spine animation from one original illustration while preserving every unapproved pixel. Use for Spine or Live2D-style open/half/closed eyelid states, v1 eyebrow linkage, fixing blink offsets or color seams, avoiding body slicing and ghosting, importing a minimal Spine project, and performing review-first plus native frame-by-frame pixel QA before any breathing, hair, limb, clothing, or accessory animation begins.
---

# Spine Original-Art Blink

Build and approve blinking as an isolated first milestone. Keep the complete
original character intact and change only explicitly approved eye and eyebrow
regions.

## Required reading

Read [references/workflow.md](references/workflow.md) completely before taking
task actions. It contains the tool routing, every production step, the Spine
commands, and the acceptance checklist.

Use [references/blink-config.example.json](references/blink-config.example.json)
for eye states. Read
[references/brow-config-v1.example.json](references/brow-config-v1.example.json)
when adding v1 eyebrow linkage.

## Non-negotiable constraints

- Preserve the original illustration as the source of truth.
- Keep `character_open.png` byte-identical to the original file.
- Use full-canvas, identically aligned open, half, and closed states.
- Change pixels only inside explicitly approved eye and eyebrow boxes.
- Do not slice, transform, key, or animate the body, hair, limbs, clothing, or
  accessories during this milestone.
- Do not resize an eye patch to make it fit. Correct the source box or redraw
  the eye state instead.
- Never use an AI-generated full character as the replacement illustration.
  Use generated output only as a local eyelid or eyebrow reference after
  visual review.
- Import a minimal Spine skeleton: one root bone, one slot, three attachments,
  one attachment timeline, and no root transform timeline.
- Build eyebrow states in an isolated review directory. Do not change formal
  images, the Spine project, or this Skill before explicit user approval.
- Export native Spine frames and prove that every pixel outside the approved
  eye and eyebrow boxes is fixed.
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
9. If eyebrows should link to the blink, generate full-canvas half/closed
   eyebrow references, but treat them only as local visual sources.
10. Run `scripts/build_eyebrow_states_v1.py` against the approved eye-only
    states. Inspect its contact sheet, loop, and review-only QA. Stop until the
    user explicitly approves the candidate.
11. Preserve the eye-only source states, then promote the approved candidate
    half/closed images. Keep open byte-identical.
12. Run `scripts/build_spine_blink_json.py`.
13. Import the JSON into Spine with the CLI, open the project, and inspect the
    `blink_only` animation in the Spine UI.
14. Export PNG frames from Spine at the intended FPS.
15. Run `scripts/validate_blink_export.py` with every approved eye and eyebrow
    change box.
16. Inspect the native contact sheet and animated preview.
17. Retain only the approved project, its exact source chain, and QA artifacts.

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

Build a review-only v1 eyebrow-linked candidate:

```bash
python3 scripts/build_eyebrow_states_v1.py \
  --open /path/eye-only/character_open.png \
  --half /path/eye-only/character_half.png \
  --closed /path/eye-only/character_closed.png \
  --half-reference /path/generated-half-brow-reference.png \
  --closed-reference /path/generated-closed-brow-reference.png \
  --config /path/brow-config-v1.json \
  --output-dir /path/review-eyebrow-v1
```

The v1 builder performs a median local color shift, composites only the two
feathered eyebrow polygons, keeps the open file byte-identical, and emits:

- `candidate_open.png`
- `candidate_half_brow.png`
- `candidate_closed_brow.png`
- `eyebrow-blink-review-contact.png`
- `eyebrow-blink-review-loop.webp`
- `eyebrow-blink-review-qa.json`

Require `changed_outside_brow_regions: false` for both half and closed.
Present the contact sheet and loop to the user before promoting either image.

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
  --allowed-box EYE_LEFT_X1 EYE_LEFT_Y1 EYE_LEFT_X2 EYE_LEFT_Y2 \
  --allowed-box EYE_RIGHT_X1 EYE_RIGHT_Y1 EYE_RIGHT_X2 EYE_RIGHT_Y2 \
  --allowed-box BROW_LEFT_X1 BROW_LEFT_Y1 BROW_LEFT_X2 BROW_LEFT_Y2 \
  --allowed-box BROW_RIGHT_X1 BROW_RIGHT_Y1 BROW_RIGHT_X2 BROW_RIGHT_Y2
```

## Acceptance gates

Require all of the following:

- Open output hash equals the original hash.
- All three states have identical dimensions, alpha handling, scale, and
  placement.
- The review candidate does not modify formal files before user approval.
- Candidate half/closed changes relative to the eye-only bases are inside the
  approved eyebrow regions.
- Open-to-half and half-to-closed difference boxes are inside the approved eye
  and eyebrow regions.
- All native frames are identical outside every approved change region.
- Repeated states are pixel-identical.
- The end frame loops to the open state without a jump.
- Frame order is open → half → closed → half → open.
- Spine reports one bone, one slot, three attachments, and one animation.
- The root bone has no animation timeline.
- Visual review shows no rectangle, color seam, duplicate edge, offset eyelid,
  face drift, antialias halo, or unexpected generated-image change.

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
