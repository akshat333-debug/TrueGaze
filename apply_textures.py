#!/usr/bin/env python3
"""UV portability proof: wraps a texture set onto a stock GNM head taken straight from Google's weights.

Nothing of ours is on the head (no fitted controls, no lashes): only GNM's mesh and GNM's UV layout.
--identity N draws a random face shape from GNM's own identity space, to show a set fits any GNM head.

  Blender --background --python apply_textures.py -- --texture 03 --identity 5 --out proof.png
"""
import argparse
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from truegaze import materials  # noqa: E402
from truegaze.gnm import GNM, to_blender  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--texture", default="01")
ap.add_argument("--identity", type=int, help="seed for a random GNM identity; omit for the template face")
ap.add_argument("--out")
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])

bpy.ops.wm.read_factory_settings(use_empty=True)
m = GNM()
identity = None if a.identity is None else np.random.default_rng(a.identity).normal(0, 1.0, len(m.identity_basis))
verts, joints = m.shape(identity)

mesh = bpy.data.meshes.new("gnm_head")
mesh.from_pydata(to_blender(verts).tolist(), [], m.quads.tolist())
uv = mesh.uv_layers.new(name="UDIM")
uv.data.foreach_set("uv", (m.quad_uvs + (m.quad_tiles() - 1001)[:, None, None] * np.array([1.0, 0.0])).ravel())
mesh.polygons.foreach_set("use_smooth", [True] * len(m.quads))
materials.assign(mesh, m.quad_tiles(), a.texture)
sc = bpy.context.scene
sc.collection.objects.link(bpy.data.objects.new("Head", mesh))

eye_mid = Vector(to_blender(joints)[2:4].mean(axis=0))
cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
cam.location = eye_mid + Vector((0, -0.6, -0.02))
cam.rotation_euler = (math.pi / 2, 0, 0)
cam.data.lens = 85  # whole face
sc.collection.objects.link(cam)
sc.camera = cam
light = bpy.data.objects.new("key", bpy.data.lights.new("key", "AREA"))
light.data.energy, light.data.size = 12, 0.5
light.location = eye_mid + Vector((0.25, -0.5, 0.25))
light.rotation_euler = (eye_mid - light.location).to_track_quat("-Z", "Y").to_euler()
sc.collection.objects.link(light)
sc.world = bpy.data.worlds.new("world")
sc.world.use_nodes = True
sc.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.02, 0.025, 1)

sc.render.engine = "CYCLES"
sc.cycles.samples = 64
sc.render.resolution_x = sc.render.resolution_y = 1024
name = f"portability_{a.texture}" + ("" if a.identity is None else f"_identity{a.identity}")
sc.render.filepath = str(a.out or ROOT / "outputs" / "renders" / f"{name}.png")
bpy.ops.render.render(write_still=True)
print("WROTE", sc.render.filepath)
