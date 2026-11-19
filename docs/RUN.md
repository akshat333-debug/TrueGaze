# Run it

Needs [Blender 4.5 LTS](https://www.blender.org/download/lts/4-5/), `ffmpeg`, and Python 3 with `pip install -r requirements.txt` (NumPy, SciPy, Pillow, for building assets; rendering uses Blender's own Python).

```bash
./reproduce.sh draft      # everything from a fresh clone, draft quality (about 40 min on an M3)
./reproduce.sh            # final quality (hours)
```

## One output at a time

```bash
BLENDER=/Applications/Blender.app/Contents/MacOS/Blender   # or "blender" on Linux
python3 -m truegaze.textures                                # 8 texture sets, about 3 min
$BLENDER --background --python render.py -- --input Left
$BLENDER --background --python render.py -- --input Right --texture 03
$BLENDER --background --python render.py -- --input "Generate Motion" --quality final
$BLENDER --background --python render.py -- --all
$BLENDER --background --python tools/stills.py -- 01 02 03
$BLENDER --background --python wrapper/eyes.py -- --sequence outputs/launch_spec
$BLENDER --background --python apply_textures.py -- --texture 05 --identity 3
python3 tools/make_launch_zip.py                            # VITVellore_ZeroDrift.zip
python3 tools/seam_audit.py
python3 tools/evaluate_motion.py
python3 -m pytest tests -q
```

`render.py` options: `--seed N` (different natural blinks and micro-movements), `--frame screen|subject` (whose left "Left" means; default the viewer's), `--quality draft|final`, `--texture 01..08`, `--view front|hero`, `--style textured|clay|wire`.

Final quality renders single frames with Cycles and joins them with `ffmpeg`. A stopped run resumes where it stopped; frame folders carry a fingerprint of the code and textures, so frames from an older look are never reused. About 25 s per frame on an M3 with 8 GB.

## Motion check against GazeBase (optional)

Download [GazeBase v2.0](https://doi.org/10.6084/m9.figshare.12912257) (6.7 GB, CC BY 4.0), then:

```bash
python3 tools/gazebase_compare.py path/to/GazeBase_v2_0.zip   # about 6 min
python3 tools/plot_main_sequence.py
```

## Demo video

```bash
SARVAM_API_KEY=... python3 tools/make_demo.py   # outputs/demo.mp4: narrated, captioned, under 3 min
```

The terminal shots replay real runs saved in `renders/tmp/capture/` (`check.txt`, `render.txt`).

## Docker

```bash
docker build -t truegaze . && docker run --rm -v "$PWD/outputs:/app/outputs" truegaze
```

x86-64 Linux, CPU rendering. Builds the assets, texture sets, seam audit, tests and stills; full videos need more than 4 GB of memory.
