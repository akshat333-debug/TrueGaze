# Architecture

Status 12 Nov: reader, eyelid control fit and scene builder work (Day-1 spike). Flat stand-in colours, no textures or motion engine yet.

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
| `truegaze/materials.py` | skin, sclera, iris, cornea shaders | B | todo |
| `truegaze/motion.py` | gaze, saccades, vergence, lids, blinks, brows, pupil | A | todo |
| `truegaze/eyes.py`, `wrapper/eyes.py` | `move(h, v)`, `reset()`, `render()` | C | todo |
| `textures/` | skin transfer, iris synthesis, detail maps, seam audit | B | todo |
| `render.py`, `apply_textures.py` | one-command outputs, portability proof | C | todo |
| `tests/`, `Dockerfile` | checks and reproducible run | C | todo |

## Conventions
- Units metres. Camera 40 cm in front of the eye midpoint; fixation plane 35 cm, bounds ±5 cm; renders 1024×1024.
- `h`, `v` in [-1, 1]. Default: +h moves gaze to the right **on screen**; `--frame subject` flips (D-006).
- Textures are UDIM files `face.<tile>.png` per set.
