# Samsung PRISM — XR Hackathon Challenge 2026

Source: `XR_Hackathon_2026_Consolidated_Slides_for_sharing_v1.pdf` (28 slides) + launch poster/invite.
Organizer: XR Perception Group + PRISM team, **Samsung R&D Institute India, Bangalore (SRI-B)**. Queries: prism@samsung.com

## Timeline — UPDATED 12 Nov 2026 (mail from Prakhar Chandrakar, PRISM)

| Date | Event |
|---|---|
| **22 Nov 2026** | **Final submission** via https://forms.gle/86xENrtqhx988hBt8. Everything (code, resources, docs, demo, ppt, package, README) in a **public GitHub repo**, link shared in the form |
| 29 Nov | Top-12 announced |
| 9 Dec | Final demo |
| 12 Dec | Final results |

Tip from organizers: first hit the required track outputs, then add brownie (extra) features. Track details come via the college PoC. Submission deck template: `Submission_Final_forGithub.pptx` (slides: Track/Team/College/Members, Problem, Solution, Architecture, Track final output, Differentiation, Demo & local setup, Brownie slides, Thank you).

## Original timeline (8 Nov, superseded)

| Date | Event |
|---|---|
| 5 Nov 2026 | Launch (online, 3 PM). Problem statements live, registration opens |
| **8 Nov 2026, 11:59 PM** | **Registration closes** (Google Form: https://forms.gle/oGBXsydqbhE3HS2o9). Final submission link shared ONLY with registered teams |
| **18 Nov 2026, 11:59 PM** | **Final submission. No extension.** Prototype code + demo video + deck |
| 23 Nov | Top 15 announced |
| 27 Nov | Final demo — top 15 present live to Samsung R&D jury |
| 2 Dec | Final results, awards |

Effective build window after registration: ~10 days (Track 1 slide literally says "10-day rapid prototyping sprint").

## Eligibility / team rules
- Student teams from **PRISM-affiliated colleges** only.
- Max **4 members**, all from **same college**.
- Team name format: `CollegeName_TeamName`.
- Per member: name, email, phone, year, branch.
- **One theme (track) per team, one submission per team.**
- Interests named: XR, CV, AI, ML, HCI.

## Generic submission package (all tracks)
- Track-specific deliverables (see below) — exact folder layout matters; evaluators run code directly; non-standard layout = fail.
- Working prototype code — public or shared GitHub repo.
- README with reproducible setup, **Docker files** & other requirements.
- Demo video, **max 3 min** (YouTube/Drive). NOTE: slides 24/27 say "5-min demo video" — conflict; safe = ≤3 min.
- Presentation (PPT/PDF) named `CollegeName_TeamName` (template `CollegeName_TeamName_Submission_ppt`): Theme ID, title, team details, problem statement in own words, solution + architecture diagram, tools/tech stack, innovation highlights, results & limitations.
- Submit via Google Form. **Not following guidelines = direct disqualification.**

## Rewards
- Prizes for **top 4 teams worth ₹1.0 L total** (likely ~1 per track — "track wise awards").
- Certificates: participation for shortlisted (top 15) teams; merit for winners.
- **PRISM worklet** with Samsung mentor for winning teams (subject to mentor availability).
- **2-month summer internship at Samsung R&D** for selected students (may need **MAGPIE coding test**).

---

## Track 1 — Synthetic Eye Movement & Virtual Camera Rendering
**Why:** Gaze-estimator training needs huge GT-annotated gaze datasets; real capture slow, costly, privacy-restricted. Need synthetic data with true 3D spherical eyeball rotation (not 2D pupil translation) + rigid metric calibration.

**Build:** textured, articulatable face rig in **Blender** (MakeHuman/MPFB CC0, GNM Head Editor, or Textured FLAME) with L/R eye bones; Python wrapper rotating both eyeballs about their centers.

**Specs**
- Fixation target **35 cm** forward of eye midpoint (motion bounds ±5 cm).
- Render camera locked **40 cm** forward facing face; **1024×1024 PNG**, constant lighting.
- API: `eyes.move(h, v)`, `eyes.reset()`, `eyes.render()`; inputs normalized [-1, +1].
- Synchronous (both eyes) articulation; 10 clockwise renders at θk = 2πk/10, k=0..9, `h = sin θk`, `v = cos θk`, start at top.
- Per-frame JSON: frame, theta, input{h,v}, eye_rotation_L/R [rx,ry,rz] (world frame), pupil_center_2D_L/R (projected at 40 cm), camera_matrix.

**Bundle `team_name.zip`:** `scene.blend`, `wrapper/eyes.py`, `renders/` (10 frames), `metadata.json`, `README.md`. Plus contact sheet or 1–2 min demo video.

**Eval (100), launch slides:** Execution & Efficiency 40 (Calibration 20, Automation 20) · Quality & Movement 60 (Direction pass/fail 40, Sequence & metadata 20). Direction check: L/R/U/D/Reset all **5/5 must pass**.

### Track 1 evaluation update (12 Nov, `Evaluation_for_SyntheticEyes (1).pptx`)
Organizer note: all outputs on slide 2 must be generated; brownie points for more natural, human-like simulation. Reference videos: https://youtu.be/TAZIvyAJfeM and https://youtu.be/gh6WbaYzwFc

**Rubric (100):** Texture photorealism **60** · Kinematic accuracy **20** · Code & UV portability **20**. Judged on visual photorealism, no seams, smooth kinematics, UV compatibility.

**Head model:** GNM or FLAME topology; use only the GNM or FLAME UV map.

**Required outputs**
1. **5–10 textured UV maps** including face and eye (iris) textures, wrapping directly onto the GNM head model. Distinct left and right iris maps; high-frequency skin and iris detail, realistic colours.
2. **Python script** that renders with the generated textures and accepts one of 3 inputs, renders frames and builds a video:
   - `Left`: both eyes move left, natural expression
   - `Right`: both eyes move right, natural expression
   - `Generate Motion`: a realistic eye movement expression (e.g. look left and right, roll eyes up)
3. **Rendered videos for all 3 inputs**, each ≤ 15 s, captured by the team.
4. **5–10 rendered images** with different textures.
5. **`.blend` file** that loads the head and animates an expression on the Timeline panel. More realism: animate eyelids, iris and eyebrows.

Suggested flow (slide 1): load GNM head → shape and expression keys → gaze shifts L/R/U/D → eyelid closure coordinated with gaze → UV texture transfer or baking → separate iris generation → render audit for seams. Toolkit: Blender, `bpy`, OpenCV, open 3D assets. Slide 2 still shows "Submission Due: Oct 28" (stale).

**What "GNM" is (verified 12 Nov):** Google's Generative aNthropometric Model, https://github.com/google/GNM, Apache 2.0. Head mesh with eyeballs (separate cornea), teeth, tongue; eye and neck joints; 253 identity and 383 expression components; official UDIM UV layout (skin 1001, eyes 1002–1005, teeth 1006, tongue 1007). **No skin or iris texture is shipped**, which is why textures carry 60 points.

**Reference videos:** both by Chris Jones, "Eye Piece" and "Flexpressions": extreme eye close-ups with eyelid skin sliding over the eyeball, wet highlights, lashes and constant micro-movement.

**Open conflict:** the launch spec (`eyes.move(h, v)` API, 35 cm target, 40 cm camera, 10-frame clockwise sequence, per-frame JSON) is not mentioned in the update. Plan: deliver both, since the launch spec is cheap once the rig exists.

## Track 2 — EchoGesture: Sign Language Prediction on Edge Device
**Why:** Real-time conversational signing needs low latency; bystander video must never leave device (privacy).

**Build:** fully on-device, **exocentric** (third-person: moving heads, angled signers, low light) pipeline: live smartphone camera → text/audio. Pose-invariant 3D hand features; quantized TFLite/ONNX Runtime model. Captions on display (HUD) or audio for two-way conversation.

**Budgets:** ≤20 MB INT8 model, ≤50 ms latency, zero cloud. Datasets: **How2Sign** (80+ h ASL), **WLASL** (2,000 words); starter baselines provided.

**API:** `def predict(video_path: str) -> dict` → `{"clip_id","prediction"(UPPERCASE, fixed vocab),"top5"(optional),"confidence","latency_ms"(self-reported; organizers re-measure)}`. One line per clip in `predictions.jsonl`; every clip_id must be present.

**results.csv targets:** top1_accuracy ≥70%, latency_p95 ≤50 ms, model_size ≤25 MB (conflicts with 20 MB elsewhere — target 20), accuracy_drop_robustness ≤5 pt, avg_power ≤500 mW, thermal_drift_10min ≤20%. Columns: metric, target, measured, unit, device (e.g. Galaxy S25 / Snapdragon 8 Elite), runtime (e.g. LiteRT INT8 GPU delegate), pass.

**Bundle:** `src/{requirements.txt, main.py, README.md}`, `results/{predictions.json(l), results.csv}`, quantized model + conversion script, demo video (2–3 min) or deployed app URL. **Python 3.11.** Evaluated on held-out dataset.

**Eval (100):** Execution 40 (Quantization 20, Edge latency 20) · Quality 60 (Top-1 acc 35, Robustness & HUD 25).

## Track 3 — Path Finder: Trajectory Estimation Under Sensor Degradation
**Why:** GPS-denied aircraft; jamming causes escalating IMU noise, bias drift, frame dropouts (2 s signal loss), then total IMU failure.

**Task:** 6-DoF trajectory (pos + orientation) through mission checkpoints using **only degraded IMU**; after IMU failure, **dead-reckon 5 s** future trajectory.

**Budgets:** ≤8 MB peak RAM, ≤20 ms compute per 1 s of IMU, single CPU thread, offline. Unknown gravity alignment.

**Data:** EuRoC MAV & TUM-VI; organizer degradation script. Input `imu0/data.csv` (EuRoC): `#timestamp [ns], w_RS_S_x/y/z [rad/s], a_RS_S_x/y/z [m/s², incl. gravity]`.

**Output:** `estimated_trajectory.txt`, space-separated TUM format, 8 cols `timestamp(s, float) tx ty tz qx qy qz qw`; `#` comments ok; **exactly one pose per IMU frame** (dropped/misaligned rows = heavy penalty/fail); ns→s conversion.

**Bundle:** `estimated_trajectory.txt`, `metadata.json` (optional perf), `src/{main.py|main.cpp, README.md}`. Plus 2–3 min pipeline walkthrough video.

**Eval:** auto via **evo**, ATE (RMSE) + RPE vs hidden GT. 100 pts: Execution 40 (Peak memory 20, Runtime 20) · Trajectory closeness 60 (Waypoints 30, Blind 5 s 20, Dropout 10). Tiers: T1 checkpoints · T2 blind 5 s (+20%) · T3 dropout resilience (+20%).

## Track 4 — Action-Aware Video Summarization
**Why:** Egocentric video = thousands of visual tokens; pruning to meaningful action segments helps downstream XR.

**Task:** first-person MP4 (2–10 min) → ~**15%** highlight from original footage; action localization (verb+noun) + importance ranking; drop idle/redundant.

**Run:** `run.sh <video.mp4> <out.json>`; one `<video_id>.json` per video, same schema all datasets:
```json
{"video_id":"P01_01","label":"category",
 "actions":[{"verb":"...","noun":"...","start":12.4,"end":15.9}],
 "highlights":[{"start":40.2,"end":58.0,"importance":0.93}]}
```
**Data:** EPIC-KITCHENS-100 (138 validation videos), FPVSum (49 videos). Student kit: manifest.csv, supported_classes.json, validate.py, TEAM_README.md, examples/. Validate: `python validate.py --dir outputs/` (6 schema keys, types/ranges, highlight sequence & budget).

**Bundle `TEAM_ID/`:** run.sh, code/, weights/, requirements.txt, outputs/, README.md.

**Eval (100):** Action mAP 25 (verb-noun, tIoU 0.1–0.5) · **Action coverage 40** (distinct GT action pairs captured; soft penalty over 15% budget) · Highlight F1 25 (frame-level vs top-15% human consensus) · Label accuracy 10 (video category on FPVSum).
Note: slide says "Submitted by Oct 28, 2026" — stale copy; real deadline 18 Nov.

## Doc inconsistencies to clarify with prism@samsung.com
1. Demo video: max 3 min (slide 25) vs 5 min (slides 24/27) vs track-specific 1–2 / 2–3 min.
2. Track 2 model size 20 MB vs 25 MB (CSV); `predictions.jsonl` vs `predictions.json`.
3. Track 4 "Oct 28" date.
4. Track 1/3/4 test data — public val sets are named; hidden test for T3 (GT hidden) and T2 (held-out).
5. Docker files required in README section but not in track bundles.

## Research findings (web, 8 Nov 2026)
- **No previous edition of the XR Hackathon found** — looks like first run. No winners list, no Reddit/LinkedIn reviews of it yet.
- Sister event: **Samsung PRISM GenAI Hackathon** (2025 = 2nd ed., 2026 = "3.0", deadline ~30 Sep 2026). 2025 format: ideation + implementation rounds, judged on innovation, technical feasibility, UX; ₹1.5 L + internships for top 3. Participant repos tag releases `PRISM_GENAI_HACKATHON_Y2026` and quote hard latency targets (p95) — same "measured numbers vs budget" style as this XR event. No official winners list published.
- PRISM itself: SRI-B industry-academia program (since 2020), "worklets" = 4–6 month projects with SRI-B mentor, patent-oriented. One Glassdoor review: good mentors/projects, vague deliverables.
- Samsung XR context: Galaxy XR headset (Android XR) uses eye tracking + hand tracking + 6DoF inside-out tracking; Samsung patents on eye-tracking input. All 4 tracks map to real headset/glasses pipelines (gaze data, accessibility HUD, tracking failover, egocentric memory/summaries).
- Feasibility benchmarks:
  - T2: pose-only WLASL2000 SOTA ≈ 47% top-1; WLASL100 ≈ 78–81%. The ≥70% target only realistic if hidden vocab is small (~100 words).
  - T3: AirIO/AirIMU (RA-L 2025) — learned IMU-only odometry for drones, body-frame features, +66.7% accuracy over global-frame; evaluated on EuRoC. Small nets + EKF fit 8 MB budget.
  - T4: EPIC-KITCHENS-100 action detection SOTA ≈ 26–32 action mAP (big InternVideo2 features). FPVSum = 98 videos, 14 categories, frame-level importance (ECCV 2018, github.com/azuxmioy/fpvsum).
  - T1: UnityEyes (Wood et al. 2016) is the canonical synthetic-gaze reference; MakeHuman plugin needs old Blender (~2.8), MPFB is the modern route.

## Track choice (final, 12 Nov)
The college PoC limited the team to Track 1 or Track 4. **Chosen: Track 1 Synthetic Eyes.** Track 4 needs ~184 GB of EPIC-KITCHENS video (more than the free disk), GPU-heavy models, and a hidden scored subset with re-runs. Track 1 runs in Blender on a laptop with concrete deliverables; risk is that 60% is judged visually, so realism and polish decide.

## Judging pattern (read from slides)
- Every track = **40% Execution/Efficiency + 60% Quality**, auto-evaluated against strict formats → format compliance is table stakes.
- Stage 1 (top-15 cut) mostly automated metrics + deck/video. Stage 2 = live jury of SRI-B XR Perception researchers.
- Samsung cares: on-device/edge budgets (RAM, latency, INT8, power, thermal), privacy, reproducibility, measured numbers on real Galaxy hardware.
