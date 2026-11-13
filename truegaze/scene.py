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
from .motion import PUPIL_REST, soft_tissue

ROOT = Path(__file__).resolve().parent.parent
CAMERA_DISTANCE = 0.40  # m in front of the eye midpoint (launch spec)


def _hair(head, arm, texture_set):
    """Lashes, brows and tear line from assets/hair.npz. Its shape keys copy the head's through drivers."""
    d = np.load(ROOT / "assets" / "hair.npz")
    mesh = bpy.data.meshes.new("hair")
    mesh.from_pydata(to_blender(d["verts"]).tolist(), [], d["quads"].tolist())
    mesh.materials.append(materials.hair(texture_set))
    mesh.materials.append(bpy.data.materials["cornea"])  # the tear line is the same clear wet material
    mesh.materials.append(materials.fuzz(texture_set))
    mesh.materials.append(materials.caruncle())
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
    soft = np.load(ROOT / "assets" / "bulge.npz")  # socket depth, lid bulge over the cornea, skin drag (tools/fit_bulge.py)
    for name in (k for k in soft.files if k != "index"):
        moved = m.template.copy()
        moved[soft["index"]] += soft[name]
        key = head.shape_key_add(name=name)
        key.data.foreach_set("co", to_blender(moved).ravel())
        key.value = 1.0 if name.startswith("socket") else 0.0  # the socket shape is always on
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
    materials.drive_wrinkles(head)

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
    for name, loc, energy, size in [("key", (0.32, -0.38, 0.30), 6, 0.30), ("fill", (-0.45, -0.40, 0.0), 1.2, 0.8)]:
        light = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA"))
        light.data.energy, light.data.size = energy, size
        light.location = eye_mid + Vector(loc)
        light.rotation_euler = (eye_mid - light.location).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(light)
    materials.set_key_direction(Vector((0.32, -0.38, 0.30)).normalized())  # the key light above; the iris shader needs it
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


def hero_view(arm, side="left"):
    """Close shot of one eye in the style of the reference video: camera 55 degrees round to the eye's
    outer side and a little below, hard light raking in from behind the cheek, shallow focus."""
    bpy.context.scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    sc = bpy.context.scene
    sign = 1 if side == "left" else -1
    eye = arm.matrix_world @ arm.pose.bones[f"{side}_eye"].head + Vector((0, -0.012, 0))  # front of the cornea
    angle = math.radians(66)
    cam = sc.camera
    cam.location = eye + Vector((sign * math.sin(angle), -math.cos(angle), -0.06)) * CAMERA_DISTANCE
    cam.rotation_euler = (eye - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 270
    cam.data.dof.use_dof, cam.data.dof.focus_distance, cam.data.dof.aperture_fstop = True, (eye - cam.location).length, 45
    for name, offset, energy, size in (("key", (sign * 0.52, -0.16, 0.20), 4, 0.10), ("fill", (-sign * 0.15, -0.50, -0.05), 0.12, 0.8)):
        light = bpy.data.objects[name]
        light.location = eye + Vector(offset)
        light.rotation_euler = (eye - light.location).to_track_quat("-Z", "Y").to_euler()
        light.data.energy, light.data.size = energy, size
    materials.set_key_direction((bpy.data.objects["key"].location - eye).normalized())
    # a dim softbox beside the camera: it adds little light, its reflection is the window highlight on the cornea
    catch = bpy.data.objects.new("catch", bpy.data.lights.new("catch", "AREA"))
    catch.data.energy, catch.data.size = 0.5, 0.35
    catch.location = cam.location + Vector((-sign * 0.10, 0.0, 0.22))
    catch.rotation_euler = (eye - catch.location).to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(catch)


def breakdown(head, arm, wire=True):
    """Making-of look: grey clay instead of textures and, with wire, the mesh's own quad edges drawn on top.
    The textured materials stay on the mesh data; only this scene's objects are overridden."""
    grey = materials.clay()
    for slot in head.material_slots:
        if slot.material.name != "cornea":
            slot.link = "OBJECT"
            slot.material = grey
    if not wire:
        return
    lines = bpy.data.objects.new("HeadWire", head.data)  # same mesh data, so it follows every shape key
    bpy.context.scene.collection.objects.link(lines)
    lines.parent = arm
    lines.modifiers.new("rig", "ARMATURE").object = arm
    mod = lines.modifiers.new("wire", "WIREFRAME")
    mod.thickness, mod.use_replace = 0.00013, True
    dark = bpy.data.materials.get("wire") or materials._flat("wire", (0.01, 0.01, 0.012), 0.8)
    for slot in lines.material_slots:
        slot.link = "OBJECT"
        slot.material = dark


def set_gaze(arm, side, yaw_deg, pitch_deg):
    """Rotates one eyeball about its centre. yaw > 0 turns toward the character's left (+X), pitch > 0 up."""
    bone = arm.pose.bones[f"{side}_eye"]
    rest = bone.bone.matrix_local
    turn = Matrix.Rotation(math.radians(yaw_deg), 4, "Z") @ Matrix.Rotation(-math.radians(pitch_deg), 4, "X")
    pivot = Matrix.Translation(rest.to_translation())
    # shortcut: assumes neck and head are at rest, switch to parent-relative maths when the head moves
    bone.matrix = pivot @ turn @ pivot.inverted() @ rest


def pose_eye(head, arm, side, yaw_deg, pitch_deg):
    """Turns one eye and sets what depends only on its gaze: lid bulge over the cornea and skin drag."""
    set_gaze(arm, side, yaw_deg, pitch_deg)
    keys = head.data.shape_keys.key_blocks
    for name, value in soft_tissue(side, yaw_deg, pitch_deg).items():
        keys[name].value = value
    return keys
