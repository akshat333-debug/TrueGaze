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
    assert blink_profile(0.38) == 0


def test_large_saccade_triggers_blink():
    c = Clip(3.0).look(1.0, 30, 0)
    assert len(c.blinks) == 1


def test_lids_follow_gaze():
    up = render_clip(Clip(2.0).look(0.2, 0, 20, blink_on_large=False))
    down = render_clip(Clip(2.0).look(0.2, 0, -20, blink_on_large=False))
    assert up["upper_lid_up"][-1] > 0.5 and up["brow_raise"][-1] > 0.4
    assert up["brow_lower"][-1] == 0  # the brow does not pull both ways at once
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


def test_head_sways_and_eyes_hold_the_target():
    out = render_clip(Clip(8.0, seed=1), fps=30)
    assert 0.5 < np.abs(out["head_yaw"]).max() < 2.5 and np.abs(out["head_roll"]).max() < 1
    gaze = (out["left_yaw"] + out["right_yaw"]) / 2 + out["head_yaw"]  # eye in head + head = gaze in space
    assert np.abs(gaze - gaze.mean()).max() < 1.0  # only fixational jitter is left
    assert out["retract"].max() == 0  # no blink, no pull-back


def test_lower_lid_follows_gaze_and_eyeball_pulls_back_in_a_blink():
    down = render_clip(Clip(2.0).look(0.2, 0, -20, blink_on_large=False))
    assert down["lower_lid_up"][-1] < -0.3  # rides down with the eye
    blink = render_clip(Clip(2.0).blink(0.5))
    assert blink["retract"].max() == pytest.approx(0.001)


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


def test_natural_is_off_by_default_and_changes_nothing():
    from truegaze.motion import preset, render_clip
    a = render_clip(preset("Generate Motion", 0), 30)
    b = render_clip(preset("Generate Motion", 0, natural=False), 30)
    assert all(np.array_equal(a[k], b[k]) for k in a) and "brow_raise_left" not in a


def test_natural_large_saccade_lands_short_then_corrects():
    from truegaze.motion import Clip, _direction
    c = Clip(2.0, seed=3, natural=True).look(0.2, 30, 0)
    assert len(c.shifts) == 2
    landing, correction = c.shifts
    assert 0.88 * 30 <= landing[1] <= 0.94 * 30 and correction[1] == 30
    assert 0.15 <= correction[0] - landing[0] <= 0.22
    yaw_between = _direction(c, landing[0] + 0.12)[0]
    assert yaw_between < 29  # still short before the corrective saccade
    assert abs(_direction(c, 1.5)[0] - 30) < 0.5  # and on target after it


def test_natural_small_saccade_has_no_correction():
    from truegaze.motion import Clip
    assert len(Clip(1.0, natural=True).look(0.2, 8, 0).shifts) == 1


def test_natural_head_follows_gaze_and_eyes_still_hit_the_target():
    from truegaze.motion import Clip, render_clip
    plain = render_clip(Clip(3.0, seed=1).look(0.5, 25, 0), 30)
    nat = render_clip(Clip(3.0, seed=1, natural=True).look(0.5, 25, 0), 30)
    end = -1
    assert nat["head_yaw"][end] - plain["head_yaw"][end] > 3  # head takes a share of the 25 deg shift
    gaze_plain = (plain["left_yaw"] + plain["right_yaw"])[end] / 2 + plain["head_yaw"][end]
    gaze_nat = (nat["left_yaw"] + nat["right_yaw"])[end] / 2 + nat["head_yaw"][end]
    assert abs(gaze_nat - gaze_plain) < 1.5  # eye + head still points at the same place (drift differs by seed)


def test_natural_brows_are_uneven_and_some_blinks_partial():
    from truegaze.motion import Clip, render_clip
    f = render_clip(Clip(8.0, seed=2, natural=True).look(1.0, 0, 20).look(4.0, 0, 0), 30)
    left, right = f["brow_raise_left"], f["brow_raise_right"]
    assert not np.allclose(left, right) and max(left.max(), right.max()) > 0
    strengths = [s for seed in range(20) for _, s in Clip(60.0, seed=seed, natural=True).natural_blinks().blinks]
    assert any(s < 1 for s in strengths) and any(s == 1 for s in strengths)
