"""Exports the textured GNM head, its rig and its shape keys to a glTF binary for the browser / WebXR demo.

    blender --background --python tools/export_web.py -- [set]   # -> docs/xr/head.glb (default set 01)

The Cycles materials do not survive glTF, so each UDIM tile gets a plain material with its own texture
(downscaled to 2K); the browser page adds the cornea, sheen and lighting itself. Shape keys become morph
targets with the same names, so the page drives blink, lid, brow, bulge and drag keys exactly as render.py does.
The facial down (fuzz) strands are left out to keep the file small.
"""
import sys
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from truegaze import scene  # noqa: E402
from truegaze.gnm import GNM  # noqa: E402
from truegaze.motion import PUPIL_REST  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
SET = args[0] if args else "01"
OUT = ROOT / "docs" / "xr" / "head.glb"
TEX = ROOT / "textures" / SET


def material(name, color=(0.8, 0.8, 0.8), image=None, roughness=0.5, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = roughness
    if image:
        img = bpy.data.images.load(str(image))
        img.scale(min(img.size[0], 2048), min(img.size[1], 2048))
        node = m.node_tree.nodes.new("ShaderNodeTexImage")
        node.image = img
        m.node_tree.links.new(node.outputs["Color"], b.inputs["Base Color"])
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    return m


head, arm = scene.build(SET)
info = __import__("json").loads((TEX / "info.json").read_text())

# head: one plain material per UDIM tile (glTF wraps UVs, so tile 1002 reads its own image)
mats = {1001: material("skin", image=TEX / "color.1001.jpg", roughness=0.55),
        1002: material("eye_left", image=TEX / "color.1002.jpg", roughness=0.4),
        1003: material("cornea", color=(1, 1, 1), roughness=0.0, alpha=0.05),
        1004: material("eye_right", image=TEX / "color.1004.jpg", roughness=0.4),
        1006: material("teeth", (0.85, 0.82, 0.75), roughness=0.3),
        1007: material("tongue", (0.7, 0.3, 0.3), roughness=0.4)}
mats[1005] = mats[1003]
mesh = head.data
mesh.materials.clear()
order = [1001, 1002, 1003, 1004, 1006, 1007]
for t in order:
    mesh.materials.append(mats[t])
slot = {t: order.index(t) for t in order} | {1005: order.index(1003)}
mesh.polygons.foreach_set("material_index", [slot[int(t)] for t in GNM().quad_tiles()])

# hair: drop the fuzz strands (material 2), plain materials for lashes/brows, tear line and inner corner
hair = bpy.data.objects["Hair"]
for key in hair.data.shape_keys.key_blocks:
    key.driver_remove("value")
bm = bmesh.new()
bm.from_mesh(hair.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index == 2], context="FACES")
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
bm.to_mesh(hair.data)
bm.free()
hair.data.materials.clear()
for m in (material("lashes", tuple(info["hair"]), roughness=0.45), material("tear", (1, 1, 1), roughness=0.0, alpha=0.15),
          material("fuzz_unused"), material("caruncle", (0.85, 0.45, 0.45), roughness=0.3)):
    hair.data.materials.append(m)

# rest pose: socket on, pupil at rest, everything else off
for key in head.data.shape_keys.key_blocks[1:]:
    key.value = 1.0 if key.name.startswith("socket") else (PUPIL_REST if key.name == "pupil" else 0.0)
head.modifiers.remove(head.modifiers["WrinklesProxy"]) if "WrinklesProxy" in head.modifiers else None

bpy.ops.object.select_all(action="DESELECT")
for obj in (head, hair, arm):
    obj.select_set(True)
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", use_selection=True, export_apply=False,
                          export_morph=True, export_morph_normal=False, export_skins=True, export_animations=False,
                          export_image_format="JPEG", export_jpeg_quality=85, export_yup=True)
print(f"WROTE {OUT} {OUT.stat().st_size / 1e6:.1f} MB")
