"""Day-1 proof: head builds, eyes rotate about their centres, lids close.
Run: Blender --background --python tools/spike.py
"""
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from truegaze import scene  # noqa: E402

head, arm = scene.build()
keys = head.data.shape_keys.key_blocks
cam = bpy.context.scene.camera
cam.data.lens = 200  # eye-region close-up from the 40 cm camera position
bpy.context.scene.render.resolution_y = 512

POSES = {"neutral": (0, 0, 0), "left": (25, 0, 0), "right": (-25, 0, 0), "up": (0, 20, 0), "down": (0, -20, 0),
         "half_blink": (0, 0, 0.5), "blink": (0, 0, 1.0)}
for name, (yaw, pitch, blink) in POSES.items():
    for side in ("left", "right"):
        scene.pose_eye(head, arm, side, yaw, pitch)
        keys[f"blink_{side}"].value = blink
    bpy.context.scene.render.filepath = str(ROOT / "renders" / "tmp" / f"spike_{name}.png")
    bpy.ops.render.render(write_still=True)
