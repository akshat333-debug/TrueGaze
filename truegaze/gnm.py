"""Minimal reader for Google's GNM Head v3 (Apache 2.0). NumPy only, so it runs inside Blender.

GNM v3.0 has zero pose correctives, so the model is: template + identity + expression, then
plain linear blend skinning over 4 joints (neck, head, left_eye, right_eye). Units are metres,
Y up, face looking along +Z, the character's left eye at +X.
"""
import hashlib
import urllib.request
from pathlib import Path

import numpy as np

URL = "https://huggingface.co/google/gnm-v3/resolve/main/v3_0/gnm_head.npz"
SHA256 = "61d78bbfb4ad8e0b38495804a4caef3214d3df00f8c3f68761e63b41ce3747eb"
CACHE = Path(__file__).resolve().parent.parent / "assets" / "cache" / "gnm_head.npz"

# UDIM tile of each region, from gnm/shape/gnm_udim.py
TILES = {1001: ("skin",), 1002: ("left_eye", "eye_interiors"), 1003: ("left_eye", "eye_exteriors"),
         1004: ("right_eye", "eye_interiors"), 1005: ("right_eye", "eye_exteriors"),
         1006: ("teeth_and_gums",), 1007: ("tongue",)}
LEFT_EYE, RIGHT_EYE = slice(0, 100), slice(100, 200)  # expression coefficient ranges
PUPIL = 382


def model_path():
    """Returns the local weights file, downloading and verifying it on first use."""
    if not CACHE.exists():
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE.with_suffix(".part")
        urllib.request.urlretrieve(URL, tmp)
        if hashlib.sha256(tmp.read_bytes()).hexdigest() != SHA256:
            tmp.unlink()
            raise RuntimeError("GNM weights failed the checksum; download again")
        tmp.rename(CACHE)
    return CACHE


class GNM:
    def __init__(self):
        d = np.load(model_path(), allow_pickle=False)
        self.template = d["template_vertex_positions"].astype(np.float64)
        self.joints = d["template_joint_positions"].astype(np.float64)
        self.joint_names = [str(n) for n in d["joint_names"]]
        self.parents = d["joint_parent_indices"]
        self.weights = d["skinning_weights"]            # (4, V)
        self.identity_basis = d["vertex_identity_basis"]  # (253, V, 3)
        self.joint_identity_basis = d["joint_identity_basis"]
        self.expression_basis = d["expression_basis"]   # (383, V, 3)
        self.quads = d["quads"]
        self.quad_uvs = d["quad_uvs"]                   # per-region layout, all in the unit square
        self._groups = {str(n): g > 0.5 for n, g in zip(d["vertex_group_names"], d["vertex_groups"])}
        self._groups["teeth_and_gums"] = self._groups["upper_teeth_and_gums"] | self._groups["lower_teeth_and_gums"]

    def group(self, *names):
        """Boolean vertex mask: intersection of the named groups."""
        return np.logical_and.reduce([self._groups[n] for n in names])

    def quad_tiles(self):
        """UDIM tile number of each quad."""
        tiles = np.zeros(len(self.quads), np.int32)
        for tile, names in TILES.items():
            tiles[self.group(*names)[self.quads].all(axis=1)] = tile
        if (tiles == 0).any():
            raise ValueError("some quads belong to no UDIM tile")
        return tiles

    def shape(self, identity=None, expression=None):
        """Unposed vertices (V, 3) and joints (4, 3)."""
        v, j = self.template.copy(), self.joints.copy()
        if identity is not None:
            v += np.tensordot(identity, self.identity_basis, 1)
            j += np.tensordot(identity, self.joint_identity_basis, 1)
        if expression is not None:
            v += np.tensordot(expression, self.expression_basis, 1)
        return v, j


def to_blender(points):
    """GNM (x right, y up, z forward) to Blender (x right, y back, z up)."""
    p = np.asarray(points)
    return np.stack([p[..., 0], -p[..., 2], p[..., 1]], axis=-1)
