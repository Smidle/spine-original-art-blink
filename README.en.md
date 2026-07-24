<p align="right">
  <a href="./README.md">简体中文</a> | English
</p>

# Spine Original-Art Eye-and-Eyebrow Blink

Create a high-fidelity Spine blink with linked eyelid and eyebrow motion from one complete character illustration. Candidate review and native Spine frames prove that every unapproved pixel remains fixed.

<p align="center">
  <img src="./assets/v1-eye-eyebrow-blink.webp" alt="Spine v1 eye-and-eyebrow blink example" width="384" />
</p>

## This release: v1 eyebrow linkage

- Upgrades the workflow from eye-only blinking to coordinated eyelid and eyebrow motion.
- Adds a review gate before formal writes: open, half, closed, contact-sheet, and loop candidates must be explicitly approved before the `.spine` project changes.
- Adds `build_eyebrow_states_v1.py` and `brow-config-v1.example.json` to reproduce the approved v1 local eyebrow treatment.
- Extends native export validation with repeatable `--allowed-box` arguments for separately approved eye and eyebrow regions while retaining legacy `--allowed-eye-box` support.
- Replaces the example with a 97-frame, 30 FPS, 3.2-second native-QA result in which the body, limbs, hair, and clothing never switch or move.

## Use cases

- Start a Spine or Live2D-style character workflow from one illustration.
- Build and approve linked eye and eyebrow motion before breathing, hair, or body motion.
- Fix shifted eyelids, broken brows, skin rectangles, color seams, ghosting, or full-body drift.
- Deliver a reproducible Spine project, native PNG frames, and pixel-level QA.

## Core rules

- The original illustration remains the source of truth.
- `character_open.png` must be byte-identical to the approved working source.
- Open, half-closed, and closed states use the same full canvas and placement.
- Pixels may change only inside approved left/right eye and eyebrow regions.
- Generated images may be used only as local eyelid or eyebrow references, never as a replacement body.
- Eyebrow candidates must be reviewed before they can overwrite formal textures or the Spine project.
- The Spine project contains one bone, one slot, three attachments, and one attachment timeline.
- Work stops after blink acceptance; breathing and body animation are not inferred.

## Installation

Install from the standalone repository:

```bash
npx skills add Smidle/spine-original-art-blink
```

Select the target agent in the interactive installer.

Alternatively, clone the repository and copy it into your Codex personal skills directory:

```bash
git clone https://github.com/Smidle/spine-original-art-blink.git
cp -R spine-original-art-blink ~/.codex/skills/
```

## Usage

Provide one original character illustration in Codex, then invoke:

```text
Use $spine-original-art-blink to create a linked eye-and-eyebrow Spine blink from this illustration, review the candidates first, then update the formal project and complete native frame-by-frame validation.
```

The skill first reads [`references/workflow.md`](./references/workflow.md), then:

1. Audits dimensions, mode, alpha, and SHA-256.
2. Defines exact eye boxes, eyebrow boxes, and feather polygons.
3. Prepares local half-closed, closed, and linked-eyebrow references.
4. Builds three aligned full-canvas candidate states.
5. Delivers a contact sheet, loop preview, and local pixel QA for explicit approval.
6. Promotes approved candidates to formal textures and creates a minimal `blink_only` Spine project.
7. Exports native PNG frames 0–96 at 30 FPS.
8. Validates fixed unapproved pixels, repeated states, and a seamless loop.
9. Delivers the Spine project, source chain, contact sheet, preview, and QA reports.

## Default frame schedule

| Frames | State |
|---|---|
| 0–34 | Open |
| 35–36 | Half-closed |
| 37–38 | Closed |
| 39–40 | Half-closed |
| 41–96 | Open |

The default animation is 30 FPS and 3.2 seconds, with attachment keys at frames 0, 34, 35, 37, 39, 41, and 96.

## Requirements

- Spine Professional 4.3, or the version matching the target project.
- Python 3.
- Pillow.
- Default macOS Spine CLI path:

```text
/Applications/Spine.app/Contents/MacOS/Spine
```

If the system Python does not include Pillow, the skill prefers the Python runtime bundled with the Codex workspace.

## Structure

```text
spine-original-art-blink/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── assets/
│   └── v1-eye-eyebrow-blink.webp
├── references/
│   ├── blink-config.example.json
│   ├── brow-config-v1.example.json
│   └── workflow.md
└── scripts/
    ├── build_eye_states.py
    ├── build_eyebrow_states_v1.py
    ├── build_spine_blink_json.py
    └── validate_blink_export.py
```

## Acceptance gates

The final result must satisfy all of the following:

- The open-state hash equals the original hash.
- All states share dimensions, alpha handling, scale, and placement.
- Every difference box stays inside an approved eye or eyebrow region.
- Every native Spine frame is pixel-identical outside approved regions.
- Frame order is open → half → closed → half → open.
- The first and last frames loop without a jump.
- The root bone has no transform timeline.
- Visual review shows no rectangular patch, color seam, duplicate edge, broken brow, white remnant at the original brow, eyelid offset, face drift, or antialiasing halo.

The example WebP shows the reviewed result from this v1 eye-and-eyebrow workflow and exists only to demonstrate the final Skill output.
