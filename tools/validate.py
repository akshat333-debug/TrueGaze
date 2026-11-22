"""One command that checks the submission against the Track 1 brief. Standard library only (+ ffprobe for videos).

    python3 tools/validate.py                          # the repo
    python3 tools/validate.py --zip VITVellore_ZeroDrift.zip   # a clean unzip of the launch-spec bundle

Checks: every required output exists, the 10 launch frames are 1024x1024 PNGs, metadata.json follows the spec
(theta = 2*pi*k/10, h = sin, v = cos, required keys, direction check 5/5), each required video is 15 s or less,
the left and right iris maps differ, and every relative link in the README and docs resolves.
Exit code 0 only when everything passes.
"""
import json
import math
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRAME_KEYS = {"frame", "theta", "input", "eye_rotation_L", "eye_rotation_R", "pupil_center_2D_L", "pupil_center_2D_R", "camera_matrix"}
results = []


def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}{'  (' + detail + ')' if detail else ''}")
    return ok


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", head[16:24])


def video_seconds(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True)
    return float(out.stdout) if out.returncode == 0 and out.stdout.strip() else None


def check_launch_spec(base, meta_path, frames_dir):
    """The launch-spec contract, wherever it lives (repo or unzipped bundle)."""
    frames = sorted(frames_dir.glob("frame_*.png"))
    check("10 launch frames", len(frames) == 10, f"{len(frames)} found in {frames_dir.relative_to(base)}")
    sizes = {png_size(f) for f in frames}
    check("launch frames are 1024x1024 PNG", sizes == {(1024, 1024)}, str(sizes))
    if not check("metadata.json exists", meta_path.is_file()):
        return
    meta = json.loads(meta_path.read_text())
    recs = meta["frames"] if isinstance(meta, dict) else meta
    check("metadata has 10 records", len(recs) == 10)
    missing = [k for r in recs for k in FRAME_KEYS if k not in r]
    check("metadata records carry every required key", not missing, ", ".join(sorted(set(missing))))
    bad = [r["frame"] for k, r in enumerate(recs)
           if r["frame"] != k or abs(r["theta"] - 2 * math.pi * k / 10) > 1e-3
           or abs(r["input"]["h"] - math.sin(r["theta"])) > 1e-3 or abs(r["input"]["v"] - math.cos(r["theta"])) > 1e-3]
    check("theta = 2*pi*k/10, h = sin(theta), v = cos(theta), clockwise from the top", not bad, f"bad frames {bad}" if bad else "")
    dc = meta.get("direction_check", {}) if isinstance(meta, dict) else {}
    check("direction check 5/5 recorded", dc and all(dc.get(d) for d in ("Left", "Right", "Up", "Down", "Reset")), str(dc))


def check_links(base, files):
    broken = []
    for f in files:
        for link in re.findall(r"\]\(([^)#\s]+)", f.read_text(errors="replace")):
            if not re.match(r"[a-z]+:", link) and not (f.parent / link).resolve().exists():
                broken.append(f"{f.relative_to(base)} -> {link}")
    check("relative links in README and docs resolve", not broken, "; ".join(broken[:5]))


def check_repo():
    need = ["render.py", "apply_textures.py", "wrapper/eyes.py", "reproduce.sh", "Dockerfile", "requirements.txt", "LICENSE",
            "README.md", "VITVellore_ZeroDrift.pptx", "docs/AI_DISCLOSURE.md", "outputs/scene.blend", "outputs/launch_spec/scene.blend"]
    missing = [p for p in need if not (ROOT / p).is_file()]
    check("required files present", not missing, ", ".join(missing))
    sets = sorted(p.name for p in (ROOT / "textures").iterdir() if p.is_dir())
    check("5-10 texture sets", 5 <= len(sets) <= 10, f"{len(sets)} sets")
    for s in sets:
        d = ROOT / "textures" / s
        tiles = [d / f"color.{t}.jpg" for t in (1001, 1002, 1004)]
        if not check(f"set {s}: skin and both eye tiles", all(t.is_file() for t in tiles)):
            continue
        check(f"set {s}: left and right iris differ", tiles[1].read_bytes() != tiles[2].read_bytes())
    check("one UV overview sheet per set", len(list((ROOT / "uv_maps").glob("*.jpg"))) == len(sets))
    renders = [ROOT / f"outputs/renders/{s}_front.png" for s in sets]
    check("one required render per texture set", all(r.is_file() for r in renders))
    for name in ("Left", "Right", "Generate_Motion"):
        v = ROOT / f"outputs/videos/{name}.mp4"
        if not check(f"video {name}.mp4 present", v.is_file()):
            continue
        sec = video_seconds(v) if shutil.which("ffprobe") else None
        if sec is None:
            print(f"SKIP  video {name}.mp4 length (ffprobe not found)")
        else:
            check(f"video {name}.mp4 is 15 s or less", 0 < sec <= 15, f"{sec:.1f} s")
    check_launch_spec(ROOT, ROOT / "outputs/launch_spec/metadata.json", ROOT / "outputs/launch_spec/renders")
    check_links(ROOT, [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))])


def check_zip(path):
    with tempfile.TemporaryDirectory() as tmp:
        zipfile.ZipFile(path).extractall(tmp)
        base = Path(tmp)
        for p in ("scene.blend", "wrapper/eyes.py", "metadata.json", "README.md"):
            check(f"zip root has {p}", (base / p).is_file())
        check_launch_spec(base, base / "metadata.json", base / "renders")


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--zip":
        check_zip(Path(sys.argv[2]))
    else:
        check_repo()
    print(f"\n{sum(results)}/{len(results)} checks passed")
    sys.exit(0 if all(results) else 1)
