# Decisions

Format: ID · date · decision · why · alternatives rejected. Never edit an old entry; supersede it.

### D-001 · 12 Nov · Track 1 Synthetic Eyes
- Why: college PoC allowed only Track 1 or 4. Track 4 needs ~184 GB of video, GPU-heavy models and a hidden scored subset. Track 1 runs in Blender on a laptop.
- Risk accepted: 60% of the score is judged visually.

### D-002 · 12 Nov · Deliver both Track 1 specs
- The 12 Nov evaluation deck (textures, 3 inputs, videos, `.blend`) and the launch spec (`eyes.move(h, v)`, 35 cm target, 40 cm camera, 10-frame sequence, per-frame JSON) differ. Both are built; the launch spec is cheap once the rig exists.
