# AI disclosure

Team Zero Drift used AI tools in building TrueGaze. This page lists which tools, and what for.

| Tool | Used for |
|---|---|
| **Claude Code** (Anthropic) | Coding assistant: helped write and debug the Python and Blender scripts, the audits and tests, the docs and README, the deck builder (`tools/make_deck.py`) and the demo builder (`tools/make_demo.py`); literature and dataset research. |
| **Sarvam AI Bulbul** (text-to-speech) | The Indian English voice-over of the demo video, generated from our script by `tools/make_demo.py`. |
| **Sarvam AI Saarika** (speech-to-text) | Checking that every voice-over line is pronounced correctly. |

## What is not AI-generated

- **No image, texture or video frame comes from a generative model.** Every pixel is rendered by Blender Cycles from our scripts: the GNM head (Google, Apache 2.0), procedural iris and sclera textures, and skin colour carried over from MakeHuman skins (CC0).
- **No trained model is part of the pipeline.** Motion, textures, controls and labels come from explicit code and published measurements.
- **Every number we report is printed by a script in this repo** (`docs/RESULTS.md`), so it can be checked independently of how the code was written.

The team set the direction, made the design decisions, reviewed the outputs, and is responsible for everything submitted.
