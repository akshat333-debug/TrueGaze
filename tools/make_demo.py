"""Cuts the narrated demo video (under 3 minutes) from the rendered outputs, real terminal runs and result plots.

    SARVAM_API_KEY=... python3 tools/make_demo.py [capture_dir]   ->  outputs/demo.mp4

Voice-over: Sarvam AI Bulbul (Indian English), one request per segment, cached in renders/tmp/voice/.
capture_dir holds the real terminal output shown on screen (default renders/tmp/capture/):
check.txt (wrapper/eyes.py --check), render.txt (render.py --input Left), pytest.txt, seam.txt, motion.txt.
Captions are timed to the pauses in the generated speech. Needs ffmpeg, Pillow and NumPy.
"""
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import urllib.request
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
V, D, OUT = ROOT / "outputs/videos", ROOT / "docs", ROOT / "outputs/demo.mp4"
CAP = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "renders/tmp/capture"
CACHE = ROOT / "renders/tmp/voice"
W, H, FPS = 1280, 720, 30
VOICE = {"model": "bulbul:v4-flash", "speaker": "shubh_en_ads", "pace": 1.1, "temperature": 0.75}
NAVY, PANEL, CYAN, AMBER, WHITE, MUTED = (11, 21, 48), (22, 36, 72), (64, 200, 230), (245, 170, 50), (240, 244, 250), (150, 165, 190)
FONTS = "/System/Library/Fonts/"  # shortcut: macOS fonts, Pillow's default font elsewhere


def font(size, mono=False, bold=False):
    try:
        if mono:
            return ImageFont.truetype(FONTS + "Menlo.ttc", size)
        return ImageFont.truetype(FONTS + "Avenir Next.ttc", size, index=2 if bold else 5)
    except OSError:
        return ImageFont.load_default(size)


# ---------------------------------------------------------------- voice

SAY = {"Saccades": "Sa-kaads", "saccade": "sa-kaad", "1.16 pixels": "one point one six pixels",
       "322 real people": "three hundred and twenty two real people",
       "8 GB": "eight G B"}  # spoken spelling; captions keep the real word


def tts(text):
    """Sarvam TTS for one segment; returns a cached WAV path."""
    for word, spoken in SAY.items():
        text = text.replace(word, spoken)
    key = hashlib.sha1(json.dumps([text, VOICE]).encode()).hexdigest()[:16]
    path = CACHE / f"{key}.wav"
    if not path.exists():
        body = json.dumps({"text": text, "language_code": "en-IN", "speech_sample_rate": 44100, **VOICE}).encode()
        req = urllib.request.Request("https://api.sarvam.ai/text-to-speech", body, {
            "api-subscription-key": os.environ["SARVAM_API_KEY"], "Content-Type": "application/json"})
        audio = json.load(urllib.request.urlopen(req, timeout=120))["audios"][0]
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_bytes(base64.b64decode(audio))
    return path


def samples(path):
    with wave.open(str(path)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768, w.getframerate()


def caption_times(path, sentences):
    """Start and end of each sentence: boundaries snapped to the nearest pause in the speech."""
    x, sr = samples(path)
    hop = int(0.01 * sr)
    loud = np.array([np.sqrt((x[i:i + hop] ** 2).mean()) for i in range(0, len(x) - hop, hop)]) > 0.015
    voiced = np.flatnonzero(loud)
    start, end = voiced[0] * 0.01, voiced[-1] * 0.01 + 0.05
    edges = np.flatnonzero(np.diff(np.r_[1, loud.astype(int), 1]))
    gaps = [(a + b) / 2 * 0.01 for a, b in zip(edges[::2], edges[1::2]) if (b - a) >= 15 and a > voiced[0]]
    chars = np.cumsum([len(s) for s in sentences])
    cuts = [start]
    for c in chars[:-1]:
        guess = start + (end - start) * c / chars[-1]
        cuts.append(min(gaps, key=lambda g: abs(g - guess)) if gaps else guess)
    cuts.append(end)
    return list(zip(cuts[:-1], cuts[1:]))


# ---------------------------------------------------------------- pictures

def caption_png(text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(30, bold=True)
    lines = textwrap.wrap(text, 62)
    lh = 40
    top = H - 34 - lh * len(lines)
    width = max(d.textlength(l, font=f) for l in lines)
    d.rounded_rectangle((W / 2 - width / 2 - 22, top - 12, W / 2 + width / 2 + 22, H - 26), 14, fill=(0, 0, 0, 170))
    for i, l in enumerate(lines):
        d.text((W / 2, top + i * lh + lh / 2), l, font=f, fill=WHITE, anchor="mm")
    img.save(path)


def chip_png(text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if not text:
        return img.save(path)
    d = ImageDraw.Draw(img)
    f = font(22, bold=True)
    w = d.textlength(text, font=f)
    d.rounded_rectangle((24, 22, 24 + w + 36, 64), 10, fill=(*NAVY, 215), outline=CYAN, width=2)
    d.ellipse((38, 38, 48, 48), fill=CYAN)
    d.text((58, 43), text, font=f, fill=WHITE, anchor="lm")
    img.save(path)


def card(path, kicker, title, rows, big=None):
    """A slide-like card: kicker, headline, bullet rows, optional big numbers."""
    img = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 6), fill=CYAN)
    d.text((70, 70), kicker, font=font(22, bold=True), fill=CYAN)
    y = 110
    for line in textwrap.wrap(title, 46):
        d.text((70, y), line, font=font(44, bold=True), fill=WHITE)
        y += 56
    y += 24
    for head, body in rows:
        d.ellipse((72, y + 14, 84, y + 26), fill=AMBER)
        d.text((100, y), head, font=font(30, bold=True), fill=WHITE)
        d.text((100 + d.textlength(head + " ", font=font(30, bold=True)), y + 2), body, font=font(28), fill=MUTED)
        y += 56
    top = y + 24  # numbers sit above the caption band at the bottom
    for i, (num, label) in enumerate(big or []):
        x = 70 + i * 290
        d.rounded_rectangle((x, top, x + 270, top + 110), 14, fill=PANEL)
        d.text((x + 20, top + 4), num, font=font(52, bold=True), fill=AMBER)
        d.text((x + 20, top + 74), label, font=font(20), fill=MUTED)
    img.save(path)


def closing(path):
    frame = ROOT / "renders/tmp/demo_close.png"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "3", "-i", str(V / "Generate_Motion_hero.mp4"), "-frames:v", "1", str(frame)], check=True)
    img = Image.open(frame).convert("RGB").resize((W, H)).filter(ImageFilter.GaussianBlur(3))
    img = Image.blend(img, Image.new("RGB", (W, H), NAVY), 0.55)
    d = ImageDraw.Draw(img)
    d.text((W / 2, 250), "TrueGaze", font=font(110, bold=True), fill=WHITE, anchor="mm")
    d.text((W / 2, 340), "Synthetic eyes that pass for human, with pixel-exact ground truth", font=font(32), fill=CYAN, anchor="mm")
    d.text((W / 2, 430), "github.com/akshat333-debug/TrueGaze", font=font(30, bold=True), fill=WHITE, anchor="mm")
    d.text((W / 2, 480), "Team Zero Drift · VIT Vellore · Samsung PRISM XR Hackathon 2026, Track 1", font=font(24), fill=MUTED, anchor="mm")
    img.save(path)


def launch_frames(tmp, seconds):
    """The 10 launch-spec frames with our pupil labels (ring) and the pupil found in the pixels (dot)."""
    meta = json.loads((ROOT / "outputs/launch_spec/metadata.json").read_text())
    err = meta["label_error_px"]["refracted"]
    paths = []
    for f in meta["frames"]:
        k = f["frame"]
        src = Image.open(ROOT / f"outputs/launch_spec/renders/frame_{k:02d}.png").convert("RGB")
        img = Image.new("RGB", (W, H), NAVY)
        s = 640 / src.width
        img.paste(src.resize((640, 640)), (40, 40))
        d = ImageDraw.Draw(img)
        for side in "LR":
            lx, ly = (40 + v * s for v in f[f"pupil_center_2D_{side}"])
            fx, fy = (40 + v * s for v in f[f"pupil_center_2D_found_{side}"])
            d.ellipse((lx - 16, ly - 16, lx + 16, ly + 16), outline=CYAN, width=3)
            d.ellipse((fx - 4, fy - 4, fx + 4, fy + 4), fill=AMBER)
        x = 720
        d.text((x, 70), "LAUNCH SPEC  ·  wrapper/eyes.py", font=font(22, bold=True), fill=CYAN)
        d.text((x, 110), f"Frame {k} of 10", font=font(46, bold=True), fill=WHITE)
        d.text((x, 175), f"theta {f['theta']:.2f}  h {f['input']['h']:+.2f}  v {f['input']['v']:+.2f}", font=font(22, mono=True), fill=MUTED)
        d.ellipse((x, 250, x + 26, 276), outline=CYAN, width=3)
        d.text((x + 40, 249), "our label, refracted by the cornea", font=font(24), fill=WHITE)
        d.ellipse((x + 8, 308, x + 18, 318), fill=AMBER)
        d.text((x + 40, 297), "pupil found in the rendered pixels", font=font(24), fill=WHITE)
        d.text((x, 380), f"{err['mean']} px", font=font(84, bold=True), fill=AMBER)
        d.text((x, 480), f"mean label error · {err['max']} px max", font=font(24), fill=MUTED)
        rot = f["eye_rotation_L"]
        d.text((x, 540), f"eye_rotation_L  [{rot[0]:.1f}, {rot[1]:.1f}, {rot[2]:.1f}] deg", font=font(20, mono=True), fill=MUTED)
        p = f"{tmp}/launch_{k}.png"
        img.save(p)
        paths.append(p)
    return paths


def terminal(tmp, name, command, lines, seconds, note):
    """Frames of a terminal: the command is typed, then its real output appears. Returns an mp4."""
    f, n = font(19, mono=True), int(seconds * FPS)
    typed_frames = min(int(len(command) / 30 * FPS), n // 3)
    show_until = n - FPS  # last second holds the full output
    rows = 17  # keeps the text above the caption band
    frames_dir = Path(tmp) / f"term_{name}"
    frames_dir.mkdir()
    for i in range(n):
        img = Image.new("RGB", (W, H), (12, 14, 20))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((40, 40, W - 40, H - 40), 16, fill=(24, 27, 36))
        for j, c in enumerate(((237, 95, 87), (245, 190, 80), (98, 197, 84))):
            d.ellipse((64 + j * 26, 60, 80 + j * 26, 76), fill=c)
        d.text((W / 2, 68), note, font=font(18), fill=MUTED, anchor="mm")
        typed = command[: int(len(command) * min(1, i / max(typed_frames, 1)))]
        shown = lines[: int(len(lines) * max(0, min(1, (i - typed_frames) / max(show_until - typed_frames, 1))))]
        body = [("$ " + typed, (120, 230, 140))] + [(l, (215, 220, 230)) for l in shown]
        for r, (text, col) in enumerate(body[-rows:]):
            d.text((70, 100 + r * 25), text[:105], font=f, fill=col)
        img.save(frames_dir / f"{i:04d}.png")
    out = f"{tmp}/{name}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", str(frames_dir / "%04d.png"),
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", out], check=True)
    return out


def clean(path, keep):
    """Real terminal output, Blender's per-sample progress lines removed."""
    text = Path(path).read_text(errors="replace").replace(str(ROOT) + "/", "")
    text = re.sub(r"/\S*/capture/", "", text).splitlines()  # scratch folder of the capture run
    out = []
    for l in text:
        if re.search(keep, l):
            out += textwrap.wrap(l.rstrip(), 100) or [""]
    return out


# ---------------------------------------------------------------- shots

def fit_video(src, start, seconds, out):
    """A clip trimmed to `seconds`; a clip that is too short holds its last frame."""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(start), "-i", str(src), "-t", str(seconds), "-filter_complex",
                    f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:-1:-1:color=#0b1530,fps={FPS},setsar=1,"
                    f"tpad=stop_mode=clone:stop_duration={seconds}", "-t", str(seconds), "-an",
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", out], check=True)


def fit_image(src, seconds, out, zoom=True, inset=False):
    if inset:  # a plot: framed on the navy background, below the chip
        img = Image.new("RGB", (W, H), NAVY)
        plot = Image.open(src).convert("RGB")
        plot.thumbnail((W - 160, H - 250))
        img.paste(plot, ((W - plot.width) // 2, 84))
        src = Path(out).with_suffix(".png")
        img.save(src)
    n = int(seconds * FPS)
    move = f",zoompan=z='1+0.04*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS}" if zoom else ""
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(src), "-t", str(seconds), "-filter_complex",
                    f"[0:v]scale={W * 2}:{H * 2}:force_original_aspect_ratio=decrease,pad={W * 2}:{H * 2}:-1:-1:color=#0b1530,setsar=1"
                    f"{move},scale={W}:{H},fps={FPS}", "-t", str(seconds), "-an", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", out], check=True)


def slideshow(paths, seconds, out):
    each = seconds / len(paths)
    lst = Path(out).with_suffix(".txt")
    lst.write_text("".join(f"file '{p}'\nduration {each}\n" for p in paths) + f"file '{paths[-1]}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-vf", f"fps={FPS},format=yuv420p",
                    "-t", str(seconds), "-c:v", "libx264", "-crf", "18", out], check=True)


# Each segment: narration, a chip label, and the pictures (kind, source, start or None, share of the time).
SEGMENTS = [
    ("Meet TrueGaze. Synthetic eyes that pass for human, and ship with pixel-exact ground truth. "
     "By Team Zero Drift, VIT Vellore.",
     "TrueGaze  ·  render.py --input \"Generate Motion\", hero view",
     [("video", V / "Generate_Motion_hero.mp4", 0.0, 1)]),
    ("Eye trackers in headsets like Galaxy XR learn from millions of labelled eye images. "
     "Real capture is slow, costly, and biometric. And Google's GNM head ships with no skin and no iris.",
     "The problem",
     [("card", "problem", None, 1)]),
    ("So we built everything by script. One command. Type Left, and TrueGaze builds the scene, "
     "turns both eyeballs about their true centres, and renders the video.",
     "Real run  ·  render.py --input Left",
     [("term", "render", None, 0.6), ("video", V / "Left.mp4", 0.0, 0.4)]),
    ("Look closely. The lids follow the eye, the skin around it moves, and the lashes ride the lid. Right works exactly the same way.",
     "Input: Left, then Right",
     [("video", V / "Left.mp4", 0.7, 0.5), ("video", V / "Right.mp4", 0.7, 0.5)]),
    ("Generate Motion is where it comes alive. Saccades timed on the real main sequence, "
     "blinks that close fast and open slow, an eye roll, and fixation drift.",
     "Input: Generate Motion",
     [("video", V / "Generate_Motion.mp4", 0.0, 1)]),
    ("Under the hood, this is real geometry. The eye sits in a socket, the lid lifts over the cornea, and nearby skin drags as the eye turns.",
     "Same motion, wireframe  ·  soft tissue is geometry",
     [("video", V / "Generate_Motion_wire.mp4", 0.0, 1)]),
    ("Eight complete texture sets. Light to dark skin, six eye colours, and the left and right iris never match, just like real people. "
     "Every set wraps onto any GNM head, with no visible seams.",
     "8 texture sets on GNM's own UDIM layout",
     [("image", D / "texture_sets.jpg", None, 0.5), ("video", V / "Generate_Motion_set03.mp4", 0.0, 0.5)]),
    ("Now, the launch spec. Ten frames, clockwise from the top. The rings are our pupil labels. "
     "We refract them through the cornea, so they land within 1.16 pixels of the pupil in the image.",
     "Launch spec  ·  10 frames + metadata.json",
     [("launch", None, None, 1)]),
    ("And our direction check does not trust our own labels. It renders every pose, and finds the pupils in the pixels. "
     "Left, right, up, down, reset. Five out of five.",
     "Real run  ·  wrapper/eyes.py --check",
     [("term", "check", None, 1)]),
    ("We also checked the motion against GazeBase, 322 real people. "
     "Our eye movements match human timing within ten milliseconds, at every size.",
     "Motion vs. 322 recorded people  ·  tools/gazebase_compare.py",
     [("image", D / "main_sequence.png", None, 1)]),
    ("So, what does Samsung get? Free, ready-labelled training data for headset eye tracking. Fairness tests across skin tones. "
     "Zero biometric capture. All on a simple 8 GB laptop.",
     "Impact for Samsung XR",
     [("card", "impact", None, 1)]),
    ("Clone the repo, run one script, and every output rebuilds. TrueGaze. Eyes that pass for human.",
     "github.com/akshat333-debug/TrueGaze",
     [("card", "close", None, 1)]),
]


def build_cards(tmp):
    card(f"{tmp}/card_problem.png", "THE PROBLEM", "Gaze AI needs millions of labelled eyes. Real capture can't scale.", [
        ("Slow and costly:", "every frame captured and labelled by hand"),
        ("Biometric data:", "consent, storage, deletion"),
        ("GNM ships bare:", "shape and UVs, no skin, no iris"),
    ], big=[("60", "points: photorealism"), ("20", "points: kinematics"), ("20", "points: portability")])
    card(f"{tmp}/card_impact.png", "IMPACT FOR SAMSUNG XR", "Every frame is a labelled training sample.", [
        ("Train eye tracking:", "rotation, pupil and camera on every frame"),
        ("Test fairness:", "8 skin tones, 6 eye colours"),
        ("Zero capture:", "no real person, no biometric data"),
        ("Scale anywhere:", "built on an 8 GB laptop, no GPU server"),
    ], big=[("5 / 5", "direction check"), ("1.16 px", "label error"), ("322", "people: saccade timing")])
    closing(f"{tmp}/card_close.png")


def main():
    if "SARVAM_API_KEY" not in os.environ and not CACHE.exists():
        raise SystemExit("set SARVAM_API_KEY (Sarvam AI) to generate the voice-over")
    terms = {
        "render": ("blender --background --python render.py -- --input Left",
                   clean(CAP / "render.txt", r"^(?!Fra:|Time:)\S"), "render.py, real run, sped up"),
        "check": ("blender --background outputs/launch_spec/scene.blend --python wrapper/eyes.py -- --check",
                  clean(CAP / "check.txt", r"^(?!Fra:|Time:)\S"), "wrapper/eyes.py --check, real run, sped up"),
    }
    with tempfile.TemporaryDirectory() as tmp:
        build_cards(tmp)
        parts, audio, t0, timeline = [], [], 0.0, []
        for i, (text, chip, shots) in enumerate(SEGMENTS):
            wav = tts(text)
            x, sr = samples(wav)
            lead, tail = 0.35, 0.55
            seconds = round(lead + len(x) / sr + tail, 2)
            sentences = re.split(r"(?<=[.!?])\s+", text)
            for s, (a, b) in zip(sentences, caption_times(wav, sentences)):
                timeline.append((t0 + lead + a, t0 + lead + b, s))
            subs = []
            for j, (kind, src, start, share) in enumerate(shots):
                sec = round(seconds * share, 2)
                out = f"{tmp}/s{i}_{j}.mp4"
                if kind == "video":
                    fit_video(src, start, sec, out)
                elif kind == "image":
                    fit_image(src, sec, out, inset=src.name == "main_sequence.png")
                elif kind == "card":
                    fit_image(f"{tmp}/card_{src}.png", sec, out, zoom=src != "problem")
                elif kind == "launch":
                    slideshow(launch_frames(tmp, sec), sec, out)
                elif kind == "term":
                    cmd, lines, note = terms[src]
                    out = terminal(tmp, f"t{i}", cmd, lines, sec, note)
                subs.append(out)
            chip_png(chip if shots[0][0] not in ("card", "launch") else "", f"{tmp}/chip{i}.png")
            lst = Path(f"{tmp}/seg{i}.txt")
            lst.write_text("".join(f"file '{p}'\n" for p in subs))
            seg = f"{tmp}/seg{i}.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", f"{tmp}/chip{i}.png",
                            "-filter_complex", f"[0:v][1:v]overlay=0:0,scale={W}:{H}:out_range=tv,setsar=1,fps={FPS},format=yuv420p",
                            "-frames:v", str(round(seconds * FPS)), "-color_range", "tv", "-c:v", "libx264", "-crf", "18", seg], check=True)
            parts.append(seg)
            padded = f"{tmp}/a{i}.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-af", f"adelay={int(lead * 1000)}:all=1,apad",
                            "-t", str(seconds), "-ar", "44100", "-ac", "1", padded], check=True)
            audio.append(padded)
            t0 += seconds
        Path(f"{tmp}/v.txt").write_text("".join(f"file '{p}'\n" for p in parts))
        Path(f"{tmp}/a.txt").write_text("".join(f"file '{p}'\n" for p in audio))
        # captions: one transparent track, a PNG per sentence held while it is spoken
        blank = f"{tmp}/blank.png"
        Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(blank)
        rows, cursor = [], 0.0
        for k, (a, b, s) in enumerate(timeline):
            caption_png(s, f"{tmp}/cap{k}.png")
            if a > cursor:
                rows.append((blank, a - cursor))
            rows.append((f"{tmp}/cap{k}.png", b - a))
            cursor = b
        rows.append((blank, max(t0 - cursor, 0.1)))
        Path(f"{tmp}/c.txt").write_text("".join(f"file '{p}'\nduration {d:.3f}\n" for p, d in rows) + f"file '{blank}'\n")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{tmp}/c.txt", "-vf", f"fps={FPS},format=rgba",
                        "-c:v", "png", f"{tmp}/captions.mov"], check=True)
        # concat filter: each segment decoded as its own input, so differing colour tags cannot stop the join
        n = len(parts)
        segs = [x for p in parts for x in ("-i", p)]
        subprocess.run(["ffmpeg", "-v", "error", "-y", *segs,
                        "-f", "concat", "-safe", "0", "-i", f"{tmp}/a.txt", "-i", f"{tmp}/captions.mov",
                        "-filter_complex", "".join(f"[{k}:v]setsar=1,format=yuv420p[s{k}];" for k in range(n))
                        + "".join(f"[s{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0[v];"
                        f"[{n + 1}:v]setpts=N/({FPS}*TB)[c];[v][c]overlay=0:0:eof_action=pass[vout];"
                        f"[{n}:a]loudnorm=I=-16:TP=-1.5:LRA=11[aout]",
                        "-map", "[vout]", "-map", "[aout]", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-movflags", "+faststart", str(OUT)], check=True)
        (ROOT / "renders/tmp/demo_captions.json").write_text(json.dumps(timeline, indent=1))
    length = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(OUT)],
                                  capture_output=True, text=True, check=True).stdout)
    assert length <= 180, f"demo is {length:.0f} s, limit is 180"
    print(f"{OUT} {length:.0f} s, {len(timeline)} captions")


if __name__ == "__main__":
    main()
