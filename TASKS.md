# Tasks

Status: `todo` / `in progress (owner)` / `done (commit)`. Owners: **A** rig + motion, **B** textures + shading, **C** pipeline, tests, docs, deck, video. Full plan: `docs/PLAN.md`.

## Next up (13 Nov — Day 1 spike)
- [x] A: GNM head in Blender; eyes rotate about their centres; clean eyelid close found (12 Nov, **GO on GNM**)
- [ ] B: export GNM UV templates per tile; collect CC0 source skins, log in `docs/ASSETS.md`
- [x] `render.py` renders Left / Right / Generate Motion to MP4 headless (draft quality, 12 Nov)
- [ ] All: install Blender 4.5.16 LTS (done on Akshat's Mac)
- [ ] All: watch the two reference videos, note traits to imitate

## 14–16 Nov
- [x] A: lid follow + brow raise/lower controls, armature, 40 cm camera (12 Nov)
- [x] A: `motion.py` gaze, saccades, vergence, lids follow gaze, blinks, brows, pupil, with 10 tests (12 Nov)
- [ ] B: first transferred skin on the head; iris generator; cornea/sclera/wetness shading
- [ ] B: Route B trial on Kaggle; 4 skin sets with normal/roughness; seam audit tool
- [ ] C: `eyes.move/reset/render`, 10-frame sequence, per-frame JSON
- [ ] C: direction and calibration tests; Left / Right draft videos

## 17 Nov — checkpoint
- [ ] Every required output exists end to end at draft quality (D-008); 8 texture sets; `render.py --all`; `.blend` with timeline animation

## 18–20 Nov
- [ ] A: Generate Motion sequence; lid bulge; motion polish against references
- [ ] B: lashes, brows, tear line; redo weakest textures; final stills
- [ ] C: Dockerfile, fresh-clone test, `apply_textures.py`, final renders, deck, demo video

## 21 Nov — freeze and submit
- [ ] Regenerate everything from a clean clone; README final; repo public; submit form. 22 Nov is buffer only.

## Done
- [x] Repo and docs for Track 1 (12 Nov)
- [x] Full plan, architecture, asset log, decisions D-003 to D-008 (12 Nov)
- [x] Blender 4.5.16 LTS installed and verified headless with Metal on Akshat's Mac (12 Nov)

---
## Handoff notes (newest on top)
### 13 Nov — reference video studied
- Done: "Eye Piece" (Chris Jones) analysed; notes and gap list in `docs/reference_eye_piece.md`. Biggest gaps vs reference: lighting, cornea refraction, wet lid margin, lashes/brows, skin micro-detail.
- Gotchas: the reference MP4 sits in the repo root but is git-ignored (`*.mp4`, except `outputs/videos/`). Never commit it.
- Next: textures (skin, iris, sclera) plus the dark-studio hero light rig.
### 12 Nov — motion engine and first videos
- Done: brow raise/lower controls; `truegaze/motion.py` (saccade main sequence + overshoot, vergence, lid-follow, blinks incl. gaze-evoked, drift + micro-saccades, pupil hippus, Bell's dip); `tests/test_motion.py` (10 pass); `render.py` with the 3 inputs, caption stamp and MP4 output; pupil shape key from GNM's iris component. Draft Left video checked: eyes go to viewer's left, blinks look right. Frames in `docs/draft_left_day1.png`.
- Cornea is now a Fresnel glass shell without refraction so it works in EEVEE; B should add refraction for Cycles in `materials.py`.
- Next: textures (biggest score item), lashes, Right and Generate Motion check, `--all`, `.blend` export, launch-spec API.
- Gotchas: draft EEVEE takes about 7 min for 9 s at 960×540 on the M3; final Cycles will be much slower, so plan Kaggle/Colab GPU or overnight renders.
- Run: `/Applications/Blender.app/Contents/MacOS/Blender --background --python render.py -- --input Left` (add `--quality final`, `--seed N`, `--frame subject`); tests: `python3 -m pytest tests -q`
### 12 Nov — Day-1 spike passed
- Done: `truegaze/gnm.py` (NumPy reader, auto-download + checksum), `tools/fit_controls.py` (named eyelid controls as GNM expression coefficients, saved to `assets/controls.npz`), `truegaze/scene.py` (mesh, UDIM UVs, shape keys, 4-bone rig, camera at 40 cm, lights), `tools/spike.py`. Renders show eyes turning left/right/up/down and a full blink with no eyeball poking through.
- Facts found: GNM v3.0 pose correctives are all zero, so the model is plain skinning and a Blender armature reproduces it exactly. Lid margin = vertices in both `eye_sockets` and `skin_exterior` (80 per eye). Blink fit: max coefficient 2.9 (normal range ±3), lid gap 0.12 mm.
- Next: lids must follow gaze (looking up hides the iris under the lid now); brow controls; `motion.py`; textures. Stand-in flat colours look washed out, expected until textures land.
- Gotchas: about 14 s per 1024×512 frame at 48 samples on the M3, so a 10 s video at 30 fps is over an hour: use draft settings while iterating. `assets/cache/` (53 MB weights) is not committed.
- Run: `python3 tools/fit_controls.py` then `/Applications/Blender.app/Contents/MacOS/Blender --background --python tools/spike.py` (images in `renders/tmp/`)
### 12 Nov — plan
- Done: plan in `docs/PLAN.md`; GNM identified as Google's Apache-2.0 head model; Blender installed at `/Applications/Blender.app` (Python 3.11, Metal GPU found).
- Next: Day 1 spike above. Go/no-go on GNM by end of 13 Nov.
- Gotchas: GNM has no skin texture. On Akshat's Mac use `/opt/homebrew/bin/git` and `/opt/anaconda3/bin/python3` until `sudo xcodebuild -license accept` is run. 8 GB RAM: keep one 4K tile, 1024² renders.
- Run Blender headless: `/Applications/Blender.app/Contents/MacOS/Blender --background --python <script.py>`
