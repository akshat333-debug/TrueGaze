"""Launch-spec eye API. Runs inside Blender.

    import eyes
    eyes.move(0.5, 0.0)   # h, v in [-1, +1]; h > 0 looks to the viewer's right, v > 0 looks up
    eyes.render("frame.png")
    eyes.reset()

Both eyes aim at one fixation point on a plane 35 cm in front of the eye midpoint; h and v move
that point up to 5 cm sideways and up/down. The camera is 40 cm in front, renders are 1024x1024.

Full required sequence (10 clockwise frames, metadata.json, direction check):
    Blender --background --python wrapper/eyes.py -- --sequence outputs/launch_spec
"""
import json
import math
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from truegaze import motion, scene  # noqa: E402

TARGET_DISTANCE = 0.35   # m, fixation plane in front of the eye midpoint
TARGET_RANGE = 0.05      # m, reach of h and v on that plane
PUPIL_DEPTH = 0.0128     # m, pupil centre in front of the eyeball centre (GNM template)
SIDES = {"L": "left", "R": "right"}
state = {"h": 0.0, "v": 0.0}


def _rig():
    """The scene's head and rig; builds the scene on first use (or uses the open scene.blend)."""
    if "Rig" not in bpy.data.objects:
        scene.build()
        sc = bpy.context.scene
        sc.render.resolution_x = sc.render.resolution_y = 1024
        sc.camera.data.lens = 140  # both eyes and brows fill the square frame from 40 cm
        sc.cycles.samples = 64
    return bpy.data.objects["Head"], bpy.data.objects["Rig"]


def _angles(arm, side, h, v):
    """Yaw and pitch (degrees) that aim one eye at the fixation point."""
    sc = bpy.context.scene
    target = Vector(sc["eye_mid"]) + Vector((h * TARGET_RANGE, -TARGET_DISTANCE, v * TARGET_RANGE))
    d = target - arm.matrix_world @ arm.data.bones[f"{side}_eye"].head_local
    return math.degrees(math.atan2(d.x, -d.y)), math.degrees(math.atan2(d.z, math.hypot(d.x, d.y)))


def move(h, v):
    """Aims both eyes. Inputs are clamped to [-1, +1]. Eyelids and brows follow the gaze."""
    h, v = max(-1.0, min(1.0, float(h))), max(-1.0, min(1.0, float(v)))
    head, arm = _rig()
    keys = head.data.shape_keys.key_blocks
    for side in SIDES.values():
        yaw, pitch = _angles(arm, side, h, v)
        scene.pose_eye(head, arm, side, yaw, pitch)
        for name, value in motion.lids(yaw, pitch).items():
            keys[f"{name}_{side}"].value = value
    bpy.context.view_layer.update()
    state.update(h=h, v=v)


def reset():
    move(0.0, 0.0)


def render(path=None):
    """Renders the current pose to a 1024x1024 PNG and returns its path."""
    _rig()
    sc = bpy.context.scene
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = str(path or ROOT / "outputs" / "launch_spec" / "frame.png")
    bpy.ops.render.render(write_still=True)
    return sc.render.filepath


def pose():
    """Measured state of both eyes: rotation in the world frame and where each pupil lands in the image."""
    _, arm = _rig()
    sc = bpy.context.scene
    out = {}
    for tag, side in SIDES.items():
        bone = arm.pose.bones[f"{side}_eye"]
        turn = (arm.matrix_world @ bone.matrix).to_3x3() @ (arm.matrix_world @ bone.bone.matrix_local).to_3x3().inverted()
        out[f"eye_rotation_{tag}"] = [round(math.degrees(a), 4) for a in turn.to_euler("XYZ")]
        pupil = arm.matrix_world @ bone.matrix @ Vector((0, PUPIL_DEPTH, 0))  # the bone's Y axis is the gaze
        ndc = world_to_camera_view(sc, sc.camera, pupil)
        out[f"pupil_center_2D_{tag}"] = [round(ndc.x * sc.render.resolution_x, 2), round((1 - ndc.y) * sc.render.resolution_y, 2)]
    return out


def camera_matrix():
    """3x3 pinhole intrinsics in pixels and the 4x4 camera-to-world pose."""
    sc = bpy.context.scene
    cam = sc.camera
    f = cam.data.lens / cam.data.sensor_width * sc.render.resolution_x
    cx, cy = sc.render.resolution_x / 2, sc.render.resolution_y / 2
    return {"intrinsics": [[f, 0, cx], [0, f, cy], [0, 0, 1]], "camera_to_world": [list(map(float, row)) for row in cam.matrix_world]}


def direction_check():
    """Left, Right, Up, Down and Reset each checked by where the pupils land in the image."""
    reset()
    rest = pose()
    results = {}
    for name, (h, v, axis, sign) in {"Left": (-1, 0, 0, -1), "Right": (1, 0, 0, 1), "Up": (0, 1, 1, -1), "Down": (0, -1, 1, 1)}.items():
        move(h, v)
        now = pose()
        results[name] = all(sign * (now[f"pupil_center_2D_{t}"][axis] - rest[f"pupil_center_2D_{t}"][axis]) > 1.0 for t in SIDES)
    reset()
    results["Reset"] = pose() == rest
    return results


def sequence(out_dir):
    """The 10 clockwise renders starting at the top, plus metadata.json."""
    out_dir = Path(out_dir)
    frames = []
    for k in range(10):
        theta = 2 * math.pi * k / 10
        h, v = math.sin(theta), math.cos(theta)
        move(h, v)
        render(out_dir / "renders" / f"frame_{k:02d}.png")
        frames.append({"frame": k, "theta": theta, "input": {"h": h, "v": v}, **pose(), "camera_matrix": camera_matrix()})
    meta = {"units": {"eye_rotation": "degrees, XYZ Euler in the world frame (X right, Y away from camera, Z up), relative to straight ahead",
                      "pupil_center_2D": "pixels, origin top-left of the 1024x1024 render", "theta": "radians"},
            "fixation_distance_m": TARGET_DISTANCE, "camera_distance_m": scene.CAMERA_DISTANCE,
            "direction_check": direction_check(), "frames": frames}
    (out_dir / "metadata.json").write_text(json.dumps(meta, indent=1))
    return meta


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if args[:1] == ["--sequence"]:
        meta = sequence(args[1] if len(args) > 1 else ROOT / "outputs" / "launch_spec")
        print("direction check:", meta["direction_check"])
        assert all(meta["direction_check"].values()), "direction check failed"
    elif args[:1] == ["--check"]:
        result = direction_check()
        print("direction check:", result)
        assert all(result.values()), "direction check failed"
