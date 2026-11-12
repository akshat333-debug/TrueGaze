# Plan (draft, 12 Nov — firms up once the head model is confirmed)

Deadline 22 Nov. Rubric: texture photorealism 60, kinematics 20, code and UV portability 20.

1. **Head and rig:** GNM (or FLAME) head in Blender; eyeball meshes with left and right bones rotating about the eye centre; eyelid and eyebrow shape keys.
2. **Textures (60 pts):** 5–10 skin UV maps on the model's own UV layout; distinct left and right iris maps; check for seams in renders.
3. **Motion (20 pts):** gaze L/R/U/D, eyelids follow gaze, natural blinks, saccades with small overshoot; brow motion. Match the two reference videos.
4. **Script (20 pts):** `python render.py --input Left|Right|"Generate Motion"` renders frames and builds a ≤15 s video; plus `eyes.move(h, v)`, `eyes.reset()`, `eyes.render()` and the 10-frame launch sequence with JSON.
5. **Deliverables:** 3 videos, 5–10 renders, `.blend` with timeline animation, README, deck, demo video, public repo.
