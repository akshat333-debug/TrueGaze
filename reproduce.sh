#!/bin/sh
# Rebuilds every deliverable from a fresh clone. Needs Blender 4.5 LTS, ffmpeg, and: pip install -r requirements.txt
#   ./reproduce.sh            everything, final-quality videos (hours)
#   ./reproduce.sh draft      everything, draft videos (about 40 minutes on an M3)
# Set BLENDER if blender is not on the PATH, e.g. BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
set -e
B=${BLENDER:-blender}
QUALITY=${1:-final}
python3 tools/fit_controls.py          # eyelid and brow controls        -> assets/controls.npz
python3 tools/fit_bulge.py             # socket depth, lid bulge, drag   -> assets/bulge.npz
python3 tools/make_hair.py             # lashes, brows, tear line, down  -> assets/hair.npz
python3 tools/transfer_skin.py         # GNM <-> MakeHuman skin lookup   -> assets/skin_transfer.npz
python3 -m truegaze.textures           # 8 texture sets                  -> textures/
python3 tools/seam_audit.py            # seam check + UV overview sheets -> uv_maps/
python3 -m pytest tests -q
"$B" --background --python tools/stills.py                                   # outputs/renders/
"$B" --background --python tools/stills.py -- 01 --style wire
"$B" --background --python apply_textures.py -- --texture 05 --identity 3   # UV portability proof
"$B" --background --python wrapper/eyes.py -- --sequence outputs/launch_spec
"$B" --background --python render.py -- --input "Generate Motion" --blend outputs/scene.blend
"$B" --background --python render.py -- --all --quality "$QUALITY"          # outputs/videos/
"$B" --background --python render.py -- --input "Generate Motion" --view hero --quality "$QUALITY"
