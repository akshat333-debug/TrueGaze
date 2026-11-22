# How it works

Two open inputs, four one-time fits, one scene builder. Full module map and conventions: [ARCHITECTURE.md](ARCHITECTURE.md).

## Head and rig
- **GNM v3, read straight from Google's weights** (`truegaze/gnm.py`, `truegaze/scene.py`): mesh, GNM's own UDIM UV layout, a four-bone rig. The eyeballs rotate about their real centres: true 3D rotation, not a pupil sliding in 2D.
- **Controls solved inside GNM's own space** (`tools/fit_controls.py`): blink, lid raise and lower, brow raise and lower are fitted as mixes of GNM's 200 eye-expression components, with a constraint that the lid never sinks into the eyeball. They work on any GNM face.
- **The eye pushes the face** (`tools/fit_bulge.py`): the eye sits 2.9 mm into a socket, the lid lifts 1.6 mm over the cornea, and nearby skin drags up to 2.7 mm as the eye turns.

## Look
- **Skin moved in 3D, not painted** (`tools/transfer_skin.py`): public-domain MakeHuman skins are carried onto GNM by fitting one head to the other (0.5 mm median, lids and lip line pinned), then resampled into GNM's UV layout.
- **8 texture sets** (`truegaze/textures.py`): per set, 4K skin colour, roughness and pore-height maps, plus a 2K map per eye with sclera, veins, iris fibres, crypts, collarette and limbal ring. The two irises share a colour but never a pattern, as in real eyes.
- **Shading** (`truegaze/materials.py`): subsurface skin; a clear cornea that refracts, so the iris has depth and shifts with view; wet lid margin and tear line; expression wrinkles driven by the same controls that move the face.
- **Hair** (`tools/make_hair.py`): about 7,400 generated lash, brow and down strands, rebuilt for every control so lashes ride the lid.

## Motion (`truegaze/motion.py`)
- Saccades on the measured main sequence (25 ms + 2.4 ms per degree), with a small overshoot.
- Both eyes aim at one 3D point, so they converge on near targets.
- Lids follow vertical gaze. Blinks close fast and open slowly, large gaze jumps trigger one, and the eyeball pulls back about 1 mm.
- Fixation drifts with micro-saccades, pupils fluctuate, and the head sways while the eyes hold their target.
- Motion blur at a 180° shutter, as a real 30 fps camera would record it.
- **Opt-in `--natural`:** saccades over 12° land 6–12 % short and a corrective saccade follows 150–220 ms later; the head follows large shifts 40 ms late and takes about a fifth of them while the eyes keep the target; about one spontaneous blink in four stops short; one brow rises a beat later and a little less. Off by default, so the submitted videos are unchanged; covered by tests.

## Launch-spec API (`wrapper/eyes.py`)
- `move(h, v)` puts one fixation point on a plane 35 cm out and turns each eyeball to it; `reset()`, `render(path)`.
- Per frame: `eye_rotation_L/R`, `pupil_center_2D_L/R` refracted by the cornea, `camera_matrix`.
- The direction check renders each pose and finds the pupils in the pixels, so it tests the images, not our own labels. Bundle details: [launch_bundle_README.md](launch_bundle_README.md).

## Live in the browser and in WebXR (`docs/xr/`)
- `tools/export_web.py` exports the GNM head, its four-bone rig, lashes and all 33 shape keys to glTF (`docs/xr/head.glb`, texture set 01).
- `docs/xr/gaze.js` is a real-time port of `truegaze/motion.py`: the same main-sequence saccades, blink profile, lid follow, bulge and drag keys, drift, micro-saccades and hippus, plus the natural extras.
- `docs/xr/index.html` (three.js): the eyes follow your cursor; **Enter XR** on a Meta Quest stands the head 60 cm in front of you and it holds your gaze. Live: https://akshat333-debug.github.io/TrueGaze/xr/. The browser version is tested; the headset path uses the standard three.js WebXR button but was not tried on a headset.

## Where it sits
Synthetic eyes for gaze research are an established line: SynthesEyes (ICCV 2015), UnityEyes (ETRA 2016), EyeRender (2014), RIT-Eyes (2020), NVGaze (CHI 2019), Microsoft Face Synthetics (ICCV 2021), GazeGene (CVPR 2025). TrueGaze brings that approach to an Apache-licensed head with controls in its own expression space, soft tissue that follows the eye, motion checked against recorded people, and labels checked against the pixels.
