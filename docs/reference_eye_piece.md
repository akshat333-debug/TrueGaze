# Reference: "Eye Piece" by Chris Jones (WIP 05/02/14)

46.7 s, 1080p30. Local copy only (not committed: third-party video, repo goes public).
What it shows, and what we take from it. Timings from frame differencing of the first 16 s.

## Structure of the video
- 0–22 s: final renders, close side view of one eye. Eye opens from closed, looks around, blinks twice (about 5.7–6.1 s and 12.7–13.0 s), then a front 3/4 view of a face patch (only the eye region is modelled).
- 24–47 s: breakdown: wireframe, lid rig with control dots, grey shading, lash and brow hair, eyeball geometry.

## Look (texture photorealism, 60 pts)
- Key light from one side and above, near-black background, strong falloff. Most of the realism comes from this lighting; copy it for our hero renders.
- Wet lid margin: a thin bright specular line along the lower lid and on the upper lid fold. We have no tear line or wet margin yet.
- Specular on the upper lid skin is broken up by pores, not a smooth sheen. Needs a roughness map plus a fine normal map.
- Sclera: off-white, slightly blue-grey, veins faint, darker near the corners. Not pure white.
- Iris: radial fibres, darker limbal ring, visible depth under a clear cornea with one sharp window highlight. Cornea refraction matters in side views.
- Caruncle and the pink inner-corner tissue are visible at 3/4 views.
- Lashes: dark, clumped, curved; lower lashes sparse and short. Brows are individual hairs.
- Skin: pores, fine wrinkles under the eye, slight redness at the lids, darker under-eye.

## Motion (kinematic accuracy 20 pts, brownie points)
- Blinks close fast and open slower, matching our 100 ms close / 200 ms open profile.
- Upper lid moves with gaze and the lid skin above the fold bulges as the eyeball turns (we have lids-follow-gaze; lid bulge is in the plan for 18–20 Nov).
- The lid wraps the eyeball tightly; the eyeball shape shows through the closed lid.

## Gaps this shows in our build (by impact)
1. Lighting: our two soft area lights look flat. Add a dark-studio hero light rig.
2. Cornea refraction and limbal ring.
3. Wet lid margin / tear line and caruncle shading.
4. Lashes and brows.
5. Skin roughness and normal detail around the eye.
6. Lid bulge following the cornea.
