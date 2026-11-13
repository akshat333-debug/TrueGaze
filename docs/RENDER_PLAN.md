# Render plan (started 13 Nov)

One chain, one Blender at a time (8 GB RAM), kept awake with `caffeinate`. Log: `renders/tmp/chain.log`.
Final-quality frames are written one by one to `renders/tmp/final/` and skipped if present, so a stopped run resumes by starting the same command again.

| # | What | Command (after `Blender --background --python`) | Settings | Output | Time on the M3 |
|---|---|---|---|---|---|
| 1 | Stills, all 8 sets: front, close, hero | `tools/stills.py -- --samples 96` | Cycles, 1280×720, 96 samples, denoised; hero has depth of field | `outputs/renders/NN_front|close|hero.png` | 25 min |
| 2 | Making-of stills, set 01 | `tools/stills.py -- 01 --samples 64 --style wire` and `--style clay` | same, clay material, mesh edges drawn | `outputs/renders/01_wire_*.png`, `01_clay_*.png` | 4 min |
| 3 | UV portability proofs | `apply_textures.py -- --texture 03`; `--texture 05 --identity 3`; `--texture 07 --identity 11` | stock GNM head, 1024², 64 samples | `outputs/renders/portability_*.png` | 3 min |
| 4 | Launch-spec sequence | `wrapper/eyes.py -- --sequence outputs/launch_spec` | 10 frames clockwise from the top, 1024², 64 samples, direction check | `outputs/launch_spec/renders/`, `metadata.json` | 6 min |
| 5 | `.blend` deliverable | `render.py -- --input "Generate Motion" --blend outputs/scene.blend` | animation keyed on the Timeline, textures packed | `outputs/scene.blend` | 1 min |
| 6 | Wireframe video | `render.py -- --input "Generate Motion" --style wire` | EEVEE draft, 960×540, 30 fps | `outputs/videos/Generate_Motion_wire.mp4` | 8 min |
| 7 | Hero-view video | `render.py -- --input "Generate Motion" --view hero --quality final` | Cycles, 1280×720, 48 samples adaptive, motion blur, depth of field, 360 frames | `outputs/videos/Generate_Motion_hero.mp4` | 2.2 h |
| 8 | The three required videos | `render.py -- --all --quality final` | Cycles, 1280×720, 48 samples adaptive, motion blur; Left 9 s, Right 9 s, Generate Motion 12 s; 900 frames | `outputs/videos/Left.mp4`, `Right.mp4`, `Generate_Motion.mp4` | 5.5 h |

Total about 8.7 hours. Order: quick deliverables first, so a stop at any point leaves the most outputs finished.

After it ends: look at every video and still, rebuild the overview images in `docs/`, run `tools/seam_audit.py` and `tools/evaluate_motion.py` once more, commit `outputs/`.

If the look or motion changes again, delete `renders/tmp/final/` first, or old frames are reused.
