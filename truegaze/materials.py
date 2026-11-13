"""Shaders for the GNM head. One material per UDIM tile, reading a texture set from textures/<name>/."""
import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent.parent
CORNEA_IOR = 1.376


def _image(nt, path, data=False):
    node = nt.nodes.new("ShaderNodeTexImage")
    node.image = bpy.data.images.load(str(path), check_existing=True)
    if data:
        node.image.colorspace_settings.name = "Non-Color"
    return node


def _principled(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    return mat, mat.node_tree, mat.node_tree.nodes["Principled BSDF"]


def skin(folder):
    mat, nt, bsdf = _principled("skin")
    nt.links.new(_image(nt, folder / "color.1001.jpg").outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(_image(nt, folder / "roughness.1001.jpg", data=True).outputs["Color"], bsdf.inputs["Roughness"])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.5
    bump.inputs["Distance"].default_value = 0.0006  # m: pores are a fraction of a millimetre deep
    nt.links.new(_image(nt, folder / "height.1001.jpg", data=True).outputs["Color"], bump.inputs["Height"])
    # relief finer than the texture can hold: breaks highlights into the pin-point glints of real skin
    grain, micro = nt.nodes.new("ShaderNodeTexNoise"), nt.nodes.new("ShaderNodeBump")
    grain.inputs["Scale"].default_value = 9000
    micro.inputs["Strength"].default_value = 0.35
    micro.inputs["Distance"].default_value = 0.00008
    nt.links.new(nt.nodes.new("ShaderNodeTexCoord").outputs["Object"], grain.inputs["Vector"])
    nt.links.new(grain.outputs["Fac"], micro.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], micro.inputs["Normal"])
    nt.links.new(micro.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Coat Weight"].default_value = 0.12   # thin oil film: a second, sharper highlight
    bsdf.inputs["Coat Roughness"].default_value = 0.28
    nt.links.new(micro.outputs["Normal"], bsdf.inputs["Coat Normal"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.3
    bsdf.inputs["Subsurface Weight"].default_value = 0.24
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    bsdf.inputs["Subsurface Scale"].default_value = 0.004
    return mat


def eye(folder, tile):
    """Sclera, iris and pupil of one eye. Matte: the shine comes from the clear shell on top."""
    mat, nt, bsdf = _principled(f"eye_{tile}")
    nt.links.new(_image(nt, folder / f"color.{tile}.jpg").outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.5
    bsdf.inputs["Specular IOR Level"].default_value = 0.0
    relief = nt.nodes.new("ShaderNodeBump")  # iris fibres stand up and crypts sink: the picture doubles as its height
    relief.inputs["Strength"].default_value = 0.5
    relief.inputs["Distance"].default_value = 0.0003
    nt.links.new(nt.nodes["Image Texture"].outputs["Color"], relief.inputs["Height"])
    nt.links.new(relief.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Subsurface Weight"].default_value = 0.25  # the white of the eye glows a little, it is not paint
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.6, 0.5)
    bsdf.inputs["Subsurface Scale"].default_value = 0.0015
    return mat


def cornea():
    """Clear wet shell over the whole eyeball. Cycles refracts through it (the iris looks deeper and
    shifts with view angle); EEVEE gets reflections only, because its refraction rendered black."""
    mat = bpy.data.materials.new("cornea")
    mat.use_nodes = True
    mat.surface_render_method = "BLENDED"
    nt = mat.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    new, link = nt.nodes.new, nt.links.new
    clear = new("ShaderNodeBsdfTransparent")

    fresnel, gloss, eevee_mix = new("ShaderNodeFresnel"), new("ShaderNodeBsdfGlossy"), new("ShaderNodeMixShader")
    fresnel.inputs["IOR"].default_value = CORNEA_IOR
    gloss.inputs["Roughness"].default_value = 0.02
    link(fresnel.outputs["Fac"], eevee_mix.inputs["Fac"])
    link(clear.outputs["BSDF"], eevee_mix.inputs[1])
    link(gloss.outputs["BSDF"], eevee_mix.inputs[2])
    out = nt.nodes["Material Output"]
    out.target = "EEVEE"
    link(eevee_mix.outputs["Shader"], out.inputs["Surface"])

    glass, path, cycles_mix, out2 = new("ShaderNodeBsdfGlass"), new("ShaderNodeLightPath"), new("ShaderNodeMixShader"), new("ShaderNodeOutputMaterial")
    glass.inputs["IOR"].default_value = CORNEA_IOR
    glass.inputs["Roughness"].default_value = 0.0
    # the wet skin over the white of the eye is slightly uneven, so its highlights wobble; the cornea stays smooth
    uv, radius = new("ShaderNodeUVMap"), new("ShaderNodeVectorMath")
    fract, centre, ramp = new("ShaderNodeVectorMath"), new("ShaderNodeVectorMath"), new("ShaderNodeMapRange")
    fract.operation, centre.operation, radius.operation = "FRACTION", "SUBTRACT", "LENGTH"
    centre.inputs[1].default_value = (0.5, 0.5, 0.0)
    ramp.inputs["From Min"].default_value, ramp.inputs["From Max"].default_value = 0.15, 0.22  # cornea ends at 0.155 in this tile
    ramp.inputs["To Max"].default_value = 0.12
    lumps, wobble = new("ShaderNodeTexNoise"), new("ShaderNodeBump")
    lumps.inputs["Scale"].default_value = 350
    wobble.inputs["Distance"].default_value = 0.0003
    link(uv.outputs["UV"], fract.inputs[0])
    link(fract.outputs["Vector"], centre.inputs[0])
    link(centre.outputs["Vector"], radius.inputs[0])
    link(radius.outputs["Value"], ramp.inputs["Value"])
    link(ramp.outputs["Result"], wobble.inputs["Strength"])
    link(new("ShaderNodeTexCoord").outputs["Object"], lumps.inputs["Vector"])
    link(lumps.outputs["Fac"], wobble.inputs["Height"])
    link(wobble.outputs["Normal"], glass.inputs["Normal"])
    link(path.outputs["Is Shadow Ray"], cycles_mix.inputs["Fac"])  # light passes through to the iris
    link(glass.outputs["BSDF"], cycles_mix.inputs[1])
    link(clear.outputs["BSDF"], cycles_mix.inputs[2])
    out2.target = "CYCLES"
    link(cycles_mix.outputs["Shader"], out2.inputs["Surface"])
    return mat


def hair(texture_set):
    """Lash and brow colour comes from the texture set's info.json."""
    color = json.loads((ROOT / "textures" / texture_set / "info.json").read_text())["hair"]
    mat, _, bsdf = _principled("hair")
    bsdf.inputs["Base Color"].default_value = (*[c * 0.55 for c in color], 1)  # hair in bulk looks darker than one strand
    bsdf.inputs["Roughness"].default_value = 0.55
    bsdf.inputs["Specular IOR Level"].default_value = 0.25
    return mat


def fuzz():
    """Vellus hair: the fine pale down on facial skin that catches light at the edge of the face."""
    mat = bpy.data.materials.new("fuzz")
    mat.use_nodes = True
    mat.surface_render_method = "BLENDED"
    nt = mat.node_tree
    bsdf, clear, mix = nt.nodes["Principled BSDF"], nt.nodes.new("ShaderNodeBsdfTransparent"), nt.nodes.new("ShaderNodeMixShader")
    bsdf.inputs["Base Color"].default_value = (0.55, 0.42, 0.33, 1)
    bsdf.inputs["Roughness"].default_value = 0.5
    mix.inputs["Fac"].default_value = 0.22
    nt.links.new(clear.outputs["BSDF"], mix.inputs[1])
    nt.links.new(bsdf.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], nt.nodes["Material Output"].inputs["Surface"])
    return mat


def caruncle():
    """Wet pink tissue in the inner corner of the eye."""
    mat, _, bsdf = _principled("caruncle")
    bsdf.inputs["Base Color"].default_value = (0.62, 0.30, 0.28, 1)
    bsdf.inputs["Roughness"].default_value = 0.22
    bsdf.inputs["Subsurface Weight"].default_value = 0.5
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.3, 0.2)
    bsdf.inputs["Subsurface Scale"].default_value = 0.002
    return mat


def clay():
    """Plain grey, for making-of shots that show shape without texture."""
    return bpy.data.materials.get("clay") or _flat("clay", (0.55, 0.55, 0.55), 0.6)


def _flat(name, color, roughness):
    mat, _, bsdf = _principled(name)
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def assign(mesh, quad_tiles, texture_set):
    """Gives every face the material of its UDIM tile."""
    folder = ROOT / "textures" / texture_set
    if not folder.is_dir():
        raise FileNotFoundError(f"no texture set {folder}; run: python3 -m truegaze.textures {texture_set}")
    shell = cornea()
    by_tile = {1001: skin(folder), 1002: eye(folder, 1002), 1003: shell, 1004: eye(folder, 1004), 1005: shell,
               1006: _flat("teeth", (0.85, 0.82, 0.75), 0.3), 1007: _flat("tongue", (0.70, 0.30, 0.30), 0.4)}
    slots = {}
    for tile, mat in by_tile.items():
        if mat.name not in mesh.materials:
            mesh.materials.append(mat)
        slots[tile] = mesh.materials.find(mat.name)
    mesh.polygons.foreach_set("material_index", [slots[int(t)] for t in quad_tiles])
