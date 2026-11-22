"""Launch-spec label maths, tested without Blender: the pupil finder, cornea refraction, direction signs,
the GazeBase saccade detector and the submission validator. bpy is replaced by mocks; only numpy code runs."""
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
for name in ("bpy", "bmesh", "bpy_extras", "bpy_extras.object_utils", "mathutils"):
    sys.modules.setdefault(name, mock.MagicMock())
sys.path[:0] = [str(ROOT), str(ROOT / "wrapper"), str(ROOT / "tools")]
import eyes  # noqa: E402
import gazebase_compare  # noqa: E402
import validate  # noqa: E402
from truegaze import motion  # noqa: E402


def fake_load(path, check_existing=False):
    """What bpy.data.images.load gives: size and flat RGBA floats, rows bottom-up."""
    im = Image.open(path).convert("RGBA")
    px = np.asarray(im, np.float32)[::-1] / 255
    return SimpleNamespace(size=im.size, pixels=px.ravel())


def eye_image(tmp_path, pupil=(130.4, 121.7), shadow=True):
    """A light sclera, a mid-grey iris, a black pupil and (optionally) a lid shadow above, as a PNG."""
    yy, xx = np.mgrid[:256, :256]
    img = np.full((256, 256), 0.85)
    img[np.hypot(xx - pupil[0], yy - pupil[1]) < 30] = 0.35
    img[np.hypot(xx - pupil[0], yy - pupil[1]) < 9] = 0.03
    if shadow:
        img[60:92, 80:180] = 0.12  # lid shadow: dark, but lighter than the pupil
    path = tmp_path / "eye.png"
    Image.fromarray((img * 255).astype(np.uint8)).save(path)
    return path


@pytest.fixture
def images():
    with mock.patch.object(eyes.bpy.data.images, "load", fake_load), mock.patch.object(eyes.bpy.data.images, "remove"):
        yield


def test_find_pupil_lands_on_the_pupil_centre(tmp_path, images):
    (x, y), size = eyes.find_pupil(eye_image(tmp_path, shadow=False), near=(128, 128))
    assert math.hypot(x - 130.4, y - 121.7) < 0.6
    assert 200 < size < 300  # a disc of radius 9 px


def test_find_pupil_ignores_a_lid_shadow(tmp_path, images):
    (x, y), _ = eyes.find_pupil(eye_image(tmp_path, shadow=True), near=(128, 110))
    assert math.hypot(x - 130.4, y - 121.7) < 0.6


def straight_camera(pixel, f=1000.0, c=512.0):
    """Pinhole at the origin looking down -z: the ray through a pixel."""
    d = np.array([(pixel[0] - c) / f, -(pixel[1] - c) / f, -1.0])
    return np.zeros(3), d / np.linalg.norm(d)


def project(p, f=1000.0, c=512.0):
    return np.array([c + f * p[0] / -p[2], c - f * p[1] / -p[2]])


CORNEA = (np.array([0.0, 0.0, -0.4]), 0.0078)  # sphere centre 40 cm away, radius 7.8 mm (human cornea)
GAZE = np.array([0.0, 0.0, 1.0])  # the eye looks back at the camera


def test_ray_through_the_cornea_centre_is_not_bent():
    with mock.patch.object(eyes, "_camera_ray", straight_camera):
        pupil = CORNEA[0] + np.array([0.0, 0.0, 0.0045])
        hit = eyes._through_cornea(project(pupil), *CORNEA, pupil, GAZE)
    assert np.allclose(hit, pupil, atol=1e-7)


def test_cornea_magnifies_an_off_axis_pupil():
    """A convex cornea makes the pupil look bigger, so its apparent centre sits further from the axis."""
    pupil = CORNEA[0] + np.array([0.0015, 0.0, 0.0045])
    straight = project(pupil)
    with mock.patch.object(eyes, "_camera_ray", straight_camera), mock.patch.object(eyes, "_cornea_sphere", lambda h, s: CORNEA):
        seen = eyes._refracted_pixel(None, "L", pupil, GAZE, straight)
        landed = eyes._through_cornea(seen, *CORNEA, pupil, GAZE)
    assert np.linalg.norm(landed - pupil) < 1e-6  # the solver found the pixel that sees the pupil centre
    assert 1.05 < abs(seen[0] - 512) / abs(straight[0] - 512) < 1.25  # about 1.13x, as a human cornea magnifies


def test_direction_signs_follow_image_coordinates():
    """x grows to the right and y grows downward, so Left and Up must shrink the coordinate."""
    assert eyes.DIRECTIONS["Left"][2:] == (0, -1) and eyes.DIRECTIONS["Right"][2:] == (0, 1)
    assert eyes.DIRECTIONS["Up"][2:] == (1, -1) and eyes.DIRECTIONS["Down"][2:] == (1, 1)
    assert eyes.MIN_SHIFT >= 3


@pytest.mark.parametrize("amp", [5, 10, 20, 30])
def test_saccade_detector_measures_a_clean_saccade(amp):
    clip = motion.Clip(1.0).look(0.2, amp, 0, blink_on_large=False)
    yaw = np.array([motion._direction(clip, t)[0] for t in np.arange(1000) / 1000])
    found = gazebase_compare.saccades(yaw, np.zeros_like(yaw), 1000)
    size, dur, peak = max(found)  # the main saccade; anything else is the small overshoot settling back
    assert all(s < 1.0 for s, _, _ in found if s != size)
    assert abs(size - amp) < 0.15 * amp
    assert dur < motion.saccade_duration(amp) + 0.01
    assert peak > amp / motion.saccade_duration(amp)  # peak beats the mean speed


def test_validator_rejects_a_broken_sequence(tmp_path):
    frames = tmp_path / "renders"
    frames.mkdir()
    for k in range(10):
        Image.new("RGB", (1024, 1024)).save(frames / f"frame_{k:02d}.png")
    recs = [{"frame": k, "theta": 2 * math.pi * k / 10, "input": {"h": math.sin(2 * math.pi * k / 10), "v": math.cos(2 * math.pi * k / 10)},
             **{key: [0, 0] for key in validate.FRAME_KEYS - {"frame", "theta", "input"}}} for k in range(10)]
    recs[3]["input"]["h"] *= -1  # counter-clockwise frame
    (tmp_path / "metadata.json").write_text(json.dumps({"frames": recs, "direction_check": {d: True for d in ("Left", "Right", "Up", "Down", "Reset")}}))
    validate.results.clear()
    validate.check_launch_spec(tmp_path, tmp_path / "metadata.json", frames)
    assert validate.results.count(False) == 1  # exactly the theta/h/v check fails
