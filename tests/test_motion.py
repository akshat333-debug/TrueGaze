import math

import numpy as np
import pytest

from truegaze.motion import Clip, blink_profile, eye_angles, preset, render_clip, saccade_duration


def test_saccade_reaches_target_and_settles():
    c = Clip(2.0).look(0.5, 30, 0, blink_on_large=False)
    out = render_clip(c, fps=200)
    t = np.arange(len(out["blink"])) / 200
    mean_yaw = (out["left_yaw"] + out["right_yaw"]) / 2
    end = saccade_duration(30)
    assert abs(mean_yaw[t < 0.45]).max() < 3            # still before the saccade
    assert abs(mean_yaw[(t > 0.5 + end + 0.15)].mean() - 30) < 2  # settled at target
    assert mean_yaw[(t > 0.5) & (t < 0.5 + end)].max() > 15       # moves fast, within ~87 ms


def test_vergence_near_target_turns_eyes_inward():
    near, far = eye_angles(0, 0, 0.35), eye_angles(0, 0, 5.0)
    assert near["left"][0] < 0 < near["right"][0]   # left eye turns right, right eye turns left
    assert abs(near["left"][0]) > abs(far["left"][0])
    assert near["left"][0] == pytest.approx(-math.degrees(math.atan(0.031 / 0.35)), abs=0.01)


def test_blink_is_fast_close_slow_open():
    assert blink_profile(0.0) == 0 and blink_profile(0.11) == 1
    assert blink_profile(0.08) > blink_profile(0.08 + 0.13 + 0.03)  # closing faster than opening
    assert blink_profile(0.34) == 0


def test_large_saccade_triggers_blink():
    c = Clip(3.0).look(1.0, 30, 0)
    assert len(c.blinks) == 1


def test_lids_follow_gaze():
    up = render_clip(Clip(2.0).look(0.2, 0, 20, blink_on_large=False))
    down = render_clip(Clip(2.0).look(0.2, 0, -20, blink_on_large=False))
    assert up["upper_lid_up"][-1] > 0.5 and up["brow_raise"][-1] > 0.4
    assert down["upper_lid_down"][-1] > 0.4 and down["upper_lid_up"][-1] == 0


@pytest.mark.parametrize("name", ["Left", "Right", "Generate Motion"])
def test_presets_fit_15_seconds(name):
    clip = preset(name)
    assert clip.duration <= 15
    out = render_clip(clip)
    assert all(np.isfinite(v).all() for v in out.values())
    assert 0 <= out["blink"].min() and out["blink"].max() <= 1


def test_left_means_screen_left_by_default():
    mid = lambda o: (o["left_yaw"] + o["right_yaw"])[90:150].mean()  # frames 3-5 s
    assert mid(render_clip(preset("Left"))) < -20     # negative yaw = character's right = viewer's left
    assert mid(render_clip(preset("Left", frame="subject"))) > 20


def test_unknown_input_rejected():
    with pytest.raises(ValueError):
        preset("Up")


def test_bulge_keys_match_gaze_direction():
    from truegaze.motion import BULGE_YAW, soft_tissue as bulge
    left = bulge("left", -BULGE_YAW, 0)    # left eye turned to the character's right = toward the nose
    assert left["bulge_in_left"] == 1 and left["bulge_out_left"] == 0
    assert bulge("right", -BULGE_YAW, 0)["bulge_out_right"] == 1
    assert bulge("left", 0, 12)["bulge_up_left"] == pytest.approx(0.25) and bulge("left", 0, 0)["bulge_down_left"] == 0
    assert bulge("left", 0, 12)["drag_up_left"] == pytest.approx(0.5)  # drag is proportional, bulge is squared
