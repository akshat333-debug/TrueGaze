# Council audit against the brief and the reference (16 Nov)

Replaces the 15 Nov audit (in git history at `528e8ac`). Run again on the renders made after the D-024 and D-025 look batches. Written to find faults, not to defend the build.

**What was looked at:** the brief and rubric (`docs/hackathondetails.md`); the reference video "Eye Piece" (frames at 4.5, 9, 14.5, 18 s); our stills at full size (`01_front`, `01_close`, `01_hero`); stills at three-quarter size (`03_close`, `03_front`, `07_close`, `07_front`, `04_close`, `08_close`, `06_hero`, `05_front`); both overview sheets; the three portability renders; contact sheets of the hero, front, `Left`, `Right` and set 03 videos; twelve consecutive frames of one blink in the hero video; the numbers printed by `tools/evaluate_motion.py` and `tools/seam_audit.py`, and `outputs/launch_spec/metadata.json`.

**Limits of this audit:** one reviewer playing eight roles, not eight people. Videos were judged from sampled frames, not watched at speed, so head sway and blink feel are not judged. The second reference ("Flexpressions") was not watched. Scores are estimates of how a strict judge would mark, not a prediction of the result. The same reviewer made the changes being scored, so the rise in score is the least reliable number here.

## Verdict

| Rubric line | Max | 15 Nov | 16 Nov | Why |
|---|---|---|---|---|
| Texture photorealism | 60 | 33 | **38** | Faults that were plainly wrong are gone (half-lit pupil, neon iris, lashes out of bare skin). It still reads as CG within a second: flat bright eye white, painted iris, wiry lashes, skin without pores or glints. |
| Kinematic accuracy | 20 | 16 | **17** | Head sway, lower lid and eyeball pull-back added; all timing still in range. Sway not judged at speed. |
| Code and UV portability | 20 | 17 | **16.5** | Unchanged build. A pale patch at the crown of every portability render was found in this audit (it was there before and was missed). |
| **Total** | 100 | 66 | **71.5** | |

All five required outputs exist. Two look batches and 17 hours of rendering moved the look score by about five points. The remaining gap is not small faults; it is the three or four things below that make an eye read as real.

## What the two batches fixed (confirmed in the new renders)
- Half-lit pupil with a hard vertical edge: gone on all eight sets.
- Iris colour: no longer neon. Limbus is a soft band.
- Lid margin: a pink wet band now sits between the lash roots and the eye, on both lids.
- Lashes no longer come in bunches with hooked ends on the lower lid; upper lashes are uneven in length.
- Down-gaze no longer makes the lower lid cut the iris.
- Blink in the hero video: lid closes over a visible bulge, crow's feet appear, lashes blur. No broken frame in twelve.
- Painted grey eye bags on dark sets: gone.

## The eight judges

### 1. Blender and rendering lead — 5.5/10 (was 5)
- **No lid shadow on the eyeball.** In the reference the upper lid and lashes throw a dark band across the top third of the eye. Ours is lit evenly from lid to lid in every view. This is the main reason the front view reads as a doll.
- Hero view is darker than before but still mid-key. The reference frame is more than half black or deep shadow; ours shows a sliver of black at the left edge and bright skin everywhere else.
- The highlight in the close view is a small jagged white shape with visible steps. In the hero view the four-pane window sits squarely on the pupil.
- Denoising gives skin an oil-paint smear in stills and videos.

### 2. Colour expert — 5.5/10 (was 5)
- **Eye white is one flat pale grey-lilac**, as bright at the corners as beside the iris, and brighter than the skin round it on dark sets (03, 06, 08), where it glows.
- Iris fibres read as radial brush strokes. Set 07 has blocky white patches, sets 05 and 08 have bright orange blocks next to dark gaps.
- Light skin is one even peach. No redness at the nose side, no blue-grey under the eye, no blotch.
- Set 03 front view: the lit cheek under the eye still shows a grey, ashy patch with a coarse texture. D-024 reduced it; it is still the first thing seen on that still.
- Set 07 has an orange cast round both eyes that reads as fake tan.

### 3. Doctor (eye anatomy) — 5.5/10 (was 4)
- Lid margin: now present. Good.
- **Pupil is a flat black disc with a hard edge.** A real pupil is a hole: its edge is soft at this size and it sits behind the cornea with visible depth.
- Lashes are thin single wires with kinks along their length. Real lashes are thicker at the root, taper, curve smoothly, and cross each other in twos and threes.
- Lower lashes are evenly spaced like a comb.
- A hard dark line runs along the lower lid edge in front views (sets 03, 07) and reads as eyeliner.
- Inner-corner tissue is still a round pink bead.
- Vessels are still thin, bright red and sharp.

### 4. Character designer — 6/10 (unchanged)
- Eye shape, socket depth and brows hold up in the front view.
- Set 04 close view: one long raised arc sweeps over the upper lid from the inner corner to the temple. Fainter arcs are still visible on set 01. The ring pattern is reduced, not gone.
- Set 07: forehead and under-eye lines still read as drawn wavy streaks in the front view.
- Brow hairs still stand up like stubble at the top edge of close and hero frames.
- Eight sets still share one face and one lash style.

### 5. Animator — 7.5/10 (was 7)
- Blink is good.
- Head sway exists (largest angle 1.7 degrees) and the eyes hold their target through it. In the hero view the eye drifts about a tenth of the frame width over the clip; from stills this cannot be told apart from camera drift. Needs a person to watch it.
- Lower lid follows gaze.
- Brows still close to static outside blinks. Upper lid still does not fold over itself.

### 6. Biomechanics and eye-movement specialist — 8.5/10 (was 8)
- Saccades 5, 10, 20, 30 degrees: 32.5, 44.5, 72, 99 ms. In range.
- Blink: closing 86.5 ms, whole 337.5 ms, 16.7 per minute. In range.
- Vergence 5.1 degrees; fixation wander 0.7 degrees, now measured as gaze in space with the head moving.
- Eyeball pulls back 1 mm in a blink: added.
- Peak-to-mean velocity for the 5 and 10 degree saccades sits on the lower limit (1.5).
- Head sway range (0.3 to 2.5 degrees) is our own choice, not from a paper; the script prints it as a note, not a sourced check.
- Still missing: upward roll under the closed lid, torsion, pupil reaction.

### 7. Pipeline and portability engineer — 8/10 (was 8.5)
- `./reproduce.sh` rebuilds everything; a fresh clone runs 16 tests and the motion check with nothing missing (checked 15 Nov).
- Seam step on the front of the face: at most 6 of 255 on every set.
- **Crown patch:** all three portability renders show a pale rectangle at the top of the skull. Cause not looked for. It is outside the eye region, but it is on the image that is meant to prove the textures wrap.
- The black-frame guard gave a false alarm on the hero view once the head moved (fixed by leaving out the left fifth of the frame) and still lists 44 frames on the finished set 03 video. It is a weaker guard than it was.
- Docker image builds; videos run out of memory in it on the M3; not tried on Linux.
- Lashes, brows and tear line are generated mesh, so textures alone give no lashes on a stock head.

### 8. Hackathon judge (brief compliance) — 9/10 (unchanged)
- 8 texture sets with distinct left and right iris; script with `Left`, `Right`, `Generate Motion`; videos 9, 9 and 12 s; 24 stills; `.blend` with a Timeline animation; launch-spec API with direction check 5 of 5: all met.
- Open: demo video not uploaded, repo not public, deck not opened in PowerPoint, reference video still in the repo.

## What to do, in order of points per hour

Any change to shared shading or to set 01 means rendering the five set 01 videos again (about 8.5 hours for everything). Stills-only changes cost about 45 minutes. Batch, test on stills of sets 01, 03 and 07, render once.

| # | Change | Judge | Cost | Renders needed |
|---|---|---|---|---|
| 1 | Lid shadow on the eyeball: darken the top of the eye under the upper lid (shading term or a real shadow from lid and lashes) | 1, 2 | 1 to 2 h | all |
| 2 | Eye white: darker overall, shaded toward the corners, slight yellow at the corners; much darker on dark sets | 2 | 1 h | all |
| 3 | Pupil: soft edge and depth; highlight: smooth shape, moved off the pupil in the hero view | 3, 1 | 1 to 2 h | all |
| 4 | Lashes: thicker at the root with taper, smooth curve without kinks, pairs that cross; lower lashes unevenly spaced | 3 | 2 to 3 h | all |
| 5 | Crown patch on the portability heads: find the cause, fix | 7 | 1 h to find | 3 portability stills |
| 6 | Hero view: move the camera or key so at least a third of the frame is shadow or black | 1 | 1 h | hero stills, hero video |
| 7 | Set 03 ashy cheek patch | 2 | 1 to 2 h, tried once already | dark-set stills, set 03 video |
| 8 | Iris: finer fibres, remove the white and orange blocks on sets 05, 07, 08 | 2 | 2 h | stills of those sets |
| 9 | Skin: visible pores and broken-up shine instead of canvas noise | 1 | 3 to 5 h, uncertain | all |
| 10 | Set 04 arc over the lid; set 07 streaks | 4 | 1 to 2 h | stills |

Items 1 to 3 are the cheapest and act on the first thing a judge looks at. Item 5 is small and removes a visible fault from a proof image. Item 9 is the largest remaining gap to the reference and the least certain.

## Not in doubt
The brief's required outputs, the motion numbers, the seam numbers and the rebuild script are solid and backed by scripts. The gap is still the look.
