# Architecture

Status 13 Nov: every required output is produced by script. Head, fitted controls, soft tissue (socket, bulge, drag), hair, photo-based skin, irises, shaders, motion engine, front and hero views, clay/wire looks, launch-spec API, seam audit, motion evaluation and the one-command `reproduce.sh` all work. Open: final-quality videos (rendering), Dockerfile, deck, demo video.

## Flow
```
Google GNM Head v3 weights (Apache 2.0, auto-download)
        | truegaze/gnm.py       (NumPy reader, runs inside Blender; weights cached in assets/cache/)
        | tools/fit_controls.py -> assets/controls.npz (named eyelid controls as GNM expression coefficients)
        | tools/fit_bulge.py    -> assets/bulge.npz    (socket depth, lid bulge, skin drag)
        | tools/make_hair.py    -> assets/hair.npz     (lashes, brows, tear line, facial down)
        | tools/transfer_skin.py-> assets/skin_transfer.npz (GNM vertex -> MakeHuman skin UV)
        | truegaze/textures.py  -> textures/01..08     (photo-based skin, irises, relief, roughness)
        | truegaze/scene.py     (inside Blender 4.5 LTS, Python 3.11)
        v
Blender scene: mesh + shape keys + armature (eye_L, eye_R, neck) + materials + cameras + lights
        ^                               ^
        | textures/NN/ (per UDIM tile)  | truegaze/motion.py (pure Python trajectories)
        v
render.py --input Left|Right|"Generate Motion"  ->  frames -> MP4, stills, metadata JSON, scene.blend
```

## GNM facts the design relies on
- Mesh regions: skin, left/right eye interior (sclera, iris, pupil), left/right eye exterior (cornea), teeth, tongue.
- UDIM tiles: 1001 skin, 1002 left eye interior, 1003 left cornea, 1004 right eye interior, 1005 right cornea, 1006 teeth, 1007 tongue.
- Controls: 253 identity, 383 expression (100 left eye, 100 right eye, 150 lower face, 32 tongue, 1 iris), joint rotations for neck and each eyeball.
- No skin or iris texture is shipped.
- v3.0 pose correctives are zero: template + identity + expression, then linear blend skinning over 4 joints (neck, head, left_eye, right_eye).

## Parts
| part | job | owner | status |
|---|---|---|---|
| `truegaze/gnm.py` | read GNM weights, UDIM tiles | A | done |
| `tools/fit_controls.py` | blink, lid and brow controls | A | done |
| `truegaze/scene.py` | mesh, shape keys, rig, camera, lights | A | done |
| `truegaze/materials.py` | skin, eye and refracting cornea shaders, one material per UDIM tile | B | works |
| `truegaze/textures.py` | generates texture sets in GNM's UV layout (`python3 -m truegaze.textures`) | B | done (8 sets) |
| `tools/stills.py` | front and close stills per texture set | B | works |
| `tools/make_hair.py` | lashes, brows, tear line with per-control shape keys (`assets/hair.npz`) | A | works |
| `tools/transfer_skin.py` | 3D fit of GNM to MakeHuman's head; per-vertex lookup into MakeHuman's skin layout (`assets/skin_transfer.npz`) | B | works |
| `tools/fit_bulge.py` | soft tissue: socket depth, lid bulge over the cornea, skin drag with gaze (`assets/bulge.npz`) | A | works |
| `tools/evaluate_motion.py` | checks saccade, blink, vergence numbers against published ranges | A | works |
| `reproduce.sh` | rebuilds every asset and output from a fresh clone | C | done, fresh-clone parts verified 13 Nov |
| `wrapper/eyes.py` | launch-spec API `move/reset/render`, 10-frame sequence, metadata, direction check | C | works |
| `apply_textures.py` | wraps a set on a stock or random-identity GNM head | C | works |
| `tools/seam_audit.py` | measures colour steps across UV seams; writes `uv_maps/` sheets | B | works |
| `truegaze/motion.py` | gaze, saccades, vergence, lids, blinks, brows, pupil | A | done, tested |
| `render.py` | 3 inputs to MP4, caption, draft/final | C | done (draft and final, black-eye frame check) |
| `tests/`, `Dockerfile` | 16 tests; container builds and runs everything except videos on an M3 (README) | C | done |
| `tools/overview.sh`, `tools/make_deck.py`, `tools/make_demo.py` | overview images, deck, demo video cut | C | done |

## Conventions
- Units metres. Camera 40 cm in front of the eye midpoint; fixation plane 35 cm, bounds ±5 cm; renders 1024×1024.
- `h`, `v` in [-1, 1]. Default: +h moves gaze to the right **on screen**; `--frame subject` flips (D-006).
- Textures are UDIM files per set: `color.<tile>.jpg` (1001 skin, 1002 and 1004 the two eyes), plus `roughness`, `height` and `wrinkle` for tile 1001.
