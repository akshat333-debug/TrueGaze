#!/usr/bin/env python3
"""Builds the submission deck from the organizers' template (docs/dev/organizer/Submission_Final_forGithub.pptx).
Slide order and headers are the template's; pictures come from docs/ and outputs/. Needs python-pptx, pillow, ffmpeg.

Numbers on the slides are printed by: tools/evaluate_motion.py (kinematics), tools/seam_audit.py (seams),
tools/fit_bulge.py (soft tissue), tools/transfer_skin.py (skin fit), tools/make_hair.py (strands),
outputs/launch_spec/metadata.json (direction check). Re-run them and edit here if anything changes.

Run: python3 tools/make_deck.py        -> VITVellore_ZeroDrift.pptx
"""
import copy
import io
import json
import subprocess
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
MEMBERS = ["Akshat Agrawal (23MIC0079)", "Hemang Dubey (23MIC0069)", "Ishita Solanki (23MID0443)"]
REPO = "github.com/akshat333-debug/TrueGaze"
REPO_URL, DEMO_URL = "https://" + REPO, "https://youtu.be/ydB1k3vBDyk"
LAUNCH = json.loads((ROOT / "outputs" / "launch_spec" / "metadata.json").read_text())
LABEL_ERR = LAUNCH["label_error_px"]["refracted"]  # written by wrapper/eyes.py --sequence
assert all(LAUNCH["direction_check"].values()), "direction check failed: fix before building the deck"

WHITE, TEXT, MUTED = RGBColor(0xFF, 0xFF, 0xFF), RGBColor(0xE8, 0xED, 0xF5), RGBColor(0x9A, 0xA8, 0xC0)
CYAN, GREEN, AMBER, PANEL = RGBColor(0x00, 0xB4, 0xD8), RGBColor(0x00, 0xE5, 0xB0), RGBColor(0xF5, 0x9E, 0x0B), RGBColor(0x0D, 0x1B, 0x3E)

prs = Presentation(ROOT / "docs" / "dev" / "organizer" / "Submission_Final_forGithub.pptx")
template = list(prs.slides)


def clone(src):
    """A copy of a template slide (python-pptx has no duplicate): same background and header shapes."""
    new = prs.slides.add_slide(src.slide_layout)
    for shape in list(new.shapes):
        shape._element.getparent().remove(shape._element)
    for el in src.shapes._spTree:
        if el.tag.endswith("}sp"):
            new.shapes._spTree.append(copy.deepcopy(el))
    new._element.cSld.insert(0, copy.deepcopy(src._element.cSld.bg))
    return new


def header(slide, title):
    for shape in list(slide.shapes):
        if shape.name == "Text 2":
            shape.text_frame.paragraphs[0].runs[0].text = title
        elif shape.name.startswith("Text Box"):  # empty box left in the template
            shape._element.getparent().remove(shape._element)


def text(slide, x, y, w, h, paragraphs, size=12, color=TEXT, bold=False, font="Calibri", anchor=MSO_ANCHOR.TOP, gap=4):
    """paragraphs: a string, or a list of strings / lists of (text, colour, bold[, url]) runs."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap, tf.vertical_anchor = True, anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, para in enumerate([paragraphs] if isinstance(paragraphs, str) else paragraphs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        for run in [(para, color, bold)] if isinstance(para, str) else para:
            r = p.add_run()
            r.text, r.font.size, r.font.name, r.font.bold = run[0], Pt(size), font, run[2]
            r.font.color.rgb = run[1]
            if len(run) > 3:  # optional 4th item: a URL, so the run is a clickable link
                r.hyperlink.address = run[3]
    return box


def headline(slide, words):
    text(slide, 0.4, 1.02, 9.2, 0.5, words, size=20, color=WHITE, bold=True)


def panel(slide, x, y, w, h):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.adjustments[0] = 0.06
    shape.fill.solid()
    shape.fill.fore_color.rgb = PANEL
    shape.line.fill.background()
    return shape


def card(slide, x, y, w, h, title, body, accent=CYAN, size=11):
    panel(slide, x, y, w, h)
    text(slide, x + 0.15, y + 0.12, w - 0.3, 0.3, title, size=13, color=accent, bold=True)
    text(slide, x + 0.15, y + 0.45, w - 0.3, h - 0.55, body, size=size, gap=size - 5)


def picture(slide, path, x, y, w, crop=None):
    """Adds a picture as JPEG (keeps the deck small). crop = (left, top, right, bottom) as fractions."""
    img = Image.open(path).convert("RGB")
    if crop:
        W, H = img.size
        img = img.crop((int(crop[0] * W), int(crop[1] * H), int(crop[2] * W), int(crop[3] * H)))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    buf.seek(0)
    return slide.shapes.add_picture(buf, Inches(x), Inches(y), width=Inches(w))


def table(slide, x, y, widths, rows, size=11, row_h=0.3):
    t = slide.shapes.add_table(len(rows), len(widths), Inches(x), Inches(y), Inches(sum(widths)), Inches(row_h * len(rows))).table
    for c, w in enumerate(widths):
        t.columns[c].width = Inches(w)
    for r, row in enumerate(rows):
        t.rows[r].height = Inches(row_h)
        for c, value in enumerate(row):
            cell = t.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = PANEL if r == 0 else RGBColor(0x0A, 0x0E, 0x1A)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            run = cell.text_frame.paragraphs[0].add_run()
            run.text, run.font.size, run.font.name, run.font.bold = value, Pt(size), "Calibri", r == 0
            run.font.color.rgb = CYAN if r == 0 else GREEN if value in ("in range", "pass", "done") else TEXT


def video_frames(name, times):
    """A strip of frames from one of our videos, as a temporary JPEG."""
    out = ROOT / "renders" / "tmp" / f"deck_{name}.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    args = []
    for t in times:
        args += ["-ss", str(t), "-i", str(ROOT / "outputs" / "videos" / f"{name}.mp4")]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", f"hstack=inputs={len(times)}", "-frames:v", "1", "-q:v", "3", str(out)], check=True)
    return out


s_title, s_problem, s_solution, s_arch, s_output, s_diff, s_demo, s_brownie, s_thanks = template
s_tex, s_kin, s_port = clone(s_output), clone(s_output), clone(s_output)
s_brownie2, s_limits, s_known = clone(s_brownie), clone(s_diff), clone(s_diff)
order = [s_title, s_problem, s_solution, s_arch, s_output, s_tex, s_kin, s_port, s_diff, s_demo, s_brownie, s_brownie2, s_limits, s_known, s_thanks]
ids = prs.slides._sldIdLst
by_id = {el.get("id"): el for el in ids}
for slide in order:
    ids.append(by_id[str(slide.slide_id)])  # append moves the element, so this leaves the list in `order`

# 1 title
for shape in s_title.shapes:
    if not shape.has_text_frame:
        continue
    runs = [r for p in shape.text_frame.paragraphs for r in p.runs]
    words = shape.text_frame.text
    if words == "Track No":
        runs[0].text = "Track 1 · Synthetic Eyes"
    elif words == "XR Hackathon":
        runs[0].text = "TrueGaze"
    elif words.startswith("Team Name"):
        runs[0].text, runs[1].text = "Team Zero Drift", "VIT Vellore"
    elif words == "Members Details":
        runs[0].text = "\n".join(MEMBERS)
text(s_title, 0.55, 3.75, 7.5, 0.5, "Synthetic eyes that pass for human, and ship with pixel-exact ground truth", size=16, color=CYAN)
picture(s_title, ROOT / "docs" / "hero_sets.jpg", 0.55, 4.25, 7.4, crop=(0, 0, 1, 0.5))

# 2 problem
header(s_problem, "THE PROBLEM")
headline(s_problem, "Gaze AI needs millions of labelled eyes. Real capture can't scale")
text(s_problem, 0.4, 1.7, 5.3, 3.4, [
    [("Real eyes are costly. ", CYAN, True), ("Capture is slow, labels are manual, and eye images are biometric data.", TEXT, False)],
    [("GNM ships bare. ", CYAN, True), ("Shape and UVs, no skin, no iris. Every pixel has to be made.", TEXT, False)],
    [("Eyes give fakes away. ", CYAN, True), ("Wrong saccade speed or lids that ignore the eyeball read as dead.", TEXT, False)],
], size=13, gap=12)
for i, (points, label) in enumerate(((60, "Texture photorealism"), (20, "Kinematic accuracy"), (20, "Code and UV portability"))):
    panel(s_problem, 6.1, 1.7 + i * 1.15, 3.5, 1.0)
    text(s_problem, 6.3, 1.7 + i * 1.15, 1.2, 1.0, str(points), size=36, color=AMBER, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s_problem, 7.4, 1.7 + i * 1.15, 2.1, 1.0, [label, [("points in the rubric", MUTED, False)]], size=12, anchor=MSO_ANCHOR.MIDDLE, gap=0)
picture(s_problem, ROOT / "outputs" / "renders" / "01_clay_front.png", 0.4, 3.75, 2.4)
text(s_problem, 2.95, 3.75, 2.7, 1.35, "The head with no texture: shape alone does not read as a person.", size=11, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)

# 3 solution
header(s_solution, "SOLUTION")
headline(s_solution, "Eight photoreal people, one command, every asset built by script")
picture(s_solution, ROOT / "outputs" / "renders" / "01_hero.png", 0.4, 1.7, 4.6)
text(s_solution, 0.4, 4.35, 4.6, 0.3, "Set 01, hero view. Rendered by tools/stills.py", size=10, color=MUTED)
text(s_solution, 5.3, 1.7, 4.3, 3.5, [
    [("True 3D gaze. ", GREEN, True), ("Eyeballs rotate about their centres and converge on one point.", TEXT, False)],
    [("8 skins. ", GREEN, True), ("4K skin, 2K irises; left and right never match.", TEXT, False)],
    [("Real timing. ", GREEN, True), ("Saccades within 10 ms of 322 recorded people.", TEXT, False)],
    [("Exact labels. ", GREEN, True), ("Pupil refracted by the cornea: 1.16 px from the pixels.", TEXT, False)],
    [("One script. ", GREEN, True), ("render.py --input Left | Right | \"Generate Motion\".", TEXT, False)],
], size=12, gap=9)

# 4 architecture
header(s_arch, "ARCHITECTURE")
headline(s_arch, "Two open inputs, four fitting steps, one scene builder")
columns = [
    ("Inputs", CYAN, ["GNM head v3\n(Google, Apache 2.0)", "MakeHuman skins\n(CC0)"]),
    ("Fit once", GREEN, ["Lid and brow controls", "Socket, bulge, skin drag", "Lashes, brows, down", "Skin transfer in 3D"]),
    ("Generate", GREEN, ["8 texture sets\n(UDIM 1001, 1002, 1004)", "Motion engine\n(gaze, lids, blinks)"]),
    ("Build and render", AMBER, ["Scene from script\n(Blender 4.5, bpy)", "render.py\nCycles on Metal"]),
    ("Outputs", AMBER, ["6 videos", "33 stills", "scene.blend", "Launch-spec frames\nand metadata"]),
]
for c, (name, accent, boxes) in enumerate(columns):
    x = 0.4 + c * 1.87
    text(s_arch, x, 1.65, 1.72, 0.3, name, size=12, color=accent, bold=True)
    for r, label in enumerate(boxes):
        panel(s_arch, x, 2.0 + r * 0.62, 1.72, 0.54)
        text(s_arch, x + 0.08, 2.0 + r * 0.62, 1.56, 0.54, label, size=10, anchor=MSO_ANCHOR.MIDDLE, gap=0)
    if c < len(columns) - 1:
        arrow = s_arch.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + 1.735), Inches(2.2), Inches(0.12), Inches(0.14))
        arrow.fill.solid()
        arrow.fill.fore_color.rgb = MUTED
        arrow.line.fill.background()
text(s_arch, 0.4, 4.6, 9.2, 0.7, [
    [("Checks on every build: ", CYAN, True), ("seam audit, motion evaluation against published ranges, 16 unit tests, direction check on the rendered pixels.", TEXT, False)],
    [("Stack: ", CYAN, True), ("Python 3, NumPy, SciPy, Pillow, Blender 4.5 LTS (bpy, Cycles), ffmpeg. No trained model, no GPU server.", TEXT, False)],
], size=11, gap=3)

# 5 required outputs
header(s_output, "TRACK FINAL OUTPUT")
headline(s_output, "Every required output exists and is rebuilt by one script")
table(s_output, 0.4, 1.7, [3.3, 3.6, 2.3], [
    ["Required", "Where in the repo", "Made by"],
    ["5 to 10 UV maps, face and distinct irises", "textures/01 to 08, sheets in uv_maps/", "truegaze/textures.py"],
    ["Script with Left, Right, Generate Motion", "render.py", "one command per input"],
    ["A video per input, 15 s or less", "outputs/videos/ (9 s, 9 s, 12 s)", "render.py --all"],
    ["5 to 10 renders with different textures", "outputs/renders/ (8 sets, 3 views each)", "tools/stills.py"],
    [".blend with an expression on the Timeline", "outputs/scene.blend", "render.py --blend"],
    ["Launch spec: move, reset, render, 10 frames", "wrapper/eyes.py, outputs/launch_spec/", "wrapper/eyes.py --sequence"],
], size=10.5, row_h=0.33)
picture(s_output, video_frames("Generate_Motion", (1.0, 2.0, 5.2, 7.0)), 0.4, 4.12, 7.2)
text(s_output, 7.75, 4.12, 1.85, 1.0, "Four frames of outputs/videos/ Generate_Motion.mp4", size=10, color=MUTED)

# 6 textures
header(s_tex, "TRACK FINAL OUTPUT · TEXTURES")
headline(s_tex, "Eight texture sets: light and dark skin, young to old, six eye colours")
picture(s_tex, ROOT / "docs" / "texture_sets.jpg", 0.4, 1.65, 6.2)
text(s_tex, 6.85, 1.65, 2.75, 3.6, [
    [("Iris: ", CYAN, True), ("cords, crypts, collarette, limbal ring, under a refracting cornea.", TEXT, False)],
    [("Sclera: ", CYAN, True), ("veins from the corners, pink corners.", TEXT, False)],
    [("Skin: ", CYAN, True), ("photo colour, pores as relief.", TEXT, False)],
    [("Seams: ", CYAN, True), ("step of 4 / 255 or less.", TEXT, False)],
    [("Left is never right: ", CYAN, True), ("each eye has its own pattern.", TEXT, False)],
], size=11, gap=7)

# 7 kinematics
header(s_kin, "TRACK FINAL OUTPUT · KINEMATICS")
headline(s_kin, "Moves like a real eye: checked against physiology and 322 people")
table(s_kin, 0.4, 1.7, [3.0, 1.3, 1.9, 0.9], [
    ["Measured on our motion engine", "Ours", "Published range", ""],
    ["Saccade duration, 10 degrees", "44.5 ms", "40 to 57 ms", "in range"],
    ["Saccade duration, 30 degrees", "99 ms", "80 to 111 ms", "in range"],
    ["Blink closing time", "86.5 ms", "50 to 130 ms", "in range"],
    ["Whole blink", "337.5 ms", "250 to 450 ms", "in range"],
    ["Closing faster than opening by", "50.7 %", "35 to 55 %", "in range"],
    ["Blink rate at rest", "16.7 per min", "10 to 20 per min", "in range"],
    ["Vergence on a 35 cm target, per eye", "5.1 degrees", "5.06 degrees (geometry)", "in range"],
], size=10.5, row_h=0.31)
card(s_kin, 7.75, 1.7, 1.85, 1.15, "5 of 5", "Left, Right, Up, Down, Reset, judged from the pupils found in the renders", accent=AMBER)
card(s_kin, 7.75, 3.0, 1.85, 1.18, "322 people", "Saccade timing within 10 ms of GazeBase recordings", accent=AMBER)
text(s_kin, 0.4, 4.35, 9.2, 0.9, [
    "Also: vergence, lids follow gaze, blinks on big jumps, drift and micro-saccades, pupil hippus.",
    [("Sources: tools/evaluate_motion.py, tools/gazebase_compare.py, outputs/launch_spec/metadata.json", MUTED, False)],
], size=11, gap=4)

# 8 portability
header(s_port, "TRACK FINAL OUTPUT · PORTABILITY")
headline(s_port, "The textures fit any GNM head, and the seams are measured")
for i, name in enumerate(("portability_03", "portability_05_identity3", "portability_07_identity11")):
    picture(s_port, ROOT / "outputs" / "renders" / f"{name}.png", 0.4 + i * 2.05, 1.7, 1.95, crop=(0.15, 0.1, 0.85, 0.9))
text(s_port, 0.4, 4.02, 6.1, 0.5, "Stock GNM heads straight from Google's weights, one template face and two random identities, wearing our sets. None of our rig is on them (apply_textures.py).", size=10, color=MUTED)
card(s_port, 6.75, 1.7, 2.85, 1.05, "Seam step 4 of 255 or less", "On the front of the face, all 8 sets. 142 seam edges checked (tools/seam_audit.py).", accent=GREEN)
card(s_port, 6.75, 2.87, 2.85, 1.05, "Fresh clone to finished videos", "./reproduce.sh rebuilds every asset and output. Downloads are pinned by SHA-256.", accent=GREEN)
card(s_port, 6.75, 4.04, 2.85, 1.2, "Plain GNM layout", "Files are named by GNM's UDIM tile. The .blend plays with no script permission.", accent=GREEN)
text(s_port, 0.4, 4.7, 6.1, 0.5, "The seam audit caught two real regressions during the build, before any render showed them.", size=12)

# 9 differentiation
header(s_diff, "DIFFERENTIATION")
headline(s_diff, "Measured where others would only claim")
cards = [
    ("3D gaze, not 2D", "Eyeballs rotate about their centres; the usual approach slides a pupil texture."),
    ("Labels that match pixels", "Cornea-refracted pupil labels: 14 % lower error than a pinhole projection."),
    ("Checked against humans", "Saccade timing within 10 ms of 40,539 recorded saccades."),
    ("The eye pushes the face", "Lid lifts 1.6 mm over the cornea, skin drags 2.7 mm, lashes follow."),
    ("Native to GNM", "Controls solved in GNM's own 200 eye components: any GNM face works."),
    ("Ship-ready licence", "Apache 2.0 head, CC0 skins, no real person. FLAME-based rigs are research-only."),
]
for i, (title, body) in enumerate(cards):
    card(s_diff, 0.4 + (i % 3) * 3.1, 1.7 + (i // 3) * 1.8, 2.95, 1.65, title, body, accent=GREEN, size=12)

# 10 demo and local setup
header(s_demo, "DEMO & LOCAL SETUP")
headline(s_demo, "Clone, run one script, get every output")
panel(s_demo, 0.4, 1.7, 5.6, 2.75)
text(s_demo, 0.6, 1.85, 5.2, 2.5, [
    [("# everything, from a fresh clone", MUTED, False)],
    "./reproduce.sh draft",
    [("# or one video at a time", MUTED, False)],
    "blender --background --python render.py -- --input Left",
    "blender --background --python render.py -- --input Right",
    "blender --background --python render.py -- \\",
    "    --input \"Generate Motion\" --quality final",
    [("# checks", MUTED, False)],
    "python3 tools/seam_audit.py",
    "python3 tools/evaluate_motion.py",
], size=10, font="Courier New", gap=3)
text(s_demo, 6.3, 1.7, 3.3, 2.8, [
    [("Needs: ", CYAN, True), ("Blender 4.5 LTS, Python 3 with numpy, scipy, pillow, and ffmpeg.", TEXT, False)],
    [("Hardware: ", CYAN, True), ("built and rendered on an M3 laptop with 8 GB of memory.", TEXT, False)],
    [("Time: ", CYAN, True), ("draft videos in about 40 minutes; final quality takes hours.", TEXT, False)],
    [("Videos: ", CYAN, True), ("outputs/videos/ in the repo.", TEXT, False)],
], size=12, gap=9)
text(s_demo, 0.4, 4.7, 9.2, 0.4, [[("Repo: ", CYAN, True), (REPO, WHITE, True, REPO_URL), ("     Demo: ", CYAN, True), ("youtu.be/ydB1k3vBDyk", WHITE, True, DEMO_URL)]], size=14)

# 11 brownie: soft tissue
header(s_brownie, "BROWNIE SLIDES · SOFT TISSUE")
headline(s_brownie, "The skin round the eye moves with the eye")
picture(s_brownie, ROOT / "docs" / "breakdown.jpg", 0.4, 1.7, 9.2)
text(s_brownie, 0.4, 3.47, 9.2, 0.25, "Mesh, grey shape and final render of the same frame (render.py --style wire | clay)", size=10, color=MUTED)
for i, (number, label) in enumerate((("2.9 mm", "eye sunk into a socket; GNM's template lids are puffy"), ("1.6 mm", "lid lifts over the cornea; before, the cornea cut through the lid"), ("2.7 mm", "skin near the lid dragged round with the eyeball"))):
    panel(s_brownie, 0.4 + i * 3.1, 3.9, 2.95, 1.35)
    text(s_brownie, 0.55 + i * 3.1, 3.98, 2.65, 0.5, number, size=26, color=AMBER, bold=True)
    text(s_brownie, 0.55 + i * 3.1, 4.55, 2.65, 0.65, label, size=11)

# 12 brownie: look and natural motion
header(s_brownie2, "BROWNIE SLIDES · NATURAL DETAIL")
headline(s_brownie2, "Details taken from the reference videos and their author's notes")
picture(s_brownie2, ROOT / "docs" / "hero_sets.jpg", 0.4, 1.7, 5.9)
text(s_brownie2, 0.4, 3.4, 5.9, 0.25, "Hero view of all eight sets: hard side light, shallow focus", size=10, color=MUTED)
text(s_brownie2, 6.55, 1.7, 3.05, 3.5, [
    [("Blink follows the eyeball: ", CYAN, True), ("a half-closed shape keeps the lid on the curve.", TEXT, False)],
    [("Wrinkles on demand: ", CYAN, True), ("forehead lines deepen as brows rise, crow's feet as lids close.", TEXT, False)],
    [("Light pooling in the iris: ", CYAN, True), ("computed in the shader. An approximation, not traced light.", TEXT, False)],
    [("Inner corner: ", CYAN, True), ("pink tissue, which GNM lacks.", TEXT, False)],
    [("Motion blur: ", CYAN, True), ("fast saccades smear like on a real camera.", TEXT, False)],
], size=11, gap=7)
picture(s_brownie2, video_frames("Generate_Motion_hero", (0.6, 1.0, 2.6, 5.2)), 0.4, 3.8, 5.9)
text(s_brownie2, 0.4, 4.68, 5.9, 0.25, "Frames of outputs/videos/Generate_Motion_hero.mp4", size=10, color=MUTED)

# 13 results and limits
header(s_limits, "RESULTS & IMPACT")
headline(s_limits, "Every number measured. Every frame a labelled training sample")
card(s_limits, 0.4, 1.7, 4.5, 3.3, "Results", [
    "Direction check 5 / 5, judged from the pixels.",
    f"Pupil labels {LABEL_ERR['mean']} px from the rendered pupil.",
    "Saccades within 10 ms of 322 people.",
    "Seam step 4 / 255 or less, all 8 skins.",
    "All outputs from one command; 16 tests pass.",
], accent=GREEN, size=13)
card(s_limits, 5.1, 1.7, 4.5, 3.3, "Impact for Samsung XR", [
    "Train Galaxy XR eye tracking: rotation, pupil and camera labels on every frame.",
    "Fairness tests across 8 skin tones and 6 eye colours.",
    "Zero biometric capture: no consent or storage burden.",
    "Unbounded variety on a laptop: seeds x skins x GNM identities.",
    "Lifelike eyes for XR avatars.",
], accent=AMBER, size=13)

# 14 limitations
header(s_known, "LIMITATIONS & NEXT STEPS")
headline(s_known, "What a close look still finds, and what we would do next")
card(s_known, 0.4, 1.7, 4.5, 3.3, "Limitations", [
    "Peak saccade speed 15-20 % below GazeBase; fewer micro-saccades than humans.",
    "Blinks lift the cheek slightly; with motion blur it softens for 1-2 frames.",
    "Upper lid creases in shading only; it does not fold into itself.",
    "Iris light pooling is a shader estimate, not traced caustics.",
    "Required videos use set 01 (set 03 in a fourth); other sets are stills.",
], accent=AMBER, size=12)
card(s_known, 5.1, 1.7, 4.5, 3.3, "Next steps", [
    "Fit saccade speed on half of GazeBase, test on the other half.",
    "Confine the blink to the lids; add a real lid fold.",
    "Render a labelled dataset across all 8 sets and GNM identities.",
    "Train a gaze estimator on it and test on real eye images.",
], accent=GREEN, size=12)

# 15 thanks
for shape in s_thanks.shapes:
    if shape.name == "Text 25":
        run = shape.text_frame.paragraphs[0].add_run()
        run.text, run.font.size, run.font.name = "Team Zero Drift · VIT Vellore · ", Pt(10), "Calibri"
        run.font.color.rgb = WHITE
        for label, url in ((REPO, REPO_URL), (" · Demo: ", None), ("youtu.be/ydB1k3vBDyk", DEMO_URL)):
            part = shape.text_frame.paragraphs[0].add_run()
            part.text, part.font.size, part.font.name = label, Pt(10), "Calibri"
            part.font.color.rgb = WHITE
            if url:
                part.hyperlink.address = url

out = ROOT / "VITVellore_ZeroDrift.pptx"
prs.save(out)

# link colour: the template's default blue vanishes on the dark slides, so use light cyan in every theme
import re
import shutil
import zipfile
tmp = out.with_suffix(".tmp")
with zipfile.ZipFile(out) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename.startswith("ppt/theme/theme"):
            data = re.sub(rb"(<a:hlink>\s*<a:srgbClr val=\")[0-9A-Fa-f]{6}", rb"\g<1>7FE3F5", data)
            data = re.sub(rb"(<a:folHlink>\s*<a:srgbClr val=\")[0-9A-Fa-f]{6}", rb"\g<1>7FE3F5", data)
        zout.writestr(item, data)
shutil.move(tmp, out)
print("wrote", out, f"({len(order)} slides)")
