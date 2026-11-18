"""Builds the launch-spec bundle with the layout the brief asks for, at the zip root:
scene.blend, wrapper/eyes.py, renders/ (10 frames), metadata.json, README.md
(plus wrapper/truegaze/, the helpers eyes.py imports, so the bundle runs on its own).

    python3 tools/make_launch_zip.py [launch_dir] [out.zip]   # default: outputs/launch_spec/ -> VITVellore_ZeroDrift.zip
"""
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "outputs" / "launch_spec"
OUT = ROOT / "VITVellore_ZeroDrift.zip"


def entries(SRC=SRC):
    yield SRC / "scene.blend", "scene.blend"
    yield SRC / "metadata.json", "metadata.json"
    yield ROOT / "docs" / "launch_bundle_README.md", "README.md"
    yield ROOT / "wrapper" / "eyes.py", "wrapper/eyes.py"
    for f in sorted((ROOT / "truegaze").glob("*.py")):
        yield f, f"wrapper/truegaze/{f.name}"
    frames = sorted((SRC / "renders").glob("frame_*.png"))
    assert len(frames) == 10, f"need 10 frames in {SRC / 'renders'}, found {len(frames)}"
    for f in frames:
        yield f, f"renders/{f.name}"


def main(src=SRC, out=OUT):
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for src, name in entries(Path(src)):
            if not src.is_file():
                sys.exit(f"missing {src}; run: blender --background --python wrapper/eyes.py -- --sequence outputs/launch_spec")
            z.write(src, name)
    names = zipfile.ZipFile(out).namelist()
    assert {"scene.blend", "wrapper/eyes.py", "metadata.json", "README.md"} <= set(names)
    print(f"wrote {out.name}: {len(names)} files, {out.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else OUT) if len(sys.argv) > 1 else main()
