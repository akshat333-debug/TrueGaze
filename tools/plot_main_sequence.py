"""Saccade duration vs amplitude: TrueGaze's motion model against 322 recorded people (GazeBase).
Reads outputs/gazebase_comparison.json (from tools/gazebase_compare.py), writes docs/main_sequence.png."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
r = json.loads((ROOT / "outputs/gazebase_comparison.json").read_text())
x = [sum(b["bin_deg"]) / 2 for b in r["human"]["main_sequence"]]
fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=150)
ax.plot(x, [b["duration_ms"] for b in r["human"]["main_sequence"]], "o-", color="#8a8f98", lw=2.5,
        label=f"Humans, GazeBase ({r['human']['subjects']} people, {r['human']['duration_fit']['n']:,} saccades)")
ax.plot(x, [b["duration_ms"] for b in r["truegaze"]["main_sequence"]], "o-", color="#1f6feb", lw=2.5, label="TrueGaze")
ax.set(xlabel="Saccade size (degrees)", ylabel="Duration (ms)", ylim=(0, 100), xlim=(0, 30), title="Saccade timing tracks real people")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(alpha=0.25)
ax.legend(frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(ROOT / "docs/main_sequence.png")
print("wrote docs/main_sequence.png")
