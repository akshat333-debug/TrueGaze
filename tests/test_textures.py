import numpy as np

from truegaze.gnm import GNM
from truegaze.textures import eye, eye_radii, skin


def test_eye_has_black_pupil_and_distinct_left_right():
    radii = eye_radii(GNM())
    assert 0 < radii[0] < radii[1] < 0.5
    left = eye(256, radii, (0.25, 0.36, 0.42), (0.45, 0.40, 0.28), seed=1)
    right = eye(256, radii, (0.25, 0.36, 0.42), (0.45, 0.40, 0.28), seed=2)
    assert left[128, 128].max() < 0.01                       # pupil centre is black
    assert left[128, 128 + int(0.12 * 256)].max() > 0.05     # iris is not
    assert np.abs(left - right).mean() > 0.01                # each eye has its own pattern


def test_skin_maps_are_valid_and_lips_are_redder():
    color, rough, height, wrinkles = skin(GNM(), 256, (0.78, 0.57, 0.46), seed=1)
    assert wrinkles[..., 0].max() > 0.3 and wrinkles[..., 1].max() > 0.3  # forehead lines and crow's feet exist
    for a in (color, rough, height, wrinkles):
        assert np.isfinite(a).all() and a.min() >= -0.05 and a.max() <= 1.05
    assert color[..., 0].mean() > color[..., 2].mean()
