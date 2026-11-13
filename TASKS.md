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
- [x] B: first transferred skin on the head; iris generator; cornea/sclera/wetness shading (13 Nov; skin is generated, not transferred yet)
- [ ] B: Route B trial on Kaggle; 4 skin sets with normal/roughness; seam audit tool
- [x] C: `eyes.move/reset/render`, 10-frame sequence, per-frame JSON
- [x] C: direction and calibration tests; Left / Right draft videos

## 17 Nov — checkpoint
- [ ] Every required output exists end to end at draft quality (D-008); 8 texture sets; `render.py --all`; `.blend` with timeline animation

## 18–20 Nov
- [ ] A: Generate Motion sequence; lid bulge; motion polish against references
- [ ] B: lashes, brows, tear line; redo weakest textures; final stills
- [ ] C: Dockerfile, fresh-clone test, `apply_textures.py`, final renders, deck, demo video

## 21 Nov — freeze and submit
- [ ] **Before making the repo public:** the reference video `Eye Piece - Chris Jones (1080p, h264).mp4` (third-party, committed 13 Nov at Akshat's request while the repo is private) must be removed **from history too**, not only deleted: `git filter-repo --path "Eye Piece - Chris Jones (1080p, h264).mp4" --invert-paths` then force-push, or publish from a fresh repo without it. A plain delete leaves it downloadable from old commits.
- [ ] Regenerate everything from a clean clone; README final; repo public; submit form. 22 Nov is buffer only.

## Done
- [x] Repo and docs for Track 1 (12 Nov)
- [x] Full plan, architecture, asset log, decisions D-003 to D-008 (12 Nov)
- [x] Blender 4.5.16 LTS installed and verified headless with Metal on Akshat's Mac (12 Nov)

---
## Handoff notes (newest on top)
### 14 Nov, 03:08 — submission deck built
- Done: `tools/make_deck.py` fills the organizers' template (`docs/organizer/Submission_Final_forGithub.pptx`) and writes `VITVellore_ZeroDrift.pptx`, 14 slides in the template's order plus a results-and-limits slide. Every slide rendered and looked at; file validates.
- Every number on the slides was re-printed by its script on 14 Nov. Two stale README numbers found and fixed: skin drag is 2.7 mm (was 1.4), final frames take 20 to 40 s (was 10 s).
- **To do before submitting:** put the two other members' names in `MEMBERS` at the top of `tools/make_deck.py` and re-run; add the demo video link to the demo slide once the video exists.
- Checked only in LibreOffice, not in PowerPoint.
- Next: demo video (3 minutes or less), commit `textures/`, Dockerfile, purge the reference video, go public.
### 14 Nov, 03:01 — skin fixes for dark sets and set 07 (D-021)
- Done: grey under-eye patch on sets 03, 06, 08 and orange streaks on set 07 fixed in `truegaze/textures.py`; facial down darkens with the skin (`materials.fuzz` reads `info.json`). Stills for 03, 06, 07, 08 and the portability proofs for 03 and 07 re-rendered, overviews rebuilt, seam audit and 14 tests pass.
- Sets 01, 02, 04, 05 are unchanged by construction, so the videos (set 01) still match.
- Gotcha: `info.json` of 01, 02, 04, 05, 07 has no `fuzz` key until those sets are regenerated; the shader falls back to the same pale colour.
- Next: commit `textures/`, deck, demo video.
### 14 Nov, 02:50 — audits re-run, overview images rebuilt
- Seam audit passes (front step ≤ 6 of 255 on all 8 sets), motion evaluation passes (every sourced row in range), 14 tests pass.
- New `tools/overview.sh` joins the stills into `docs/texture_sets.jpg`, `docs/hero_sets.jpg`, `docs/breakdown.jpg`; added as the last line of `reproduce.sh`.
- Hair count corrected in the deck outline (7,458, was 9,900) and self audit.
- Seen in the stills, not fixed: sets 03 and 08 (dark skin) show a grey patch under the eye on the lit side in the front view; set 07 (old skin) looks blotchy orange in the hero view.
- Next: decide on those two, commit `textures/`, deck, demo video.
### 13 Nov night — final renders; black-eye bug found and fixed
- Final Left and Right (9 s each), stills for all 8 sets, wire/clay stills, portability proofs, launch-spec sequence, `.blend` and wireframe video are done and committed.
- Bug: in both final Generate Motion videos the eyes rendered solid black from about frame 185 on. The same frame rendered alone was correct, so the cause was Cycles' persistent data going stale over a long sequential run. Persistent data is now off in `render.py`; frames 175+ of both Generate Motion videos were deleted and re-rendered. Checked 14 Nov 02:25: both videos 360 frames, one frame every 0.5 s viewed, eyes correct to the end; crow's-feet wrinkles show on blinks in the hero view.
- Gotcha: always look at the end of a long render, not only the start.
### 13 Nov — light pooling, plica, expression wrinkles; render chain started (D-020)
- Done: iris light pooling (shader), plica ridge, `wrinkle.1001` map with drivers (forehead lines on brow raise, crow's feet on lid closure), Burley eye scattering, Voronoi micro relief. All 8 sets regenerated (`textures/` is now 104 MB); seam audit, 14 tests and motion evaluation pass.
- Running: the chain in `docs/RENDER_PLAN.md` (about 8.7 h, resumable; log `renders/tmp/chain.log`).
- Checked only in stills so far: wrinkles, pooling, plica, new blink, stronger drag. Watch them in motion when the videos finish.
### 13 Nov — third critique pass, from the reference author's forum notes (D-019)
- Done: `blink_mid` control (lid follows the eyeball through a blink), lid drag 30%, caruncle, iris rework with relief, soft blue-grey limbus, wet pink lid edge, shinier lids, uneven sclera surface, hero catchlight. All 8 sets regenerated; seam audit, 14 tests and motion evaluation pass.
- Running: full chain again (stills, wire/clay, sequence, `.blend`, wire video, hero final, three finals; `renders/tmp/chain.log`, about 9 h, resumable).
- Not done: Flexpressions video unwatched; plica; caustics.
### 13 Nov — motion evaluation, docs refresh
- Done: `tools/evaluate_motion.py` (all sourced checks pass after four fixes, D-018); motion blur in final quality; `reproduce.sh` + `requirements.txt`; fresh-clone test passed; README, PLAN status, ARCHITECTURE, SELF_AUDIT refreshed; overview images `docs/hero_sets.jpg`, `docs/texture_sets.jpg`, `docs/breakdown.jpg`. Reference video committed at Akshat's request (see the 21 Nov checklist: purge from history before going public).
- Running: `.blend`, wireframe video, final videos with motion blur, hero final video (`renders/tmp/chain.log`, about 8 h, resumable; about 22 s per frame).
- Gotcha: the draft videos in `outputs/videos/` still show the old motion timing until the finals replace them.
### 13 Nov — critique pass against the reference (D-017)
- Done: hero view, skin micro-glints and oil coat, under-eye fine lines, richer sclera, wetter lid edge, iris freckles, facial down, denser darker lashes. Table of gaps and what is still short: `docs/reference_eye_piece.md`.
- Running: full chain incl. final-quality videos and a hero-view Generate Motion (log `renders/tmp/chain.log`, about 5 h). Frames resume if stopped.
- Not done: no fresh macro-photo research (worked from anatomy knowledge); "Flexpressions" reference still unwatched.
### 13 Nov — socket depth, skin drag, veins, wireframe (D-016)
- Done: `tools/fit_bulge.py` now also fits `socket_*` (always on) and `drag_*` keys; `motion.soft_tissue()` replaces `bulge()`; hair follows all of them; skin texture has periorbital veins and an upper-lid crease; `--style clay|wire` making-of renders. Comparison image: `docs/socket_veins_wireframe.jpg`. 14 tests and the seam audit pass.
- Build order is now: `fit_controls.py` → `fit_bulge.py` → `make_hair.py` → `transfer_skin.py` (once) → `python3 -m truegaze.textures`.
- Running: stills for all sets, wire and clay stills, launch-spec sequence, `.blend`, wireframe Generate Motion video, then final-quality videos (log `renders/tmp/chain.log`, about 3.5 h).
### 13 Nov — final-quality video renders
- `render.py --quality final` now writes single PNG frames to `renders/tmp/final/<input>_<texture>_<seed>_<frame>/` and skips frames that exist, so a stopped run resumes where it left off; ffmpeg (must be on the PATH) joins them into `outputs/videos/`. Cycles 48 samples with adaptive sampling and persistent data: about 10 s per 1280×720 frame on the M3, so about 2.5 h for all three videos.
- Run: `caffeinate -i /Applications/Blender.app/Contents/MacOS/Blender --background --python render.py -- --all --quality final` (log in `renders/tmp/final.log`). To redo a video from scratch delete its frame folder first.
- Gotcha: frames from an older look are reused if the folder is left in place after changing textures, lighting or motion.
### 13 Nov — photo-based skin
- Done: `tools/transfer_skin.py` fits GNM to MakeHuman's head (median 0.5 mm) and writes `assets/skin_transfer.npz`; `truegaze/textures.py` pulls MakeHuman's CC0 skins into GNM's layout for all 8 sets (D-015). Licence verified at the source and logged in `docs/ASSETS.md`. Seam audit passes (front ≤ 6/255) after fading the photo out on seams. Draft videos reviewed: Left, Right, Generate Motion all move the right way, blinks and lashes fine.
- Tweaks: fill light 0.5 → 1.2 W (the shadow-side eye was too dark in videos); video lens 130 → 118 so brows are not cut off; inner-lip pink patch removed.
- Gotchas: MakeHuman files download on first texture run (30 MB, plain HTTP, checked by SHA-256). The seam audit must be re-run after any texture change: it caught a regression from the photo skin at the lip line.
- Outputs rendered with photo skin and committed in `outputs/`: 3 draft videos (9 s, 9 s, 12 s), 16 stills + 3 portability proofs, `scene.blend` (17 MB, textures packed), launch-spec sequence with `metadata.json` and contact sheet (direction check 5/5). Overview: `docs/texture_sets.jpg`.
- Next: final-quality videos on a faster GPU, Dockerfile and fresh-clone test, deck and demo video.
### 13 Nov — lashes, brows, tear line, launch-spec API, .blend, audits
- Done: `tools/make_hair.py` (about 2,800 strands + tear line in `assets/hair.npz`, shape keys per control, driven from the head's keys); per-set hair colour in `textures/<set>/info.json`; skin texture now shaded under brows and along the lash line; iris has wavy fibres, collarette, furrows, pupil frill. `wrapper/eyes.py` (move/reset/render, 10-frame sequence, `metadata.json`, direction check 5/5). `render.py --all` and `--blend`. `apply_textures.py` (stock or random-identity GNM head). `tools/seam_audit.py` (+ `uv_maps/` sheets). README rewritten. 13 tests pass.
- Facts found: GNM lid margin ring is the wet inner edge; lash roots must sit 0.9–1.6 mm further out. Only front-of-face UV seams are along the inner lip line. The pale cheek streak was plain specular sheen from the softbox (gone with specular off); skin is now rougher (0.62) with lower specular (0.3).
- Lid bulge added (`tools/fit_bulge.py`, D-014): the cornea was cutting up to 1.5 mm into the lids at large gaze angles.
- Order matters: `tools/fit_controls.py` → `tools/fit_bulge.py` and `tools/make_hair.py` → `python3 -m truegaze.textures` (textures read brow/lash positions from `assets/hair.npz`).
- Gotchas: never edit a running chain script; on 8 GB RAM run one Blender at a time. EEVEE draft shows lashes and blink fine.
- Next: photo-based skin albedo (biggest remaining realism gap), lid bulge over the cornea, final-quality videos on a faster GPU, Dockerfile + fresh-clone test, deck and demo video, commit `textures/` at the 17 Nov checkpoint.
### 13 Nov — first textures and shading
- Done: `truegaze/textures.py` makes 8 texture sets in GNM's UV layout (4K skin colour/roughness/height in tile 1001; 2K eye colour for 1002 left and 1004 right, each eye its own iris and vein pattern). `truegaze/materials.py` assigns one material per UDIM tile; cornea refracts in Cycles. Dark-studio lighting (softbox key + weak fill). Pupil now rests at about 3.8 mm (`PUPIL_REST`; GNM's template pupil is dilated). `tools/stills.py` renders a front and a close still per set. `render.py --texture 01..08`. 12 tests pass.
- Facts found: eye tiles are polar (eye axis at centre; pupil edge r=0.050, iris edge r=0.185 in UV, non-linear vs real radius). Skin tile: eyes are only 0.14 UV apart, so 4K gives about 0.11 mm per texel at the eyes.
- Honest state: eyes read fairly well; skin is a clean procedural baseline and still looks CG. Biggest missing realism: lashes, brows, wet lid margin, photo-based skin albedo (Route A/B in the plan).
- Gotchas: `textures/` is git-ignored until the 17 Nov checkpoint (69 MB, still changing). After cloning run `python3 -m truegaze.textures` (about 3 min) before any render.
- Next: lashes and brows (hair curves), wet lid margin, then photo-based skin; Right and Generate Motion draft videos; `.blend` export.
- Run: `python3 -m truegaze.textures` then `/Applications/Blender.app/Contents/MacOS/Blender --background --python tools/stills.py -- 01 --samples 48`
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
