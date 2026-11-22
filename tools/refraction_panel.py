"""Why the eyes read as real: the same close view rendered with the cornea refracting (IOR 1.376) and with
refraction switched off (IOR 1.0: same reflections, no bending). Two steps:

    blender --background --python tools/refraction_panel.py -- [set]   # renders outputs/renders/refraction_{on,off}.png
    python3 tools/refraction_panel.py                                  # joins them into docs/refraction.jpg
"""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "renders"

try:
    import bpy
except ImportError:
    bpy = None

if bpy:
    from mathutils import Vector
    sys.path.insert(0, str(ROOT))
    from truegaze import scene
    from truegaze.materials import CORNEA_IOR

    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    head, arm = scene.build(args[0] if args else "01")
    sc = bpy.context.scene
    sc.cycles.samples = 128
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    for side in ("left", "right"):  # look a little across, so the iris sits at an angle to the camera
        scene.pose_eye(head, arm, side, 12, 2)
    # the close view from tools/stills.py: left eye, camera swung 35 degrees to its side, 40 cm away
    cam = sc.camera
    eye = arm.matrix_world @ arm.pose.bones["left_eye"].head
    angle = math.radians(35)
    cam.location = eye + Vector((math.sin(angle), -math.cos(angle), 0.08)) * scene.CAMERA_DISTANCE
    cam.rotation_euler = (eye - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 300
    glass = [n for n in bpy.data.materials["cornea"].node_tree.nodes if n.type == "BSDF_GLASS"]
    assert glass, "cornea material has no Glass BSDF"
    for label, ior in (("on", CORNEA_IOR), ("off", 1.0)):
        for n in glass:
            n.inputs["IOR"].default_value = ior
        sc.render.filepath = str(OUT / f"refraction_{label}.png")
        bpy.ops.render.render(write_still=True)
else:
    from PIL import Image, ImageDraw, ImageFont

    on, off = (Image.open(OUT / f"refraction_{k}.png").convert("RGB") for k in ("on", "off"))
    w, h = on.size
    panel = Image.new("RGB", (w * 2 + 16, h + 70), (11, 21, 48))
    panel.paste(off, (0, 70))
    panel.paste(on, (w + 16, 70))
    d = ImageDraw.Draw(panel)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Avenir Next.ttc", 34, index=2)
    except OSError:
        font = ImageFont.load_default(34)
    d.text((w // 2, 35), "Cornea refraction off (IOR 1.0)", font=font, fill=(150, 165, 190), anchor="mm")
    d.text((w + 16 + w // 2, 35), "TrueGaze: refracting cornea (IOR 1.376)", font=font, fill=(64, 200, 230), anchor="mm")
    panel.thumbnail((1800, 1800))
    panel.save(ROOT / "docs" / "refraction.jpg", quality=88)
    print("wrote docs/refraction.jpg")
