"""Generates texture sets in GNM's UV layout. NumPy + SciPy + Pillow, no Blender.

One set = textures/<name>/: color.1001 (skin), roughness.1001, height.1001 (pores, used as bump),
color.1002 (left eye: sclera + iris + pupil), color.1004 (right eye, its own iris pattern).
Numbers are GNM's UDIM tiles. Eye tiles are polar: eye axis at the centre, pupil, iris, then sclera.

  python3 -m truegaze.textures            # all sets
  python3 -m truegaze.textures 01 --size 2048
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.interpolate import LinearNDInterpolator
from scipy.ndimage import gaussian_filter, zoom

from .gnm import GNM

ROOT = Path(__file__).resolve().parent.parent

# name: skin albedo, iris outer colour, iris inner colour (around the pupil), hair colour, seed
SETS = {
    "01": ((0.78, 0.57, 0.46), (0.25, 0.36, 0.42), (0.45, 0.40, 0.28), (0.1, 0.06, 0.035), 1),   # light skin, blue-grey eyes
    "02": ((0.62, 0.42, 0.30), (0.30, 0.17, 0.07), (0.45, 0.25, 0.08), (0.03, 0.02, 0.012), 2),   # medium skin, brown eyes
    "03": ((0.36, 0.22, 0.15), (0.14, 0.07, 0.03), (0.25, 0.12, 0.04), (0.012, 0.009, 0.007), 3),   # dark skin, dark brown eyes
    "04": ((0.82, 0.62, 0.52), (0.28, 0.38, 0.20), (0.55, 0.38, 0.12), (0.16, 0.08, 0.04), 4),   # fair skin, green eyes
    "05": ((0.70, 0.50, 0.36), (0.36, 0.26, 0.10), (0.50, 0.30, 0.08), (0.04, 0.025, 0.015), 5),   # olive skin, hazel eyes
    "06": ((0.50, 0.32, 0.22), (0.22, 0.11, 0.04), (0.38, 0.18, 0.05), (0.015, 0.01, 0.008), 6),   # brown skin, brown eyes
    "07": ((0.85, 0.66, 0.58), (0.38, 0.45, 0.50), (0.60, 0.55, 0.40), (0.2, 0.14, 0.08), 7),   # pale skin, grey eyes
    "08": ((0.66, 0.46, 0.34), (0.42, 0.26, 0.06), (0.60, 0.36, 0.08), (0.05, 0.03, 0.018), 8),   # tan skin, amber eyes
}


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def noise(n, cell, rng):
    """Smooth noise with features about `cell` pixels wide, unit standard deviation."""
    cell = max(cell, 4)
    small = gaussian_filter(rng.standard_normal((4 * n // cell + 8,) * 2).astype(np.float32), 2.0)
    big = zoom(small, cell / 4, order=1)[:n, :n]
    return big / big.std()


def save(array, path):
    img = Image.fromarray((np.clip(array, 0, 1) * 255 + 0.5).astype(np.uint8))
    img.save(path, quality=93)


# ---------- skin (tile 1001) ----------

def skin_masks(m, n, seam):
    """Face regions painted into UV space, from GNM's vertex groups. Dict of (n, n) arrays in 0..1."""
    regions = {
        "lips": m.group("upper_lip") | m.group("lower_lip"),
        "orbital": m.group("left_orbital_region") | m.group("right_orbital_region"),
        "under_eye": m.group("left_infraorbital_region") | m.group("right_infraorbital_region"),
        "nose": m.group("nose_region"),
        "cheeks": m.group("left_cheek_region") | m.group("right_cheek_region"),
        "inside": m.group("skin") & ~m.group("skin_exterior"),  # eye sockets, mouth: wet pink tissue
    }
    sel = m.quad_tiles() == 1001
    uv, first = np.unique(m.quad_uvs[sel].reshape(-1, 2), axis=0, return_index=True)
    vertex = m.quads[sel].ravel()[first]
    values = np.stack([g[vertex] for g in regions.values()], axis=1).astype(np.float32)
    small = min(n, 1024)  # interpolate at reduced size and enlarge; finer than this changes nothing visible
    c = (np.arange(small) + 0.5) / small
    grid = LinearNDInterpolator(uv, values, fill_value=0)(*np.meshgrid(c, 1 - c))
    # groups are on/off per vertex; blur so regions fade into each other (lips and wet tissue stay crisper)
    # ...except on seams, where the unblurred value is kept: it is the same on both sides of the seam
    out = {}
    for i, k in enumerate(regions):
        sharp = np.clip(zoom(grid[..., i], n / small, order=1), 0, 1)
        out[k] = sharp + (1 - seam) * (gaussian_filter(sharp, n / (600 if k in ("lips", "inside") else 130)) - sharp)
    return out


def seam_mask(m, n):
    """1 on the skin's UV seams, fading to 0 a few millimetres away. Random detail is faded out there:
    it cannot match on both sides of a seam, and a mismatch shows as a line on the head."""
    sel = m.quad_tiles() == 1001
    edges = {}
    for v, uv in zip(m.quads[sel], m.quad_uvs[sel]):
        for k in range(4):
            a, b = int(v[k]), int(v[(k + 1) % 4])
            edges.setdefault((min(a, b), max(a, b)), []).append((uv[k], uv[(k + 1) % 4]))
    small = n // 4
    img = Image.new("L", (small, small))
    draw = ImageDraw.Draw(img)
    for sides in edges.values():
        if len(sides) == 1 or np.abs(np.add(*sides[0]) - np.add(*sides[1])).max() > 1e-5:
            for p, q in sides:
                draw.line([(p[0] * small, (1 - p[1]) * small), (q[0] * small, (1 - q[1]) * small)], fill=255, width=2)
    sigma = small / 150
    blurred = gaussian_filter(np.asarray(img, np.float32) / 255, sigma) * sigma * 2.5
    return np.clip(zoom(blurred, n / small, order=1), 0, 1)


def skin(m, n, tone, seed):
    """Returns colour (n, n, 3), roughness (n, n), height (n, n), all 0..1."""
    rng = np.random.default_rng(seed)
    tone = np.array(tone, np.float32)
    dark = 1 - tone.mean()  # darker skin shows less redness
    seam = seam_mask(m, n)
    k, detail = skin_masks(m, n, seam), 1 - seam

    color = np.ones((n, n, 3), np.float32) * tone
    color *= (1 + detail * (0.025 * noise(n, n // 24, rng) + 0.015 * noise(n, n // 160, rng)))[..., None]
    blotch = noise(n, n // 60, rng)  # uneven blood flow
    red = 0.025 * blotch * detail + 0.10 * k["cheeks"] + 0.08 * k["nose"] + 0.06 * k["orbital"]
    color *= 1 + red[..., None] * np.array([0.6, -0.5, -0.6]) * (0.4 + 0.6 * (1 - dark))
    color *= 1 - k["under_eye"][..., None] * np.array([0.10, 0.10, 0.06])
    color *= 1 - 0.08 * k["orbital"][..., None]
    lip = tone * np.array([0.95, 0.60, 0.62])
    color += k["lips"][..., None] * (lip - color) * 0.85
    wet = np.array([0.72, 0.36, 0.34]) * (0.6 + 0.4 * tone.mean())
    color += k["inside"][..., None] * (wet - color)
    # freckles and small moles
    spots = gaussian_filter(rng.random((n, n), np.float32), 1.5)
    spots = smoothstep(np.quantile(spots[::8, ::8], 0.997), spots.max(), spots)
    color *= 1 - 0.35 * (spots * detail)[..., None] * (1 - k["lips"][..., None])

    # pores: small dents, plus fine creases, stronger on nose and cheeks
    white = rng.standard_normal((n, n)).astype(np.float32)
    pores = gaussian_filter(white, n / 4096 * 0.8) - gaussian_filter(white, n / 4096 * 2.0)
    pores = -np.clip(pores / (pores.std() + 1e-9), 0, None)  # tiny previews blur to nothing
    creases = gaussian_filter(white, (n / 4096 * 0.7, n / 4096 * 5)) + gaussian_filter(white, (n / 4096 * 5, n / 4096 * 0.7))
    creases = -np.abs(creases / creases.std())
    amount = 0.55 + 0.45 * np.clip(k["nose"] + k["cheeks"], 0, 1) - 0.4 * k["lips"]
    bumps = (0.6 * pores + 0.25 * creases) * amount * (1 - k["inside"]) + 0.08 * noise(n, n // 400, rng)
    height = 0.5 + 0.12 * bumps

    rough = 0.62 - 0.08 * k["nose"] - 0.14 * k["lips"] - 0.04 * k["orbital"] - 0.30 * k["inside"]
    rough = rough + 0.03 * noise(n, n // 200, rng) - 0.10 * bumps * 0.3
    return color, rough, height


# ---------- eye (tiles 1002 and 1004) ----------

def eye_radii(m):
    """UV radius of the pupil edge and the iris edge in the eye tile, measured from the model."""
    sel = m.quad_tiles() == 1002
    r = np.linalg.norm(m.quad_uvs[sel] - 0.5, axis=2).ravel()
    vertex = m.quads[sel].ravel()
    return float(r[m.group("pupils")[vertex]].max()), float(r[m.group("irises")[vertex]].max())


def eye(n, radii, outer, inner, seed):
    """Sclera with veins, iris with fibres, black pupil. Returns colour (n, n, 3)."""
    rng = np.random.default_rng(seed)
    pupil_r, iris_r = radii
    c = (np.arange(n) + 0.5) / n - 0.5
    u, v = np.meshgrid(c, -c)
    r, theta = np.hypot(u, v), np.arctan2(v, u)

    def polar(nr, nt, blur_r, blur_t):
        """Noise sampled in (radius across the iris, angle), seamless around the circle."""
        g = gaussian_filter(rng.standard_normal((nr, nt)), (blur_r, blur_t), mode=("nearest", "wrap"))
        g /= g.std()
        t = np.clip((r - pupil_r) / (iris_r - pupil_r), 0, 1)
        return g[(t * (nr - 1)).astype(int), ((theta + np.pi) / (2 * np.pi) * nt).astype(int) % nt]

    # sclera: off-white, pinker toward the corners, thin red veins that fade before the iris
    sclera = np.array([0.64, 0.63, 0.62]) * (1 + 0.03 * noise(n, n // 6, rng))[..., None]
    sclera += smoothstep(0.30, 0.46, r)[..., None] * (np.array([0.66, 0.46, 0.43]) - sclera)
    sclera *= (1 - 0.35 * smoothstep(iris_r + 0.03, 0.40, r))[..., None]  # darker toward the lids, as real eyes look
    veins = np.zeros((n, n), np.float32)
    for _ in range(34):
        ang, rad = rng.uniform(0, 2 * np.pi), 0.44
        stop = iris_r + rng.uniform(0.02, 0.13)
        walkers = [(ang, rad, 1.0)]
        while walkers:
            ang, rad, w = walkers.pop()
            turn = 0.0
            while rad > stop:
                turn = 0.97 * turn + rng.normal(0, 0.00012)  # smooth wander, so veins curve instead of jitter
                ang += turn
                rad -= 0.0003
                veins[int((0.5 - rad * np.sin(ang)) * n) % n, int((0.5 + rad * np.cos(ang)) * n) % n] += w
                if rng.random() < 0.0015 and w > 0.3:
                    walkers.append((ang + rng.choice([-1, 1]) * 0.04, rad, w * 0.6))
    veins = gaussian_filter(veins, n / 1400)
    veins = np.clip(veins / np.quantile(veins[veins > 0], 0.97), 0, 1) * smoothstep(iris_r, iris_r + 0.08, r)
    sclera += (0.40 * veins)[..., None] * (np.array([0.62, 0.16, 0.13]) - sclera)

    # iris: inner colour near the pupil, outer colour beyond the collarette, radial fibres, dark rim
    t = np.clip((r - pupil_r) / (iris_r - pupil_r), 0, 1)
    wavy = polar(4, 90, 0, 3.0)
    mix = smoothstep(0.15, 0.42, t + 0.07 * wavy)
    iris = np.array(inner) + mix[..., None] * (np.array(outer) - np.array(inner))
    fibres = 0.6 * polar(40, 900, 9, 1.3) + 0.4 * polar(90, 1800, 14, 0.9)
    crypts = smoothstep(1.3, 2.2, polar(30, 160, 2.5, 1.5)) * smoothstep(0.15, 0.35, t) * (1 - smoothstep(0.6, 0.85, t))
    shade = (1 + 0.42 * fibres) * (1 - 0.40 * crypts) * (1 - 0.70 * smoothstep(0.78, 1.0, t)) * (0.75 + 0.25 * smoothstep(0, 0.12, t))
    iris = iris * np.clip(shade, 0.05, 2.2)[..., None]

    edge = 0.018  # soft limbus: the iris edge is never a hard line
    out = sclera + (1 - smoothstep(iris_r - edge, iris_r + edge, r))[..., None] * (iris - sclera)
    return out * smoothstep(pupil_r * 0.96, pupil_r * 1.04, r)[..., None]


def make_set(name, size=4096, eye_size=2048, out=ROOT / "textures"):
    tone, outer, inner, hair, seed = SETS[name]
    m = GNM()
    folder = Path(out) / name
    folder.mkdir(parents=True, exist_ok=True)
    color, rough, height = skin(m, size, tone, seed)
    save(color, folder / "color.1001.jpg")
    save(rough, folder / "roughness.1001.jpg")
    save(height, folder / "height.1001.jpg")
    (folder / "info.json").write_text(json.dumps({"hair": hair}))  # read by materials.py
    radii = eye_radii(m)
    save(eye(eye_size, radii, outer, inner, seed * 100 + 1), folder / "color.1002.jpg")  # left
    save(eye(eye_size, radii, outer, inner, seed * 100 + 2), folder / "color.1004.jpg")  # right
    return folder


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("sets", nargs="*", default=list(SETS))
    ap.add_argument("--size", type=int, default=4096)
    a = ap.parse_args()
    for s in a.sets:
        print("wrote", make_set(s, a.size))
