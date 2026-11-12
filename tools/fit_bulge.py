#!/usr/bin/env python3
"""Eyelid bulge: the cornea stands 1.6 mm proud of the eyeball, so when the eye turns, the lid skin
over it must lift. Without this the cornea pokes through the lid at large gaze angles.

For each eye and each of four gaze directions at the limit angle, finds the skin the turned
cornea would cut into and pushes it out just enough, then spreads the push into a soft mound.
Output: assets/bulge.npz with the affected vertex indices and one displacement array per key
(bulge_<in|out|up|down>_<side>). truegaze/motion.py `bulge()` gives the weights for a gaze.

Run from the repo root: python3 tools/fit_bulge.py
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.fit_controls import LID_GAP, Eyeball  # noqa: E402
from truegaze.gnm import GNM  # noqa: E402
from truegaze.motion import BULGE_PITCH, BULGE_YAW  # noqa: E402


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


if __name__ == "__main__":
    m = GNM()
    T = m.template
    idx_all, keys = [], {}
    for side in ("left", "right"):
        ball = Eyeball(m, side)
        sign = 1 if side == "left" else -1
        idx = np.flatnonzero(m.group("skin") & (np.linalg.norm(T - ball.centre, axis=1) < 0.024))
        near = neighbours(m, idx)
        rest, unit = clearance(ball, T[idx], np.eye(3))
        floor = np.minimum(rest, LID_GAP)  # never ask for more room than the lid has at rest
        # "in" is toward the nose: negative yaw for the left eye, positive for the right
        for name, (yaw, pitch) in {"in": (-sign * BULGE_YAW, 0), "out": (sign * BULGE_YAW, 0),
                                   "up": (0, BULGE_PITCH), "down": (0, -BULGE_PITCH)}.items():
            push = np.clip(floor - clearance(ball, T[idx], gaze_matrix(yaw, pitch))[0], 0, None)
            hit = int((push > 1e-5).sum())
            for _ in range(8):  # spread into a soft mound, never lowering the push that is needed
                push = np.maximum(push, 0.5 * push + 0.5 * np.array([push[n].mean() if len(n) else 0 for n in near]))
            keys[f"bulge_{name}_{side}"] = (push[:, None] * unit).astype(np.float32)
            print(f"{side} {name}: {hit} vertices cut by the cornea, max lift {push.max() * 1000:.2f} mm")
            assert push.max() < 0.003, "lift larger than the cornea bulge: something is wrong"
        idx_all.append(idx)
    n_left = len(idx_all[0])
    out = {"index": np.concatenate(idx_all).astype(np.int32)}
    for name, d in keys.items():  # pad each key to the full index list (zeros for the other eye)
        full = np.zeros((len(out["index"]), 3), np.float32)
        (full[:n_left] if name.endswith("left") else full[n_left:])[:] = d
        out[name] = full
    np.savez_compressed(ROOT / "assets" / "bulge.npz", **out)
