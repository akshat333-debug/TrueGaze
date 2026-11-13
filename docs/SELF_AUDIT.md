# Self-audit against the judging rubric (13 Nov, status line updated 14 Nov)

Rubric: texture photorealism 60 · kinematic accuracy 20 · code and UV portability 20 · brownie points for natural motion. Judged on "visual photorealism, no seams, smooth kinematics, UV compatibility".

## One-sentence answer to the brief
Eight scripted texture sets with distinct left/right irises wrap onto any GNM head, and one command renders physiologically timed Left / Right / Generate Motion videos with lids, lashes and brows moving with the eyes.

## Texture photorealism (60) — the weakest area, and the largest
| What a judge looks at | State | Evidence |
|---|---|---|
| Iris detail | good | wavy fibres, collarette, furrows, limbal ring, refracting cornea; left ≠ right |
| Sclera | fair | veins, corner darkening; no blood-vessel depth, uniform wetness |
| Lashes, brows, wet lid edge | good | about 7,500 strands incl. facial down, tear bead, follow the lids |
| Skin colour | good (was weak) | photo-based: MakeHuman CC0 skins transferred in 3D (D-015); young, middle-aged and old, light and dark |
| Skin micro-detail | fair | pores and creases as bump; no real wrinkle direction, no lid crease |
| Seams | good, measured | `tools/seam_audit.py`: front-of-face step ≤ 6/255 |
| 5–10 sets | done | 8 sets, 3 skin-tone groups, 6 eye colours |

**Update, same day:** route B below was taken and is in all 8 sets. Remaining gaps: no lid crease in the geometry, uniform wetness on the eyeball, skin micro-relief is still partly generated.

**Largest credibility gap (before the update):** skin. Close-ups read as a good CG render, not a photograph. The reference ("Eye Piece") wins on skin: pores that break up the highlight, lid creases, redness at the lid edge.

**Fork for the team (rebuild, not reword):**
- A. Keep generated skin and polish (lid crease, wrinkle direction, capillary layer). Cheap, safe, bounded ceiling.
- B. Photo-based albedo from CC0 scans, transferred into GNM UV space. Highest ceiling; needs a mesh registration step and per-asset licence checks.
- C. Diffusion-generated identities on a free cloud GPU, projected into UV. High ceiling, more moving parts, lighting must be removed from the result.
Decided 13 Nov: B for all 8 sets (D-015). 14 Nov: dark-skin sheen and old-skin streaks fixed (D-021).

## Kinematic accuracy (20) — strong
- Saccade main sequence, overshoot, vergence, lid-follow, blink shape, gaze-evoked blinks, drift, micro-saccades, pupil fluctuation: all unit-tested (`tests/test_motion.py`).
- Eyes rotate about GNM's real eye joints; lids never cut the eyeball (fit constraint) and lift over the cornea (`tools/fit_bulge.py`).
- Direction check Left/Right/Up/Down/Reset 5/5, measured from projected pupil positions.
- `tools/evaluate_motion.py` (13 Nov) checks saccade duration, blink timing and rate, and vergence against published ranges; it found four numbers off and they were fixed (D-018). Still not done: comparison against our own recordings of real eyes.

## Code and UV portability (20) — strong
- One command per output; scene built from script; GNM weights fetched and checksum-verified.
- `apply_textures.py` wraps sets on stock and random-identity GNM heads with none of our rig.
- Texture files named by GNM UDIM tile numbers.
- Not yet done (14 Nov): Dockerfile and a fresh-clone run on Linux; FLAME-topology version (spec allows GNM *or* FLAME, so not required).

## Brownie points (natural motion)
- Present: micro-movements, natural and gaze-evoked blinks, lids and brows following gaze, lash motion, lid bulge, pupil changes.
- Missing: small head movement with large gaze shifts; cheek/lower-lid squeeze in a full blink; a second expression.

## Risks
- Final-quality video is slow on the M3 (about 14 s per frame in Cycles). Needs a cloud GPU or overnight runs; drafts use EEVEE.
- `textures/` is not in git until the 17 Nov checkpoint; a fresh clone must generate it (about 3 minutes).
- Repo must be public before the form is submitted.
