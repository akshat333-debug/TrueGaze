# Architecture

Status 12 Nov: reader, eyelid/brow controls, scene, motion engine and `render.py` work. 13 Nov: generated texture sets (skin, left/right iris) and shaders are wired in; skin is a procedural baseline, photo-based skin still to come.

## Flow
```
Google GNM Head v3 weights (Apache 2.0, auto-download)
        | truegaze/gnm.py       (NumPy reader, runs inside Blender; weights cached in assets/cache/)
        | tools/fit_controls.py -> assets/controls.npz (named eyelid controls as GNM expression coefficients)
        | truegaze/scene.py     (inside Blender 4.5 LTS, Python 3.11)
        v
Blender scene: mesh + shape keys + armature (eye_L, eye_R, neck) + materials + cameras + lights
        ^                               ^
        | uv_maps/set_NN/ (textures)    | truegaze/motion.py (pure Python trajectories)
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
| `tools/fit_controls.py` | blink and lid controls | A | done (brows, lid-follow todo) |
| `truegaze/scene.py` | mesh, shape keys, rig, camera, lights | A | done (flat colours) |
| `truegaze/materials.py` | skin, eye and refracting cornea shaders, one material per UDIM tile | B | works |
| `truegaze/textures.py` | generates texture sets in GNM's UV layout (`python3 -m truegaze.textures`) | B | baseline |
| `tools/stills.py` | front and close stills per texture set | B | works |
| `tools/make_hair.py` | lashes, brows, tear line with per-control shape keys (`assets/hair.npz`) | A | works |
| `wrapper/eyes.py` | launch-spec API `move/reset/render`, 10-frame sequence, metadata, direction check | C | works |
| `apply_textures.py` | wraps a set on a stock or random-identity GNM head | C | works |
| `tools/seam_audit.py` | measures colour steps across UV seams; writes `uv_maps/` sheets | B | works |
| `truegaze/motion.py` | gaze, saccades, vergence, lids, blinks, brows, pupil | A | done, tested |
| `truegaze/eyes.py`, `wrapper/eyes.py` | `move(h, v)`, `reset()`, `render()` | C | todo |
| `render.py` | 3 inputs to MP4, caption, draft/final | C | done (draft) |
| `tests/`, `Dockerfile` | checks and reproducible run | C | todo |

## Conventions
- Units metres. Camera 40 cm in front of the eye midpoint; fixation plane 35 cm, bounds ±5 cm; renders 1024×1024.
- `h`, `v` in [-1, 1]. Default: +h moves gaze to the right **on screen**; `--frame subject` flips (D-006).
- Textures are UDIM files `face.<tile>.png` per set.
