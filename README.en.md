<p align="right">
  <a href="./README.md">简体中文</a> | English
</p>

# Spine Original-Art Blink

Create a high-fidelity, blink-only Spine animation from one complete character illustration, then prove with native Spine frames that the body, hair, clothing, limbs, accessories, and background remain pixel-fixed.

<p align="center">
  <img src="./assets/blink-example.gif" alt="Spine blink-only example" width="384" />
</p>

## Use cases

- Start a Spine or Live2D-style character workflow from one illustration.
- Build and approve blinking before breathing, hair, or body motion.
- Fix shifted eyelids, skin rectangles, color seams, ghosting, or full-body drift.
- Deliver a reproducible Spine project, native PNG frames, and pixel-level QA.

## Core rules

- The original illustration remains the source of truth.
- `character_open.png` must be byte-identical to the approved working source.
- Open, half-closed, and closed states use the same full canvas and placement.
- Pixels may change only inside approved left/right eye boxes.
- Generated images may be used only as local eyelid references, never as a replacement body.
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
Use $spine-original-art-blink to create a blink-only Spine animation from this illustration and complete native frame-by-frame validation.
```

The skill first reads [`references/workflow.md`](./references/workflow.md), then:

1. Audits dimensions, mode, alpha, and SHA-256.
2. Defines exact eye boxes and feather polygons.
3. Prepares half-closed and closed local eye references.
4. Builds three aligned full-canvas states.
5. Creates a minimal `blink_only` Spine project.
6. Exports native PNG frames 0–96 at 30 FPS.
7. Validates fixed non-eye pixels, repeated states, and a seamless loop.
8. Delivers the Spine project, source chain, contact sheet, preview, and QA reports.

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
│   └── blink-example.gif
├── references/
│   ├── blink-config.example.json
│   └── workflow.md
└── scripts/
    ├── build_eye_states.py
    ├── build_spine_blink_json.py
    └── validate_blink_export.py
```

## Acceptance gates

The final result must satisfy all of the following:

- The open-state hash equals the original hash.
- All states share dimensions, alpha handling, scale, and placement.
- Every difference box stays inside the approved eye region.
- Every native Spine frame is pixel-identical outside the eyes.
- Frame order is open → half → closed → half → open.
- The first and last frames loop without a jump.
- The root bone has no transform timeline.
- Visual review shows no rectangular patch, color seam, duplicate edge, eyelid offset, face drift, or antialiasing halo.

The example GIF uses a completely original Japanese fantasy character and exists only to demonstrate the final blink workflow.
