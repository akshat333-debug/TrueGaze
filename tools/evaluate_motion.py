#!/usr/bin/env python3
"""Checks the motion engine against published measurements of real eyes. Prints a table and fails
if a number leaves its range. The ranges come from the literature, not from our output.

Checked against sources on 13 Nov 2026:
- saccade duration = a + b x amplitude, with a between 20 and 30 ms and b between 2 and 2.7 ms/deg
  (Collewijn et al. 1988: 23 + 2.7; range used by Lee, Badler & Badler 2002 and Gu et al. 2008;
  reviewed in Duchowski et al., J. Eye Movement Research 10(3), https://mdpi.com/1995-8692/10/3/17).
  Duration is measured the lab way: time spent above 30 deg/s.
- blink: closing 50-130 ms, whole blink 250-450 ms, closing 40-47% faster than opening
  (review: https://www.frontiersin.org/articles/10.3389/fnsys.2023.1242654 ; optoelectronic study:
  https://pubmed.ncbi.nlm.nih.gov/18565090/). Opening range here is derived from those two.
- spontaneous blink rate at rest: 11-19 per minute, about 15 on average (same two sources); 10-20 used.

From geometry, no source needed:
- vergence: both eyes on a 35 cm target turn inward by atan(half eye spacing / distance)

Not confirmed against a source in this check (textbook values from memory, treat as a sanity band):
- saccade peak velocity 1.5-1.8 x mean velocity
- fixational movement under 1 degree

Run: python3 tools/evaluate_motion.py
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from truegaze.motion import EYE_HALF_SPAN, Clip, _direction, blink_profile, eye_angles, preset, render_clip  # noqa: E402

FPS = 2000  # fine time step, so the numbers describe the model and not the video frame rate
rows, failed = [], False


def check(name, value, low, high, unit, sourced=True):
    """sourced=False: the range is not confirmed against a source, so it is reported but cannot fail the run."""
    global failed
    ok = low <= value <= high
    failed |= sourced and not ok
    rows.append(f"{'ok  ' if ok else 'FAIL' if sourced else 'note'} {name:<46} {value:8.1f} {unit:<8} expected {low:g} to {high:g}")


for amplitude in (5, 10, 20, 30):
    clip = Clip(1.0)
    clip.look(0.2, amplitude, 0, blink_on_large=False)
    yaw = np.array([_direction(clip, i / FPS)[0] for i in range(FPS)])  # the gaze itself, without fixational jitter
    speed = np.abs(np.gradient(yaw) * FPS)
    peak = speed.max()
    low, high = 20 + 2.0 * amplitude, 30 + 2.7 * amplitude
    duration = (speed > 30).sum() / FPS * 1000  # the usual lab definition: time spent above 30 deg/s
    check(f"saccade {amplitude:>2} deg: duration", duration, low, high, "ms")
    check(f"saccade {amplitude:>2} deg: peak / mean velocity", peak / (amplitude / (duration / 1000)), 1.5, 1.8, "ratio", sourced=False)

t = np.arange(0, 0.5, 1 / FPS)
lid = np.array([blink_profile(x) for x in t])
closed = np.flatnonzero(lid > 0.98)
closing = closed[0] / FPS * 1000
check("blink: closing time", closing, 50, 130, "ms")
opening = (np.flatnonzero(lid > 0.02)[-1] - closed[-1]) / FPS * 1000
check("blink: closing faster than opening by", (1 - closing / opening) * 100, 35, 55, "percent")
check("blink: total", np.flatnonzero(lid > 0.02)[-1] / FPS * 1000, 250, 450, "ms")

rates = [len(preset("Left", seed).blinks) / preset("Left", seed).duration * 60 for seed in range(20)]
check("blink rate over 20 seeds (Left clip)", float(np.mean(rates)), 10, 20, "per min")

inward = -eye_angles(0, 0, 0.35)["left"][0]
check("vergence at 35 cm, per eye", inward, math.degrees(math.atan(EYE_HALF_SPAN / 0.35)) - 0.05, math.degrees(math.atan(EYE_HALF_SPAN / 0.35)) + 0.05, "deg")

still = render_clip(Clip(6.0, seed=3), 60)
check("fixation wander (max from mean, 6 s)", float(np.abs((gaze := still["left_yaw"] + still["head_yaw"]) - gaze.mean()).max()), 0.05, 1.0, "deg", sourced=False)

check("head sway (largest angle, 6 s)", float(np.abs(still["head_yaw"]).max()), 0.3, 2.5, "deg", sourced=False)

print("\n".join(rows))
sys.exit(1 if failed else 0)
