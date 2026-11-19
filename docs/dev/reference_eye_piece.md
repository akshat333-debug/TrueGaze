# Reference: "Eye Piece" by Chris Jones (WIP 05/02/14)

46.7 s, 1080p30. The video file is in the repo root for now, at Akshat's request while the repo is private; it is third-party and must be removed from git history before the repo goes public.
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

## Third pass, 13 Nov: the author's own notes (Blender Artists thread "Human Progress")

Source: https://blenderartists.org/t/human-progress/1143224 (2,282 posts; the 49 eye-related posts by Chris Jones were read in full, plus five of his images: eyeball diagram, 2021 plica close-up, 2022 hazel eye, specular map, tear line). Nothing from the thread is copied into the repo; only what we learned.

| What he does | What it told us | Change made |
|---|---|---|
| Eyelids are weighted to a bone that copies the eyeball's rotation at a fraction, "so that they appear to drag" | our 16% lid drag was timid | drag raised to 30% of the gaze angle at the lid edge, up to 2.7 mm |
| Blink is five shapes blended non-linearly "so the eyelids follow the curvature of the eyeball" | our blink was one straight-line shape: half way, the lid cut a chord through the eyeball | new fitted half-closed shape; `blink_mid` corrective weighted 4b(1−b) |
| Eyelid bulge by a warp from pupil to cornea | same idea as our fitted bulge keys | none needed |
| Tear line is a ring duplicated from the eyelid so it shares its motion | same as ours (rebuilt from the lid edge per control) | none needed |
| Caruncle and plica modelled, with their own drag; "most time spent per millimetre" | GNM has neither | small sunk pink caruncle added to the generated mesh, following both lids |
| One eyeball material, sclera fading to clear cornea through a ramp; limbus "the hardest part" | our limbus was too sharp | limbus blend widened, blue-grey ring added where the white thins |
| Iris: sculpted relief plus colour; thick cords, crypts, ragged collarette | ours was hundreds of hairlines, flat | about sixty thick cords, crypt pits between them, ragged starburst centre, relief from the picture itself |
| Caustics: months lost, shadow caustics "failed to deliver" | not worth chasing in a week | still not attempted (stated limit) |
| Specular map brightest on eyelids and lips, mottled everywhere | our lids were as matte as cheeks | lids shinier, roughness contrast raised, wet pink lid edge with lashes rooted outside it |
| Advice to another artist: look at "uniformity of the vellus hair" and "evenness of the rim highlights"; reduce SSS around eyelids and nose | applies to us directly | SSS 0.30 → 0.24, sclera surface made slightly uneven so highlights wobble, catchlight softbox in the hero shot |

Not done from this pass: plica semilunaris (thin flap behind the caruncle), separate SSS colour map, wrinkle/tension maps that change with expression, sculpted iris displacement.

"Flexpressions" (the second reference) was not watched: no local copy and it shows whole-face expressions, outside this track's eye focus. Macro photo study was limited to the author's own close-up renders above; the Wikimedia search returned nothing usable.

## Fourth pass, 13 Nov: the three items left out, and the rest of the thread

All 682 posts by the author were downloaded; beyond the 49 eye posts, the 112 with technical content (skin, hair, wrinkles, lighting, render settings) were read.

| Item | How he does it | How we did it | Honest difference |
|---|---|---|---|
| Light pooling in the iris | real refracted caustics; months of trouble, usable only once path guiding arrived | computed in the iris shader: for each iris point, how far it lies on the side away from the key light, as a crescent near the rim (`materials.eye`, `set_key_direction`) | an approximation of where the light gathers, not traced light; follows the key light only |
| Plica semilunaris | a thin modelled flap, "the most time I've spent per millimetre" | none since 19 Nov: the ridge we had read as a bright bar and was removed (D-027) | no plica |
| Wrinkles that change with expression | two sculpted wrinkle height maps, revealed by masks "driven directly by the shape key values" (he gave up on tension maps for the face) | same scheme: `wrinkle.1001` map (red = forehead lines, green = crow's feet and under-eye lines) faded in by drivers on brow raise and lid closure (`materials.drive_wrinkles`) | lines are drawn by rule, not sculpted; two expression groups, not fifty |

Also taken from the wider thread: Christensen-Burley scattering for the eyeball (random walk "creates a grey outline at the limbus"), random-walk skin mode for skin, Voronoi cells for the finest skin relief ("the finest bump is Voronoi"), and his remark that darker skin is "less translucent and more reflective" (already true of our sets through roughness and tone).

Noted but not applicable: his hair cannot follow shader displacement (ours is bump only, so no gap opens); motion blur with hair was unusably slow for him (ours costs 22 s per frame).
