#!/usr/bin/env python3
"""Soft tissue around the eye. Three effects, all stored as vertex displacements in assets/bulge.npz:

- socket_<side> (always on): GNM's template lids are puffy, 4-13 mm off the eyeball where a real
  lid is 1-3 mm. This sinks the hollow between lid and brow and the groove under the lower lid,
  never closer to the eyeball than MIN_SKIN, so the eye sits in a socket.
- bulge_<in|out|up|down>_<side>: the cornea stands 1.6 mm proud of the eyeball, so when the eye
  turns, the lid skin over it must lift. Without this the cornea cuts through the lid.
- drag_<in|out|up|down>_<side>: lids are stuck to the wet eyeball, so the skin near the lid edge is
  carried a little way round with it, fading out over a centimetre. This is the stretch and slide
  of the skin around a moving eye.

truegaze/motion.py `soft_tissue()` gives the bulge and drag weights for a gaze.

Run from the repo root: python3 tools/fit_bulge.py
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.fit_controls import LID_GAP, Eyeball, curve, lid_ring  # noqa: E402
from tools.make_hair import vertex_normals  # noqa: E402
from truegaze.gnm import GNM  # noqa: E402
from truegaze.motion import BULGE_PITCH, BULGE_YAW  # noqa: E402

MIN_SKIN = 0.0016     # m, thinnest the lid may get over the eyeball
DRAG = 0.30           # share of the eye's turn that the lid edge follows
DRAG_REACH = 0.008    # m, how far from the lid edge the drag fades out


def gaze_matrix(yaw_deg, pitch_deg):
    """GNM frame (Y up, Z forward): yaw > 0 turns toward +X (the character's left), pitch > 0 up."""
    y, p = np.radians(yaw_deg), np.radians(pitch_deg)
    ry = np.array([[np.cos(y), 0, np.sin(y)], [0, 1, 0], [-np.sin(y), 0, np.cos(y)]])
    rx = np.array([[1, 0, 0], [0, np.cos(p), np.sin(p)], [0, -np.sin(p), np.cos(p)]])
    return ry @ rx


def clearance(ball, points, turn):
    """Distance of points outside the eyeball after it has turned, and the outward direction."""
    rel = points - ball.centre
    dist = np.linalg.norm(rel, axis=1)
    local = (rel @ turn) / dist[:, None]  # the same points seen from the turned eyeball
    return dist - ball.radii[ball.tree.query(local, k=3)[1]].mean(axis=1), rel / dist[:, None]


def neighbours(m, idx):
    """For each vertex in idx, the positions (within idx) of the vertices it shares a quad edge with."""
    where = -np.ones(len(m.template), int)
    where[idx] = np.arange(len(idx))
    out = [set() for _ in idx]
    for q in m.quads[(where[m.quads] >= 0).all(axis=1)]:
        for k in range(4):
            out[where[q[k]]].add(where[q[(k + 1) % 4]])
            out[where[q[(k + 1) % 4]]].add(where[q[k]])
    return [np.array(sorted(s), int) for s in out]


def spread(push, near, rounds):
    for _ in range(rounds):
        push = 0.5 * push + 0.5 * np.array([push[n].mean() if len(n) else 0 for n in near])
    return push


if __name__ == "__main__":
    m = GNM()
    T = m.template
    normals = vertex_normals(m)
    idx_all, keys = [], {}
    for side in ("left", "right"):
        ball = Eyeball(m, side)
        sign = 1 if side == "left" else -1
        idx = np.flatnonzero(m.group("skin") & (np.linalg.norm(T - ball.centre, axis=1) < 0.03))
        near = neighbours(m, idx)
        P = T[idx]
        up, low = lid_ring(m, side)
        ring = T[np.r_[up, low]]
        edge = np.linalg.norm(P[:, None] - ring[None], axis=2).min(axis=1)  # distance to the lid edge

        # socket: sink the hollow above the upper lid and the groove under the lower lid
        rel = P - ball.centre
        below = curve(T[low])(P[:, 0]) - P[:, 1]
        above = P[:, 1] - curve(T[up])(P[:, 0])
        across = np.exp(-((sign * rel[:, 0] - 0.001) / 0.013) ** 2)
        want = 0.0035 * np.exp(-((above - 0.008) / 0.0045) ** 2) * across + 0.0012 * np.exp(-((below - 0.007) / 0.004) ** 2) * across
        want *= m.group("skin_exterior")[idx] * (rel[:, 2] > 0)
        room, _ = clearance(ball, P, np.eye(3))
        sink = spread(np.clip(np.minimum(want, room - MIN_SKIN), 0, None), near, 3)
        socket = -sink[:, None] * normals[idx]
        keys[f"socket_{side}"] = socket.astype(np.float32)
        P = P + socket  # everything below is fitted on the sunk shape, which is what is rendered
        print(f"{side} socket: sunk up to {sink.max() * 1000:.2f} mm, {int((sink > 2e-4).sum())} vertices")

        rest, unit = clearance(ball, P, np.eye(3))
        floor = np.minimum(rest, LID_GAP)  # never ask for more room than the lid has at rest
        follow = DRAG * np.exp(-(edge / DRAG_REACH) ** 2)
        # "in" is toward the nose: negative yaw for the left eye, positive for the right
        for name, (yaw, pitch) in {"in": (-sign * BULGE_YAW, 0), "out": (sign * BULGE_YAW, 0),
                                   "up": (0, BULGE_PITCH), "down": (0, -BULGE_PITCH)}.items():
            push = np.clip(floor - clearance(ball, P, gaze_matrix(yaw, pitch))[0], 0, None)
            hit = int((push > 1e-5).sum())
            for _ in range(8):  # spread into a soft mound, never lowering the push that is needed
                push = np.maximum(push, 0.5 * push + 0.5 * np.array([push[n].mean() if len(n) else 0 for n in near]))
            keys[f"bulge_{name}_{side}"] = (push[:, None] * unit).astype(np.float32)
            assert push.max() < 0.003, "lift larger than the cornea bulge: something is wrong"
            # drag: each vertex turns about the eye centre by its share of the gaze angle
            share = follow * (0.5 if pitch else 1.0)  # lids already follow vertical gaze through their own controls
            moved = np.stack([gaze_matrix(f * yaw, f * pitch) @ r for f, r in zip(share, P - ball.centre)]) + ball.centre
            keys[f"drag_{name}_{side}"] = (moved - P).astype(np.float32)
            print(f"{side} {name}: {hit} vertices cut by the cornea, max lift {push.max() * 1000:.2f} mm; "
                  f"skin drag up to {np.linalg.norm(moved - P, axis=1).max() * 1000:.2f} mm")
        idx_all.append(idx)
    n_left = len(idx_all[0])
    out = {"index": np.concatenate(idx_all).astype(np.int32)}
    for name, d in keys.items():  # pad each key to the full index list (zeros for the other eye)
        full = np.zeros((len(out["index"]), 3), np.float32)
        (full[:n_left] if name.endswith("left") else full[n_left:])[:] = d
        out[name] = full
    np.savez_compressed(ROOT / "assets" / "bulge.npz", **out)
