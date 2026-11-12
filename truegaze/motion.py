"""Eye, eyelid, brow and pupil trajectories. Pure Python + NumPy, no Blender, so it is unit-tested.

A clip is a list of timed gaze targets and blinks. `render_clip` turns it into per-frame values:
eye yaw/pitch per eye (degrees; yaw > 0 = toward the character's left, pitch > 0 = up) and shape-key
weights. Physiology used:
- saccade duration 21 ms + 2.2 ms per degree (main sequence), minimum-jerk profile, small overshoot
  that settles back (glissade)
- both eyes aim at one point, so they converge for near targets (vergence)
- upper lid follows vertical gaze; brows lift on up-gaze
- blinks: fast close (~100 ms), slower open (~200 ms); large saccades often trigger one
- fixation is never frozen: slow drift plus occasional micro-saccades; pupil size fluctuates (hippus)
"""
import math

import numpy as np

EYE_HALF_SPAN = 0.031  # m, eye centre to face midline (GNM template)
DEFAULT_DISTANCE = 0.6  # m, fixation distance for conversational gaze
PUPIL_REST = -0.9  # pupil key at rest: GNM's template pupil is dilated (5.4 mm), this gives about 3.8 mm


def saccade_duration(amplitude_deg):
    return 0.021 + 0.0022 * amplitude_deg


def min_jerk(tau):
    tau = np.clip(tau, 0.0, 1.0)
    return tau**3 * (10 - 15 * tau + 6 * tau * tau)


def blink_profile(t):
    """Lid closure 0..1 at time t (s) since blink start; 0 again after 0.33 s."""
    close, hold, opening = 0.10, 0.03, 0.20
    if t < 0:
        return 0.0
    if t < close:
        return float(min_jerk(t / close))
    if t < close + hold:
        return 1.0
    return float(1 - min_jerk((t - close - hold) / opening))


def eye_angles(direction_yaw, direction_pitch, distance=DEFAULT_DISTANCE):
    """Per-eye (yaw, pitch) in degrees for a fixation point at the given head-centred direction."""
    y, p = math.radians(direction_yaw), math.radians(direction_pitch)
    point = np.array([distance * math.sin(y) * math.cos(p), distance * math.sin(p), distance * math.cos(y) * math.cos(p)])
    out = {}
    for side, x in (("left", EYE_HALF_SPAN), ("right", -EYE_HALF_SPAN)):
        rel = point - np.array([x, 0.0, 0.0])
        out[side] = (math.degrees(math.atan2(rel[0], rel[2])), math.degrees(math.atan2(rel[1], math.hypot(rel[0], rel[2]))))
    return out


class Clip:
    """Timeline of gaze shifts and blinks. Times in seconds."""

    def __init__(self, duration, seed=0):
        self.duration = duration
        self.shifts = []   # (start time, yaw, pitch, distance)
        self.blinks = []   # (start time, strength 0..1)
        self.rng = np.random.default_rng(seed)

    def look(self, t, yaw, pitch, distance=DEFAULT_DISTANCE, blink_on_large=True):
        self.shifts.append((t, yaw, pitch, distance))
        prev = self.shifts[-2] if len(self.shifts) > 1 else (0, 0, 0, distance)
        if blink_on_large and math.hypot(yaw - prev[1], pitch - prev[2]) > 20:
            self.blink(t - 0.02)
        return self

    def blink(self, t, strength=1.0):
        self.blinks.append((t, strength))
        return self

    def natural_blinks(self, every=(2.5, 4.5)):
        """Spontaneous blinks at random intervals, skipping ones too close to existing blinks."""
        t = self.rng.uniform(0.6, 1.5)
        while t < self.duration - 0.4:
            if all(abs(t - b) > 0.8 for b, _ in self.blinks):
                self.blink(t)
            t += self.rng.uniform(*every)
        return self


def _direction(clip, t):
    """Head-centred gaze direction (yaw, pitch, distance) at time t, with saccade dynamics."""
    yaw, pitch, dist = 0.0, 0.0, DEFAULT_DISTANCE
    for start, y, p, d in sorted(clip.shifts):
        if t < start:
            break
        amp = math.hypot(y - yaw, p - pitch)
        dur = saccade_duration(amp)
        s = float(min_jerk((t - start) / dur))
        # overshoot ~4% of amplitude, settling over 60 ms after the main movement
        after = t - start - dur
        if after > 0:
            s += 0.04 * math.exp(-after / 0.025) * math.sin(math.pi * min(after / 0.06, 1.0))
        yaw, pitch, dist = yaw + s * (y - yaw), pitch + s * (p - pitch), dist + s * (d - dist)
    return yaw, pitch, dist


def render_clip(clip, fps=30):
    """Per-frame dict of arrays: eye angles, shape-key weights, pupil."""
    n = int(round(clip.duration * fps))
    t = np.arange(n) / fps
    rng = np.random.default_rng(clip.rng.integers(1 << 31))
    # fixational eye movement: slow drift (random walk pulled back) + micro-saccade steps
    drift = np.zeros((n, 2))
    for i in range(1, n):
        drift[i] = 0.92 * drift[i - 1] + rng.normal(0, 0.05, 2)
    micro = np.zeros((n, 2))
    for when in np.cumsum(rng.uniform(0.6, 1.6, 20)):
        if when < clip.duration:
            micro[t >= when] += rng.normal(0, 0.35, 2)
    micro *= 0.6  # keep the accumulated jitter under about a degree

    out = {k: np.zeros(n) for k in ("left_yaw", "left_pitch", "right_yaw", "right_pitch", "blink",
                                     "upper_lid_up", "upper_lid_down", "lower_lid_up", "brow_raise", "pupil")}
    for i, ti in enumerate(t):
        yaw, pitch, dist = _direction(clip, ti)
        yaw, pitch = yaw + drift[i, 0] + micro[i, 0], pitch + drift[i, 1] + micro[i, 1]
        closure = max([s * blink_profile(ti - b) for b, s in clip.blinks] + [0.0])
        # eyes dip down and in during a blink (Bell's phenomenon, mild)
        pitch -= 4 * closure
        for side, (y, p) in eye_angles(yaw, pitch, dist).items():
            out[f"{side}_yaw"][i], out[f"{side}_pitch"][i] = y, p
        out["blink"][i] = closure
        out["upper_lid_up"][i] = np.clip(pitch / 25, 0, 1)
        out["upper_lid_down"][i] = np.clip(-pitch / 30, 0, 1)
        out["lower_lid_up"][i] = np.clip(-pitch / 60, 0, 0.3) + 0.1 * np.clip(abs(yaw) / 30, 0, 1)
        out["brow_raise"][i] = np.clip(pitch / 30, 0, 0.8)
        out["pupil"][i] = PUPIL_REST + 0.2 * math.sin(2 * math.pi * 0.35 * ti) + 0.1 * math.sin(2 * math.pi * 0.9 * ti + 1)
    return out


# The three required inputs. Directions: "Left" means toward the viewer's left by default (screen),
# which is the character's right (negative yaw). frame="subject" uses the character's own left.
def preset(name, seed=0, frame="screen"):
    side = -1 if frame == "screen" else 1
    if name == "Left":
        return Clip(9.0, seed).look(1.0, 28 * side, 0).look(5.5, 0, 0).natural_blinks()
    if name == "Right":
        return Clip(9.0, seed).look(1.0, -28 * side, 0).look(5.5, 0, 0).natural_blinks()
    if name == "Generate Motion":
        rng = np.random.default_rng(seed)
        c = Clip(12.0, seed)
        c.look(0.8, 25, 3).look(2.0, -25, -2).look(3.4, 0, 0)
        # eye roll: sweep the upper arc right to left in small steps
        for k, a in enumerate(np.linspace(-150, -30, 7)):
            c.look(4.6 + 0.12 * k, 22 * math.cos(math.radians(a)), -22 * math.sin(math.radians(a)), blink_on_large=False)
        c.look(5.7, 0, 0).blink(6.2).blink(6.55, 0.9)
        c.look(7.6, rng.uniform(10, 20) * rng.choice([-1, 1]), -12)  # thinking glance down to one side
        c.look(9.4, 0, 0, distance=0.35)  # back to the camera, converging closer
        return c.natural_blinks()
    raise ValueError(f"unknown input {name!r}; use Left, Right or Generate Motion")
