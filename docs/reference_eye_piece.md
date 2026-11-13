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

## Second pass, 13 Nov: frame-by-frame critique against our renders

Six reference frames (4.5, 7, 9, 11.5, 14.5, 18 s) were set beside our front, close and new hero renders. The reference frames stay local (third-party video); only our renders are in the repo.

| # | What the reference has | Ours before | Done now | Still short |
|---|---|---|---|---|
| 1 | Hard raking key, black background, shallow focus | soft front light, everything sharp | `scene.hero_view`: camera 66° round to the outer side, hard key, depth of field; `--view hero` on `render.py`, hero still per set | our frame is still brighter and lower-contrast |
| 2 | Skin highlight broken into pin-point glints | one broad soft sheen | micro-relief noise finer than the texture, thin oil coat layer, lower roughness (0.52) | fewer, softer glints than theirs |
| 3 | Fine crosshatch wrinkles under the eye | none | concentric and radial fine lines round each socket in the relief map | regular-looking; real lines follow muscle direction |
| 4 | White of the eye is grey-cream with yellow patches, veins from the corners, pink corners | clean white, even veins | warmer base, yellowish patches beside the iris, 60 vessels in two thicknesses entering from the corners, pink corners, subsurface glow | no separate fleshy inner-corner tissue (caruncle) in GNM's mesh |
| 5 | Thick wet pink lid edge with a bright tear line | thin bead, dry edge | wetter lid edge (roughness −0.42), tear bead 0.42 mm | GNM's lid edge has no flat shelf; ours is narrower |
| 6 | Iris with brown crypt spots, strong dark rim, light pooling on the far side | fibres, collarette, rim | pigment freckles added | no refracted light pooling (needs caustics) |
| 7 | Fine facial down lit along the silhouette | none | 4,500 short pale hairs round the eyes | subtle by design; first try was far too visible |
| 8 | Lashes: many, fine, dark, lower ones long | 150 / 65 per eye | 190 / 85, lower longer, darker, less shiny | no tip clumping by moisture |
| 9 | Deep socket, lid fold, skin sliding over the eye | puffy lids | socket depth, crease, bulge and drag (D-014, D-016) | their upper lid folds into itself when open; ours only creases in shading |

Real-eye facts used (from anatomy, not from new photo research): conjunctival vessels enter from the two corners and thin toward the iris; pingueculae are yellowish patches in the exposed strip beside the iris; iris freckles sit in the middle zone; lower-lid skin is the thinnest on the body, hence visible veins and fine lines.
