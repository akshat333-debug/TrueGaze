"""Renders still images of texture sets: a front view of both eyes, a close side view of one eye,
and a hero shot in the style of the reference video (dark studio, raking light, shallow focus).

  Blender --background --python tools/stills.py -- 01 02      (default: every set in textures/)
  add --samples 32 for a quick look, --style clay|wire for making-of looks. Output: outputs/renders/<set>_front.png, <set>_close.png, <set>_hero.png
"""
import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from truegaze import scene  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("sets", nargs="*", default=sorted(p.name for p in (ROOT / "textures").iterdir() if p.is_dir()))
ap.add_argument("--samples", type=int, default=128)
ap.add_argument("--style", default="textured", choices=["textured", "clay", "wire"])
ap.add_argument("--out", default=str(ROOT / "outputs" / "renders"))
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

for name in a.sets:
    head, arm = scene.build(name)
    if a.style != "textured":
        scene.breakdown(head, arm, wire=a.style == "wire")
    name += "" if a.style == "textured" else f"_{a.style}"
    sc = bpy.context.scene
    sc.cycles.samples = a.samples
    cam = sc.camera
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    cam.data.lens = 130  # both eyes and brows from the 40 cm camera
    sc.render.filepath = str(Path(a.out) / f"{name}_front.png")
    bpy.ops.render.render(write_still=True)

    # close view of the character's left eye, camera swung 35 degrees to its side, still 40 cm away
    eye = arm.matrix_world @ arm.pose.bones["left_eye"].head
    angle = math.radians(35)
    cam.location = eye + Vector((math.sin(angle), -math.cos(angle), 0.08)) * scene.CAMERA_DISTANCE
    cam.rotation_euler = (eye - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 300
    sc.render.filepath = str(Path(a.out) / f"{name}_close.png")
    bpy.ops.render.render(write_still=True)

    # hero: the reference video's shot, the eye turned part-way toward a camera at its outer side
    scene.hero_view(arm)
    for side in ("left", "right"):
        scene.pose_eye(head, arm, side, 22, 4)
    sc.render.filepath = str(Path(a.out) / f"{name}_hero.png")
    bpy.ops.render.render(write_still=True)
