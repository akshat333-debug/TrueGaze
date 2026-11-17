# Council audit against the brief and the reference (17 Nov)

Replaces the 16 Nov audit (in git history at `6042fa7`). Run again on the renders made after the D-026 look batch. Written to find faults, not to defend the build.

**What was looked at:** our stills at full size (`01_front`, `01_close`, `01_hero`); both overview sheets (all eight sets, front, close and hero); contact sheets, one frame per second, of the front, `Left`, `Right` and set 03 videos and of the demo; mean brightness of each eye region on every frame of those four videos; the test run and the deck validator. The portability renders and the hero video were looked at on 16 Nov after the batch, not again today.

**Limits of this audit:** one reviewer playing eight roles, not eight people. Videos were judged from sampled frames, not watched at speed, so head sway and blink feel are not judged. The reference video was not opened again today; comparisons to it rest on the 16 Nov viewing. "Flexpressions" was not watched. Judges 5 to 8 below are carried over from 16 Nov with only the changed lines edited. Scores are estimates of how a strict judge would mark, not a prediction of the result. The same reviewer made the changes being scored, so the rise in score is the least reliable number here.

## Verdict

| Rubric line | Max | 16 Nov | 17 Nov | Why |
|---|---|---|---|---|
| Texture photorealism | 60 | 38 | **40** | The eye now sits in its socket: lid shadow, darker eye white, soft pupil, hero view half in shadow. It still reads as CG: iris looks painted and smeared, skin has canvas noise instead of pores, lashes are wires. |
| Kinematic accuracy | 20 | 17 | **17** | Motion code unchanged. |
| Code and UV portability | 20 | 16.5 | **17** | Crown patch gone. |
| **Total** | 100 | 71.5 | **74** | |

All five required outputs exist. Three look batches and about 27 hours of rendering moved the look score from 33 to about 40. Each batch has bought less than the one before.

## What the third batch fixed (confirmed in the new renders)
- Lid shadow: the top of the eyeball is darker under the upper lid in front and close views, on all eight sets.
- Eye white: no longer brighter than the skin on dark sets (03, 06, 08); shaded toward the corners.
- Pupil edge is soft in the close view. The hero highlight sits above the pupil, not on it.
- Hero view: brow and nose side are in shadow, about half the frame; the black strip at the left is larger.
- Lower lashes are unevenly spaced; upper lashes taper.
- Crown patch on the portability heads: gone.

## New or remaining look faults

### 1. Blender and rendering lead — 6/10 (was 5.5)
- **Hero view, eye white on the far side of the iris is one flat dark grey-blue slab** with a hard edge against the lid. It reads as a painted shape, not a wet ball in shadow. New with D-026.
- Hero view: a bright crescent sits on the lower left of the iris (light caught at the cornea edge). Reads as an artefact.
- Close view: a hard white vertical bar at the inner edge of the eye, next to the pink corner bead.
- Denoising still gives skin an oil-paint smear.

### 2. Colour expert — 6/10 (was 5.5)
- Iris still reads as radial brush strokes; in `01_close` it looks smeared, as if motion-blurred. White and orange blocks on sets 05, 07, 08 unchanged.
- In `Left` and `Right`, the eye that turns toward the nose shows a wide pink area on its outer white. Reads as an irritated eye.
- Set 03 front view: ashy patch on the lit cheek still there.
- Light skin still one even peach.

### 3. Doctor (eye anatomy) — 6/10 (was 5.5)
- Pupil still has no depth: it is a dark disc on the iris surface.
- Upper lashes in the close view: still single wires, with small hooks and forks at the tips. No crossing pairs.
- Inner-corner tissue still a round pink bead. Vessels still thin, sharp, bright red.

### 4. Character designer — 6/10 (unchanged)
- Not looked at again in detail. Set 04 arc, set 07 streaks, stubble-like brow hairs at the frame top: assumed unchanged; the brow hairs are visible in `01_hero` and `01_close`.

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

### 7. Pipeline and portability engineer — 8.5/10 (was 8)
- `./reproduce.sh` rebuilds everything; a fresh clone runs 16 tests and the motion check with nothing missing (checked 15 Nov).
- Seam step on the front of the face: at most 6 of 255 on every set.
- Crown patch on the portability renders: gone (seam fill takes the photo's local tone, D-026). A small red spot sits at the nostril on `portability_03`; cause not looked for.
- The black-frame guard gave a false alarm on the hero view once the head moved (fixed by leaving out the left fifth of the frame); the hero view now needs a wider margin (4 instead of 2). It is a weaker guard than it was, so on 17 Nov the eye regions of the four front videos were also measured frame by frame: no dark frame.
- Docker image builds; videos run out of memory in it on the M3; not tried on Linux.
- Lashes, brows and tear line are generated mesh, so textures alone give no lashes on a stock head.

### 8. Hackathon judge (brief compliance) — 9/10 (unchanged)
- 8 texture sets with distinct left and right iris; script with `Left`, `Right`, `Generate Motion`; videos 9, 9 and 12 s; 24 stills; `.blend` with a Timeline animation; launch-spec API with direction check 5 of 5: all met.
- Open: demo video not uploaded, repo not public, deck not opened in PowerPoint, reference video still in the repo.

## What to do, in order of points per hour

Any change to shared shading or to set 01 means rendering the five set 01 videos again (about 9.5 hours). The form is due 21 Nov. There is time for one more batch at most, and a fourth batch is expected to buy two or three points.

| # | Change | Cost | Renders needed |
|---|---|---|---|
| 1 | Hero view: lift the fill on the eyeball so the far-side eye white is shaded, not flat; remove the crescent on the iris | 1 to 2 h | hero stills, hero video (2.3 h) |
| 2 | Pink area on the outer eye white when the eye turns in | 1 h | all front videos |
| 3 | Iris: finer fibres, no smear, no blocks on 05 / 07 / 08 | 2 h | stills, set 01 videos |
| 4 | White bar at the inner eye edge in the close view | 1 h to find | stills |
| 5 | Skin pores instead of canvas noise | 3 to 5 h, uncertain | all |
| 6 | Set 03 ashy cheek | 1 to 2 h, tried twice | dark-set stills, set 03 video |

Item 1 is the only one that touches the first frame of the demo and needs only the hero video rendered again. The submission steps (demo link, PowerPoint check, history purge, clean-clone rebuild, public repo) are worth more than any row here if time runs short.

## Not in doubt
The brief's required outputs, the motion numbers, the seam numbers and the rebuild script are solid and backed by scripts. The gap is still the look.
