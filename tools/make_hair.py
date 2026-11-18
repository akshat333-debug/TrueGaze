#!/usr/bin/env python3
"""Builds eyelashes, eyebrows and the tear line as one mesh that follows every eye control.

GNM has no hair. Each strand is a thin tube. Lashes and the tear line are rebuilt from the lid
margin for every control (so they turn with the lid as it closes); brow hairs ride on the skin
under them. Output: assets/hair.npz with rest vertices, quads, a material index per quad
(0 hair, 1 tear film, 2 facial down, 3 caruncle) and one displacement array per control in assets/controls.npz.

Run from the repo root: python3 tools/make_hair.py   (after tools/fit_controls.py and tools/fit_bulge.py)
Numbers are human averages: upper lashes 8-10 mm in several rows, lower 5-6 mm, brow hairs 5-8 mm.
"""
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.fit_controls import lid_ring  # noqa: E402
from truegaze.gnm import GNM  # noqa: E402

MM = 0.001
K_LASH, K_BROW, K_TEAR = 16, 5, 48


def unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def tubes(centres, radii, sides):
    """centres (n, K, 3), radii (n, K) -> vertices (n*K*sides, 3), quads (m, 4)."""
    n, k, _ = centres.shape
    d = unit(np.gradient(centres, axis=1))
    a = unit(np.cross(d, [0.0, 0.31, 0.95]))
    b = np.cross(d, a)
    ang = 2 * np.pi * np.arange(sides) / sides
    ring = np.cos(ang)[:, None] * a[:, :, None] + np.sin(ang)[:, None] * b[:, :, None]
    # radii may instead be ready-made offsets (n, K, sides, 3) for a cross-section that is not round
    verts = centres[:, :, None] + (radii if radii.ndim == 4 else radii[:, :, None, None] * ring)
    i, kk, j = np.meshgrid(np.arange(n), np.arange(k - 1), np.arange(sides), indexing="ij")
    at = lambda kk, j: (i * k + kk) * sides + j % sides
    quads = np.stack([at(kk, j), at(kk, j + 1), at(kk + 1, j + 1), at(kk + 1, j)], axis=-1)
    return verts.reshape(-1, 3), quads.reshape(-1, 4)


class Lid:
    """One lid margin as a curve from the inner to the outer corner, with a frame at each point:
    t along the margin, r straight out of the eyeball, away = along the lid, leaving the opening."""

    def __init__(self, m, side, upper):
        sign = 1 if side == "left" else -1
        idx = lid_ring(m, side)[0 if upper else 1]
        self.idx = idx[np.argsort(sign * m.template[idx, 0])]
        self.centre = m.joints[m.joint_names.index(f"{side}_eye")]
        self.up = 1 if upper else -1
        self.rest = m.template
        # The margin: GNM's lid is about 2 mm thick, with a flat shelf between the eyeball and the lid's front
        # edge. For each ring vertex find that front edge: the skin vertex straight out of the eyeball from it.
        skin = np.flatnonzero(m.group("skin_exterior"))
        P = m.template[self.idx]
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
        self.s = s / s[-1]
        p, t, r, away = self.frame(m.template, self.s)
        self.front, depth = self.idx.copy(), np.zeros(len(self.idx))
        for j in range(len(self.idx)):
            d = m.template[skin] - p[j]
            along, out = d @ away[j], d @ r[j]
            ok = (np.abs(d @ t[j]) < 1.5 * MM) & (along > -1.5 * MM) & (along < 0.5 * MM) & (out > 0) & (out < 2.9 * MM)
            if ok.any():
                self.front[j], depth[j] = skin[ok][np.argmax(out[ok])], out[ok].max()
        self.depth = gaussian_filter1d(depth, 1.5, mode="nearest")

    def frame(self, V, u):
        P = V[self.idx]
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
        at = lambda x: np.stack([np.interp(x, s / s[-1], P[:, i]) for i in range(3)], axis=-1)
        p, t = at(u), unit(at(u + 0.03) - at(u - 0.03))
        r = unit(p - self.centre)
        away = unit(np.cross(t, r))
        away *= np.sign(away[:, 1:2]) * self.up
        return p, t, r, away


def lashes(lid, rng):
    """Returns a function V -> centres (n, K, 3), and radii (n, K)."""
    upper = lid.up > 0
    n = 190 if upper else 80
    lo, hi = (0.10, 0.98) if upper else (0.22, 0.96)
    # one per slot (pure chance leaves bald gaps); lower lashes stray further from their slot, or they read as a comb
    u = np.sort(np.clip(lo + (hi - lo) * (np.arange(n) + rng.uniform(0, 1, n) + (0 if upper else rng.normal(0, 1.2, n))) / n, lo, hi))
    mid = np.sin(np.pi * u ** 0.85)                                  # longest in the middle of the lid
    length = (8.0 if upper else 5.0) * MM * (0.5 + 0.5 * mid) * rng.uniform(0.55, 1.15, n)  # uneven: lashes are at every stage of growth
    out = np.maximum(np.interp(u, lid.s, lid.depth) * rng.uniform(0.75, 1.0, n), 0.9 * MM)  # follicles sit on the front edge of the lid margin,
    row = rng.uniform(0.0, 0.6, n) * MM                              # across the lid's thickness, in a few rows
    clump = np.repeat(rng.normal(0, 4, n // 3 + 1), 3)[:n]  # neighbours lean together, a little: strong bunches look like combs
    lean = np.radians(-25 + 65 * u + clump + rng.normal(0, 5 if upper else 7, n))   # fan out toward the outer corner
    start = np.radians(rng.normal(-14 if upper else -5, 5, n))       # leave the lid pointing forward
    end = np.radians(rng.normal(27 if upper else 18, 9 if upper else 5, n))         # then curl away from the opening
    s = np.linspace(0, 1, K_LASH - 1)
    phi = start[:, None] + (end - start)[:, None] * s ** 0.6        # most of the bend is near the root; the tip runs straight, no hook

    def centres(V):
        p, t, r, away = lid.frame(V, u)
        root = p + away * row[:, None] + r * out[:, None]
        d = np.cos(phi)[..., None] * r[:, None] + np.sin(phi)[..., None] * away[:, None] + np.tan(lean)[:, None, None] * t[:, None] * s[:, None]
        steps = unit(d) * (length / (K_LASH - 1))[:, None, None]
        return np.concatenate([root[:, None], root[:, None] + np.cumsum(steps, axis=1)], axis=1)

    # a lash keeps its thickness for two thirds of its length and only then tapers to a point
    radii = (0.06 if upper else 0.048) * MM * (1 - 0.9 * np.linspace(0, 1, K_LASH) ** 2.5) * rng.uniform(0.8, 1.2, (n, 1))
    return centres, radii


def tear_line(lid):
    """The tear film where the lid edge meets the eyeball. Tear fluid wets both surfaces, so it fills the
    corner between them with a concave face (a meniscus); the lower one is deeper, because fluid collects there."""
    u = np.linspace(0.04, 0.97, K_TEAR)
    radius = (0.50 if lid.up < 0 else 0.26) * MM
    blur = np.exp(-0.5 * (np.arange(-4, 5) / 2.0) ** 2)

    def centres(V):
        p, t, r, away = lid.frame(V, u)
        c = np.pad(p - away * 0.1 * MM + r * 0.2 * MM, ((4, 4), (0, 0)), mode="edge")  # smooth out the mesh's corners
        return np.stack([np.convolve(c[:, i], blur / blur.sum(), mode="valid") for i in range(3)], axis=-1)[None]

    # cross-section: the corner itself, then an arc from the lid margin (height h up the lid) round to the
    # eyeball (h out into the opening), bowed toward the corner. r = out of the eyeball, away = up the lid.
    smooth = lambda x: np.stack([np.convolve(np.pad(x, ((4, 4), (0, 0)), mode="edge")[:, i], blur / blur.sum(), mode="valid") for i in range(3)], axis=-1)
    _, _, r, away = lid.frame(lid.rest, u)
    r, away = unit(smooth(r)), unit(smooth(away))
    h = (radius * np.sin(np.pi * np.linspace(0.02, 0.98, K_TEAR)) ** 0.3)[:, None, None]
    a = np.linspace(0, np.pi / 2, 5)[None, :, None]
    arc = h * (r[:, None] * (1 - np.sin(a)) + 1.15 * away[:, None] * (1 - np.cos(a)) * -1)   # from h*r round to -1.15*h*away
    ring = np.concatenate([np.zeros((K_TEAR, 1, 3)), arc], axis=1) - 0.06 * MM * (r - away)[:, None]  # sunk a little into both
    return centres, ring[None]


def brows(m, side, rng, normals):
    """Brow hairs lying along the brow ridge. Returns V -> centres (n, K, 3), and radii."""
    sign = 1 if side == "left" else -1
    T = m.template
    centre = m.joints[m.joint_names.index(f"{side}_eye")]
    n = 1200
    u = rng.uniform(0, 1, n) ** 0.9                              # 0 = by the nose, 1 = tail at the temple
    w = (rng.uniform(-1, 1, n) + rng.uniform(-1, 1, n)) / 2       # across the brow, denser in the middle
    x = (-13 + 36 * u) * MM
    y = (15 + 5 * np.sin(np.pi * 0.8 * u) - 3 * u ** 3) * MM + w * 5.5 * MM * (1 - 0.72 * u)
    skin = np.flatnonzero(m.group("skin_exterior") & (T[:, 2] > centre[2] - 0.01))
    xy = np.stack([centre[0] + sign * x, centre[1] + y], axis=1)
    dist, near = cKDTree(T[skin, :2]).query(xy, k=3)
    weight = 1 / (dist + 1e-6)
    weight /= weight.sum(1, keepdims=True)
    near = skin[near]
    root = (T[near] * weight[..., None]).sum(1)
    normal = unit((normals[near] * weight[..., None]).sum(1))

    # growth direction: up at the head of the brow, sideways along the body, both edges combing to the middle
    grow = np.radians(60 - 54 * np.clip(u / 0.35, 0, 1) ** 0.8 - 28 * w - 18 * u + rng.normal(0, 9, n))
    flat = np.stack([sign * np.cos(grow), np.sin(grow), np.zeros(n)], axis=1)
    flat = unit(flat - (flat * normal).sum(1, keepdims=True) * normal)
    length = 6.5 * MM * (0.75 + 0.5 * np.sin(np.pi * u) - 0.25 * u) * rng.uniform(0.6, 1.1, n)
    lift = np.radians(np.linspace(22, -8, K_BROW - 1))            # rises off the skin, then lies back down
    steps = (np.cos(lift)[:, None] * flat[:, None] + np.sin(lift)[:, None] * normal[:, None]) * (length / (K_BROW - 1))[:, None, None]
    rest = np.concatenate([root[:, None], root[:, None] + np.cumsum(steps, axis=1)], axis=1) + normal[:, None] * 0.05 * MM

    def centres(V):
        return rest + ((V - T)[near] * weight[..., None]).sum(1)[:, None]

    centres.root_uv = (skin_uv(m)[near] * weight[..., None]).sum(1)
    return centres, 0.03 * MM * np.linspace(1, 0.2, K_BROW) * rng.uniform(0.8, 1.3, (n, 1))


def fuzz(m, rng, normals):
    """Fine down on the skin around the eyes, growing downward. Returns V -> centres (n, 3, 3), and radii."""
    T = m.template
    mid = m.joints[2:4].mean(axis=0)
    eyes = [m.joints[m.joint_names.index(f"{s}_eye")] for s in ("left", "right")]
    ok = m.group("skin_exterior") & (T[:, 2] > mid[2] - 0.025) & (np.abs(T[:, 1] - mid[1]) < 0.05)
    ok &= np.min([np.linalg.norm(T - e, axis=1) for e in eyes], axis=0) > 0.016  # not on the lids
    pool = np.flatnonzero(ok)
    tri = m.quads[np.isin(m.quads, pool).all(axis=1)]
    pick = tri[rng.integers(len(tri), size=4500)]
    w = rng.dirichlet(np.ones(4), size=len(pick))
    root, normal = (T[pick] * w[..., None]).sum(1), unit((normals[pick] * w[..., None]).sum(1))
    down = np.array([0.0, -1.0, 0.0]) + rng.normal(0, 0.35, (len(pick), 3))
    flat = unit(down - (down * normal).sum(1, keepdims=True) * normal)
    step = (flat * 0.8 + normal * 0.6) * (rng.uniform(0.5, 1.5, (len(pick), 1)) * MM / 2)
    rest = np.stack([root, root + step, root + 1.9 * step - normal * 0.1 * MM], axis=1)

    def centres(V):
        return rest + ((V - T)[pick] * w[..., None]).sum(1)[:, None]

    return centres, 0.006 * MM * np.array([1.0, 0.8, 0.3]) * np.ones((len(pick), 1))


def caruncle(upper, lower):
    """The pink fleshy bump in the inner corner of the eye, between the two lids. GNM has none."""
    u = np.linspace(0.035, 0.13, 7)  # tucked inside the corner, not at its tip

    def centres(V):
        (p1, _, r1, _), (p2, _, r2, _) = upper.frame(V, u), lower.frame(V, u)
        return ((p1 + p2) / 2 - unit(r1 + r2) * 0.25 * MM)[None]  # mostly sunk between the lids

    return centres, (np.array([0.3, 0.65, 0.85, 0.85, 0.7, 0.45, 0.12]) * MM)[None]


def skin_uv(m):
    """UV position of every vertex in the skin tile (seams are far from the brows and lids)."""
    sel = m.quad_tiles() == 1001
    uv = np.zeros((len(m.template), 2))
    uv[m.quads[sel].ravel()] = m.quad_uvs[sel].reshape(-1, 2)
    return uv


def vertex_normals(m):
    q = m.template[m.quads]
    face = np.cross(q[:, 2] - q[:, 0], q[:, 3] - q[:, 1])
    out = np.zeros_like(m.template)
    for k in range(4):
        np.add.at(out, m.quads[:, k], face)
    out = unit(out + 1e-12)
    return out if out[m.group("nose_region"), 2].mean() > 0 else -out  # the face looks along +Z


if __name__ == "__main__":
    m = GNM()
    rng = np.random.default_rng(7)
    normals = vertex_normals(m)
    parts = []  # (centres function, radii, tube sides, material)
    brow_uv, lash_uv, lid_uv, margin_uv = [], [], [], []
    for side in ("left", "right"):
        lids, rings, fronts = [Lid(m, side, True), Lid(m, side, False)], [], []
        for lid in lids:
            parts.append((*lashes(lid, rng), 3, 0))
            parts.append((*tear_line(lid), 6, 1))
            rings.append(gaussian_filter1d(skin_uv(m)[lid.idx], 2.0, axis=0, mode="nearest"))  # smoothed: the mesh edge zigzags
            fronts.append(gaussian_filter1d(skin_uv(m)[lid.front], 2.0, axis=0, mode="nearest"))
            print(side, "upper" if lid.up > 0 else "lower", "margin depth mm:", np.round(lid.depth[::4] / MM, 1))
        parts.append((*caruncle(*lids), 8, 3))
        # no plica: a ridge on the eyeball read as a bright bar in the inner corner whatever its size (18 Nov)
        for ring, front in zip(rings, fronts):
            resample = lambda r, n: np.stack([np.interp(np.linspace(0, len(r) - 1, n), np.arange(len(r)), r[:, i]) for i in range(2)], axis=1)
            lash_uv.append(resample(front, 12 * len(ring)))  # lashes root on the front edge of the margin
            lid_uv.append(resample(ring, 64))
            margin_uv.append(resample(front, 64))
        parts.append((*brows(m, side, rng, normals), 3, 0))
        brow_uv.append(parts[-1][0].root_uv)

    parts.append((*fuzz(m, rng, normals), 3, 2))

    verts, quads, mats, rest = [], [], [], []
    offset = 0
    for fn, radii, sides, mat in parts:
        c = fn(m.template)
        v, q = tubes(c, radii, sides)
        verts.append(v), quads.append(q + offset), mats.append(np.full(len(q), mat)), rest.append(c)
        offset += len(v)
    out = {"verts": np.concatenate(verts).astype(np.float32), "quads": np.concatenate(quads).astype(np.int32),
           "material": np.concatenate(mats).astype(np.int8),
           # where hair grows, in skin UV space: the skin texture is darkened there (follicles, lash line)
           "brow_uv": np.concatenate(brow_uv).astype(np.float32), "lash_uv": np.concatenate(lash_uv).astype(np.float32),
           # lid edges as 64-point curves: left upper, left lower, right upper, right lower
           "lid_uv": np.stack(lid_uv).astype(np.float32),
           # the front edge of each lid margin, same order: between it and lid_uv lies the wet shelf
           "margin_uv": np.stack(margin_uv).astype(np.float32)}
    assert np.isfinite(out["verts"]).all()
    for name, coef in np.load(ROOT / "assets" / "controls.npz").items():
        V = m.template + np.tensordot(coef, m.expression_basis, 1)
        moved = [np.repeat((fn(V) - c).reshape(-1, 3), sides, axis=0) for (fn, _, sides, _), c in zip(parts, rest)]
        out[f"move_{name}"] = np.concatenate(moved).astype(np.float32)
        assert np.isfinite(out[f"move_{name}"]).all()
        print(name, "max hair movement mm:", round(float(np.abs(out[f"move_{name}"]).max() * 1000), 2))
    soft = np.load(ROOT / "assets" / "bulge.npz")  # socket, bulge and drag keys move the skin too (tools/fit_bulge.py)
    for name in (k for k in soft.files if k != "index"):
        V = m.template.copy()
        V[soft["index"]] += soft[name]
        out[f"move_{name}"] = np.concatenate([np.repeat((fn(V) - c).reshape(-1, 3), sides, axis=0) for (fn, _, sides, _), c in zip(parts, rest)]).astype(np.float32)
    np.savez_compressed(ROOT / "assets" / "hair.npz", **out)
    print("strands:", sum(len(c) for c in rest), "vertices:", len(out["verts"]))
