"""Eye, eyelid, brow and pupil trajectories. Pure Python + NumPy, no Blender, so it is unit-tested.

A clip is a list of timed gaze targets and blinks. `render_clip` turns it into per-frame values:
eye yaw/pitch per eye (degrees; yaw > 0 = toward the character's left, pitch > 0 = up) and shape-key
weights. Physiology used:
- saccade duration 25 ms + 2.4 ms per degree (main sequence; published fits span 20-30 ms + 2-2.7 ms/deg), measured peak-to-mean velocity ratio, small overshoot
  that settles back (glissade)
- both eyes aim at one point, so they converge for near targets (vergence)
- both lids follow vertical gaze (the lower one about 2 mm down at 30 degrees of down-gaze); brows lift on up-gaze
- the eyeball is pulled about 1 mm back into the socket while the lids are closed
- the head is never still: slow sway of a degree or two plus breathing; the eyes counter-turn to hold the target
- blinks: fast close (~100 ms), slower open (~240 ms); large saccades often trigger one
- fixation is never frozen: slow drift plus occasional micro-saccades; pupil size fluctuates (hippus)
"""
import math

import numpy as np

EYE_HALF_SPAN = 0.031  # m, eye centre to face midline (GNM template)
DEFAULT_DISTANCE = 0.6  # m, fixation distance for conversational gaze
BULGE_YAW, BULGE_PITCH = 32.0, 24.0  # gaze angles (deg) at which the lid-bulge keys were fitted
PUPIL_REST = -0.9  # pupil key at rest: GNM's template pupil is dilated (5.4 mm), this gives about 3.8 mm


def saccade_duration(amplitude_deg):
    return 0.025 + 0.0024 * amplitude_deg  # middle of the published range: 20-30 ms + 2-2.7 ms per degree


def min_jerk(tau):
    tau = np.clip(tau, 0.0, 1.0)
    return tau**3 * (10 - 15 * tau + 6 * tau * tau)


def saccade_profile(tau):
    """Share of a saccade completed at fraction tau of its duration. A blend of a minimum-jerk and a
    cosine curve: peak velocity is 1.68 x the mean, as measured on real saccades (minimum-jerk alone
    gives 1.88, too peaked)."""
    tau = np.clip(tau, 0.0, 1.0)
    return 0.35 * min_jerk(tau) + 0.65 * (1 - np.cos(np.pi * tau)) / 2


def blink_profile(t):
    """Lid closure 0..1 at time t (s) since blink start; 0 again after 0.37 s."""
    close, hold, opening = 0.10, 0.03, 0.24
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


def lids(yaw, pitch):
    """Lid and brow shape-key weights that go with a gaze direction (degrees): lids follow the eye."""
    return {"upper_lid_up": float(np.clip(pitch / 25, 0, 1)), "upper_lid_down": float(np.clip(-pitch / 30, 0, 1)),
            # one unit of this key is about 2 mm: the lower lid rides down with the eye and up a little on up-gaze
            "lower_lid_up": float(-0.8 * np.clip(-pitch / 30, 0, 1) + 0.15 * np.clip(pitch / 25, 0, 1) + 0.1 * np.clip(abs(yaw) / 30, 0, 1)),
            "brow_raise": float(np.clip(pitch / 30, 0, 0.8)),
            "brow_lower": float(np.clip(-pitch / 45, 0, 0.45))}  # the brow sinks a little when looking down


def soft_tissue(side, yaw, pitch):
    """Weights of one eye's lid-bulge and skin-drag keys for its gaze (degrees).
    Drag follows the eye in proportion. The cornea only reaches the lid at larger angles, so the
    bulge grows slowly at first: weight = (angle / limit) squared."""
    toward_nose = -yaw if side == "left" else yaw
    out = {}
    for name, angle, limit in (("in", toward_nose, BULGE_YAW), ("out", -toward_nose, BULGE_YAW),
                               ("up", pitch, BULGE_PITCH), ("down", -pitch, BULGE_PITCH)):
        w = float(np.clip(angle / limit, 0, 1))
        out[f"bulge_{name}_{side}"], out[f"drag_{name}_{side}"] = w * w, w
    return out


class Clip:
    """Timeline of gaze shifts and blinks. Times in seconds."""

    def __init__(self, duration, seed=0, natural=False):
        self.duration = duration
        self.shifts = []   # (start time, yaw, pitch, distance)
        self.blinks = []   # (start time, strength 0..1)
        self.rng = np.random.default_rng(seed)
        self.natural = natural  # opt-in extras: corrective saccades, head follows gaze, partial blinks, uneven brows

    def look(self, t, yaw, pitch, distance=DEFAULT_DISTANCE, blink_on_large=True):
        prev = self.shifts[-1] if self.shifts else (0, 0, 0, distance)
        amp = math.hypot(yaw - prev[1], pitch - prev[2])
        if self.natural and amp > 12:
            # large saccades land 6-12 % short; a small corrective saccade follows 150-220 ms later
            short = self.rng.uniform(0.88, 0.94)
            self.shifts.append((t, prev[1] + short * (yaw - prev[1]), prev[2] + short * (pitch - prev[2]), distance))
            self.shifts.append((t + self.rng.uniform(0.15, 0.22), yaw, pitch, distance))
        else:
            self.shifts.append((t, yaw, pitch, distance))
        if blink_on_large and amp > 20:
            self.blink(t - 0.02)
        return self

    def blink(self, t, strength=1.0):
        self.blinks.append((t, strength))
        return self

    def natural_blinks(self, every=(3.0, 6.0)):
        """Spontaneous blinks at random intervals, skipping ones too close to existing blinks."""
        t = self.rng.uniform(0.6, 1.5)
        while t < self.duration - 0.4:
            if all(abs(t - b) > 0.8 for b, _ in self.blinks):
                # natural: about one spontaneous blink in four stops short of full closure
                self.blink(t, self.rng.uniform(0.6, 0.85) if self.natural and self.rng.random() < 0.25 else 1.0)
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
        s = float(saccade_profile((t - start) / dur))
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

    out = {k: np.zeros(n) for k in ("left_yaw", "left_pitch", "right_yaw", "right_pitch", "blink", "blink_mid",
                                     "upper_lid_up", "upper_lid_down", "lower_lid_up", "brow_raise", "brow_lower", "pupil")}
    # head sway (degrees, same signs as the eyes; roll > 0 tips toward the character's left): slow postural
    # drift, plus breathing at 15 per minute in pitch. Amounts are our own; no measured data was looked up.
    phase = rng.uniform(0, 2 * np.pi, 5)
    wave = lambda hz, k: np.sin(2 * np.pi * hz * t + phase[k])
    out["head_yaw"] = 1.2 * wave(0.11, 0) + 0.5 * wave(0.29, 1)
    out["head_pitch"] = 0.7 * wave(0.17, 2) + 0.3 * wave(0.25, 3)
    out["head_roll"] = 0.5 * wave(0.13, 4)
    if clip.natural:
        # the head follows large gaze shifts about 40 ms after the eyes and takes a share of them;
        # the eyes counter-turn below, so the gaze still lands on the target
        gaze = np.array([_direction(clip, ti)[:2] for ti in t])
        late = np.stack([np.interp(t - 0.04, t, gaze[:, k]) for k in (0, 1)], 1)
        follow = np.zeros_like(late)
        alpha = 1 - math.exp(-1 / (fps * 0.15))  # head lags with a 150 ms time constant
        for i in range(1, n):
            follow[i] = follow[i - 1] + alpha * (late[i] - follow[i - 1])
        out["head_yaw"] += 0.2 * follow[:, 0]
        out["head_pitch"] += 0.15 * follow[:, 1]
    for i, ti in enumerate(t):
        yaw, pitch, dist = _direction(clip, ti)
        yaw, pitch = yaw + drift[i, 0] + micro[i, 0], pitch + drift[i, 1] + micro[i, 1]
        closure = max([s * blink_profile(ti - b) for b, s in clip.blinks] + [0.0])
        # eyes dip down and in during a blink (Bell's phenomenon, mild)
        pitch -= 4 * closure
        # the eyes turn against the head, so the gaze stays on its target (vestibulo-ocular reflex)
        yaw, pitch = yaw - out["head_yaw"][i], pitch - out["head_pitch"][i]
        for side, (y, p) in eye_angles(yaw, pitch, dist).items():
            out[f"{side}_yaw"][i], out[f"{side}_pitch"][i] = y, p
        out["blink"][i] = closure
        out["blink_mid"][i] = 4 * closure * (1 - closure)  # keeps the half-closed lid on the eyeball
        for name, value in lids(yaw, pitch).items():
            out[name][i] = value
        # the muscle that closes the lids also pulls the brow down and the lower lid up a little
        out["brow_lower"][i] = min(out["brow_lower"][i] + 0.18 * closure, 0.6)
        out["lower_lid_up"][i] = min(out["lower_lid_up"][i] + 0.10 * closure, 0.4)
        out["pupil"][i] = PUPIL_REST + 0.2 * math.sin(2 * math.pi * 0.35 * ti) + 0.1 * math.sin(2 * math.pi * 0.9 * ti + 1)
    out["retract"] = 0.001 * out["blink"]  # m: the closing muscle pulls the eyeball about 1 mm back
    if clip.natural:  # brows are not perfectly symmetric: one side rises a beat later and a little less
        lead, lag = ("left", "right") if rng.random() < 0.5 else ("right", "left")
        out[f"brow_raise_{lead}"] = out["brow_raise"].copy()
        out[f"brow_raise_{lag}"] = 0.85 * np.interp(t - 0.06, t, out["brow_raise"])
    return out


# The three required inputs. Directions: "Left" means toward the viewer's left by default (screen),
# which is the character's right (negative yaw). frame="subject" uses the character's own left.
def preset(name, seed=0, frame="screen", natural=False):
    side = -1 if frame == "screen" else 1
    if name == "Left":
        return Clip(9.0, seed, natural).look(1.0, 28 * side, 0).look(5.5, 0, 0).natural_blinks()
    if name == "Right":
        return Clip(9.0, seed, natural).look(1.0, -28 * side, 0).look(5.5, 0, 0).natural_blinks()
    if name == "Generate Motion":
        rng = np.random.default_rng(seed)
        c = Clip(12.0, seed, natural)
        c.look(0.8, 25, 3).look(2.0, -25, -2).look(3.4, 0, 0)
        # eye roll: sweep the upper arc right to left in small steps
        for k, a in enumerate(np.linspace(-150, -30, 7)):
            c.look(4.6 + 0.12 * k, 22 * math.cos(math.radians(a)), -22 * math.sin(math.radians(a)), blink_on_large=False)
        c.look(5.7, 0, 0).blink(6.2).blink(6.55, 0.9)
        c.look(7.6, rng.uniform(10, 20) * rng.choice([-1, 1]), -12)  # thinking glance down to one side
        c.look(9.4, 0, 0, distance=0.35)  # back to the camera, converging closer
        return c.natural_blinks()
    raise ValueError(f"unknown input {name!r}; use Left, Right or Generate Motion")

