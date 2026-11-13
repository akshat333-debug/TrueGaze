from pathlib import Path

import numpy as np

HAIR = Path(__file__).resolve().parent.parent / "assets" / "hair.npz"


def test_hair_follows_only_its_own_eye_and_lashes_drop_in_a_blink():
    d = np.load(HAIR)
    v, move = d["verts"], d["move_blink_left"]
    assert d["quads"].max() < len(v) and set(np.unique(d["material"])) == {0, 1, 2}
    left = v[:, 0] > 0  # GNM: the character's left eye is at +X
    assert np.abs(move[v[:, 0] < -0.015]).max() < 1e-4   # a left blink leaves the right eye's hair alone (down on the nose bridge moves a little)
    assert move[left, 1].min() < -0.006            # upper lashes come down by more than 6 mm
    assert np.abs(d["move_brow_raise_left"][left, 1]).max() > 0.003  # brow hairs ride up with the brow
