# Required outputs and where they are

| Required (Track 1 brief) | Where | Made by |
|---|---|---|
| 5–10 UV texture maps, face + distinct left/right iris | `textures/01` … `08`, one overview sheet each in `uv_maps/` | `python3 -m truegaze.textures` |
| Python script with inputs `Left`, `Right`, `Generate Motion` | `render.py` | — |
| A video for each input, ≤ 15 s | `outputs/videos/` (9, 9 and 12 s) | `render.py --all` |
| 5–10 renders with different textures | **`outputs/renders/01_front.png` … `08_front.png`**, one per set; 27 extra views (close, hero, clay, wire, portability, refraction on/off) | `tools/stills.py` |
| `.blend` with an expression on the Timeline | `outputs/scene.blend`: eyes, lids, brows and pupil keyed, textures packed | `render.py --input "Generate Motion" --blend outputs/scene.blend` |
| Launch spec: `move(h, v)`, `reset()`, `render()`, 10 clockwise frames at 1024², per-frame JSON | `wrapper/eyes.py`, `outputs/launch_spec/` | `wrapper/eyes.py -- --sequence outputs/launch_spec` |

## Videos

| Input | Video | Length |
|---|---|---|
| `Left` | [Left.mp4](../outputs/videos/Left.mp4) | 9 s |
| `Right` | [Right.mp4](../outputs/videos/Right.mp4) | 9 s |
| `Generate Motion` | [Generate_Motion.mp4](../outputs/videos/Generate_Motion.mp4) | 12 s |
| `Generate Motion`, close hero view | [Generate_Motion_hero.mp4](../outputs/videos/Generate_Motion_hero.mp4) | 12 s |
| `Generate Motion`, dark skin (set 03) | [Generate_Motion_set03.mp4](../outputs/videos/Generate_Motion_set03.mp4) | 12 s |
| `Generate Motion`, mesh on top | [Generate_Motion_wire.mp4](../outputs/videos/Generate_Motion_wire.mp4) | 12 s |

## Submission package

| Asked for | Where |
|---|---|
| Working code in a public GitHub repo | this repo |
| README with reproducible setup and Docker file | `README.md`, `reproduce.sh`, `Dockerfile`, [RUN.md](RUN.md) |
| Deck named `CollegeName_TeamName` | `VITVellore_ZeroDrift.pptx`, built from the organizers' template by `tools/make_deck.py` |
| Demo video, ≤ 3 min | `outputs/demo.mp4` (2 min 48 s, Indian English voice-over by Sarvam AI Bulbul, captions timed to the speech, built by `tools/make_demo.py`), on YouTube: https://youtu.be/ydB1k3vBDyk |
| Launch-spec bundle | `python3 tools/make_launch_zip.py` writes `VITVellore_ZeroDrift.zip` with `scene.blend`, `wrapper/eyes.py`, `renders/`, `metadata.json`, `README.md` at the root. Passes 5 / 5 from a clean unzip. Download: [release `submission`](https://github.com/akshat333-debug/TrueGaze/releases/tag/submission) |
| AI disclosure | [AI_DISCLOSURE.md](AI_DISCLOSURE.md) |
