#!/usr/bin/env python3
"""Builds the submission deck from the organizers' template (docs/organizer/Submission_Final_forGithub.pptx).
Slide order and headers are the template's; pictures come from docs/ and outputs/. Needs python-pptx, pillow, ffmpeg.

Numbers on the slides are printed by: tools/evaluate_motion.py (kinematics), tools/seam_audit.py (seams),
tools/fit_bulge.py (soft tissue), tools/transfer_skin.py (skin fit), tools/make_hair.py (strands),
outputs/launch_spec/metadata.json (direction check). Re-run them and edit here if anything changes.

Run: python3 tools/make_deck.py        -> VITVellore_ZeroDrift.pptx
"""
import copy
import io
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

WHITE, TEXT, MUTED = RGBColor(0xFF, 0xFF, 0xFF), RGBColor(0xE8, 0xED, 0xF5), RGBColor(0x9A, 0xA8, 0xC0)
CYAN, GREEN, AMBER, PANEL = RGBColor(0x00, 0xB4, 0xD8), RGBColor(0x00, 0xE5, 0xB0), RGBColor(0xF5, 0x9E, 0x0B), RGBColor(0x0D, 0x1B, 0x3E)

prs = Presentation(ROOT / "docs" / "organizer" / "Submission_Final_forGithub.pptx")
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
    """paragraphs: a string, or a list of strings / lists of (text, colour, bold) runs."""
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
s_brownie2, s_limits = clone(s_brownie), clone(s_diff)
order = [s_title, s_problem, s_solution, s_arch, s_output, s_tex, s_kin, s_port, s_diff, s_demo, s_brownie, s_brownie2, s_limits, s_thanks]
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
text(s_title, 0.55, 3.75, 7.5, 0.5, "Photoreal, animated eyes on Google's GNM head, built entirely by script", size=16, color=CYAN)
picture(s_title, ROOT / "docs" / "hero_sets.jpg", 0.55, 4.25, 7.4, crop=(0, 0, 1, 0.5))

# 2 problem
header(s_problem, "THE PROBLEM")
headline(s_problem, "A bare head model has to pass for a living person, up close")
text(s_problem, 0.4, 1.7, 5.3, 3.4, [
    [("Nothing to look at. ", CYAN, True), ("Google's GNM head ships shape and a UV layout, but no skin and no iris texture. Every pixel of the face has to be made.", TEXT, False)],
    [("Eyes give fakes away. ", CYAN, True), ("People read eyes first. Wrong saccade speed, a blink that opens as fast as it closes, or lids that ignore the eyeball all read as dead.", TEXT, False)],
    [("It must travel. ", CYAN, True), ("Textures have to wrap onto any GNM head with no visible seam, and one script has to turn an input word into a finished video.", TEXT, False)],
], size=13, gap=12)
for i, (points, label) in enumerate(((60, "Texture photorealism"), (20, "Kinematic accuracy"), (20, "Code and UV portability"))):
    panel(s_problem, 6.1, 1.7 + i * 1.15, 3.5, 1.0)
    text(s_problem, 6.3, 1.7 + i * 1.15, 1.2, 1.0, str(points), size=36, color=AMBER, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    text(s_problem, 7.4, 1.7 + i * 1.15, 2.1, 1.0, [label, [("points in the rubric", MUTED, False)]], size=12, anchor=MSO_ANCHOR.MIDDLE, gap=0)
picture(s_problem, ROOT / "outputs" / "renders" / "01_clay_front.png", 0.4, 3.75, 2.4)
text(s_problem, 2.95, 3.75, 2.7, 1.35, "The head with no texture: shape alone does not read as a person.", size=11, color=MUTED, anchor=MSO_ANCHOR.MIDDLE)

# 3 solution
header(s_solution, "SOLUTION")
headline(s_solution, "Eight people, one command per video, every asset built by script")
picture(s_solution, ROOT / "outputs" / "renders" / "01_hero.png", 0.4, 1.7, 4.6)
text(s_solution, 0.4, 4.35, 4.6, 0.3, "Set 01, hero view. Rendered by tools/stills.py", size=10, color=MUTED)
text(s_solution, 5.3, 1.7, 4.3, 3.5, [
    [("Textures. ", GREEN, True), ("8 sets: 4K skin, roughness, relief and wrinkle maps, plus a 2K map per eye. Left and right irises always differ.", TEXT, False)],
    [("Skin. ", GREEN, True), ("Public-domain MakeHuman skins, fitted onto GNM in 3D to a median 0.5 mm.", TEXT, False)],
    [("Motion. ", GREEN, True), ("Saccades, vergence, blinks and lid-follow timed from published eye measurements.", TEXT, False)],
    [("Soft tissue. ", GREEN, True), ("Lids lift over the cornea and skin drags with the eye. About 7,500 hair strands follow the lids.", TEXT, False)],
    [("One script. ", GREEN, True), ("render.py --input Left | Right | \"Generate Motion\" writes the video.", TEXT, False)],
], size=12, gap=9)

# 4 architecture
header(s_arch, "ARCHITECTURE")
headline(s_arch, "Two open inputs, four fitting steps, one scene builder")
columns = [
    ("Inputs", CYAN, ["GNM head v3\n(Google, Apache 2.0)", "MakeHuman skins\n(CC0)"]),
    ("Fit once", GREEN, ["Lid and brow controls", "Socket, bulge, skin drag", "Lashes, brows, down", "Skin transfer in 3D"]),
    ("Generate", GREEN, ["8 texture sets\n(UDIM 1001, 1002, 1004)", "Motion engine\n(gaze, lids, blinks)"]),
    ("Build and render", AMBER, ["Scene from script\n(Blender 4.5, bpy)", "render.py\nCycles on Metal"]),
    ("Outputs", AMBER, ["3 videos", "24 stills", "scene.blend", "Launch-spec frames\nand metadata"]),
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
    [("Checks on every build: ", CYAN, True), ("seam audit, motion evaluation against published ranges, 14 unit tests, direction check.", TEXT, False)],
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
    [("Iris: ", CYAN, True), ("thick cords, crypts, collarette, freckles, limbal ring, under a cornea that refracts.", TEXT, False)],
    [("White of the eye: ", CYAN, True), ("veins entering from the corners, yellowish patches, pink corners.", TEXT, False)],
    [("Skin: ", CYAN, True), ("photo colour, pores and fine lines as relief, thin skin with faint veins round the eye.", TEXT, False)],
    [("Lid edge: ", CYAN, True), ("wet pink margin with a tear line.", TEXT, False)],
    [("Left is never right: ", CYAN, True), ("each eye has its own pattern.", TEXT, False)],
], size=11, gap=7)

# 7 kinematics
header(s_kin, "TRACK FINAL OUTPUT · KINEMATICS")
headline(s_kin, "Motion numbers sit inside published ranges for real eyes")
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
card(s_kin, 7.75, 1.7, 1.85, 1.15, "5 of 5", "Left, Right, Up, Down, Reset pass the direction check", accent=AMBER)
card(s_kin, 7.75, 3.0, 1.85, 1.18, "4 fixed", "The check found four numbers off. All four were corrected", accent=AMBER)
text(s_kin, 0.4, 4.35, 9.2, 0.9, [
    "Also in the motion: both eyes converge, upper lids follow vertical gaze, large gaze jumps trigger a blink, the eye never freezes (drift and micro-saccades), pupils fluctuate.",
    [("Source: tools/evaluate_motion.py, which lists the papers. Direction check: outputs/launch_spec/metadata.json", MUTED, False)],
], size=11, gap=4)

# 8 portability
header(s_port, "TRACK FINAL OUTPUT · PORTABILITY")
headline(s_port, "The textures fit any GNM head, and the seams are measured")
for i, name in enumerate(("portability_03", "portability_05_identity3", "portability_07_identity11")):
    picture(s_port, ROOT / "outputs" / "renders" / f"{name}.png", 0.4 + i * 2.05, 1.7, 1.95, crop=(0.15, 0.1, 0.85, 0.9))
text(s_port, 0.4, 4.02, 6.1, 0.5, "Stock GNM heads straight from Google's weights, one template face and two random identities, wearing our sets. None of our rig is on them (apply_textures.py).", size=10, color=MUTED)
card(s_port, 6.75, 1.7, 2.85, 1.05, "Seam step 6 of 255 or less", "On the front of the face, all 8 sets. 142 seam edges checked (tools/seam_audit.py).", accent=GREEN)
card(s_port, 6.75, 2.87, 2.85, 1.05, "Fresh clone to finished videos", "./reproduce.sh rebuilds every asset and output. Downloads are pinned by SHA-256.", accent=GREEN)
card(s_port, 6.75, 4.04, 2.85, 1.2, "Plain GNM layout", "Files are named by GNM's UDIM tile. The .blend plays with no script permission.", accent=GREEN)
text(s_port, 0.4, 4.7, 6.1, 0.5, "The seam audit caught two real regressions during the build, before any render showed them.", size=12)

# 9 differentiation
header(s_diff, "DIFFERENTIATION")
headline(s_diff, "Measured where others would only claim")
cards = [
    ("Numbers, not adjectives", "Seams, saccades, blinks and the skin fit each have a script that prints the number and fails the build if it leaves its range."),
    ("Controls inside GNM's own space", "Blink, lid and brow controls are solved as mixes of GNM's 200 unnamed eye components, so they work on any GNM face."),
    ("Skin moved in 3D, not painted", "Public-domain skins are carried onto GNM by fitting one head to the other: median 0.5 mm, lids and lip line pinned."),
    ("The eye pushes the face", "Fitted shapes lift the lid 1.6 mm over the cornea and drag nearby skin up to 2.7 mm as the eye turns. Lashes follow."),
    ("Nothing hand-made", "No hand-edited .blend, no painted texture. Anyone can rebuild all of it from a clone."),
    ("Licence-clean", "GNM is Apache 2.0, MakeHuman skins are CC0. No photo or scan of an identifiable person."),
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
text(s_demo, 0.4, 4.7, 9.2, 0.4, [[("Repo: ", CYAN, True), (REPO, WHITE, True)]], size=14)

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
    [("Inner corner: ", CYAN, True), ("pink tissue and its fine ridge, which GNM lacks.", TEXT, False)],
    [("Motion blur: ", CYAN, True), ("fast saccades smear like on a real camera.", TEXT, False)],
], size=11, gap=7)
picture(s_brownie2, video_frames("Generate_Motion_hero", (0.6, 1.0, 2.6, 5.2)), 0.4, 3.8, 5.9)
text(s_brownie2, 0.4, 4.68, 5.9, 0.25, "Frames of outputs/videos/Generate_Motion_hero.mp4", size=10, color=MUTED)

# 13 results and limits
header(s_limits, "RESULTS & LIMITATIONS")
headline(s_limits, "What works, and what a close look will still find")
card(s_limits, 0.4, 1.7, 4.5, 3.3, "Results", [
    "All six required outputs, rebuilt by one script.",
    "8 texture sets; seam step 6 of 255 or less on the face.",
    "Every sourced motion check in range; direction check 5 of 5.",
    "Textures wrap onto stock and random GNM heads.",
    "Skin fit to the photo source: median 0.5 mm.",
    "14 unit tests pass.",
], accent=GREEN, size=13)
card(s_limits, 5.1, 1.7, 4.5, 3.3, "Limits", [
    "Iris light pooling is a shader estimate, not traced caustics.",
    "The upper lid creases in shading only; it does not fold into itself.",
    "Skin wrinkles are drawn by rule, not sculpted.",
    "Sheen on dark skin was tuned by eye, not measured.",
    "The three videos use one face (set 01); the other sets are stills.",
    "Motion is checked against published ranges, not our own eye recordings.",
], accent=AMBER, size=13)

# 14 thanks
for shape in s_thanks.shapes:
    if shape.name == "Text 25":
        run = shape.text_frame.paragraphs[0].add_run()
        run.text, run.font.size, run.font.name = f"Team Zero Drift · VIT Vellore · {REPO}", Pt(10), "Calibri"
        run.font.color.rgb = WHITE

out = ROOT / "VITVellore_ZeroDrift.pptx"
prs.save(out)
print("wrote", out, f"({len(order)} slides)")
