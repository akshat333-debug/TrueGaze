#!/usr/bin/env python3
"""Finds, for every GNM skin vertex, the matching place in MakeHuman's skin texture layout.

MakeHuman's skins (CC0) are photo-quality but drawn for MakeHuman's head, not GNM's. This fits
the GNM head onto the MakeHuman head in 3D and records where each GNM vertex lands in
MakeHuman's UV map. truegaze/textures.py then pulls any MakeHuman skin into GNM's UV layout.

Fit: scale and place by the eye centres, rigid refinement, then a smooth deformation that pulls
GNM onto the MakeHuman surface. Eyelid edges, the lip line and the nose tip are pinned to their
MakeHuman counterparts, because a texture that is a millimetre off at the lid edge looks wrong.

Output: assets/skin_transfer.npz (uv per GNM vertex, valid flag). Run: python3 tools/transfer_skin.py
"""
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix, diags
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.fit_controls import lid_ring  # noqa: E402
from tools.make_hair import unit, vertex_normals  # noqa: E402
from truegaze.gnm import GNM  # noqa: E402
from truegaze.textures import makehuman_file  # noqa: E402

PIN = 30.0  # weight of a pinned landmark against 1.0 for an ordinary surface match


def load_makehuman():
    """Vertices in metres, UVs, and quads (vertex index, uv index) per named group."""
    V, VT, groups, name = [], [], {}, None
    for line in open(makehuman_file("base.obj")):
        p = line.split()
        if not p:
            continue
        if p[0] == "v":
            V.append(p[1:4])
        elif p[0] == "vt":
            VT.append(p[1:3])
        elif p[0] == "g":
            name = p[1]
        elif p[0] == "f":
            groups.setdefault(name, []).append([[int(i) - 1 for i in c.split("/")[:2]] for c in p[1:]])
    return np.array(V, float) * 0.1, np.array(VT, float), {k: np.array(v) for k, v in groups.items()}


def curve_at(points, t):
    """Points along a polyline at fractions t of its length."""
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    return np.stack([np.interp(t, s / s[-1], points[:, i]) for i in range(3)], axis=1)


def fractions(points):
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    return s / s[-1]


def seam_vertices(quads):
    """Vertices on edges whose two faces disagree about the UV: the cuts of the UV layout."""
    seen, out = {}, set()
    for q in quads:
        for k in range(4):
            (a, ta), (b, tb) = q[k], q[(k + 1) % 4]
            key, uv = (min(a, b), max(a, b)), ((ta, tb) if a < b else (tb, ta))
            if seen.setdefault(key, uv) != uv:
                out.update(key)
    return np.array(sorted(out))


if __name__ == "__main__":
    m = GNM()
    T = m.template
    V, VT, groups = load_makehuman()
    eye = {s: V[np.unique(groups[f"helper-{s[0]}-eye"][:, :, 0])].mean(axis=0) for s in ("left", "right")}
    gnm_eye = {s: m.joints[m.joint_names.index(f"{s}_eye")] for s in ("left", "right")}

    # 1. MakeHuman into GNM's space: scale by the distance between the eyes, eye midpoints together
    scale = np.linalg.norm(gnm_eye["left"] - gnm_eye["right"]) / np.linalg.norm(eye["left"] - eye["right"])
    mid, gnm_mid = (eye["left"] + eye["right"]) / 2, (gnm_eye["left"] + gnm_eye["right"]) / 2
    V = (V - mid) * scale + gnm_mid
    body = groups["body"]
    head = body[(V[body[:, :, 0], 1] > gnm_mid[1] - 0.20).all(axis=1)]

    def surface():
        """Dense samples of the MakeHuman head surface with their UVs."""
        w = (np.arange(6) + 0.5) / 6
        a, b = [x.ravel() for x in np.meshgrid(w, w)]
        weights = np.stack([(1 - a) * (1 - b), a * (1 - b), a * b, (1 - a) * b], axis=1)  # (36, 4)
        return np.einsum("sk,qkc->qsc", weights, V[head[:, :, 0]]).reshape(-1, 3), np.einsum("sk,qkc->qsc", weights, VT[head[:, :, 1]]).reshape(-1, 2)

    skin = np.flatnonzero(m.group("skin"))
    front = skin[(T[skin, 2] > gnm_mid[2] - 0.03) & m.group("skin_exterior")[skin]]
    for _ in range(12):  # 2. rigid refinement on the front of the face (Kabsch), about the eye midpoint
        pts, _ = surface()
        near = pts[cKDTree(pts).query(T[front])[1]]
        a, b = near - near.mean(0), T[front] - T[front].mean(0)
        u, _, vt = np.linalg.svd(a.T @ b)
        R = (u @ np.diag([1, 1, np.sign(np.linalg.det(u @ vt))]) @ vt).T
        V = (V - near.mean(0)) @ R.T + T[front].mean(0)
    pts, uvs = surface()
    tree = cKDTree(pts)
    print(f"scale {scale:.4f}; after rigid fit, front of face is {np.median(tree.query(T[front])[0]) * 1000:.2f} mm (median) from MakeHuman")

    # 3. landmarks: GNM vertex -> position on the MakeHuman head
    pins = {}
    body_tree = cKDTree(V[np.unique(head[:, :, 0])])
    for side in ("left", "right"):
        sign = 1 if side == "left" else -1
        for upper, group in ((True, "eyelashes-2"), (False, "eyelashes-1")):
            lash = V[np.unique(groups[f"helper-{side[0]}-{group}"][:, :, 0])]
            root = lash[body_tree.query(lash)[0] < np.median(body_tree.query(lash)[0])]  # the edge on the lid
            root = root[np.argsort(sign * root[:, 0])]
            ring = lid_ring(m, side)[0 if upper else 1]
            ring = ring[np.argsort(sign * T[ring, 0])]
            pins.update(zip(ring.tolist(), curve_at(root, fractions(T[ring]))))
    lip_mh = seam_vertices(head)
    lip_mh = V[lip_mh[(np.abs(V[lip_mh, 0] - gnm_mid[0]) < 0.035) & (V[lip_mh, 2] > gnm_mid[2] - 0.01) & (V[lip_mh, 1] < gnm_mid[1] - 0.045)]]
    lip_mh = lip_mh[np.argsort(lip_mh[:, 0])]
    sel = m.quad_tiles() == 1001
    uv_of = {}
    for v, uv in zip(m.quads[sel].ravel(), m.quad_uvs[sel].reshape(-1, 2)):
        uv_of.setdefault(int(v), set()).add(tuple(np.round(uv, 5)))
    seam = np.array([v for v in uv_of if len(uv_of[v]) > 1])
    lip_gnm = np.intersect1d(seam, np.flatnonzero(m.group("upper_lip") | m.group("lower_lip")))
    half = np.abs(T[lip_gnm, 0] - gnm_mid[0]).max()
    half_mh = np.abs(lip_mh[:, 0] - gnm_mid[0]).max()
    x = (T[lip_gnm, 0] - gnm_mid[0]) / half * half_mh + gnm_mid[0]
    pins.update(zip(lip_gnm.tolist(), np.stack([x, np.interp(x, lip_mh[:, 0], lip_mh[:, 1]), np.interp(x, lip_mh[:, 0], lip_mh[:, 2])], axis=1)))
    nose = np.flatnonzero(m.group("nose_region"))
    centre = np.unique(head[:, :, 0])
    centre = centre[(np.abs(V[centre, 0] - gnm_mid[0]) < 0.01) & (V[centre, 1] < gnm_mid[1]) & (V[centre, 1] > lip_mh[:, 1].mean())]
    pins[int(nose[np.argmax(T[nose, 2])])] = V[centre[np.argmax(V[centre, 2])]]
    print(f"landmarks: {len(pins)} (lids, {len(lip_gnm)} lip line, nose tip); MakeHuman lip line points: {len(lip_mh)}")

    # 4. smooth deformation of the GNM skin onto MakeHuman, stiff first, then looser
    where = -np.ones(len(T), int)
    where[skin] = np.arange(len(skin))
    quads = where[m.quads[(where[m.quads] >= 0).all(axis=1)]]
    i, j = np.concatenate([quads[:, k] for k in range(4)]), np.concatenate([quads[:, (k + 1) % 4] for k in range(4)])
    A = coo_matrix((np.ones(len(i)), (i, j)), shape=(len(skin),) * 2).tocsr()
    A = ((A + A.T) > 0).astype(float)
    L = diags(np.asarray(A.sum(axis=1)).ravel()) - A
    normals = vertex_normals(m)[skin]
    X, D = T[skin], np.zeros((len(skin), 3))
    pin_idx, pin_pos = where[np.array(list(pins))], np.array(list(pins.values()))
    for stiffness in (60, 25, 10, 4, 2, 1):
        dist, near = tree.query(X + D)
        target, weight = pts[near], (dist < 0.012).astype(float)
        target[pin_idx], weight[pin_idx] = pin_pos, PIN
        solve = lambda rhs: spsolve((diags(weight) + stiffness * L).tocsc(), weight * rhs)
        D = np.stack([solve(target[:, c] - X[:, c]) for c in range(3)], axis=1)
    dist, near = tree.query(X + D)
    print(f"final distance to MakeHuman: median {np.median(dist) * 1000:.2f} mm, 95% {np.quantile(dist, 0.95) * 1000:.2f} mm; "
          f"landmark error max {np.abs((X + D)[pin_idx] - pin_pos).max() * 1000:.2f} mm; largest move {np.linalg.norm(D, axis=1).max() * 1000:.1f} mm")

    uv = np.zeros((len(T), 2), np.float32)
    valid = np.zeros(len(T), bool)
    uv[skin], valid[skin] = uvs[near], dist < 0.004
    np.savez_compressed(ROOT / "assets" / "skin_transfer.npz", uv=uv, valid=valid)
    print(f"valid vertices: {int(valid.sum())} of {len(skin)} skin vertices")
