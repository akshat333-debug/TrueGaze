#!/usr/bin/env python3
"""Derives named eye controls from GNM's unnamed statistical eye components.

Each control is a coefficient vector in GNM's own 383-dim expression space, so it works on any
GNM head, not only in our scene. Output: assets/controls.npz.

Run from the repo root: python3 tools/fit_controls.py
"""
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from truegaze.gnm import GNM, LEFT_EYE, RIGHT_EYE  # noqa: E402

LID_GAP = 0.0002      # m, skin stays this far outside the eyeball
RIDGE = 2e-7          # keeps coefficients small; raise if lids look lumpy
CLOSED_AT = 0.2       # closed lid line sits this fraction of the opening above the lower lid


def lid_ring(m, side):
    """Indices of the lid margin vertices of one eye, split into upper and lower."""
    sign = 1 if side == "left" else -1
    T = m.template
    idx = np.flatnonzero(m.group("eye_sockets", "skin_exterior") & (sign * T[:, 0] > 0))
    P = T[idx]
    inner, outer = P[np.argmin(sign * P[:, 0])], P[np.argmax(sign * P[:, 0])]
    slope = (outer[1] - inner[1]) / (outer[0] - inner[0])
    upper = P[:, 1] > inner[1] + slope * (P[:, 0] - inner[0])
    return idx[upper], idx[~upper]


def curve(points):
    """Lid height as a function of x, from margin vertices."""
    order = np.argsort(points[:, 0])
    return lambda x: np.interp(x, points[order, 0], points[order, 1])


class Eyeball:
    """Radius of the eyeball surface in any direction from its centre (the cornea bulges)."""

    def __init__(self, m, side):
        self.centre = m.joints[m.joint_names.index(f"{side}_eye")]
        rel = m.template[m.group(f"{side}_eye", "eye_exteriors")] - self.centre
        self.radii = np.linalg.norm(rel, axis=1)
        self.tree = cKDTree(rel / self.radii[:, None])

    def clearance(self, points):
        """Signed distance outside the eyeball, and the unit direction from its centre."""
        rel = points - self.centre
        dist = np.linalg.norm(rel, axis=1)
        unit = rel / dist[:, None]
        return dist - self.radii[self.tree.query(unit, k=3)[1]].mean(axis=1), unit


def solve(m, comps, targets, ball, keep_out):
    """Ridge least squares for coefficients moving `targets` vertices by given offsets,
    iterating so that `keep_out` skin vertices do not sink into the eyeball."""
    basis = m.expression_basis[comps]  # (K, V, 3)
    # the neutral face already touches the eye near the lid edge; never demand more than it has
    floor = np.minimum(ball.clearance(m.template[keep_out])[0], LID_GAP)
    want = dict(targets)
    for _ in range(12):
        idx = np.array(sorted(want))
        A = basis[:, idx].reshape(len(basis), -1).T.astype(np.float64)
        b = np.array([want[i] for i in idx]).ravel()
        coef = np.linalg.solve(A.T @ A + RIDGE * np.eye(len(basis)), A.T @ b)
        moved = m.template[keep_out] + np.tensordot(coef, basis[:, keep_out], 1)
        clear, unit = ball.clearance(moved)
        bad = clear < floor - 1e-4
        if not bad.any():
            break
        for i, p, c, u, f in zip(keep_out[bad], moved[bad], clear[bad], unit[bad], floor[bad]):
            want[int(i)] = p + u * (f - c + 1e-4) - m.template[i]
    return coef, int(bad.sum())


def fit_eye(m, side):
    comps = LEFT_EYE if side == "left" else RIGHT_EYE
    ball = Eyeball(m, side)
    joint = ball.centre
    up, low = lid_ring(m, side)
    T = m.template
    upper_y, lower_y = curve(T[up]), curve(T[low])
    ring = np.zeros(len(m.template), bool)
    ring[up], ring[low] = True, True
    region = np.flatnonzero(m.group(f"{side}_orbital_region", "skin_exterior") & ~ring)

    def on_eyeball(i, y):
        """Offset moving margin vertex i to height y while staying on its own sphere."""
        r = np.linalg.norm(T[i] - joint)
        dx, dy = T[i, 0] - joint[0], y - joint[1]
        z = joint[2] + np.sqrt(max(r * r - dx * dx - dy * dy, 0.0))
        return np.array([T[i, 0], y, z]) - T[i]

    def targets(upper_amount, lower_amount):
        """Margin offsets: amounts are fractions of the way from open to the closed line."""
        out = {}
        for i in up:
            closed = lower_y(T[i, 0]) + CLOSED_AT * (upper_y(T[i, 0]) - lower_y(T[i, 0]))
            out[int(i)] = on_eyeball(i, T[i, 1] + upper_amount * (min(closed, T[i, 1]) - T[i, 1]))
        for i in low:
            closed = lower_y(T[i, 0]) + CLOSED_AT * (upper_y(T[i, 0]) - lower_y(T[i, 0]))
            out[int(i)] = on_eyeball(i, T[i, 1] + lower_amount * (max(closed, T[i, 1]) - T[i, 1]))
        return out

    controls, report = {}, {}
    for name, (ua, la) in {"blink": (1.0, 1.0), "upper_lid_down": (0.5, 0.0), "upper_lid_up": (-0.35, 0.0),
                           "lower_lid_up": (0.0, 1.0)}.items():
        coef, bad = solve(m, comps, targets(ua, la), ball, region)
        full = np.zeros(383)
        full[comps] = coef
        controls[f"{name}_{side}"] = full
        moved = T + np.tensordot(coef, m.expression_basis[comps], 1)
        gap = np.mean([moved[i, 1] for i in up]) - np.mean([moved[i, 1] for i in low])
        report[name] = (round(float(np.abs(coef).max()), 2), round(gap * 1000, 2), bad)
    return controls, report


if __name__ == "__main__":
    m = GNM()
    out = {}
    for side in ("left", "right"):
        controls, report = fit_eye(m, side)
        out.update(controls)
        coef, gap, sunk = report["blink"]
        assert coef < 4 and gap < 0.5 and sunk < 10, f"{side} blink fit degraded: {report['blink']}"
        print(side, "(max |coef|, mean lid gap mm, verts sunk into eyeball):", report)
    np.savez_compressed(ROOT / "assets" / "controls.npz", **out)
