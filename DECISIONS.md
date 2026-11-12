# Decisions

Format: ID · date · decision · why · alternatives rejected. Never edit an old entry; supersede it.

### D-001 · 12 Nov · Track 1 Synthetic Eyes
- Why: college PoC allowed only Track 1 or 4. Track 4 needs ~184 GB of video, GPU-heavy models and a hidden scored subset. Track 1 runs in Blender on a laptop.
- Risk accepted: 60% of the score is judged visually.

### D-002 · 12 Nov · Deliver both Track 1 specs
- The 12 Nov evaluation deck (textures, 3 inputs, videos, `.blend`) and the launch spec (`eyes.move(h, v)`, 35 cm target, 40 cm camera, 10-frame sequence, per-frame JSON) differ. Both are built; the launch spec is cheap once the rig exists.

### D-003 · 12 Nov · Head model = Google GNM Head v3
- "GNM" in the organizer deck is Google's Generative aNthropometric Model (github.com/google/GNM), Apache 2.0 for code and weights, so it can sit in a public repo. Includes eyeballs with separate cornea, eye joints, eyelid/brow expression components and an official UDIM UV layout.
- Rejected: FLAME (licence limits, no eyeball detail). Fallback if GNM cannot be driven in Blender by end of 13 Nov: MPFB CC0 head.

### D-004 · 12 Nov · Export GNM once, build the Blender scene from our own script
- GNM's package needs Python 3.13 and TensorFlow; Blender 4.5 ships Python 3.11. Exporting to `assets/gnm_head.npz` keeps the judge's setup to "install Blender, run one command".
- Rejected: community GNM Blender add-on (licence unclear, extra dependency).

### D-005 · 12 Nov · Textures: two routes, renders decide
- GNM ships no skin texture. Route A: CC0 MakeHuman/MPFB skins baked into the GNM UV layout (the floor). Route B: synthetic non-existent identities generated with a depth-conditioned diffusion model and projected to UV. A Route B set ships only if it beats Route A side by side.
- Iris and sclera are generated procedurally; left and right differ.

### D-006 · 12 Nov · Direction convention
- Organizers have not said whose left "Left" means. Default: left **on screen**; `--frame subject` gives the character's left. Videos carry a caption naming the input; metadata records both.

### D-007 · 12 Nov · Close-up framing for showcase videos
- Reference videos (Chris Jones, "Eye Piece" and "Flexpressions") are eye-region close-ups. A close-up camera shows what is scored and hides the missing hair. The 40 cm launch-spec camera is kept for the spec renders.

### D-008 · 12 Nov · Required outputs before brownie features
- By 17 Nov every required output exists end to end at draft quality. Extras (lid bulge, lashes, tear line, head follow) only after that.

### D-009 · 12 Nov · GO on GNM; no export step (amends D-004)
- Spike passed: head builds in Blender, eyes rotate, eyelids close cleanly. The MPFB fallback is dropped.
- GNM's weights are a plain `.npz` and v3.0 has zero pose correctives, so `truegaze/gnm.py` reads the official file directly with NumPy inside Blender. No Python 3.13 environment, no TensorFlow, no `export_gnm.py`.
- Our controls are stored as coefficient vectors in GNM's own expression space (`assets/controls.npz`, a few KB), so they work on any GNM head, which supports the portability score.

