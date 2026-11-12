#!/usr/bin/env python3
"""Seam audit: measures the colour step across every UV seam of the skin, and draws the UV layout.

A seam is a mesh edge whose two faces sit at different places in the UV map. If the texture colour
differs across it, a line shows on the head. Reports the colour step (0-255) for seams on the
front of the face (what the camera sees) and for all seams, and fails if a front seam is visible.

  python3 tools/seam_audit.py [textures folder]   # all sets; also writes uv_maps/<set>.jpg overview sheets
"""
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from truegaze.gnm import GNM  # noqa: E402

VISIBLE_STEP = 8.0  # of 255 (3%): below this a seam cannot be seen on textured skin


def skin_seams(m):
    """Pairs of UV points (inset a little into each face) on the two sides of each skin seam edge."""
    sel = np.flatnonzero(m.quad_tiles() == 1001)
    sides = defaultdict(list)
    for q in sel:
        v, uv = m.quads[q], m.quad_uvs[q]
        inside = uv.mean(axis=0)
        for k in range(4):
            a, b = int(v[k]), int(v[(k + 1) % 4])
            mid = (uv[k] + uv[(k + 1) % 4]) / 2
            sides[(min(a, b), max(a, b))].append((mid + 0.05 * (inside - mid), mid))  # just inside the face, at the seam
    pairs, verts = [], []
    for (a, b), s in sides.items():
        if len(s) == 2 and np.abs(s[0][1] - s[1][1]).max() > 1e-5:
            pairs.append((s[0][0], s[1][0]))
            verts.append((a, b))
    return np.array(pairs), np.array(verts)


def sample(img, uv):
    h, w = img.shape[:2]
    return img[np.clip(((1 - uv[:, 1]) * h).astype(int), 0, h - 1), np.clip((uv[:, 0] * w).astype(int), 0, w - 1)].astype(float)


def uv_sheet(m, folder, out):
    """Overview image of one set: skin, left eye and right eye maps with the UV mesh drawn on top."""
    size = 1024
    sheet = Image.new("RGB", (size * 3, size))
    tiles = m.quad_tiles()
    for i, tile in enumerate((1001, 1002, 1004)):
        img = Image.open(folder / f"color.{tile}.jpg").resize((size, size))
        draw = ImageDraw.Draw(img, "RGBA")
        for uv in m.quad_uvs[tiles == tile][:: 3 if tile == 1001 else 1]:
            draw.polygon([(u * size, (1 - v) * size) for u, v in uv], outline=(255, 255, 255, 60))
        sheet.paste(img, (i * size, 0))
    sheet.save(out, quality=90)


if __name__ == "__main__":
    m = GNM()
    pairs, verts = skin_seams(m)
    centre = m.joints[2:4].mean(axis=0)
    front = (m.template[verts].mean(axis=1)[:, 2] > centre[2] - 0.02) & m.group("skin_exterior")[verts].all(axis=1)
    print(f"skin seam edges: {len(pairs)}, on the visible front of the face: {int(front.sum())}")
    (ROOT / "uv_maps").mkdir(exist_ok=True)
    worst = 0.0
    textures = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "textures"
    for folder in sorted(p for p in textures.iterdir() if p.is_dir()):
        img = np.asarray(Image.open(folder / "color.1001.jpg"))
        step = np.abs(sample(img, pairs[:, 0]) - sample(img, pairs[:, 1])).max(axis=1)
        front_step = step[front].max() if front.any() else 0.0
        worst = max(worst, front_step)
        print(f"set {folder.name}: front seams max step {front_step:.1f}, all seams mean {step.mean():.1f} max {step.max():.1f}")
        uv_sheet(m, folder, ROOT / "uv_maps" / f"{folder.name}.jpg")
    assert worst <= VISIBLE_STEP, f"a seam on the front of the face is visible (step {worst:.1f})"
    print("PASS: no visible seam on the front of the face")
