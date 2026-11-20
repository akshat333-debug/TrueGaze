# AI disclosure

TrueGaze was designed and built by Team Zero Drift: Akshat Agrawal, Hemang Dubey and Ishita Solanki. We chose the track, the approach and every major design decision: building on Google's GNM head, carrying real skin onto it in 3D, timing the motion on measured eye physiology, refracting pupil labels through the cornea, and checking every claim with a script. We reviewed every output and own everything submitted.

Along the way we used AI tools as assistants, as most engineering teams now do:

| Tool | How it assisted us |
|---|---|
| **Claude Code** (Anthropic) | Coding assistant: helped draft and debug scripts, tests and documentation, and helped with literature and dataset search. |
| **Sarvam AI Bulbul** (text-to-speech) | Read our demo script aloud in Indian English for the demo video voice-over. |
| **Sarvam AI Saarika** (speech-to-text) | Checked that every voice-over line is pronounced correctly. |

## What is not AI-generated

- **No image, texture or video frame comes from a generative model.** Every pixel is rendered by Blender Cycles from our scripts: the GNM head (Google, Apache 2.0), procedural iris and sclera textures, and skin colour carried over from MakeHuman skins (CC0).
- **No trained model is part of the pipeline.** Motion, textures, controls and labels come from explicit code and published measurements.
- **Every number we report is printed by a script in this repo** ([RESULTS.md](RESULTS.md)), so anyone can check it.
