# Tasks

Status: `todo` / `in progress (owner)` / `done (commit)`. Owners: **A** rig + motion, **B** textures + shading, **C** pipeline, tests, docs, deck, video. Full plan: `docs/PLAN.md`.

## Next up (13 Nov — Day 1 spike)
- [ ] A: `tools/export_gnm.py`; GNM head in Blender; eyes rotate about their centres; find a clean eyelid close
- [ ] B: export GNM UV templates per tile; collect CC0 source skins, log in `docs/ASSETS.md`
- [ ] C: `render.py` skeleton renders a grey head to MP4 headless
- [ ] All: install Blender 4.5.16 LTS (done on Akshat's Mac)
- [ ] All: watch the two reference videos, note traits to imitate

## 14–16 Nov
- [ ] A: lid/brow controls, armature, 40 cm camera + close-up camera
- [ ] A: `motion.py` gaze, saccades, vergence, lids follow gaze, blinks, brows, with tests
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
### 12 Nov — plan
- Done: plan in `docs/PLAN.md`; GNM identified as Google's Apache-2.0 head model; Blender installed at `/Applications/Blender.app` (Python 3.11, Metal GPU found).
- Next: Day 1 spike above. Go/no-go on GNM by end of 13 Nov.
- Gotchas: GNM has no skin texture. On Akshat's Mac use `/opt/homebrew/bin/git` and `/opt/anaconda3/bin/python3` until `sudo xcodebuild -license accept` is run. 8 GB RAM: keep one 4K tile, 1024² renders.
- Run Blender headless: `/Applications/Blender.app/Contents/MacOS/Blender --background --python <script.py>`
