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
    # expression wrinkles: a second height map, revealed by how far the brows are raised and the eyes squeezed.
    # The two Value nodes are driven by the head's shape keys (see drive_wrinkles).
    new, link = nt.nodes.new, nt.links.new
    lines, split = _image(nt, folder / "wrinkle.1001.jpg", data=True), new("ShaderNodeSeparateColor")
    link(lines.outputs["Color"], split.inputs["Color"])
    total = _image(nt, folder / "height.1001.jpg", data=True).outputs["Color"]
    for channel, name in (("Red", "wrinkle_brow"), ("Green", "wrinkle_squint")):
        amount, scaled, minus = new("ShaderNodeValue"), new("ShaderNodeMath"), new("ShaderNodeMath")
        amount.name = name
        scaled.operation, minus.operation = "MULTIPLY", "SUBTRACT"
        link(split.outputs[channel], scaled.inputs[0])
        link(amount.outputs[0], scaled.inputs[1])
        link(total, minus.inputs[0])
        link(scaled.outputs[0], minus.inputs[1])
        total = minus.outputs[0]
    link(total, bump.inputs["Height"])
    # relief finer than the texture can hold: breaks highlights into the pin-point glints of real skin
    grain, micro = nt.nodes.new("ShaderNodeTexVoronoi"), nt.nodes.new("ShaderNodeBump")  # cells, like skin's own micro-pattern
    grain.inputs["Scale"].default_value = 3500
    micro.inputs["Strength"].default_value = 0.35
    micro.inputs["Distance"].default_value = 0.00008
    nt.links.new(nt.nodes.new("ShaderNodeTexCoord").outputs["Object"], grain.inputs["Vector"])
    nt.links.new(grain.outputs["Distance"], micro.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], micro.inputs["Normal"])
    nt.links.new(micro.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Coat Weight"].default_value = 0.12   # thin oil film: a second, sharper highlight
    bsdf.inputs["Coat Roughness"].default_value = 0.28
    nt.links.new(micro.outputs["Normal"], bsdf.inputs["Coat Normal"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.3
    bsdf.subsurface_method = "RANDOM_WALK_SKIN"
    bsdf.inputs["Subsurface Weight"].default_value = 0.24
    bsdf.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.2)
    bsdf.inputs["Subsurface Scale"].default_value = 0.004
    return mat


def eye(folder, tile):
    """Sclera, iris and pupil of one eye. Matte: the shine comes from the clear shell on top."""
    mat, nt, bsdf = _principled(f"eye_{tile}")
    picture = _image(nt, folder / f"color.{tile}.jpg")
    bsdf.inputs["Roughness"].default_value = 0.5
    bsdf.subsurface_method = "BURLEY"  # random-walk scattering leaves a grey outline at the iris edge
    # Light pooling. The cornea is a lens: light arriving from one side is gathered onto the far side of
    # the iris as a bright crescent. Path tracing finds this only with very many samples, so it is computed
    # here instead: for each point of the iris, how far it lies on the side away from the key light.
    new, link = nt.nodes.new, nt.links.new

    def vec(operation, a, b=None):
        node = new("ShaderNodeVectorMath")
        node.operation = operation
        link(a, node.inputs[0]) if hasattr(a, "node") else setattr(node.inputs[0], "default_value", a)
        if b is not None:
            link(b, node.inputs[1]) if hasattr(b, "node") else setattr(node.inputs[1], "default_value", b)
        return node.outputs["Value" if operation in ("DOT_PRODUCT", "LENGTH") else "Vector"]

    def num(operation, a, b):
        node = new("ShaderNodeMath")
        node.operation = operation
        for socket, value in zip(node.inputs, (a, b)):
            link(value, socket) if hasattr(value, "node") else setattr(socket, "default_value", value)
        return node.outputs[0]

    def ramp(value, low, high):
        node = new("ShaderNodeMapRange")
        node.interpolation_type = "SMOOTHSTEP"
        node.inputs["From Min"].default_value, node.inputs["From Max"].default_value = low, high
        link(value, node.inputs["Value"])
        return node.outputs["Result"]

    uv, tangent, light = new("ShaderNodeUVMap"), new("ShaderNodeTangent"), new("ShaderNodeCombineXYZ")
    tangent.direction_type, tangent.uv_map = "UV_MAP", "UDIM"
    light.name = "key_direction"  # unit vector from the eyes to the key light, set by set_key_direction
    place = vec("SUBTRACT", vec("FRACTION", uv.outputs["UV"]), (0.5, 0.5, 0.0))       # position on the iris, tile centre = pupil
    across = tangent.outputs["Tangent"]                                             # where +u points in the world
    upward = vec("CROSS_PRODUCT", new("ShaderNodeNewGeometry").outputs["Normal"], across)  # where +v points
    flat, radius = new("ShaderNodeCombineXYZ"), vec("LENGTH", place)
    link(vec("DOT_PRODUCT", light.outputs[0], across), flat.inputs[0])
    link(vec("DOT_PRODUCT", light.outputs[0], upward), flat.inputs[1])
    away = num("DIVIDE", num("MULTIPLY", vec("DOT_PRODUCT", place, flat.outputs[0]), -1.0), radius)  # 0..1: far side, light from the side
    crescent = num("MULTIPLY", num("MULTIPLY", ramp(away, 0.10, 0.75), ramp(radius, 0.075, 0.15)), num("SUBTRACT", 1.0, ramp(radius, 0.165, 0.19)))
    glow = new("ShaderNodeVectorMath")
    glow.operation = "SCALE"
    link(picture.outputs["Color"], glow.inputs[0])
    link(num("ADD", 1.0, num("MULTIPLY", crescent, 2.6)), glow.inputs["Scale"])
    link(glow.outputs["Vector"], bsdf.inputs["Base Color"])
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


def fuzz(texture_set):
    """Vellus hair: the fine pale down on facial skin that catches light at the edge of the face."""
    mat = bpy.data.materials.new("fuzz")
    mat.use_nodes = True
    mat.surface_render_method = "BLENDED"
    nt = mat.node_tree
    bsdf, clear, mix = nt.nodes["Principled BSDF"], nt.nodes.new("ShaderNodeBsdfTransparent"), nt.nodes.new("ShaderNodeMixShader")
    info = json.loads((ROOT / "textures" / texture_set / "info.json").read_text())
    bsdf.inputs["Base Color"].default_value = (*info.get("fuzz", (0.55, 0.42, 0.33)), 1)
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


def set_key_direction(direction):
    """Tells the eye shaders where the key light is (unit vector from the eyes to the light, world space)."""
    for mat in bpy.data.materials:
        node = mat.node_tree.nodes.get("key_direction") if mat.use_nodes else None
        if node:
            for socket, value in zip(node.inputs, direction):
                socket.default_value = value


def drive_wrinkles(head):
    """Expression wrinkles follow the face: forehead lines with the brow raise, crow's feet with lid closure.
    Plain averaging drivers (no Python), so they also work when the saved .blend is opened."""
    tree = bpy.data.materials["skin"].node_tree
    for node, keys in (("wrinkle_brow", ("brow_raise_left", "brow_raise_right")), ("wrinkle_squint", ("blink_left", "blink_right"))):
        driver = tree.driver_add(f'nodes["{node}"].outputs[0].default_value').driver
        driver.type = "AVERAGE"
        for key in keys:
            target = driver.variables.new().targets[0]
            target.id_type, target.id = "KEY", head.data.shape_keys
            target.data_path = f'key_blocks["{key}"].value'


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
