# TrueGaze launch-spec bundle — VIT Vellore, Team Zero Drift

Samsung PRISM XR Hackathon 2026, Track 1 (Synthetic Eyes). Full project: https://github.com/akshat333-debug/TrueGaze

| File | What it is |
|---|---|
| `scene.blend` | Google GNM head (Apache 2.0) with two eye bones, launch camera 40 cm in front, textures packed in |
| `wrapper/eyes.py` | `move(h, v)`, `reset()`, `render(path)`, `pose()`, `direction_check()`, `sequence(dir)` |
| `wrapper/truegaze/` | the rig helpers `eyes.py` imports (eyelids and brows follow the gaze) |
| `renders/` | 10 frames, 1024x1024, clockwise from the top: `h = sin θ`, `v = cos θ`, `θ = 2πk/10` |
| `metadata.json` | per frame: `frame`, `theta`, `input{h,v}`, `eye_rotation_L/R`, `pupil_center_2D_L/R`, `camera_matrix` |

## Run (Blender 4.5 LTS, nothing else to install)

```bash
blender --background scene.blend --python wrapper/eyes.py -- --check              # direction check, about 2 min
blender --background scene.blend --python wrapper/eyes.py -- --sequence out_dir    # 10 frames + metadata.json
```

Interactive, from Blender's Python console with `scene.blend` open:

```python
import sys; sys.path.insert(0, bpy.path.abspath("//wrapper")); import eyes
eyes.move(0.5, 0.0)   # h, v in [-1, +1]; h > 0 looks to the viewer's right, v > 0 looks up
eyes.render("//frame.png")
eyes.reset()
```

## How it works

- `move(h, v)` puts one fixation point on a plane 35 cm in front of the eye midpoint, up to 5 cm sideways
  and up/down, and turns each eyeball about its own centre to look at it (true 3D rotation, with vergence).
  Upper and lower lids and the brows follow the gaze.
- `eye_rotation_L/R`: XYZ Euler degrees in the world frame (X right, Y away from the camera, Z up), relative to straight ahead.
- `pupil_center_2D_L/R`: pixels, origin top-left. It is where the pupil centre *appears*: the camera ray is
  refracted by the cornea (sphere fitted to the posed cornea, IOR 1.376) before it reaches the pupil.
  `pupil_center_2D_unrefracted_*` is the plain pinhole projection, kept for comparison.
- `pupil_center_2D_found_*`: the pupil centre found in the rendered PNG by `find_pupil` (darkest blob, plain
  numpy, no labels). `label_error_px` in `metadata.json` is the distance between the label and that.
- Direction check (Left, Right, Up, Down, Reset): each pose is **rendered**, the pupils are found in the pixels,
  and each must move at least 3 px the right way (Reset: back within 1 px). It tests the images, not the labels.
- `camera_matrix`: 3x3 intrinsics in pixels and the 4x4 camera-to-world pose.
