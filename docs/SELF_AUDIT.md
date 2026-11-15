# Council audit against the brief and the reference (15 Nov)

Replaces the 13 Nov self-audit. Written to find faults, not to defend the build.

**What was looked at:** the brief and rubric (`docs/hackathondetails.md`); the reference video "Eye Piece" (frames at 4.5, 9, 14.5, 18 s and its blink at 5.6 to 6.1 s); our stills at full size (`01_front`, `01_close`, `01_hero`, `07_close`, sets 03 and 08 front, the three overview sheets); contact sheets of all six videos and a frame-by-frame strip of one blink in the hero video; `uv_maps/01.jpg`; the numbers printed by `tools/evaluate_motion.py`, `tools/seam_audit.py` and `outputs/launch_spec/metadata.json`.

**Since this audit:** items 1 to 7 and 12 were worked on in D-024 and items 8 to 11 in D-025 (`DECISIONS.md` says what each achieved and what is still visible). The scores below are from before those changes and were not re-estimated.

**Limits of this audit:** one reviewer playing eight roles, not eight people. Videos were judged from sampled frames, not watched at speed. The second reference ("Flexpressions") was not watched. Scores are estimates of how a strict judge would mark, not a prediction of the result.

## Verdict

| Rubric line | Max | Estimate | Why |
|---|---|---|---|
| Texture photorealism | 60 | **33** | Reads as good CG, not as a photograph. Eye surface, lashes and lighting give it away within a second. |
| Kinematic accuracy | 20 | **16** | Timing is measured and in range. The face around the eyes is too still. |
| Code and UV portability | 20 | **17** | One script rebuilds everything; textures wrap on stock and random GNM heads. Docker does not finish videos. |
| **Total** | 100 | **66** | |

All five required outputs exist. The risk is not a missing deliverable; it is that 60 of 100 points are for a look we only half reach.

## The eight judges

### 1. Blender and rendering lead — 5/10
- **Lighting is the largest single gap.** The reference is low-key: one hard raking light, black background, most of the frame in shadow. Our "hero" view is high-key and evenly lit, with skin filling the background. Flat light exposes every weakness in the materials; shadow would hide half of them.
- Front view has no visible shadow shape at all: no brow shadow, no nose shadow edge.
- The window highlight on the cornea is sharp and large and sits over the pupil. It reads as a pasted reflection.
- Motion blur and depth of field work and help.
- 48 samples with denoising smears pore detail in the videos compared with the stills.

### 2. Colour expert — 5/10
- **Iris is too saturated.** A real blue iris is grey-blue; ours is poster blue. Green (set 04) and amber (sets 05, 08) are close to neon.
- The cream collarette is drawn as bright radial blocks. It is the first thing that reads as painted.
- Limbal ring is a hard dark line. A real limbus is a soft gradient about 1 mm wide.
- Skin on light sets is one even peach with pink rings under the eye that read as make-up or rash.
- Eye white is an even neutral grey: no yellowing toward the corners, no blue cast near the iris.
- Dark sets: the painted grey eye bags are gone (15 Nov, D-023), but a broad whitish sheen on the lit cheek remains (sets 03, 06, 08) and still reads as a grey patch at thumbnail size. Only half fixed.

### 3. Doctor (eye anatomy) — 4/10
- **No lid margin.** A real lid edge is a flat wet shelf about 2 mm thick; lashes leave its outer edge and the inner edge touches the eye. Ours is a knife edge: lashes grow straight out of skin next to the eyeball.
- **Lashes are wrong in three ways:** upper lashes are too long and too even; lower lashes come in comb-like bunches with hooked tips; neither tapers.
- Eye white looks dry and matt. A real eye is wet: it shows a bright moving highlight and a visible tear line.
- Vessels are few, all one width, too red and too sharp. Real ones branch, vary in width and sit blurred under the surface.
- The inner-corner tissue is a pink bead, not a fold.
- **Pupil fault in the close view:** the pupil shows a hard vertical edge with one half lighter (`01_close`, `07_close`). Cause not yet found.

### 4. Character designer — 6/10
- Eye shape, socket depth and brows are believable in the front view.
- Brow hairs stand up like grass at the top edge of the hero frame.
- Fine relief lines round the socket form visible concentric rings, like a fingerprint (`01_close` and `07_close`, lower right).
- Set 07 (old skin): forehead wrinkles still read as horizontal streaks at close range.
- Eight sets vary skin and iris colour but share one face and one lash style, so the sheet reads as one person recoloured.

### 5. Animator — 7/10
- Blink is good: fast close, slower open, crow's feet appear, lashes follow, blur looks right.
- Lids follow gaze. Skin near the lid slides with the eye.
- **Lower lid hardly moves** in a blink or on down-gaze.
- **The head is locked.** No sway, no breathing. Eyes move in a statue.
- Brows are close to static outside blinks.
- Upper lid does not fold over itself when open; the crease is shading only.

### 6. Biomechanics and eye-movement specialist — 8/10
- Saccade durations for 5, 10, 20, 30 degrees: 32.5, 44.5, 72, 99 ms, all inside published ranges.
- Blink: closing 86.5 ms, whole blink 337.5 ms, rate 16.7 per minute. In range.
- Vergence 5.1 degrees per eye at 35 cm; fixation wander 0.7 degrees. In range.
- Peak-to-mean velocity for the 5 degree saccade sits on the lower limit (1.5).
- Missing: the eyeball does not pull back in a blink (about 1 mm in life); no upward roll under the closed lid; no torsion; pupil does not react to gaze distance or light.

### 7. Pipeline and portability engineer — 8.5/10
- `./reproduce.sh` rebuilds every asset and output; downloads are checksum-pinned; 14 tests pass.
- Textures are named by GNM tile and wrap onto stock and random-identity GNM heads.
- Seam step on the front of the face is at most 6 of 255 on every set.
- Every final video is checked frame by frame for the black-eye fault.
- Docker image builds but videos run out of memory in it on the M3; not tried on Linux.
- Lashes, brows and tear line are generated mesh, not texture. On a stock head the textures alone give no lashes.
- FLAME is not supported (the brief allows GNM or FLAME, so not required).

### 8. Hackathon judge (brief compliance) — 9/10
- 8 texture sets with distinct left and right iris: met.
- Script with `Left`, `Right`, `Generate Motion`: met. Videos 9, 9 and 12 s: met.
- 24 stills across 8 sets: met. `.blend` with a Timeline animation of lids, iris and brows: met.
- Launch-spec API and direction check 5 of 5: met.
- Open: demo video not uploaded, repo not public, deck not opened in PowerPoint.

## What to do, in order of points per hour

Any change to set 01 or to shared shading means rendering the five set 01 videos again (about 11 hours). So: batch items 1 to 8, test on stills of sets 01, 03 and 07, then render once.

| # | Change | Judge | Cost | Renders needed |
|---|---|---|---|---|
| 1 | Hero view low-key: black background, raking key, weak rim, lower exposure | 1 | 1 h | hero stills, hero video |
| 2 | Lashes: upper shorter and uneven, taper both, lower sparse with no bunches or hooks | 3 | 2 to 3 h | all |
| 3 | Wet eye white: glossy coat with a visible highlight; more, finer, blurred, less red vessels | 3 | 2 h | all |
| 4 | Iris: cut saturation about a third, break up the collarette blocks, soften the limbus | 2 | 1 to 2 h | all |
| 5 | Find and fix the half-lit pupil in the close view | 3 | 1 h to find | close stills at least |
| 6 | Remove the concentric ring pattern in the fine relief lines | 4 | 1 h | all |
| 7 | Light sets: calm the pink rings under the eye | 2 | 30 min | all |
| 8 | Lid margin: a visible wet shelf between lash roots and eye | 3 | 3 to 5 h, may not work on GNM's mesh | all |
| 9 | Lower lid moves with blink and down-gaze; eyeball pulls back about 1 mm in a blink | 5, 6 | 2 h | videos |
| 10 | Slow head sway of a degree or two | 5 | 2 h | videos |
| 11 | Set 07 forehead streaks | 4 | 1 h | set 07 stills |
| 12 | Dark sets: whitish sheen on the lit cheek (pale down hairs or the oil coat; cause not confirmed) | 2 | 1 to 2 h | dark-set stills, set 03 video |

Items 1 to 7 are the realistic batch. Item 8 is the highest-value anatomy fix and the least certain.

## Not in doubt
The brief's required outputs, the motion numbers, the seam numbers and the rebuild script are solid and backed by scripts. The gap is the look.
