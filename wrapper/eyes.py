"""Launch-spec eye API. Runs inside Blender.

    import eyes
    eyes.move(0.5, 0.0)   # h, v in [-1, +1]; h > 0 looks to the viewer's right, v > 0 looks up
    eyes.render("frame.png")
    eyes.reset()

Both eyes aim at one fixation point on a plane 35 cm in front of the eye midpoint; h and v move
that point up to 5 cm sideways and up/down. The camera is 40 cm in front, renders are 1024x1024.

Full required sequence (10 clockwise frames, metadata.json, image-based direction check, scene.blend):
    Blender --background --python wrapper/eyes.py -- --sequence outputs/launch_spec
From the unzipped launch bundle (scene.blend at the zip root):
    Blender --background scene.blend --python wrapper/eyes.py -- --check

pupil_center_2D is where the pupil centre appears in the image: the ray from the camera is refracted
by the cornea (fitted sphere, IOR 1.376) before it reaches the pupil. The direction check renders the
five poses and finds the pupil in the pixels, so it tests the image, not the labels.
"""
import json
import math
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path[:0] = [str(ROOT), str(HERE)]  # repo layout: truegaze/ beside wrapper/; launch zip: wrapper/truegaze/
from truegaze import motion, scene  # noqa: E402
from truegaze.materials import CORNEA_IOR  # noqa: E402
from truegaze.motion import PUPIL_REST  # noqa: E402

TARGET_DISTANCE = 0.35   # m, fixation plane in front of the eye midpoint
TARGET_RANGE = 0.05      # m, reach of h and v on that plane
PUPIL_DEPTH = 0.0128     # m, pupil centre in front of the eyeball centre (GNM template)
CORNEA_TILE = {"left": 2, "right": 4}  # UDIM column of each eye's outer shell (truegaze/materials.assign)
CORNEA_UV_RADIUS = 0.14  # the clear cornea ends at 0.155 from the tile centre
SIDES = {"L": "left", "R": "right"}
state = {"h": 0.0, "v": 0.0}
_cornea_index = {}


def _rig():
    """The scene's head and rig; builds the scene on first use, or uses the open scene.blend.
    The launch camera is set every time, so an animated .blend renders the same frames."""
    if "Rig" not in bpy.data.objects:
        scene.build()
    sc = bpy.context.scene
    head, arm = bpy.data.objects["Head"], bpy.data.objects["Rig"]
    if not sc.get("launch_spec"):
        for owner in (arm, head.data.shape_keys, sc.camera):
            if owner.animation_data:
                owner.animation_data_clear()
        arm.location, arm.rotation_euler = (0, 0, 0), (0, 0, 0)  # head sway moves the rig object
        for bone in arm.pose.bones:
            bone.matrix_basis.identity()
        for key in head.data.shape_keys.key_blocks[1:]:
            key.value = 1.0 if key.name.startswith("socket") else PUPIL_REST if key.name == "pupil" else 0.0
        sc.camera.location = Vector(sc["eye_mid"]) + Vector((0, -scene.CAMERA_DISTANCE, 0))
        sc.camera.rotation_euler = (math.pi / 2, 0, 0)
        sc.camera.data.lens = 140  # both eyes and brows fill the square frame from 40 cm
        sc.render.resolution_x = sc.render.resolution_y = 1024
        sc.render.resolution_percentage = 100
        sc.cycles.samples = 64
        sc["launch_spec"] = True
    return head, arm


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


def _cornea_sphere(head, side):
    """Least-squares sphere through the posed cornea vertices of one eye (world frame): centre, radius."""
    if side not in _cornea_index:
        mesh, uv = head.data, head.data.uv_layers["UDIM"].data
        _cornea_index[side] = np.array(sorted({mesh.loops[i].vertex_index for i in range(len(mesh.loops))
                                               if int(uv[i].uv[0]) == CORNEA_TILE[side]
                                               and math.hypot(uv[i].uv[0] % 1 - 0.5, uv[i].uv[1] - 0.5) < CORNEA_UV_RADIUS}))
    ev = head.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
    co = np.empty(len(ev.vertices) * 3)
    ev.vertices.foreach_get("co", co)
    p = co.reshape(-1, 3)[_cornea_index[side]] @ np.array(head.matrix_world)[:3, :3].T + np.array(head.matrix_world)[:3, 3]
    a = np.c_[2 * p, np.ones(len(p))]
    sol = np.linalg.lstsq(a, (p * p).sum(1), rcond=None)[0]
    return sol[:3], math.sqrt(sol[3] + sol[:3] @ sol[:3])


def _camera_ray(pixel):
    sc = bpy.context.scene
    k = camera_matrix()["intrinsics"]
    d = np.array([(pixel[0] - k[0][2]) / k[0][0], -(pixel[1] - k[1][2]) / k[1][1], -1.0])
    rot = np.array(sc.camera.matrix_world)[:3, :3]
    d = rot @ d
    return np.array(sc.camera.matrix_world.translation), d / np.linalg.norm(d)


def _through_cornea(pixel, centre, radius, pupil, gaze):
    """Where the camera ray through this pixel meets the pupil plane after refraction at the cornea."""
    o, d = _camera_ray(pixel)
    oc = o - centre
    b = oc @ d
    disc = b * b - (oc @ oc - radius * radius)
    if disc < 0:
        return None
    s = o + (-b - math.sqrt(disc)) * d
    n = (s - centre) / radius
    eta, cos_i = 1.0 / CORNEA_IOR, -(n @ d)
    t = eta * d + (eta * cos_i - math.sqrt(1 - eta * eta * (1 - cos_i * cos_i))) * n
    return s + ((pupil - s) @ gaze) / (t @ gaze) * t


def _refracted_pixel(head, side, pupil, gaze, start):
    """Pixel whose refracted camera ray passes through the pupil centre (Gauss-Newton from the straight projection)."""
    centre, radius = _cornea_sphere(head, side)
    px = np.array(start, float)
    for _ in range(12):
        q = _through_cornea(px, centre, radius, pupil, gaze)
        if q is None:
            return None
        jac = np.stack([(_through_cornea(px + e, centre, radius, pupil, gaze) - q) for e in np.eye(2) * 0.25], 1) / 0.25
        step = np.linalg.lstsq(jac, pupil - q, rcond=None)[0]
        px += step
        if np.abs(step).max() < 1e-3:
            break
    return px


def pose():
    """Measured state of both eyes: rotation in the world frame and where each pupil appears in the image."""
    head, arm = _rig()
    sc = bpy.context.scene
    res = sc.render.resolution_x, sc.render.resolution_y
    out = {}
    for tag, side in SIDES.items():
        bone = arm.pose.bones[f"{side}_eye"]
        turn = (arm.matrix_world @ bone.matrix).to_3x3() @ (arm.matrix_world @ bone.bone.matrix_local).to_3x3().inverted()
        out[f"eye_rotation_{tag}"] = [round(math.degrees(a), 4) for a in turn.to_euler("XYZ")]
        world = arm.matrix_world @ bone.matrix
        pupil = world @ Vector((0, PUPIL_DEPTH, 0))  # the bone's Y axis is the gaze
        gaze = np.array((world.to_3x3() @ Vector((0, 1, 0))).normalized())
        ndc = world_to_camera_view(sc, sc.camera, pupil)
        straight = [ndc.x * res[0], (1 - ndc.y) * res[1]]
        seen = _refracted_pixel(head, side, np.array(pupil), gaze, straight)
        out[f"pupil_center_2D_{tag}"] = [round(float(c), 2) for c in (straight if seen is None else seen)]
        out[f"pupil_center_2D_unrefracted_{tag}"] = [round(c, 2) for c in straight]
    return out


def find_pupil(png, near, radius=48):
    """Pupil centre found in a rendered PNG: centroid of the darkest blob within `radius` px of `near`.
    Plain numpy on the pixels, no labels used, so it checks the image independently of pose().
    The 0.02 threshold was fixed on four 8-sample test poses (not the launch frames) and then frozen."""
    img = bpy.data.images.load(str(png), check_existing=False)
    w, h = img.size
    rgb = np.array(img.pixels[:]).reshape(h, w, 4)[::-1, :, :3]  # Blender stores rows bottom-up
    bpy.data.images.remove(img)
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722])
    cx, cy = int(round(near[0])), int(round(near[1]))
    y0, x0 = max(cy - radius, 0), max(cx - radius, 0)
    roi = lum[y0:cy + radius, x0:cx + radius]
    yy, xx = np.mgrid[:roi.shape[0], :roi.shape[1]]
    inside = (xx + x0 - cx) ** 2 + (yy + y0 - cy) ** 2 <= radius ** 2
    dark = inside & (roi < roi[inside].min() + 0.02 * (np.median(roi[inside]) - roi[inside].min()))
    seed = np.unravel_index(np.where(dark, -np.hypot(xx + x0 - cx, yy + y0 - cy), -np.inf).argmax(), roi.shape)
    blob = np.zeros_like(dark)
    blob[seed] = True
    while True:  # grow the blob through dark neighbours (4-connected)
        grown = blob.copy()
        grown[1:] |= blob[:-1]; grown[:-1] |= blob[1:]; grown[:, 1:] |= blob[:, :-1]; grown[:, :-1] |= blob[:, 1:]
        grown &= dark
        if (grown == blob).all():
            break
        blob = grown
    ys, xs = np.nonzero(blob)
    return [float(xs.mean() + x0), float(ys.mean() + y0)], int(blob.sum())


def camera_matrix():
    """3x3 pinhole intrinsics in pixels and the 4x4 camera-to-world pose."""
    sc = bpy.context.scene
    cam = sc.camera
    f = cam.data.lens / cam.data.sensor_width * sc.render.resolution_x
    cx, cy = sc.render.resolution_x / 2, sc.render.resolution_y / 2
    return {"intrinsics": [[f, 0, cx], [0, f, cy], [0, 0, 1]], "camera_to_world": [list(map(float, row)) for row in cam.matrix_world]}


DIRECTIONS = {"Left": (-1, 0, 0, -1), "Right": (1, 0, 0, 1), "Up": (0, 1, 1, -1), "Down": (0, -1, 1, 1)}
MIN_SHIFT = 3.0  # px the found pupil must move the right way


def _found(png):
    """Pupils found in one render, searched around where the straight (unrefracted) projection puts them."""
    now = pose()
    return {t: find_pupil(png, now[f"pupil_center_2D_unrefracted_{t}"])[0] for t in SIDES}


def direction_check(out_dir=None):
    """Left, Right, Up, Down and Reset, judged from the rendered pixels: each pose is rendered and the
    pupils are found in the image (find_pupil), then compared with the straight-ahead render."""
    out_dir = Path(out_dir or tempfile.mkdtemp())
    reset()
    rest = _found(render(out_dir / "rest.png"))
    results, shifts = {}, {}
    for name, (h, v, axis, sign) in DIRECTIONS.items():
        move(h, v)
        now = _found(render(out_dir / f"{name.lower()}.png"))
        shifts[name] = {t: round(now[t][axis] - rest[t][axis], 2) for t in SIDES}
        results[name] = all(sign * shifts[name][t] > MIN_SHIFT for t in SIDES)
    reset()
    back = _found(render(out_dir / "reset.png"))
    shifts["Reset"] = {t: round(math.dist(back[t], rest[t]), 2) for t in SIDES}
    results["Reset"] = all(d < 1.0 for d in shifts["Reset"].values())
    return results, shifts


def sequence(out_dir):
    """The 10 clockwise renders starting at the top, metadata.json and scene.blend."""
    out_dir = Path(out_dir)
    frames, errors = [], {"refracted": [], "unrefracted": []}
    for k in range(10):
        theta = 2 * math.pi * k / 10
        h, v = math.sin(theta), math.cos(theta)
        move(h, v)
        png = render(out_dir / "renders" / f"frame_{k:02d}.png")
        now = pose()
        found = {t: find_pupil(png, now[f"pupil_center_2D_unrefracted_{t}"])[0] for t in SIDES}
        for t in SIDES:
            now[f"pupil_center_2D_found_{t}"] = [round(c, 2) for c in found[t]]
            errors["refracted"].append(math.dist(found[t], now[f"pupil_center_2D_{t}"]))
            errors["unrefracted"].append(math.dist(found[t], now[f"pupil_center_2D_unrefracted_{t}"]))
        frames.append({"frame": k, "theta": theta, "input": {"h": h, "v": v}, **now, "camera_matrix": camera_matrix()})
    check, shifts = direction_check(out_dir / "direction_check")
    meta = {"units": {"eye_rotation": "degrees, XYZ Euler in the world frame (X right, Y away from camera, Z up), relative to straight ahead",
                      "pupil_center_2D": "pixels, origin top-left of the 1024x1024 render; where the pupil centre appears, refracted by the cornea",
                      "pupil_center_2D_unrefracted": "pixels, straight pinhole projection of the 3D pupil centre (no cornea)",
                      "pupil_center_2D_found": "pixels, pupil centre found in the rendered PNG by find_pupil (no labels used)",
                      "theta": "radians"},
            "fixation_distance_m": TARGET_DISTANCE, "camera_distance_m": scene.CAMERA_DISTANCE,
            "direction_check": check, "direction_check_shift_px": shifts,
            "label_error_px": {k: {"mean": round(float(np.mean(v)), 2), "max": round(float(np.max(v)), 2)} for k, v in errors.items()},
            "frames": frames}
    (out_dir / "metadata.json").write_text(json.dumps(meta, indent=1))
    reset()
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str((out_dir / "scene.blend").resolve()), compress=True)
    return meta


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if args[:1] == ["--sequence"]:
        meta = sequence(args[1] if len(args) > 1 else ROOT / "outputs" / "launch_spec")
        print("direction check:", meta["direction_check"], meta["direction_check_shift_px"])
        print("label error px:", meta["label_error_px"])
        assert all(meta["direction_check"].values()), "direction check failed"
    elif args[:1] == ["--check"]:
        result, shifts = direction_check(args[1] if len(args) > 1 else None)
        print("direction check:", result, shifts)
        assert all(result.values()), "direction check failed"
