# Tasks

Status: `todo` / `in progress (owner)` / `done (commit)`. Owners: **A** rig + motion, **B** textures + shading, **C** pipeline, tests, docs, deck, video. Full plan: `docs/PLAN.md`.

## Status for whoever picks this up (16 Nov, 08:30)
Full re-render with the D-024 / D-025 look finished 16 Nov 07:57 and is committed (`528e8ac`): 8 texture sets, 24 stills, wire and clay stills, portability proofs, overviews, launch-spec frames, `.blend`, six videos (Left, Right, Generate Motion front / hero / wire, Generate Motion on set 03), deck and demo. Seam audit, motion evaluation and 16 tests pass. The deck passes the pptx validator. All twelve look tasks from the 15 Nov audit are done; what is left below needs Akshat. Read the newest handoff note first, then `DECISIONS.md` (latest D-025).

## Open, in priority order
Look tasks come from the 15 Nov council audit (`docs/SELF_AUDIT.md`: estimate 66 of 100, photorealism 33 of 60). Batch 1 to 7, test on stills of sets 01, 03, 07, then render all videos once (about 11 h).
- [x] 1. (D-024) Hero view low-key: black background, raking key, weak rim, lower exposure (1 h). **A**
- [x] 2. (D-024) Lashes: upper shorter and uneven, tapered; lower sparse, no bunches or hooked tips (2 to 3 h). **A**
- [x] 3. (D-024) Wet eye white: glossy coat with a visible highlight; more, finer, blurred, less red vessels (2 h). **B**
- [x] 4. (D-024) Iris: cut saturation about a third, break up the cream collarette blocks, soften the limbus (1 to 2 h). **B**
- [x] 5. (D-024) Half-lit pupil with a hard vertical edge in the close view (`01_close`, `07_close`): find the cause, fix. **B**
- [x] 6. (D-024) Concentric ring pattern in the fine relief lines round the socket: remove. **B**
- [x] 7. (D-024) Light sets: calm the pink rings under the eye. **B**
- [x] 8. (D-025) Lid margin as a visible wet shelf between lash roots and eye. **A**
- [x] 9. (D-025) Lower lid moves with down-gaze; eyeball pulls back about 1 mm in a blink. **A**
- [x] 10. (D-025) Slow head sway of a degree or two. **A**
- [x] 11. (D-025) Set 07 streaks: fold relief halved. **B**
- [x] 12. (D-024) Dark sets: whitish sheen on the lit cheek still reads as a grey patch at small size. Test with down hairs off, then with the coat off, to find the cause (1 to 2 h). **B**
- [x] Full re-render after the batch, then `tools/overview.sh`, `tools/make_deck.py`, `tools/make_demo.py` (16 Nov, `528e8ac`). **C**
Third look batch, from the 16 Nov audit (`docs/SELF_AUDIT.md`: estimate 71.5 of 100, photorealism 38 of 60). Akshat said go on 16 Nov. Code done (D-026); full re-render running.
- [x] 13. (D-026) Lid shadow on the eyeball under the upper lid. **B**
- [x] 14. (D-026) Eye white darker, shaded toward the corners; darker on dark sets. **B**
- [x] 15. (D-026) Pupil soft edge; round highlight, off the pupil in the hero view. Pupil depth not done. **B**
- [x] 16. (D-026) Lashes: taper, smooth curve; lower lashes unevenly spaced. **A**
- [x] 17. (D-026) Pale patch at the crown: seam fill now takes the photo's local tone. **B**
- [x] 18. (D-026) Hero view: brow shades the socket, a third or more of the frame in shadow. **A**
- [ ] Full re-render with the D-026 look (`renders/tmp/chain2.sh`, about 9 h), then check frames, commit outputs, run the audit again. **C** in progress
- [ ] 19. Later, if time: set 03 ashy cheek, iris blocks on 05 / 07 / 08, skin pores, set 04 arc, set 07 streaks.
- [ ] Watch `outputs/videos/Generate_Motion_hero.mp4` at speed and decide whether the head sway reads as camera drift (if so: halve it in `truegaze/motion.py`, hero re-render about 2.3 h). **Akshat**
- [ ] Demo video: upload `outputs/demo.mp4` (voice-over optional), put the link on the deck's demo slide. **C**
- [ ] Open the deck once in PowerPoint (only checked in LibreOffice). **C**
- [ ] Watch "Flexpressions" (second reference video; not done, no local copy).
- [ ] **Before making the repo public (not now; Akshat said on 15 Nov to keep it for the time being):** remove the reference video `Eye Piece - Chris Jones (1080p, h264).mp4` from the repo **and from git history**.
- [ ] 21 Nov: regenerate from a clean clone, make repo public, submit the form (https://forms.gle/86xENrtqhx988hBt8). 22 Nov is buffer only.

## How to run
See README "Run it". Blender 4.5 LTS headless; on Akshat's Mac use `/Applications/Blender.app/Contents/MacOS/Blender`. Final frames take 20 to 40 s each on an M3 with 8 GB.

## Done
- [x] Repo and docs for Track 1 (12 Nov)
- [x] Full plan, architecture, asset log, decisions D-003 to D-008 (12 Nov)
- [x] Blender 4.5.16 LTS installed and verified headless with Metal on Akshat's Mac (12 Nov)

---
## Handoff notes (newest on top)
### 16 Nov — third look batch D-026 done, full re-render started
- **Done:** tasks 13 to 18 (see D-026). Files: `truegaze/materials.py`, `truegaze/textures.py`, `truegaze/scene.py`, `tools/make_hair.py`, `assets/hair.npz`, `render.py`. 16 tests and the seam audit pass.
- **Next:** when `renders/tmp/chain2.sh` prints `CHAIN_DONE`: look at stills of all eight sets, contact sheets of the videos, commit outputs, run the audit again.
- **Gotchas:** the frame cache no longer needs emptying after a look change (folder names carry a fingerprint), but old folders in `renders/tmp/final/` pile up: delete by hand. The hero view is darker now; a black-frame guard failure there is the first thing to check. Not checked on stills before the render: sets 02, 04, 05, 06, 08 with the new look.
- **How to run:** `sh renders/tmp/chain2.sh > renders/tmp/chain2.log 2>&1`
### 16 Nov, 09:15 — audit run again on the new renders
- **Done:** `docs/SELF_AUDIT.md` rewritten from the D-025 renders. Estimate 71.5 of 100 (was 66); photorealism 38 of 60 (was 33). No code changed.
- **Found:** no lid shadow on the eyeball, flat bright eye white, flat hard-edged pupil, wiry lashes; a pale patch at the crown on all three portability renders (old fault, missed before); set 03 ashy cheek still visible.
- **Next:** Akshat decides whether to run look tasks 13 to 18 (one more full render).
### 16 Nov, 08:10 — full re-render with the D-025 look finished and committed
- **Done:** all stills, six videos, overviews, launch-spec frames, `.blend`, deck and demo rebuilt with the D-025 look (finished 07:57). 16 tests pass. Contact sheets of the hero, front, `Left`, `Right` and set 03 videos and both overview sheets were looked at: no black eyes, lid shelf and lashes intact on all eight sets.
- **Gotchas:** the first run stopped at 23:27 on a false alarm. Head sway shows more of the hero view's black background in some frames, which `black_frames` read as dark eyes. The guard now leaves out the left fifth of the frame (`render.py`). On the finished set 03 `.mp4` the guard still lists 44 frames (dark skin in shadow sits near its threshold after compression); it passed on the rendered frames, and frames 40, 200 and 255 look right.
- **Not judged:** head sway at speed. In the hero view the eye drifts about a tenth of the frame width. If it reads as camera drift, halve the sway in `truegaze/motion.py` and render the hero video again (about 2.3 h).
- **Next:** upload `outputs/demo.mp4` and put the link in the deck; open the deck in PowerPoint; watch "Flexpressions"; then the going-public steps.
### 15 Nov, 18:30 — second look batch D-025 done, full re-render started
- **Done:** audit tasks 8 to 11 (see D-025). 16 tests pass, `tools/evaluate_motion.py` passes. `assets/hair.npz` rebuilt (lash roots moved, new `margin_uv`).
- **Running:** `renders/tmp/chain2.sh` (everything, about 8.5 h; log `renders/tmp/chain2.log`). Until it prints `CHAIN_DONE`, `textures/` (only 01, 03, 07 regenerated so far), `outputs/`, `uv_maps/`, `docs/*.jpg`, the deck and the demo show the D-024 look.
- **Next:** check all videos, commit textures and outputs together.
- **Gotchas:** `renders/tmp/final/` was emptied before the run. Head sway moves the eye a few millimetres in the hero view; that is intended.
### 15 Nov, 16:30 — full re-render with the D-024 look finished and committed
- **Done:** `renders/tmp/chain2.sh` printed `CHAIN_DONE` at 16:22 (about 8.5 h). All stills, six videos, overviews, launch-spec frames, `.blend`, deck and demo rebuilt. `black_frames` is empty for all six videos; contact sheets of five videos and the three overview images were looked at; 14 tests pass.
- **Seen in the new renders:** pupil fault gone on all eight sets. Still open: a faint arc of relief lines above the outer corner on light sets in the close view; whitish cheek sheen on dark sets in the front view (weaker); set 07 streaks; hero view still brighter than the reference.
- **Next:** upload `outputs/demo.mp4` and put the link in the deck; open the deck in PowerPoint; tasks 8 to 11 only if another 8.5 h render is acceptable.
### 15 Nov, 08:00 — look batch D-024 done, full re-render started
- **Done:** audit tasks 1 to 7 and 12 (see D-024). Tested on stills of sets 01, 03, 07 only.
- **Running:** `renders/tmp/chain2.sh` again (everything, about 11 h; log `renders/tmp/chain2.log`). Until it prints `CHAIN_DONE`, `outputs/`, `uv_maps/`, `docs/*.jpg`, the deck and the demo still show the old look.
- **Next:** check all videos, commit outputs, rebuild deck and demo. Then tasks 8 to 11 only if time allows another render.
- **Gotchas:** `renders/tmp/final/` was emptied before the run: old frames there would have been reused. Keep the Mac awake with the lid open.
### 15 Nov, 06:15 — dark-skin patch fixed, names in the deck, council audit, new task list
- **Done:** D-023 (painted grey eye bags and a matt island removed on sets 03, 06, 08; a whitish cheek sheen remains, task 12). Member names and registration numbers in `tools/make_deck.py`. `docs/SELF_AUDIT.md` rewritten as an eight-judge audit against the brief and the reference video; the open list above is built from it.
- **Running:** `renders/tmp/chain3.sh` (stills of 03, 06, 08, `portability_03`, overviews, set 03 video; log `renders/tmp/chain3.log`).
- **Next:** tasks 1 to 7 as one batch, then one full re-render.
- **Gotchas:** only the three dark sets changed; set 01 videos were not touched and are still valid.
### 15 Nov, 06:00 — repo clean-up and docs pass
- **Done:** removed the day-1 spike script and three unused images, `docs/RENDER_PLAN.md` and `docs/DECK_OUTLINE.md` (both overtaken by `reproduce.sh`, `tools/make_deck.py`, `tools/make_demo.py`), one unused import. `reproduce.sh` now makes all three portability proofs that are committed. README has a submission-package table and a repository layout. `docs/ARCHITECTURE.md` parts table, `CLAUDE.md` ownership line and the reference-video note corrected.
- **Not moved:** no folder was renamed; every script and doc points at the current paths and there is no time to re-verify a full render after a move.
- **Next:** member names in the deck; demo upload and link; purge the reference video when Akshat says; go public; submit by 21 Nov.
- **Run:** `./reproduce.sh` as before.
### 15 Nov, 05:10 — textures committed; Docker built and tested
- **Done:** `textures/` is in git (56 files, 103 MB; no longer ignored). Docker image built (2.91 GB, `--platform=linux/amd64` because Blender has no Linux arm64 build).
- **Docker test on the M3 (emulated, 4 GB Docker memory):** asset fitting, textures, seam audit (PASS), 14 tests, three Cycles clay stills (correct image, about 2 min each) all ran. Draft video `Left`: 1.8 min per frame in software OpenGL, then killed (exit 137, out of memory) at frame 12. So `./reproduce.sh draft` does not finish in the container on this Mac.
- **Next:** demo upload and link, member names in the deck, purge the reference video, go public, submit.
- **Gotchas:** EGL warnings in the container log are harmless (software OpenGL). Test output is in `renders/tmp/docker_out/` (ignored).
### 15 Nov, 04:00 — full re-render done and committed
- **Done:** `renders/tmp/chain2.sh` finished (about 11 h from the 16:59 restart). `outputs/`, `uv_maps/`, `docs/*.jpg` and the deck now all show the D-022 look. New: `outputs/videos/Generate_Motion_set03.mp4` (dark skin, 12 s). `black_frames` on all six videos: none flagged, and no frame needed a second render. `tools/make_demo.py` cut `outputs/demo.mp4` (85 s, silent, captioned; mp4 outside `outputs/videos/` is git-ignored, so it is local only).
- **Next:** upload the demo (add voice-over if wanted) and put its link in the deck; member names in the deck; build the Dockerfile once; commit `textures/`; purge the reference video; go public; submit.
- **Gotchas:** the Mac must stay awake with the lid open for long renders (`caffeinate -i` does not stop lid-close sleep). Set 03 / 08 under-eye patch is weaker than before D-021 but still visible.
- **Run:** `python3 tools/make_demo.py`, `python3 tools/make_deck.py`.
### 14 Nov, 17:30 — black-eye guard; a second real case found; Dockerfile
- **Found:** the committed `outputs/videos/Right.mp4` has solid black eyes in its last 3 frames (268 to 270). The 13 Nov check missed it: it sampled the Generate Motion videos only. So the fault was not only "from frame 185 on"; it can hit any late frame of a long run. Right is in the re-render queue anyway.
- **Guard added:** `render.py` sets `use_persistent_data = False` explicitly, and `black_frames()` measures each frame's share of near-black pixels with ffmpeg before joining; frames that jump 2 points above the clip's median are deleted and rendered again, and the run fails if they are still dark. Tested: flags exactly frames 268 to 270 of the old Right.mp4 and frames 186 on of a video with the eyes blacked out by hand; flags nothing in the three good videos.
- Limit of the guard: it sees eyes going black, not other faults. Dark-skin clips have a higher baseline of dark pixels; the rule is relative to the clip, but it has not been tried on a real dark-skin failure.
- The render chain was restarted at 16:59 (the Mac slept with the lid closed around 15:00; `caffeinate -i` does not stop lid-close sleep). Keep the lid open and the charger in.
- `Dockerfile` written (Blender 4.5.16 Linux, CPU rendering). **Not built or run yet**: building during the render would starve it of memory. Build and run `draft` once the render is done.
### 14 Nov, morning — eight look and motion changes (D-022); full re-render running
- Done: tasks 1 to 8 of `docs/IMPROVEMENTS.md`: lid shadow on the eyeball, greyer eye whites, concave tear film, window catchlight in the hero view, softer lower-lash roots, more skin shine contrast, brow lowers with down-gaze and blinks, set 01 iris toned down. Tests (14) and motion evaluation pass. Checked on test stills of sets 01 and 03.
- **Running:** `renders/tmp/chain2.sh` (log `renders/tmp/chain2.log`): all textures, all stills, proofs, overviews, launch-spec sequence, `.blend`, wire video, then final videos in this order: Generate Motion hero, Generate Motion, Left, Right, Generate Motion on set 03 (new). About 1,620 final frames at 20 to 40 s each: 12 to 15 hours. It prints `STILLS_DONE`, `SMALL_DONE`, `CHAIN_DONE`.
- **Until it finishes, `outputs/` in git is the old look.** Do not commit half the outputs: wait for `CHAIN_DONE`, check each video over its whole length (the 13 Nov black-eye bug showed only after frame 185), then commit `outputs/` and `docs/*.jpg` together and re-run `python3 tools/make_deck.py`.
- If the machine sleeps or the run stops: start `./renders/tmp/chain2.sh` again; finished frames are kept. The early steps repeat (about 40 minutes).
- Gotcha: the tear film must stay a reflect-only material. As glass it drew a black line round the eye.
- Next after the render: deck names, demo video, Dockerfile, commit `textures/`, purge the reference video, go public.
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
