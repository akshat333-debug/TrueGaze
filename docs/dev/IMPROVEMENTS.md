# Improvement list (14 Nov)

Historical (14 Nov). The current list of faults and next steps is `docs/SELF_AUDIT.md`.

Two inputs: an outside frame-by-frame review of our renders against "Eye Piece" (pasted by Akshat), and a web search across papers, engine docs and artist forums. Every claim in the review was checked against this repo before it was accepted.

## 1. The outside review, checked

The review's *observations* are partly right. Its *code references* are not ours: none of the lines it quotes exist here (`energy=14`, `rough = 0.42 + 0.04 * skin_bump`, `Coat Weight 0.06`, `SEGMENTS = 8`, `socket_depth()` in `fit_controls.py`, `_EYELID_RIMS`, `in_iris = r < iris_r`, fuzz `Alpha=0.32`). Do not apply its numbers as written.

| # | Review says | Checked against the repo | Verdict |
|---|---|---|---|
| 1 | Flat light, plain rectangle catchlight | Hero key is hard and raking already, but the frame is brighter and lower in contrast than the reference; catchlight is a plain softbox | **Partly true.** Window-pane catchlight and darker fill are worth doing |
| 2 | No tear meniscus | We have one: a 0.42 mm round bead per lid (`make_hair.tear_line`). It is a tube, not a concave film joining lid and eyeball | **Partly true.** Reshape, do not add |
| 3 | Iris flush with the cornea; hard limbus; 8-sided pupil | Measured on GNM: iris plane 4.1 to 4.5 mm from the eye centre, cornea apex 7.3 mm, so the chamber is about 3 mm deep (real eyes: about 3 mm). Limbus is already a soft blend. Pupil rim has 24 vertices | **False.** A real iris is close to flat; the "concave cone" is an old game trick for faking caustics |
| 4 | Skin is matte, no pore-to-ridge shine contrast | Pores already lower the shine (`- 0.07 * bumps`) and there is a coat layer, but the effect is weak next to the reference | **Partly true** |
| 5 | Lid crease is painted; no wrinkles on blink | Wrinkles on blink and brow raise exist (D-020). The lid not folding under an overhang is true and already a stated limit | **Half false, half known** |
| 6 | Lashes kinked, dark dots under lower lashes, fuzz too dark | Dark lash-root shading is real (`0.35 * dots`) and can read as dirt under the lower lid. Fuzz was fixed tonight in the opposite direction for dark skin (D-021): pale fuzz showed as specks there | **Partly true**; ignore the fuzz advice |
| 7 | Brow and head never move with gaze | `brow_lower` is fitted but never driven: true. Head is fixed: true | **True for the brow.** Head: see research below |

## 2. What the search added

- **Tear line and eye occlusion are standard parts.** Reallusion's and Universal Human's eye shaders both ship a separate tear-line material and an "eye occlusion" layer that darkens the eyeball under the lids. We have the first as a bead and nothing for the second. https://manual.reallusion.com/CC_and_IC_Auto_Setup_Plugin/ENU/CC_and_iC_Auto_Setup/1.2/02_for_Unreal/Eye-and-Eye-Occlusion.htm · https://sites.google.com/view/universalhuman/documentation/eye-shader-docs
- **Meniscus shape:** a CG patent on tear menisci notes the upper one is thinner than the lower because of gravity. https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/9269185
- **Sclera is the common giveaway.** Forum critiques repeat it: whites too bright and too white, corners need pink, and a hard iris edge "must" be avoided. Ours is still bright in the close-ups. https://blenderartists.org/t/skin-shader-procedural-eyeball/1364002
- **Fake iris caustics is an accepted method.** A real-time paper bends the iris normal half-way toward concave so the bright side lands opposite the light; a 2018 Disney talk gets better caustics from a more accurate iris depth and renders the limbal arc as part of sclera scattering. Our shader crescent is the same family; state it as such. https://apps.dtic.mil/sti/trecms/pdf/AD1171449.pdf · https://history.siggraph.org/learning/plausible-iris-caustics-and-limbal-arc-rendering
- **True caustics in Cycles** are slow; path guiding helps, "shadow caustics" give poor results (same as the reference author found). https://sites.google.com/view/universalhuman/documentation/eye-shader-docs
- **Skin:** Epic's digital humans use two specular lobes and a base roughness near 0.4; a USC paper argues missing skin microstructure is one reason digital humans look uncanny. https://dev.epicgames.com/documentation/unreal-engine/creating-human-skin-in-unreal-engine · https://vgl.ict.usc.edu/Research/Microgeometry/Measurement_Based_Synthesis_of_Facial_Microgeometry.pdf
- **Eyelids:** Disney's eyelid capture found the skin rolls and folds inward as the eye opens and stretches over the eyeball when shut, and wrinkles differ per person and per side. Their blink study found real blinks are asymmetric in time and space, and fully closing blinks were rated most natural. https://phys.org/news/2015-08-wrinkles-hi-res-eyelid-reconstruction-digital.html · https://la.disneyresearch.com/publication/modeling-and-animating-eye-blinks/
- **Head movement:** for gaze shifts under 20 to 25 degrees the head contributes "practically nil". Our largest shift is about 22 degrees, so a head that follows gaze is not supported by the data; the review's item is rejected on that ground. https://pmc.ncbi.nlm.nih.gov/articles/PMC3191847
- **Open reference code:** RoboPoets/digital_human (MIT, CC0 art): eye shader with limbus width and darkness, iris caustics. Worth reading before touching the limbus. https://github.com/RoboPoets/digital_human

Not found: any measured data on brow or cheek movement coupled to saccades. Item 7's numbers are the reviewer's own.

## 3. Tasks, in order of value for the 60 texture points

**Status 15 Nov:** tasks 1 to 9 are done (D-022; task 9 is `outputs/videos/Generate_Motion_set03.mp4`) and all videos are re-rendered. Tasks 10 to 12 are open.

Cost is work plus test renders. "Videos" = the change alters set 01, so the five final videos must be re-rendered (about 9 h of machine time in total) to stay consistent.

| # | Task | Where | Cost | Videos |
|---|---|---|---|---|
| 1 | **Eye occlusion:** darken the eyeball under the upper lid and into the corners (soft shadow the big lights do not give) | `materials.eye` / `cornea` | small | yes |
| 2 | **Sclera less white:** lower brightness, warmer, pinker corners; check against two real macro photos | `textures.eye` | small | yes |
| 3 | **Tear film:** replace the round bead with a concave strip joining lid edge and eyeball, lower one thicker than upper, clear wet shader | `make_hair.tear_line`, `materials` | medium | yes |
| 4 | **Window catchlight:** mullion pattern on the catch light so the cornea reflects a window, not a rectangle; lower hero fill | `scene.hero_view` | small | hero video only |
| 5 | **Lash roots:** soften the baked dark dots under the lower lashes; check lash curve smoothness in close-up | `textures.skin`, `make_hair` | small | yes |
| 6 | **Skin shine contrast:** stronger pore-versus-ridge roughness, second lobe tuned; test on light and dark sets | `textures.skin`, `materials.skin` | medium | yes |
| 7 | **Brow and cheek in the motion:** drive the fitted `brow_lower` slightly on down-gaze and blinks; small lower-lid rise on squint | `motion.py`, `render.py`, tests | small | yes |
| 8 | **Iris:** tone set 01's blue toward a natural slate; tune the pooling strength; darker limbal ring | `textures.SETS`, `materials.eye` | small | yes |
| 9 | **Second-set video:** one final video on a dark or old set (all videos are set 01 now) | `render.py --texture` | 3 h render | new video |
| 10 | **Upper-lid fold with overhang** (skin tucks under the brow fold when the eye is open) | `fit_bulge.py` | large, risky on GNM's coarse lid mesh | yes |
| 11 | True caustics with path guiding (CPU only) for one hero still | `stills.py` | large | no |
| 12 | Idle head sway (not gaze-following) | done 15 Nov (D-025): the rig object turns about the neck, no rework needed | done | yes |

Recommended batch: 1 to 8 together, tested on stills of sets 01, 03, 07, then one overnight re-render of the five videos plus task 9. Tasks 10 to 12 only if time remains after the deck and demo video.

Still open from before: member names in the deck, demo video, Dockerfile, commit `textures/`, purge the reference video, go public, submit (see `TASKS.md`).
