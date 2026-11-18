"""Compares TrueGaze's eye-motion model (truegaze/motion.py) with recorded human gaze from GazeBase
(Griffith et al. 2021, CC BY 4.0, 1000 Hz EyeLink, https://doi.org/10.6084/m9.figshare.12912257).

Measurement only: no parameter in motion.py was tuned to this data. Metrics were fixed before the data
was opened, and the same saccade detector runs on both sides.

    python3 tools/gazebase_compare.py ~/datasets/GazeBase/GazeBase_v2_0.zip [n_subjects]
Writes outputs/gazebase_comparison.json and prints a table. Uses Round 1, session 1 of each subject:
RAN (random saccades) for the main sequence, FXS (fixation) for drift and micro-saccades,
VD1 (free video viewing) for blinks.
"""
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from truegaze import motion  # noqa: E402

BINS = [(4, 8), (8, 12), (12, 16), (16, 20), (20, 25), (25, 30)]  # saccade amplitude bins, degrees


def velocity(x, y, hz):
    """Gaze speed in deg/s, 5-point central difference (standard for 1000 Hz EyeLink data)."""
    vx = np.zeros_like(x)
    vy = np.zeros_like(y)
    vx[2:-2] = (x[4:] + x[3:-1] - x[1:-3] - x[:-4]) * hz / 6
    vy[2:-2] = (y[4:] + y[3:-1] - y[1:-3] - y[:-4]) * hz / 6
    return np.hypot(vx, vy)


def saccades(x, y, hz, on=30.0, min_ms=8):
    """(amplitude deg, duration s, peak velocity deg/s) for each run above `on` deg/s with valid samples."""
    v = velocity(x, y, hz)
    fast = np.nan_to_num(v) > on
    edges = np.flatnonzero(np.diff(np.r_[0, fast.astype(int), 0]))
    out = []
    for a, b in zip(edges[::2], edges[1::2]):
        if b - a < min_ms * hz / 1000 or a < 3 or b > len(x) - 3:
            continue
        seg = slice(a - 1, b + 1)
        if np.isnan(x[seg]).any():
            continue  # blink or tracking loss inside
        amp = float(np.hypot(x[b] - x[a - 1], y[b] - y[a - 1]))
        out.append((amp, (b - a) / hz, float(v[a:b].max())))
    return out


def load(z, name):
    with z.open(name) as f:
        d = np.genfromtxt(f, delimiter=",", names=True)
    x, y = d["x"].copy(), d["y"].copy()
    bad = d["val"] != 0
    x[bad] = y[bad] = np.nan
    return d, x, y


def binned(rows):
    rows = np.array(rows) if rows else np.zeros((0, 3))
    out = []
    for lo, hi in BINS:
        r = rows[(rows[:, 0] >= lo) & (rows[:, 0] < hi)] if len(rows) else rows
        out.append({"bin_deg": [lo, hi], "n": int(len(r)),
                    "duration_ms": round(float(np.median(r[:, 1])) * 1000, 1) if len(r) else None,
                    "peak_velocity": round(float(np.median(r[:, 2])), 0) if len(r) else None})
    return out


def fit_duration(rows):
    """Least-squares duration = a + b * amplitude over 4-30 degrees (the main-sequence form motion.py uses)."""
    r = np.array([row for row in rows if 4 <= row[0] < 30])
    b, a = np.polyfit(r[:, 0], r[:, 1] * 1000, 1)
    return {"intercept_ms": round(float(a), 1), "slope_ms_per_deg": round(float(b), 2), "n": int(len(r))}


def fixation_stats(d, x, y):
    """Per 1 s fixation window (from 300 ms after a target appears): RMS dispersion of the 30 Hz-averaged
    gaze around its mean, and micro-saccade count (runs over 15 deg/s with amplitude < 1 deg)."""
    disp, micro, secs = [], 0, 0.0
    tx, ty = d["xT"], d["yT"]
    change = np.flatnonzero((np.diff(tx) != 0) | (np.diff(ty) != 0)) + 1
    for a, b in zip(np.r_[0, change], np.r_[change, len(tx)]):
        for s in range(a + 300, b - 1000, 1000):
            wx, wy = x[s:s + 1000], y[s:s + 1000]
            if np.isnan(wx).any():
                continue
            m = np.array([(wx[i:i + 33].mean(), wy[i:i + 33].mean()) for i in range(0, 990, 33)])
            disp.append(float(np.sqrt(((m - m.mean(0)) ** 2).sum(1).mean())))
            micro += sum(1 for amp, _, _ in saccades(wx, wy, 1000, on=15, min_ms=6) if amp < 1)
            secs += 1
    return disp, micro, secs


def blink_stats(d):
    """Tracking-loss runs of 60-500 ms count as blinks (shorter = noise, longer = looked away)."""
    bad = (d["val"] != 0).astype(int)
    edges = np.flatnonzero(np.diff(np.r_[0, bad, 0]))
    runs = edges[1::2] - edges[::2]
    blinks = runs[(runs >= 60) & (runs <= 500)]
    return list(blinks / 1000), len(d) / 1000


def model_side():
    """Same measurements on motion.py. Saccades: one clean saccade per amplitude, sampled at 1000 Hz,
    through the same detector. Fixation: a 120 s static clip at 30 fps (the rate we render), gaze in
    the world (eye + head, as the chin-rested GazeBase subjects' gaze is)."""
    rows = []
    for amp in range(5, 30):
        clip = motion.Clip(1.0).look(0.2, amp, 0, blink_on_large=False)
        t = np.arange(1000) / 1000
        yaw = np.array([motion._direction(clip, ti)[0] for ti in t])
        rows += saccades(yaw, np.zeros_like(yaw), 1000)
    disp = []
    for seed in range(5):
        clip = motion.Clip(120.0, seed)
        f = motion.render_clip(clip, fps=30)
        gx = (f["left_yaw"] + f["right_yaw"]) / 2 + f["head_yaw"]
        gy = (f["left_pitch"] + f["right_pitch"]) / 2 + f["head_pitch"]
        for s in range(0, len(gx) - 30, 30):
            m = np.c_[gx[s:s + 30], gy[s:s + 30]]
            disp.append(float(np.sqrt(((m - m.mean(0)) ** 2).sum(1).mean())))
    # micro-saccades: motion.py draws gaps uniform(0.6, 1.6) s; blinks: natural_blinks every uniform(3, 6) s
    closed = [t for t in np.arange(0, 0.5, 0.001) if motion.blink_profile(t) > 0.5]
    return {"saccades": rows, "dispersion": disp, "micro_per_s": 1 / 1.1, "blinks_per_min": 60 / 4.5,
            "blink_closed_ms": round((closed[-1] - closed[0]) * 1000)}


def main(zpath, limit=None):
    outer = zipfile.ZipFile(zpath)
    subjects = sorted(n for n in outer.namelist() if n.startswith("Round_1/Subject_") and n.endswith(".zip"))[:limit]
    sac, disp, micro, secs, blinks, blink_secs = [], [], 0, 0.0, [], 0.0
    for k, name in enumerate(subjects):
        inner = zipfile.ZipFile(io.BytesIO(outer.read(name)))
        files = {Path(n).stem.split("_")[-1]: n for n in inner.namelist() if "/S1/" in "/" + n and n.endswith(".csv")}
        if not {"RAN", "FXS", "VD1"} <= files.keys():
            continue
        d, x, y = load(inner, files["RAN"])
        sac += saccades(x, y, 1000)
        d, x, y = load(inner, files["FXS"])
        a, b, c = fixation_stats(d, x, y)
        disp, micro, secs = disp + a, micro + b, secs + c
        d, _, _ = load(inner, files["VD1"])
        a, b = blink_stats(d)
        blinks, blink_secs = blinks + a, blink_secs + b
        print(f"\r{k + 1}/{len(subjects)} subjects", end="", flush=True)
    print()
    m = model_side()
    human = {"subjects": len(subjects), "duration_fit": fit_duration(sac), "main_sequence": binned(sac),
             "fixation_dispersion_deg": {"median": round(float(np.median(disp)), 3), "p10": round(float(np.percentile(disp, 10)), 3),
                                         "p90": round(float(np.percentile(disp, 90)), 3), "windows": len(disp)},
             "micro_saccades_per_s": round(micro / secs, 2),
             "blinks_per_min": round(len(blinks) / blink_secs * 60, 1),
             "blink_loss_ms_median": round(float(np.median(blinks)) * 1000)}
    model = {"duration_fit": fit_duration(m["saccades"]), "main_sequence": binned(m["saccades"]),
             "fixation_dispersion_deg": {"median": round(float(np.median(m["dispersion"])), 3),
                                         "p10": round(float(np.percentile(m["dispersion"], 10)), 3),
                                         "p90": round(float(np.percentile(m["dispersion"], 90)), 3)},
             "micro_saccades_per_s": round(m["micro_per_s"], 2), "blinks_per_min": round(m["blinks_per_min"], 1),
             "blink_closed_ms": m["blink_closed_ms"]}
    report = {"source": "GazeBase v2.0, Round 1, session 1 (CC BY 4.0)", "human": human, "truegaze": model}
    out = ROOT / "outputs" / "gazebase_comparison.json"
    out.write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
    assert human["duration_fit"]["n"] > 100 and model["duration_fit"]["n"] >= 20, "too few saccades detected"


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
