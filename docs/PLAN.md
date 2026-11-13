# TrueGaze — Track 1 "Synthetic Eyes" full win plan

## Status against this plan (14 Nov)
Every required output is done at final quality and committed, two days before the 17 Nov checkpoint.
- **Changed from the plan:** no export step or MPFB fallback (D-009); skin is MakeHuman CC0 photo skins transferred in 3D instead of the diffusion route (D-015); hair is generated mesh strands (D-011); added socket depth, skin drag, hero view, clay/wire breakdowns, motion evaluation, iris light pooling, expression wrinkles (D-014 to D-021).
- **Left:** member names in the deck, demo video, Dockerfile, commit `textures/`, purge the reference video from history, make the repo public, submit. Open list: `TASKS.md`.
- The sections below are the original plan, kept for reference.

## Context
Team Zero Drift (VIT Vellore, 3 members with Claude agents) switched to Track 1 on 12 Nov. Submission **22 Nov 2026** through the Google form, everything in the **public** repo `akshat333-debug/TrueGaze`. Goal: win the track (prize + PPO). The college PoC is not answering questions, so the build must satisfy **every reading** of the spec: the 12 Nov evaluation deck and the 5 Nov launch slides.

Rubric (12 Nov deck): **texture photorealism 60**, kinematic accuracy 20, code and UV portability 20, plus brownie points for natural human-like motion. Launch-slide rubric (calibration, automation, direction pass/fail, sequence + metadata) is covered too.

## Facts verified today (primary sources)
- **GNM = Google's "Generative aNthropometric Model"**, github.com/google/GNM, **Apache 2.0** (code and model), so it can live in a public repo. FLAME is not needed.
- GNM Head v3 mesh contains skin, **both eyeballs (interior sclera/iris/pupil + separate cornea shell)**, teeth, tongue. Joints rotate the **neck and each eyeball**. Expression basis: 100 left-eye + 100 right-eye components (eyelids, brows), 150 lower face, 32 tongue, **1 iris component** (pupil size). 253 identity components. Semantic samplers give identities (gender × 4 ethnicities) and 20 named expressions (incl. SQUINT, WINK_LEFT/RIGHT, SURPRISE, HAPPY).
- **Official UV layout is UDIM**: tile 1001 skin, 1002/1003 left eye interior/cornea, 1004/1005 right eye, 1006 teeth, 1007 tongue. Legacy per-region UVs also exist.
- **GNM ships no skin or iris texture** (only an edge-flow test image). That is exactly why textures are worth 60 points, and where the work goes.
- Weights download automatically from Hugging Face/Kaggle via `GNM.from_remote`. Package targets Python 3.13 and pulls TensorFlow; Blender's Python is 3.11.
- Organizer reference videos are **Chris Jones' "Eye Piece" and "Flexpressions"**: extreme close-up realism, eyelid skin sliding over the eyeball, wet highlights, lashes, micro-movements. That is the taste of the judges.
- This Mac: Apple M3, **8 GB RAM**, 32 GB free disk, Homebrew and ffmpeg present, Blender not installed. System git/python are blocked by an unaccepted Xcode licence; use `/opt/homebrew/bin/git` and `/opt/anaconda3/bin/python3`.

## Strategy in one paragraph
Build our own small, dependency-light pipeline: export GNM once to a compact file, build the Blender scene from a script, and put most effort into **skin + iris textures and eye-region shading** (60 pts), a **physiologically modelled motion engine** (20 pts + brownie), and **one-command reproducibility with textures that drop onto a stock GNM head** (20 pts). Close-up framing on the eye region, like the reference videos, hides what GNM lacks (hair) and shows what is judged.

> **Update 12 Nov (D-009):** Day-1 spike passed. GNM is read directly with NumPy inside Blender, so `tools/export_gnm.py` and `assets/gnm_head.npz` below are replaced by `truegaze/gnm.py` and a small `assets/controls.npz`.

## Architecture
```
TrueGaze/
├── tools/export_gnm.py        # runs outside Blender (py3.13 venv): GNM -> assets/gnm_head.npz
├── assets/gnm_head.npz        # template, UDIM UVs, joints, skin weights, 8 identity presets,
│                              # ~40 expression directions (lids, brows, squint, smile...)  (Apache 2.0)
├── truegaze/
│   ├── motion.py              # pure Python, no bpy: gaze/lid/blink/brow/pupil trajectories
│   ├── scene.py               # bpy: mesh, shape keys, armature, materials, lights, camera
│   ├── materials.py           # skin (SSS), sclera, iris, refractive cornea, tear film
│   ├── eyes.py                # API: move(h, v), reset(), render()
│   └── metadata.py            # per-frame JSON: rotations, projected pupil centres, camera matrix
├── textures/                  # generators: skin transfer/bake, iris synth, detail maps
├── uv_maps/set_01..08/        # DELIVERABLE: face.1001.png + eye tiles, plus normal/roughness
├── render.py                  # CLI: --input Left|Right|"Generate Motion" [--texture N]
├── apply_textures.py          # proves portability: wraps any set onto a stock GNM head
├── wrapper/eyes.py, scene.blend, renders/, metadata.json   # launch-spec bundle
├── outputs/videos/, outputs/images/                        # 3 videos, 5-10 stills
├── tests/                     # motion maths, direction checks, UV/texture validation
├── Dockerfile                 # headless Blender on Linux, CPU Cycles
└── docs/  README.md  TASKS.md  DECISIONS.md
```
Why export instead of importing GNM inside Blender: avoids TensorFlow and the Python-version mismatch, keeps the judge's setup to "install Blender, run one command", and makes the repo self-contained. A community GNM Blender add-on exists but its licence is unclear, so it is not used.

## Workstream 1 — Head, rig, scene (owner A)
1. `export_gnm.py`: template + UDIM UVs + eye/neck joints + skin weights; 8 identity presets from `IdentitySampler` (both genders, 4 groups); expression directions.
2. **Eyelid and brow controls.** GNM's eye components are statistical, not named. Derive clean controls by least squares on lid-margin vertices: *upper lid close, lower lid raise, lid follow up/down, squint, brow raise/lower/furrow*. Use the named samples (WINK, SQUINT, SURPRISE) as starting points. This is the **day-1 spike**; if a clean full blink cannot be reached, add a corrective sculpted shape key.
3. `scene.py`: one mesh with material slots per UDIM region, shape keys, armature with `eye_L`, `eye_R`, `neck` bones rotating about the true eyeball centres.
4. **Eyeball-follows-skin detail** (brownie): lid bulge shape driven by gaze so the cornea visibly pushes the lid, as in the reference videos.
5. Camera locked 40 cm in front of the eye midpoint, 1024×1024, constant lighting (launch spec). A second **close-up camera** (85 mm, shallow depth of field) for the showcase videos.
6. Eyelashes and eyebrows as hair curves bound to the lid-margin and brow vertices so they follow the shape keys. Thin tear-line mesh along the lower lid for the wet highlight.

## Workstream 2 — Textures, 60 points (owner B, most of the effort)
Deliver **8 sets** (rule asks 5–10), each: skin albedo 4K (tile 1001), left iris/sclera and right iris/sclera 2K (1002, 1004), cornea tiles (1003, 1005), plus matching normal and roughness maps. Teeth and tongue tiles included so the head is complete.

**Skin albedo, two routes, best result per set wins by side-by-side render:**
- *Route A (guaranteed, day 2):* CC0 MakeHuman/MPFB skins transferred into the GNM UV layout. Fit the MPFB head to the GNM template (landmarks + shrinkwrap), bake albedo across in Cycles. This is the "bake by comparing UV maps" method the organizer slide names.
- *Route B (quality and diversity):* synthetic identities. Render the untextured GNM head from 5 views, generate photoreal skin for a **non-existent person** with a depth-conditioned diffusion model on free Kaggle/Colab GPU, project the views back into UV space and blend, then remove baked lighting. No real person's face is used, which matches the track's privacy motivation.
- Both routes finish with the same pass: seam repair across UV island borders, symmetric-artifact removal, colour calibration to measured skin tones.

**High-frequency detail (what "photorealism" is judged on):** pore-level normal map (procedural cell noise + albedo-derived detail), roughness variation (oily T-zone, dry cheeks), lip and eyelid-margin colour, painted brow shadow under the hair curves, subsurface scattering with reddish radius, thin specular coat.

**Iris and eye (distinct left and right, as required):** procedural generator in numpy/OpenCV: radial stroma fibres, collarette, crypts, pigment spots, dark limbal ring, pupil edge ruff. Left and right share base colour but use different fibre seeds, like real eyes. Sclera with fine veins and a yellow-pink gradient toward the corners. Shading: **refractive cornea over a recessed iris** (GNM already separates them), wet clear-coat, soft shadow from the upper lid, pupil size driven by the GNM iris component.

**Seam audit:** automated check rendering each set under flat lighting and measuring colour discontinuity along UV island borders, plus a turntable contact sheet reviewed by eye.

## Workstream 3 — Motion engine, 20 points + brownie (owner A)
`motion.py` has no Blender dependency, so it is unit-tested.
- **Gaze:** inputs h, v in [-1, 1] map to a fixation point on a plane **35 cm** ahead, ±5 cm. Each eye aims at the point, giving true 3D rotation and natural **vergence**; torsion follows Listing's law.
- **Saccades:** duration from the main sequence (about 2.2 ms per degree + 21 ms), minimum-jerk velocity profile, small overshoot and corrective glissade.
- **Fixation life:** micro-saccades, slow drift and tremor, so a held gaze never looks frozen.
- **Eyelids:** upper lid follows vertical gaze; lower lid shifts slightly; lids narrow on side gaze.
- **Blinks:** fast close (~100 ms), slower open (~200 ms), every 3–5 s and usually paired with large saccades; eyes dip down and in during a blink.
- **Brows and face:** brows lift on up-gaze; small squint/cheek coupling; optional few-degree head follow on large shifts.
- **Pupil:** slow hippus and constriction on convergence.

**The three required inputs** (`render.py --input ...`, each video ≤ 15 s, target 8–10 s):
- `Left`: settle, saccade left, hold with micro-motion and a blink, return.
- `Right`: mirror.
- `Generate Motion`: seeded natural sequence (look around, eye roll upward, thinking glance, double blink, small smile). `--seed` gives new variations.

**Direction convention (cannot be clarified, so made explicit):** default "Left" = **left on screen**, which is what a judge watching the video sees; `--frame subject` flips to the character's anatomical left. Each video carries a small caption naming the input, and metadata records both.

## Workstream 4 — Automation, portability, both specs (owner C)
- `render.py`: one command builds the scene, renders frames, writes MP4 through Blender's built-in FFmpeg. Flags: `--input`, `--texture 1..8`, `--identity`, `--seed`, `--quality draft|final`.
- `python render.py --all`: regenerates every deliverable (3 videos, 8 stills, 10-frame sequence, metadata, `.blend`).
- **Launch-spec bundle:** `wrapper/eyes.py` with `eyes.move(h, v)`, `eyes.reset()`, `eyes.render()`; 10 clockwise frames at θk = 2πk/10 with h = sin θ, v = cos θ starting at top; per-frame JSON with eye rotations (world frame), projected 2D pupil centres, camera matrix; `scene.blend`; `metadata.json`.
- **`.blend` deliverable:** saved with the expression keyframed on the **Timeline** (bones + shape keys baked to keyframes), textures packed, opens and plays with no scripts.
- **UV portability proof:** `apply_textures.py` loads a fresh GNM head straight from Google's weights and wraps any set on it; also export textures in the legacy per-region naming.
- Dockerfile for headless Linux rendering; README with exact setup; pinned Blender version.

## Verification
- `pytest`: saccade timing and smoothness, vergence geometry, blink profile, 10-frame θ sequence values.
- **Direction test in the render itself:** for Left/Right/Up/Down/Reset, projected pupil centre must move the right way in the image (the launch rubric's 5/5 pass/fail check), and calibration test that the fixation point sits at 35 cm and the camera at 40 cm.
- Texture validator: tile sizes, no empty texels inside UV islands, seam score below threshold, left and right iris differ.
- Fresh-clone test on a second machine and in Docker: one command reproduces the videos.
- Visual gate each day: contact sheet of all 8 sets and the three videos, compared against the reference videos; weakest item gets the next day's effort.
- Final checklist against every required output in `docs/hackathondetails.md`.

## Schedule (12 → 22 Nov)
| Day | Date | A: rig + motion | B: textures | C: pipeline + docs |
|---|---|---|---|---|
| 0 | 12 | plan approved; Blender 4.5.16 LTS installed from blender.org; docs updated | install Blender | install Blender |
| 1 | 13 | **Spike:** GNM export, Blender head, eyes rotate, eyelid close found | Route A source skins, GNM UV templates exported | `render.py` skeleton renders a grey head to MP4 |
| 2 | 14 | lid/brow controls, armature, cameras | first transferred skin on the head; iris generator v1 | launch-spec API + 10-frame sequence + JSON |
| 3 | 15 | `motion.py` gaze, saccades, vergence + tests | eye shading (cornea, sclera, wetness); Route B trial on Kaggle | direction and calibration tests |
| 4 | 16 | lids follow gaze, blinks, brows | 4 skin sets + detail maps; seam audit tool | Left / Right videos, draft quality |
| 5 | 17 | **Checkpoint: all required outputs exist end to end**, draft quality | 8 sets done | `--all`, `.blend` timeline export |
| 6 | 18 | Generate Motion sequence, lid bulge | lashes, brows, tear line, skin shading polish | Docker, fresh-clone test, `apply_textures.py` |
| 7 | 19 | motion polish against reference videos | weakest textures redone | final-quality renders start |
| 8 | 20 | bug fixes only | final stills | deck (organizer template), demo video |
| 9 | 21 | **freeze**, full regeneration from clean clone | — | repo public, README final, **submit** |
| 10 | 22 | buffer only | | |

**Go/no-go rules.** Day 1: if GNM cannot be driven in Blender, fall back to the MPFB CC0 head (allowed by the launch slides) the same day. Day 5: required outputs before any brownie feature, as the organizers advise. Route B textures ship only if they beat Route A in side-by-side renders.

## Risks
- **Photorealism is 60 points and judged by eye against very high references.** Mitigation: close-up framing, most hours on skin/iris/cornea shading, daily visual gate.
- **No GNM texture exists**, so texture transfer must work. Route A is the floor; verified on day 2.
- **Eyelid control from statistical components** may not close cleanly. Day-1 spike, corrective shape key as backup.
- **8 GB RAM.** One 4K skin tile, 2K eyes, 1024² renders, denoised low-sample Cycles; if too slow, final renders on free Kaggle GPU with Linux Blender.
- **Spec ambiguity** (two specs, left/right meaning, no PoC answers). Both specs built; direction flag and captions.
- **Licences in a public repo.** Only Apache/CC0 inputs and our own generated textures; every asset logged in `docs/ASSETS.md`.
