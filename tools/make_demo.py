"""Cuts the demo video (under 3 minutes, silent, captioned) from the rendered clips and overview images.
Run after ./reproduce.sh:  python3 tools/make_demo.py  ->  outputs/demo.mp4. Needs ffmpeg and Pillow."""
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
V, D = ROOT / "outputs/videos", ROOT / "docs"
# (source, caption, seconds shown for a still image)
SHOTS = [
    (V / "Generate_Motion_hero.mp4", "TrueGaze, Team Zero Drift: script input \"Generate Motion\", close view", 0),
    (V / "Left.mp4", "Script input \"Left\": both eyes turn left, lids and skin follow", 0),
    (V / "Right.mp4", "Script input \"Right\"", 0),
    (V / "Generate_Motion.mp4", "Script input \"Generate Motion\": saccades, blinks, small drift", 0),
    (V / "Generate_Motion_wire.mp4", "Same motion in wireframe: socket, lid lift and skin drag are geometry", 0),
    (D / "breakdown.jpg", "Wireframe, clay, final", 5),
    (D / "texture_sets.jpg", "Eight texture sets on the GNM UV layout, left and right iris distinct", 8),
    (D / "hero_sets.jpg", "The same eight sets, close view", 6),
    (V / "Generate_Motion_set03.mp4", "Any set, any input: set 03.  Everything rebuilds with ./reproduce.sh", 0),
]
FONT = "/System/Library/Fonts/Helvetica.ttc"  # shortcut: macOS path, falls back to Pillow's built-in font elsewhere


def caption(text, path):
    strip = Image.new("RGBA", (1280, 56), (0, 0, 0, 150))
    try:
        font = ImageFont.truetype(FONT, 26)
    except OSError:
        font = ImageFont.load_default(26)
    ImageDraw.Draw(strip).text((640, 28), text, font=font, fill="white", anchor="mm")
    strip.save(path)


def main():
    missing = [str(s) for s, _, _ in SHOTS if not s.exists()]
    if missing:
        raise SystemExit("missing: " + ", ".join(missing))
    with tempfile.TemporaryDirectory() as tmp:
        parts = []
        for i, (source, text, seconds) in enumerate(SHOTS):
            strip, part = f"{tmp}/{i}.png", f"{tmp}/{i}.mp4"
            caption(text, strip)
            still = ["-loop", "1", "-t", str(seconds)] if seconds else []
            fit = "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:-1:-1,fps=30,setsar=1"
            subprocess.run(["ffmpeg", "-v", "error", "-y", *still, "-i", str(source), "-i", strip, "-filter_complex",
                            f"[0:v]{fit}[v];[v][1:v]overlay=0:664", "-an", "-c:v", "libx264", "-crf", "18",
                            "-pix_fmt", "yuv420p", part], check=True)
            parts.append(part)
        Path(f"{tmp}/list.txt").write_text("".join(f"file '{p}'\n" for p in parts))
        out = ROOT / "outputs/demo.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt",
                        "-c", "copy", str(out)], check=True)
        length = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                       str(out)], capture_output=True, text=True, check=True).stdout)
        assert length <= 180, f"demo is {length:.0f} s, limit is 180"
        print(f"{out} {length:.0f} s")


if __name__ == "__main__":
    main()
