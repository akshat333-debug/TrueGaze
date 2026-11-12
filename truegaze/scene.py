"""Builds the Blender scene from GNM weights: mesh, UDIM UVs, shape keys, armature, camera, lights.

Blender frame: character faces -Y, up is +Z, the character's left is +X (screen right).
"""
import math
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

from .gnm import GNM, to_blender

ROOT = Path(__file__).resolve().parent.parent
CAMERA_DISTANCE = 0.40  # m in front of the eye midpoint (launch spec)

# stand-in colours until textures exist: name -> (base colour, roughness)
FLAT = {"skin": ((0.80, 0.56, 0.45), 0.45), "sclera": ((0.92, 0.90, 0.88), 0.25),
        "iris": ((0.30, 0.17, 0.08), 0.4), "pupil": ((0.0, 0.0, 0.0), 0.5),
        "teeth": ((0.85, 0.82, 0.75), 0.3), "tongue": ((0.70, 0.30, 0.30), 0.4)}


def _flat_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*FLAT[name][0], 1)
    bsdf.inputs["Roughness"].default_value = FLAT[name][1]
    if name == "skin":
        bsdf.inputs["Subsurface Weight"].default_value = 0.25
        bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
        bsdf.inputs["Subsurface Scale"].default_value = 0.004
    return mat


def _cornea_material():
    """Clear refractive shell; shadow rays pass through so the iris is not darkened."""
    mat = bpy.data.materials.new("cornea")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.02
    bsdf.inputs["IOR"].default_value = 1.376
    out = nt.nodes["Material Output"]
    mix, clear, path = nt.nodes.new("ShaderNodeMixShader"), nt.nodes.new("ShaderNodeBsdfTransparent"), nt.nodes.new("ShaderNodeLightPath")
    nt.links.new(path.outputs["Is Shadow Ray"], mix.inputs["Fac"])
    nt.links.new(bsdf.outputs["BSDF"], mix.inputs[1])
    nt.links.new(clear.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return mat


def _face_materials(m):
    """Material name of each quad."""
    names = np.full(len(m.quads), "skin", dtype=object)
    for mat, groups in [("cornea", ("eye_exteriors",)), ("sclera", ("scleras",)), ("iris", ("irises",)),
                        ("pupil", ("pupils",)), ("teeth", ("teeth_and_gums",)), ("tongue", ("tongue",))]:
        names[m.group(*groups)[m.quads].all(axis=1)] = mat
    return names


def build(controls_path=ROOT / "assets" / "controls.npz"):
    """Clears the file and builds head, rig, camera and lights. Returns (head object, armature object)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    m = GNM()

    mesh = bpy.data.meshes.new("gnm_head")
    mesh.from_pydata(to_blender(m.template).tolist(), [], m.quads.tolist())
    uv = mesh.uv_layers.new(name="UDIM")
    offsets = (m.quad_tiles() - 1001)[:, None, None] * np.array([1.0, 0.0])
    uv.data.foreach_set("uv", (m.quad_uvs + offsets).ravel())
    face_mats = _face_materials(m)
    order = ["skin", "sclera", "iris", "pupil", "cornea", "teeth", "tongue"]
    for name in order:
        mesh.materials.append(_cornea_material() if name == "cornea" else _flat_material(name))
    mesh.polygons.foreach_set("material_index", [order.index(n) for n in face_mats])
    mesh.polygons.foreach_set("use_smooth", [True] * len(m.quads))
    head = bpy.data.objects.new("Head", mesh)
    bpy.context.scene.collection.objects.link(head)

    head.shape_key_add(name="Basis")
    for name, coef in np.load(controls_path).items():
        key = head.shape_key_add(name=name)
        key.slider_min = -1.0  # controls are linear, so negative values are valid
        key.data.foreach_set("co", to_blender(m.template + np.tensordot(coef, m.expression_basis, 1)).ravel())

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

    eye_mid = Vector(joints[2:4].mean(axis=0))
    cam = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
    cam.location = eye_mid + Vector((0, -CAMERA_DISTANCE, 0))
    cam.rotation_euler = (math.pi / 2, 0, 0)
    cam.data.lens = 85
    scene = bpy.context.scene
    scene.collection.objects.link(cam)
    scene.camera = cam
    scene["eye_mid"] = eye_mid

    for name, loc, energy, size in [("key", (0.35, -0.5, 0.35), 30, 0.4), ("fill", (-0.45, -0.4, 0.05), 8, 0.6)]:
        light = bpy.data.objects.new(name, bpy.data.lights.new(name, "AREA"))
        light.data.energy, light.data.size = energy, size
        light.location = eye_mid + Vector(loc)
        light.rotation_euler = (eye_mid - light.location).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(light)
    world = bpy.data.worlds.new("world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.05, 0.05, 0.055, 1)
    scene.world = world

    scene.render.engine = "CYCLES"
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
