"""Generates texture sets in GNM's UV layout. NumPy + SciPy + Pillow, no Blender.

One set = textures/<name>/: color.1001 (skin), roughness.1001, height.1001 (pores, used as bump),
color.1002 (left eye: sclera + iris + pupil), color.1004 (right eye, its own iris pattern).
Numbers are GNM's UDIM tiles. Eye tiles are polar: eye axis at the centre, pupil, iris, then sclera.

  python3 -m truegaze.textures            # all sets
  python3 -m truegaze.textures 01 --size 2048
"""
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy.interpolate import LinearNDInterpolator
from scipy.ndimage import gaussian_filter, map_coordinates, zoom

from .gnm import GNM

ROOT = Path(__file__).resolve().parent.parent

# name: fallback skin tone, iris outer colour, iris inner colour (around the pupil), hair colour, seed,
# MakeHuman skin photo (CC0) that gives the skin its colour
SETS = {
    "01": ((0.78, 0.57, 0.46), (0.25, 0.36, 0.42), (0.45, 0.40, 0.28), (0.1, 0.06, 0.035), 1, "young_lightskinned_male_diffuse"),   # light skin, blue-grey eyes
    "02": ((0.62, 0.42, 0.30), (0.30, 0.17, 0.07), (0.45, 0.25, 0.08), (0.03, 0.02, 0.012), 2, "middleage_lightskinned_male_diffuse"),   # medium skin, brown eyes
    "03": ((0.36, 0.22, 0.15), (0.14, 0.07, 0.03), (0.25, 0.12, 0.04), (0.012, 0.009, 0.007), 3, "young_darkskinned_male_diffuse"),   # dark skin, dark brown eyes
    "04": ((0.82, 0.62, 0.52), (0.28, 0.38, 0.20), (0.55, 0.38, 0.12), (0.16, 0.08, 0.04), 4, "young_lightskinned_female_diffuse"),   # fair skin, green eyes
    "05": ((0.70, 0.50, 0.36), (0.36, 0.26, 0.10), (0.50, 0.30, 0.08), (0.04, 0.025, 0.015), 5, "young_lightskinned_male_diffuse2"),   # olive skin, hazel eyes
    "06": ((0.50, 0.32, 0.22), (0.22, 0.11, 0.04), (0.38, 0.18, 0.05), (0.015, 0.01, 0.008), 6, "young_darkskinned_female_diffuse"),   # brown skin, brown eyes
    "07": ((0.85, 0.66, 0.58), (0.38, 0.45, 0.50), (0.60, 0.55, 0.40), (0.2, 0.14, 0.08), 7, "old_lightskinned_male_diffuse"),   # pale skin, grey eyes
    "08": ((0.66, 0.46, 0.34), (0.42, 0.26, 0.06), (0.60, 0.36, 0.08), (0.05, 0.03, 0.018), 8, "middleage_darkskinned_male_diffuse"),   # tan skin, amber eyes
}


# MakeHuman assets (CC0, see docs/ASSETS.md) with their SHA-256, fetched on first use
MAKEHUMAN_SKINS = "http://download.tuxfamily.org/makehuman/assets/1.2/base/skins/textures/"
MAKEHUMAN_MESH = "https://raw.githubusercontent.com/makehumancommunity/makehuman/master/makehuman/data/3dobjs/"
MAKEHUMAN = {
    "base.obj": "8e761e6624b8f54536409135d1636da63b32486a90d4897f84e121d144f6fb4c",
    "middleage_darkskinned_male_diffuse.png": "ced478cfdd2b86391f0f92a4408b287ad70adb0dd0e9271ba606d0b028b47c6b",
    "middleage_lightskinned_male_diffuse.png": "3f94f3f6a5cab92dedf5cce392a87332312fc435f1cb44c6e7b897daef9a5fbb",
    "old_lightskinned_male_diffuse.png": "dfb2310ed3e0ad024ea7a3ad321215e2e9e2994cca64043d9f3d07c6543ec847",
    "young_darkskinned_female_diffuse.png": "96aa4a96b247fc90d371587bb88e6ae3bfc77e83f5126f17e6bbb713aa200470",
    "young_darkskinned_male_diffuse.png": "e3f0dbb634e4c68561338f0087f7a122444e84ec56df102212f1222aa12e4d50",
    "young_lightskinned_female_diffuse.png": "b2a6ac8cd4f9febdb447368e29c76cd68410bb66e46d9dcfa2d5f75126eea8fc",
    "young_lightskinned_male_diffuse.png": "862a26e335e958b70534cb5f0d7c47ef30ab148a56c42b3e9da969cf76f12963",
    "young_lightskinned_male_diffuse2.png": "03efe1f6b0ae52429649dcefc9dcaef6058032f874a251169cc3e2ed473c3874",
}


def makehuman_file(name):
    """Local path of a MakeHuman asset, downloading and verifying it on first use."""
    path = ROOT / "assets" / "cache" / "makehuman" / name
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".part")
        urllib.request.urlretrieve((MAKEHUMAN_MESH if name.endswith(".obj") else MAKEHUMAN_SKINS) + name, tmp)
        if hashlib.sha256(tmp.read_bytes()).hexdigest() != MAKEHUMAN[name]:
            tmp.unlink()
            raise RuntimeError(f"{name} failed the checksum; download again")
        tmp.rename(path)
    return path


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
    out["inside"] *= 1 - out["lips"]  # the lips' contact line is not wet inner tissue
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


def photo_skin(m, n, name):
    """A MakeHuman skin photo pulled into GNM's UV layout through assets/skin_transfer.npz.
    Returns the picture (n, n, 3) and how far to trust it per texel (0..1; 0 where the two heads
    could not be matched, or where MakeHuman's own UV layout is cut)."""
    t = np.load(ROOT / "assets" / "skin_transfer.npz")
    sel = m.quad_tiles() == 1001
    src = t["uv"][m.quads[sel]]
    ok = t["valid"][m.quads[sel]].all(axis=1) & (np.ptp(src, axis=1).max(axis=1) < 0.05)
    uv = m.quad_uvs[sel][ok]
    small = min(n, 1024)
    c = (np.arange(small) + 0.5) / small
    grid = LinearNDInterpolator(uv.reshape(-1, 2), src[ok].reshape(-1, 2), fill_value=0)(*np.meshgrid(c, 1 - c))
    cover = Image.new("L", (small, small))
    draw = ImageDraw.Draw(cover)
    for q in uv:
        draw.polygon([(u * small, (1 - v) * small) for u, v in q], fill=255)
    cover = np.clip(gaussian_filter(np.asarray(cover, np.float32) / 255, small / 200) * 3 - 2, 0, 1)  # pull in from the edges
    img = np.asarray(Image.open(makehuman_file(name + ".png")).convert("RGB"), np.float32) / 255
    size = img.shape[0]
    rows = (1 - zoom(grid[..., 1].astype(np.float32), n / small, order=1)) * size - 0.5
    cols = zoom(grid[..., 0].astype(np.float32), n / small, order=1) * size - 0.5
    picture = np.stack([map_coordinates(img[..., i], [rows, cols], order=1, mode="nearest") for i in range(3)], axis=-1)
    return picture, zoom(cover, n / small, order=1)


def skin(m, n, tone, seed, hair=(0.03, 0.02, 0.012), photo=None):
    """Returns colour (n, n, 3), roughness (n, n), height (n, n), all 0..1."""
    rng = np.random.default_rng(seed)
    seam = seam_mask(m, n)
    k, detail = skin_masks(m, n, seam), 1 - seam
    if photo:  # the generated skin below takes the photo's own tone, so the two blend without an edge
        picture, cover = photo_skin(m, n, photo)
        cover = cover * (1 - seam)  # on a seam only generated colour is the same on both sides
        tone = np.median(picture[(cover > 0.95) & (k["cheeks"] > 0.5)], axis=0)
    else:
        cover = np.zeros((n, n), np.float32)
    tone = np.array(tone, np.float32)
    dark = 1 - tone.mean()  # darker skin shows less redness

    color = np.ones((n, n, 3), np.float32) * tone
    color *= (1 + detail * (0.025 * noise(n, n // 24, rng) + 0.015 * noise(n, n // 160, rng)))[..., None]
    blotch = noise(n, n // 60, rng)  # uneven blood flow
    red = 0.025 * blotch * detail + 0.10 * k["cheeks"] + 0.08 * k["nose"] + 0.06 * k["orbital"]
    color *= 1 + red[..., None] * np.array([0.6, -0.5, -0.6]) * (0.4 + 0.6 * (1 - dark))
    color *= 1 - k["under_eye"][..., None] * np.array([0.10, 0.10, 0.06])
    color *= 1 - 0.08 * k["orbital"][..., None]
    lip = tone * np.array([0.95, 0.60, 0.62])
    color += k["lips"][..., None] * (lip - color) * 0.85
    if photo:
        color += cover[..., None] * (picture - color)
    wet = np.array([0.72, 0.36, 0.34]) * (0.6 + 0.4 * tone.mean())
    color += k["inside"][..., None] * (wet - color)
    # hair roots: brow skin is shaded by follicles, and the lash line reads as a dark edge on the lid
    roots = np.load(ROOT / "assets" / "hair.npz")
    for uv, strength, blur in ((roots["brow_uv"], 0.30, n / 500), (roots["lash_uv"], 0.35, n / 1400)):
        dots = np.zeros((n, n), np.float32)
        np.add.at(dots, (np.clip(((1 - uv[:, 1]) * n).astype(int), 0, n - 1), np.clip((uv[:, 0] * n).astype(int), 0, n - 1)), 1)
        dots = gaussian_filter(dots, blur)
        dots = np.clip(dots / np.quantile(dots[dots > dots.max() * 0.02], 0.6), 0, 1)
        color += (strength * dots)[..., None] * (np.array(hair, np.float32) * 2 + 0.25 * tone - color)
    # thin skin around the eye: faint blue veins show through, and the upper lid folds along a crease
    crease = np.zeros((n, n), np.float32)
    veins = Image.new("L", (n, n))
    pen = ImageDraw.Draw(veins)
    to_px = lambda uv: [(float(u) * n, float(1 - v) * n) for u, v in uv]
    for upper, lower in roots["lid_uv"].reshape(2, 2, 64, 2):
        centre, half = (upper.mean(axis=0) + lower.mean(axis=0)) / 2, np.ptp(upper[:, 0]) / 2
        fold = upper + (upper - centre) * 0.95 * np.sin(np.pi * np.linspace(0.08, 0.95, 64))[:, None] ** 0.5  # follows the lid, above it
        line = Image.new("L", (n, n))
        ImageDraw.Draw(line).line(to_px(fold[4:-3]), fill=255, width=max(1, n // 1400))
        crease += gaussian_filter(np.asarray(line, np.float32) / 255, n / 1300)
        for _ in range(8):  # veins wander around the socket, mostly below and to the sides of the eye
            angle = rng.uniform(np.pi * 0.9, np.pi * 2.1)
            p = centre + half * rng.uniform(1.15, 1.6) * np.array([np.cos(angle), 0.75 * np.sin(angle)])
            heading, path = angle + rng.choice([-1, 1]) * rng.uniform(0.9, 1.5), [p]
            for _ in range(int(rng.uniform(25, 60))):
                heading += rng.normal(0, 0.09)
                p = p + half * 0.035 * np.array([np.cos(heading), np.sin(heading)])
                path.append(p)
            pen.line(to_px(path), fill=int(rng.uniform(90, 255)), width=max(1, n // 2000))
    crease = np.clip(crease / crease.max(), 0, 1)
    # fine lines of the thin skin round the eye: they run round the socket, crossed by fainter radial ones
    lines = np.zeros((n, n), np.float32)
    rings = gaussian_filter(rng.standard_normal((700, 48)).astype(np.float32), (0.8, 2.5), mode=("nearest", "wrap"))
    rays = gaussian_filter(rng.standard_normal((40, 900)).astype(np.float32), (3.0, 0.8), mode=("nearest", "wrap"))
    for upper, lower in roots["lid_uv"].reshape(2, 2, 64, 2):
        centre, half = (upper.mean(axis=0) + lower.mean(axis=0)) / 2, np.ptp(upper[:, 0]) / 2
        r0, r1 = int((1 - centre[1] - 3.4 * half) * n), int((1 - centre[1] + 3.4 * half) * n)
        c0, c1 = int((centre[0] - 3.4 * half) * n), int((centre[0] + 3.4 * half) * n)
        yy, xx = np.mgrid[r0:r1, c0:c1]
        du, dv = (xx + 0.5) / n - centre[0], (1 - (yy + 0.5) / n) - centre[1]
        rho, ang = np.hypot(du, dv / 0.75) / half, (np.arctan2(dv, du) / (2 * np.pi)) % 1
        both = (np.abs(map_coordinates(rings, [np.clip(rho / 3.4, 0, 1) * 699, ang * 47], order=1, mode="nearest"))
                + 0.5 * np.abs(map_coordinates(rays, [np.clip(rho / 3.4, 0, 1) * 39, ang * 899], order=1, mode="nearest")))
        lines[r0:r1, c0:c1] += both / both.std() * np.exp(-((rho - 1.9) / 0.8) ** 2) * (0.55 + 0.45 * (dv < 0))  # more below the eye
    veins = gaussian_filter(np.asarray(veins, np.float32) / 255, n / 1100) * (1 - k["inside"]) * detail
    veins = np.clip(veins / (veins.max() + 1e-9), 0, 1) * (0.25 + 0.75 * tone.mean())  # dark skin hides them more
    color *= 1 - veins[..., None] * np.array([0.11, 0.07, 0.02])    # blue-green: red is absorbed most
    color *= 1 - 0.12 * crease[..., None]
    # freckles and small moles
    spots = gaussian_filter(rng.random((n, n), np.float32), 1.5)
    spots = smoothstep(np.quantile(spots[::8, ::8], 0.997), spots.max(), spots)
    color *= 1 - 0.35 * (spots * detail * (1 - cover))[..., None] * (1 - k["lips"][..., None])

    # pores: small dents, plus fine creases, stronger on nose and cheeks
    white = rng.standard_normal((n, n)).astype(np.float32)
    pores = gaussian_filter(white, n / 4096 * 0.8) - gaussian_filter(white, n / 4096 * 2.0)
    pores = -np.clip(pores / (pores.std() + 1e-9), 0, None)  # tiny previews blur to nothing
    creases = gaussian_filter(white, (n / 4096 * 0.7, n / 4096 * 5)) + gaussian_filter(white, (n / 4096 * 5, n / 4096 * 0.7))
    creases = -np.abs(creases / creases.std())
    amount = 0.55 + 0.45 * np.clip(k["nose"] + k["cheeks"], 0, 1) - 0.4 * k["lips"]
    bumps = (0.6 * pores + 0.25 * creases) * amount * (1 - k["inside"]) + 0.08 * noise(n, n // 400, rng)
    if photo:  # the photo's own fine detail (pores, lines) also becomes relief, so shine follows what is drawn
        luma = picture.mean(axis=2)
        fine = luma - gaussian_filter(luma, n / 4096 * 4)
        bumps = bumps + 0.8 * cover * fine / (fine.std() + 1e-9) * (1 - k["inside"])
    height = 0.5 + 0.12 * bumps - 0.20 * crease - 0.05 * lines * (1 - k["inside"])

    rough = 0.52 - 0.08 * k["nose"] - 0.14 * k["lips"] - 0.06 * k["orbital"] - 0.42 * k["inside"]
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
        g = np.concatenate([g, g[:, :1]], axis=1)  # repeat the first column so the lookup wraps around smoothly
        return map_coordinates(g, [t * (nr - 1), ((theta + bend + np.pi) / (2 * np.pi) % 1) * nt], order=1, mode="nearest")

    bend = 0.0
    bend = 0.045 * polar(10, 40, 1.5, 2.5)  # fibres wander sideways on their way out, they are not ruler-straight

    # sclera: off-white, pinker toward the corners, thin red veins that fade before the iris
    sclera = np.array([0.62, 0.60, 0.57]) * (1 + 0.03 * noise(n, n // 6, rng))[..., None]
    sclera += smoothstep(0.30, 0.46, r)[..., None] * (np.array([0.66, 0.46, 0.43]) - sclera)
    sclera *= (1 - 0.35 * smoothstep(iris_r + 0.03, 0.40, r))[..., None]  # darker toward the lids, as real eyes look
    # yellowish fatty patches left and right of the iris, where the eye is exposed between the lids
    patch = np.exp(-((r - iris_r - 0.09) / 0.05) ** 2) * np.abs(np.cos(theta)) ** 3 * np.clip(0.5 + 0.6 * noise(n, n // 12, rng), 0, 1)
    sclera += (0.45 * patch)[..., None] * (np.array([0.66, 0.58, 0.38]) - sclera)
    veins = np.zeros((n, n), np.float32)
    for _ in range(60):
        ang, rad = rng.choice([0, np.pi]) + rng.normal(0, 0.75), 0.44  # most vessels come in from the two corners
        stop = iris_r + rng.uniform(0.02, 0.13)
        walkers = [(ang, rad, rng.choice([1.0, 0.45, 0.45]))]  # a few thick vessels, more fine ones
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
    sclera += (0.50 * veins)[..., None] * (np.array([0.62, 0.16, 0.13]) - sclera)
    sclera += (0.5 * smoothstep(0.24, 0.42, r) * np.abs(np.cos(theta)) ** 2)[..., None] * (np.array([0.66, 0.36, 0.33]) - sclera)  # pink corners

    # iris: inner colour near the pupil, outer colour beyond the collarette, radial fibres, dark rim
    t = np.clip((r - pupil_r) / (iris_r - pupil_r), 0, 1)
    wavy = polar(4, 90, 0, 3.0)
    mix = smoothstep(0.15, 0.42, t + 0.07 * wavy)
    iris = np.array(inner) + mix[..., None] * (np.array(outer) - np.array(inner))
    fibres = 0.6 * polar(40, 900, 9, 1.3) + 0.4 * polar(90, 1800, 14, 0.9)
    crypts = smoothstep(1.3, 2.2, polar(30, 160, 2.5, 1.5)) * smoothstep(0.15, 0.35, t) * (1 - smoothstep(0.6, 0.85, t))
    ring = 0.30 + 0.05 * wavy                                       # collarette: a paler zigzag ring a third of the way out
    collarette = np.exp(-((t - ring) / 0.035) ** 2)
    furrows = sum(np.exp(-((t - c - 0.02 * wavy) / 0.018) ** 2) for c in (0.62, 0.76, 0.88))  # contraction furrows
    ruff = 1 - 0.6 * (1 - smoothstep(0.0, 0.05, t))                  # dark pigment frill at the pupil edge
    shade = (1 + 0.36 * fibres) * (1 - 0.40 * crypts) * (1 + 0.22 * collarette) * (1 - 0.10 * furrows) * ruff * (1 - 0.70 * smoothstep(0.78, 1.0, t))
    iris = iris * np.clip(shade, 0.05, 2.2)[..., None]
    spots = smoothstep(2.3, 2.8, polar(44, 120, 1.2, 1.2)) * smoothstep(0.12, 0.3, t) * (1 - smoothstep(0.75, 0.9, t))  # a few brown freckles
    iris += (0.6 * spots)[..., None] * (np.array([0.22, 0.11, 0.04]) - iris)

    edge = 0.018  # soft limbus: the iris edge is never a hard line
    out = sclera + (1 - smoothstep(iris_r - edge, iris_r + edge, r))[..., None] * (iris - sclera)
    return out * smoothstep(pupil_r * 0.96, pupil_r * 1.04, r)[..., None]


def make_set(name, size=4096, eye_size=2048, out=ROOT / "textures"):
    tone, outer, inner, hair, seed, photo = SETS[name]
    m = GNM()
    folder = Path(out) / name
    folder.mkdir(parents=True, exist_ok=True)
    color, rough, height = skin(m, size, tone, seed, hair, photo)
    save(color, folder / "color.1001.jpg")
    save(rough, folder / "roughness.1001.jpg")
    save(height, folder / "height.1001.jpg")
    (folder / "info.json").write_text(json.dumps({"hair": hair, "skin_photo": f"MakeHuman {photo} (CC0)"}))  # read by materials.py
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
