#!/usr/bin/env python3
"""Builds eyelashes, eyebrows and the tear line as one mesh that follows every eye control.

GNM has no hair. Each strand is a thin tube. Lashes and the tear line are rebuilt from the lid
margin for every control (so they turn with the lid as it closes); brow hairs ride on the skin
under them. Output: assets/hair.npz with rest vertices, quads, a material index per quad
(0 hair, 1 tear film) and one displacement array per control in assets/controls.npz.

Run from the repo root: python3 tools/make_hair.py   (after tools/fit_controls.py)
Numbers are human averages: upper lashes 8-10 mm in several rows, lower 5-6 mm, brow hairs 5-8 mm.
"""
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.fit_controls import lid_ring  # noqa: E402
from truegaze.gnm import GNM  # noqa: E402

MM = 0.001
K_LASH, K_BROW, K_TEAR = 7, 5, 48


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
    verts = centres[:, :, None] + radii[:, :, None, None] * ring
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
    n = 150 if upper else 65
    u = np.sort(rng.uniform(0.10, 0.98, n) if upper else rng.uniform(0.22, 0.96, n))
    mid = np.sin(np.pi * u ** 0.85)                                  # longest in the middle of the lid
    length = (9.5 if upper else 5.5) * MM * (0.5 + 0.5 * mid) * rng.uniform(0.8, 1.15, n)
    out = rng.uniform(0.9, 1.6, n) * MM                              # follicles sit on the front edge of the lid,
    row = rng.uniform(0.0, 0.6, n) * MM                              # across the lid's thickness, in a few rows
    clump = np.repeat(rng.normal(0, 9, n // 3 + 1), 3)[:n]          # neighbours lean together
    lean = np.radians(-25 + 65 * u + clump + rng.normal(0, 5 if upper else 12, n))   # fan out toward the outer corner
    start = np.radians(rng.normal(-20 if upper else -5, 6, n))      # leave the lid pointing forward
    end = np.radians(rng.normal(45 if upper else 30, 9, n))         # then curl away from the opening
    s = np.linspace(0, 1, K_LASH - 1)
    phi = start[:, None] + (end - start)[:, None] * s

    def centres(V):
        p, t, r, away = lid.frame(V, u)
        root = p + away * row[:, None] + r * out[:, None]
        d = np.cos(phi)[..., None] * r[:, None] + np.sin(phi)[..., None] * away[:, None] + np.tan(lean)[:, None, None] * t[:, None] * s[:, None]
        steps = unit(d) * (length / (K_LASH - 1))[:, None, None]
        return np.concatenate([root[:, None], root[:, None] + np.cumsum(steps, axis=1)], axis=1)

    radii = (0.065 if upper else 0.05) * MM * np.linspace(1, 0.15, K_LASH) * rng.uniform(0.8, 1.2, (n, 1))
    return centres, radii


def tear_line(lid):
    """A thin clear bead where the lid edge meets the eyeball: it catches the light like tear fluid."""
    u = np.linspace(0.04, 0.97, K_TEAR)
    radius = (0.26 if lid.up < 0 else 0.15) * MM
    blur = np.exp(-0.5 * (np.arange(-4, 5) / 2.0) ** 2)

    def centres(V):
        p, t, r, away = lid.frame(V, u)
        c = np.pad(p - away * 0.1 * MM + r * 0.2 * MM, ((4, 4), (0, 0)), mode="edge")  # smooth out the mesh's corners
        return np.stack([np.convolve(c[:, i], blur / blur.sum(), mode="valid") for i in range(3)], axis=-1)[None]

    return centres, (radius * np.sin(np.pi * np.linspace(0.02, 0.98, K_TEAR)) ** 0.3)[None]


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
    brow_uv, lash_uv = [], []
    for side in ("left", "right"):
        for upper in (True, False):
            lid = Lid(m, side, upper)
            parts.append((*lashes(lid, rng), 3, 0))
            ring = skin_uv(m)[lid.idx]  # densely resampled, so the lash line is a line and not a row of dots
            fine = np.linspace(0, len(ring) - 1, 12 * len(ring))
            lash_uv.append(np.stack([np.interp(fine, np.arange(len(ring)), ring[:, i]) for i in range(2)], axis=1))
            parts.append((*tear_line(lid), 6, 1))
        parts.append((*brows(m, side, rng, normals), 3, 0))
        brow_uv.append(parts[-1][0].root_uv)

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
           "brow_uv": np.concatenate(brow_uv).astype(np.float32), "lash_uv": np.concatenate(lash_uv).astype(np.float32)}
    assert np.isfinite(out["verts"]).all()
    for name, coef in np.load(ROOT / "assets" / "controls.npz").items():
        V = m.template + np.tensordot(coef, m.expression_basis, 1)
        moved = [np.repeat((fn(V) - c).reshape(-1, 3), sides, axis=0) for (fn, _, sides, _), c in zip(parts, rest)]
        out[f"move_{name}"] = np.concatenate(moved).astype(np.float32)
        assert np.isfinite(out[f"move_{name}"]).all()
        print(name, "max hair movement mm:", round(float(np.abs(out[f"move_{name}"]).max() * 1000), 2))
    np.savez_compressed(ROOT / "assets" / "hair.npz", **out)
    print("strands:", sum(len(c) for c in rest), "vertices:", len(out["verts"]))
