"""Builds the Blender scene from GNM weights: mesh, UDIM UVs, shape keys, armature, camera, lights.

Blender frame: character faces -Y, up is +Z, the character's left is +X (screen right).
"""
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

from . import materials
from .gnm import GNM, PUPIL, to_blender
from .motion import PUPIL_REST

ROOT = Path(__file__).resolve().parent.parent
CAMERA_DISTANCE = 0.40  # m in front of the eye midpoint (launch spec)


def _hair(head, arm, texture_set):
    """Lashes, brows and tear line from assets/hair.npz. Its shape keys copy the head's through drivers."""
    d = np.load(ROOT / "assets" / "hair.npz")
    mesh = bpy.data.meshes.new("hair")
    mesh.from_pydata(to_blender(d["verts"]).tolist(), [], d["quads"].tolist())
    mesh.materials.append(materials.hair(texture_set))
    mesh.materials.append(bpy.data.materials["cornea"])  # the tear line is the same clear wet material
    mesh.polygons.foreach_set("material_index", d["material"].astype(int).tolist())
    mesh.polygons.foreach_set("use_smooth", [True] * len(d["quads"]))
    obj = bpy.data.objects.new("Hair", mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.shape_key_add(name="Basis")
    for name in (k[5:] for k in d.files if k.startswith("move_")):
        key = obj.shape_key_add(name=name)
        key.slider_min = -1.0
        key.data.foreach_set("co", to_blender(d["verts"] + d[f"move_{name}"]).ravel())
        driver = key.driver_add("value").driver
        driver.type = "AVERAGE"  # plain copy, no Python, so the .blend opens without a script warning
        target = driver.variables.new().targets[0]
        target.id_type, target.id = "KEY", head.data.shape_keys
        target.data_path = f'key_blocks["{name}"].value'
    obj.parent = arm  # shortcut: assumes neck and head bones stay at rest, skin it to the head bone when the head moves
    return obj


def build(texture_set="01", controls_path=ROOT / "assets" / "controls.npz"):
    """Clears the file and builds head, rig, camera and lights. Returns (head object, armature object)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    m = GNM()

    mesh = bpy.data.meshes.new("gnm_head")
    mesh.from_pydata(to_blender(m.template).tolist(), [], m.quads.tolist())
    uv = mesh.uv_layers.new(name="UDIM")
    offsets = (m.quad_tiles() - 1001)[:, None, None] * np.array([1.0, 0.0])
    uv.data.foreach_set("uv", (m.quad_uvs + offsets).ravel())
    materials.assign(mesh, m.quad_tiles(), texture_set)
    mesh.polygons.foreach_set("use_smooth", [True] * len(m.quads))
    head = bpy.data.objects.new("Head", mesh)
    bpy.context.scene.collection.objects.link(head)

    head.shape_key_add(name="Basis")
    for name, coef in np.load(controls_path).items():
        key = head.shape_key_add(name=name)
        key.slider_min = -1.0  # controls are linear, so negative values are valid
        key.data.foreach_set("co", to_blender(m.template + np.tensordot(coef, m.expression_basis, 1)).ravel())
    key = head.shape_key_add(name="pupil")  # GNM's own iris component: positive dilates
    key.slider_min = -2.0
    key.value = PUPIL_REST
    key.data.foreach_set("co", to_blender(m.template + m.expression_basis[PUPIL]).ravel())

    arm_data = bpy.data.armatures.new("rig")
    arm = bpy.data.objects.new("Rig", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    joints = to_blender(m.joints)
    bones = []
    for name, pos, parent in zip(m.joint_names, joints, m.parents):
        bone = arm_data.edit_bones.new(name)
        bone.head = pos
        # eyes point forward along the gaze; neck and head point up
        bone.tail = Vector(pos) + (Vector((0, -0.02, 0)) if "eye" in name else Vector((0, 0, 0.03)))
        if parent >= 0:
            bone.parent = bones[parent]
        bones.append(bone)
    bpy.ops.object.mode_set(mode="OBJECT")
    for name, weights in zip(m.joint_names, m.weights):
        group = head.vertex_groups.new(name=name)
        for w in np.unique(weights[weights > 0]):
            group.add(np.flatnonzero(weights == w).tolist(), float(w), "REPLACE")
    head.modifiers.new("rig", "ARMATURE").object = arm
    head.parent = arm
    _hair(head, arm, texture_set)

    eye_mid = Vector(joints[2:4].mean(axis=0))
    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    cam.location = eye_mid + Vector((0, -CAMERA_DISTANCE, 0))
    cam.rotation_euler = (math.pi / 2, 0, 0)
    cam.data.lens = 85
    scene = bpy.context.scene
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene["eye_mid"] = eye_mid

    # dark studio: one softbox key from the side and above (its reflection is the eye highlight), weak fill
    for name, loc, energy, size in [("key", (0.32, -0.38, 0.30), 6, 0.30), ("fill", (-0.45, -0.40, 0.0), 0.5, 0.8)]:
        light = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA"))
        light.data.energy, light.data.size = energy, size
        light.location = eye_mid + Vector(loc)
        light.rotation_euler = (eye_mid - light.location).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(light)
    world = bpy.data.worlds.new("world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.01, 0.01, 0.012, 1)
    scene.world = world

    scene.render.engine = "CYCLES"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.resolution_x = scene.render.resolution_y = 1024
    scene.cycles.samples = 48
    scene.cycles.use_denoising = True
    prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for device in prefs.devices:
            device.use = True
        scene.cycles.device = "GPU"
    except TypeError:  # no Metal on this machine (Linux/Docker): stay on CPU
        scene.cycles.device = "CPU"
    return head, arm


def set_gaze(arm, side, yaw_deg, pitch_deg):
    """Rotates one eyeball about its centre. yaw > 0 turns toward the character's left (+X), pitch > 0 up."""
    bone = arm.pose.bones[f"{side}_eye"]
    rest = bone.bone.matrix_local
    turn = Matrix.Rotation(math.radians(yaw_deg), 4, "Z") @ Matrix.Rotation(-math.radians(pitch_deg), 4, "X")
    pivot = Matrix.Translation(rest.to_translation())
    # shortcut: assumes neck and head are at rest, switch to parent-relative maths when the head moves
    bone.matrix = pivot @ turn @ pivot.inverted() @ rest
