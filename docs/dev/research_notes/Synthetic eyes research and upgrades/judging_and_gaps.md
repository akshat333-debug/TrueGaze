# Samsung PRISM XR Hackathon judging, and how TrueGaze measures up (18 Nov 2026)

## What is public about the Samsung PRISM XR Hackathon 2026, Track 1, and earlier PRISM events or winners?

### Takeaway
Nothing public describes this XR hackathon, its judges or any past winner. The organizer files in this repo are the only authoritative source. PRISM's own public identity is an R&D and worklet program (mentored projects, patents), so the jury will likely be SRI-B researchers judging like reviewers, not like a startup-pitch panel.

### Cited Findings
- Web searches for "Samsung PRISM XR Hackathon 2026" return only unrelated XR events (MIT Reality Hack on Galaxy XR, Google's Android XR hackathon). No page, post or winners list for the PRISM XR event — [search results incl. Qualcomm MIT Hack recap](https://www.qualcomm.com/developer/blog/2026/04/mit-hack-recap-2026), [Unity on Google's XR hackathon](https://unity.com/blog/inside-google-s-first-xr-hackathon)
- The only public "Samsung Prism Hackathon" artifact found is a 10-slide deck by Team Pythonic, 6 Apr 2024 (smart-home LLM assistant). It covers aim, features, tech stack, future work and team. No result or award is stated, so it is not evidence of what wins — [SpeakerDeck](https://speakerdeck.com/metal0bird/samsung-prism-hackathon-team-pythonic)
- PRISM ("Preparing and Inspiring Student Minds") is SRI-B's industry-academia program. Student teams and a professor work on live R&D projects ("worklets") with an SRI-B mentor. Students are selected by an SRI-B test — [Samsung Newsroom India](https://news.samsung.com/in/samsung-prism-new-industry-academia-program-in-india-to-collaborate-with-engineering-students-on-ai-iot-5g-launched)
- Samsung's newsroom frames PRISM's success as students filing patents, with the program growing to 70 engineering colleges — [Samsung Newsroom India (headline)](https://news.samsung.com/in/samsung-prism-industry-academia-program-successfully-drives-students-to-file-patents-expanding-to-70-engineering-colleges-in-india) (page timed out; headline only)
- Public worklet posts on LinkedIn are computer vision and video research projects (OCR, food detection, video highlight detection), described in terms of skills and research outputs — [Srinidhi R](https://www.linkedin.com/in/srinidhi-r-b1958b287/), [Harish Parthasarathy](https://www.linkedin.com/in/harish-parthasarathy/)
- Organizer files (local, primary): the 12 Nov Track 1 rubric is texture photorealism 60, kinematic accuracy 20, code and UV portability 20. Judges look for "visual photorealism, no seams, smooth kinematics, UV compatibility". Brownie points go to more natural, human-like motion. Stages: top-12 named 29 Nov, live final demo 9 Dec, results 12 Dec. Breaking the guidelines means direct disqualification — `docs/hackathondetails.md`, `docs/organizer/Evaluation_for_SyntheticEyes.pptx`
- The launch rubric (5 Nov, not withdrawn) also scored Calibration 20, Automation 20, Direction pass/fail 40 (all 5 of 5 must pass), Sequence and metadata 20. It said "exact folder layout matters; evaluators run code directly" — `docs/hackathondetails.md`

### Inferences
- With no past winners to copy, the two rubrics are the whole target. Under the 12 Nov rubric, 60 % depends on how the renders look, so the first frames of the demo video and README carry the most weight.
- The final jury is SRI-B's XR Perception group. A gaze-dataset team will ask whether the labels are correct and whether the data could train a gaze estimator. Claims of metric correctness are worth more to them than polish. PRISM's research and patent culture points the same way.
- The launch spec may still be scored automatically ("evaluators run code directly"). Its packaging has to match exactly.

### Gaps
- No public information on who judges, how stage 1 is scored (automatic or manual), or whether the launch rubric still applies alongside the 12 Nov one. Only prism@samsung.com can answer that.
- No earlier XR edition, so no past winners exist. The 2025 PRISM GenAI hackathon published no winners list (searched, none found).

## What do judges of technical, R&D-style hackathons value (video, README, reproducibility, metrics, limitations)?

### Takeaway
The common advice: put what judges need at the top, tailor the write-up to the published criteria, keep the video within the limit and show the thing actually working, and make sure every required item is submitted. Judges may spend only about five minutes per project.

### Cited Findings
- Judges may spend about five minutes per project. Put what they need at the top, keep the template headings, tailor the write-up to the criteria, and check that every required item is in. Missing items may mean judges never see the project — [Jacklyn Biggin, DEV](https://dev.to/jacklynbiggin/how-to-make-your-devpost-submissions-not-suck-37i0)
- Video advice across event guides: respect the time limit (one guide calls a 15-minute video for a 2-minute slot "crazy"), use fewer cuts so the result looks authentic, lead with the purpose, give a clear 30-second pitch, and start editing early — [HackHCC guide](https://hackhcc.gitbook.io/hackhcc-docs/other-resources/submission-and-judging-guide), [civiso Notion](https://civiso.notion.site/What-do-I-include-in-my-Devpost-Submission-Demo-c2cb13c36bae44cb8847d7f1ad403e8a), [RevenueCat Shipaton](https://www.revenuecat.com/blog/engineering/how-to-win-shipaton-part-4-pitching-your-app)
- Some events score "clarity of video presentation" as its own criterion (1–10) — summarized from the search above (individual events)
- In the synthetic-gaze field, the canonical value proof is downstream use. UnityEyes rendered 1M eye images and reported competitive gaze estimation on an in-the-wild benchmark. Later work trains only on UnityEyes and tests on real images (MPIIGaze) and names the synthetic-to-real domain gap as the central problem — [UnityEyes project](https://www.cl.cam.ac.uk/research/rainbow/projects/unityeyes/), [Wood et al. ETRA 2016](https://perceptualui.org/publications/wood16_etra/), [Lahiri et al. 2018](https://ar5iv.labs.arxiv.org/html/1810.07926), [Wood et al. 2018](https://ar5iv.labs.arxiv.org/html/1805.04771)
- Blender ground-truth precedent: Świrski and Dodgson rendered eyes in Blender to get sub-pixel pupil contours and gaze vectors as ground truth for evaluating eye trackers — [Świrski & Dodgson 2014](https://www.cl.cam.ac.uk/research/rainbow/projects/eyerender/files/Swirski,%20Dodgson%20-%202014%20-%20Rendering%20synthetic%20ground%20truth%20images%20for%20eye%20tracker%20evaluation.pdf). LEyes reports that models trained on its synthetic eye images match or beat models trained on real data — [LEyes](https://arxiv.org/pdf/2309.06129v2)

### Inferences
- The README already follows best practice: a hero GIF up top, a numbers table with a command next to each number, required-outputs mapping and limitations. Its weak spots are the missing demo link and the private repo.
- The demo video (85 s, silent, captions) is within every stated limit (3 min, 1–2 min). A voice-over or a stronger opening is optional polish. A missing link is a hard fail.
- The domain-standard evidence that a synthetic eye pipeline works is (a) labels verified against the image and (b) a downstream gaze model. (b) cannot be done properly by 22 Nov. (a) can.

### Gaps
- The MLH judging-criteria page has moved (404 at guide.mlh.com). The brainbound judge guide returned 403. No MLH wording is cited.
- No source gives a standard pupil reprojection-error threshold for synthetic eye data.

## How does each rubric item map to our evidence, and what are the gaps?

### Takeaway
Compliance and engineering evidence are strong. The scored weakness is photorealism: the team's own audit puts it at about 40 of 60. Three items are submission blockers, not quality items: the repo is private, the reference video is in git history, and the demo link is missing. Two credibility gaps are cheap to close: the direction and calibration check is circular, and the launch-spec zip does not have the layout the brief asks for.

### Cited Findings (all local, checked 18 Nov)
| Rubric item | Points | Our evidence | Gap |
|---|---|---|---|
| Texture photorealism | 60 | 8 sets, 4K skin plus 2K eye maps, seam audit (step of 4 of 255 or less), stills and hero video | Self-audit estimate 40/60 (`docs/SELF_AUDIT.md`): iris reads as painted, skin shows canvas noise instead of pores, lashes look like wires, hero eye white is a flat slab, crescent on the hero iris, pink outer eye white in Left/Right |
| Kinematic accuracy | 20 | `tools/evaluate_motion.py` 15 of 15 in published ranges; saccade main sequence; blinks; vergence | Head sway not watched at speed; no torsion, no upward roll under a closed lid, no pupil light reaction |
| Code and UV portability | 20 | `apply_textures.py` on stock and random GNM identities; `reproduce.sh` with SHA-pinned downloads; 16 tests; Dockerfile | Docker videos run out of memory; never run on Linux; lashes do not port (they are geometry) |
| Launch: Direction 5/5 | 40 | `metadata.json` direction_check all True | **Circular:** `wrapper/eyes.py:113` judges direction from the projected pupil coordinates it computed itself (`eyes.py:92`), not from the rendered pixels |
| Launch: Calibration | 20 | Intrinsics and camera_to_world per frame; 35 cm target, 40 cm camera | No independent check that `pupil_center_2D` matches the pupil in the PNG |
| Launch: Sequence and metadata | 20 | 10 frames, 1024², clockwise from top, per-frame JSON with all required keys | Bundle layout: the README's `zip -r … outputs/scene.blend wrapper outputs/launch_spec README.md` puts files under `outputs/…`. The brief lists `scene.blend`, `wrapper/eyes.py`, `renders/`, `metadata.json`, `README.md` at the zip root |
| Required: 5–10 renders | — | `outputs/renders/` has **33** PNGs (24 sets, 6 wire/clay, 3 portability) | Over-delivery. The README says 24, the folder has 33, and the brief asks for 5–10. No folder holds exactly the required set |
| Submission | DQ risk | Deck follows the template's 14 slides; README; Dockerfile | Repo is **PRIVATE** (`gh repo view`). **`.git` is 1.5 GB** and `Eye Piece - Chris Jones (1080p, h264).mp4` is still tracked (copyright, plus clone size for evaluators). Demo `outputs/demo.mp4` (85 s) not uploaded; no link in README or deck. Deck opened only in LibreOffice |

- Textures ship as JPG (`textures/01/color.1001.jpg` etc.), while the brief stresses high-frequency detail — local listing. Minor, but a reviewer might ask.

### Inferences — ranked improvements (impact vs hours, ~3 days left; team target 21 Nov)
| # | Change | Why | Hours | Re-render? |
|---|---|---|---|---|
| 1 | **Submission blockers:** purge the reference video from history (git filter-repo), check a clean clone's size, make the repo public, upload the demo and put the link in README and deck, open the deck in PowerPoint, submit the form | Disqualification and copyright risk outweigh any look point | 2–3 | No |
| 2 | **Exact launch-spec zip:** a script that builds `VITVellore_ZeroDrift.zip` with `scene.blend`, `wrapper/eyes.py`, `renders/` (10 PNGs), `metadata.json`, `README.md` at the root. Commit it or attach it to a GitHub release, and test that `eyes.py` runs from the unzipped folder | "Non-standard layout = fail"; evaluators run code directly | 1 | No |
| 3 | **Independent label check:** detect the pupil in each of the 10 launch-spec PNGs (OpenCV dark-blob or ellipse fit), report pixel error against `pupil_center_2D_L/R`, and base the direction check on the detected pixels. Add one row to the README table | Removes the circular check; shows "rigid metric calibration" in the domain's own terms (Świrski and Dodgson precedent); exactly what an XR Perception jury probes | 2–3 | No |
| 4 | **Required-renders clarity:** README row "the 8 required renders = `outputs/renders/0N_front.png`" (or a `required/` folder of 8), the rest marked extras; fix "24" vs 33 | A five-minute judge has to see 5–10 at once | 0.5 | No |
| 5 | Hero view fix (flat far-side eye white, iris crescent): self-audit item 1 | The only look fix that touches the demo's first frame; hero video only | 1–2 + 2.3 render | Hero only |
| 6 | Demo video: open on the hero clip, then Left/Right/Generate Motion side by side; one slide of numbers; show `reproduce.sh` running; voice-over optional; stay ≤ 3 min | Clarity of the video is often scored; within all stated limits already | 2–3 | No |
| 7 | Live-demo prep for 9 Dec (if top 12): `eyes.move(h,v)` driven live in Blender (EEVEE viewport), the label-check script run live | Stage 2 is a live jury; this can be done after 22 Nov | after submission | No |
| 8 | Pink outer eye white in Left/Right; iris fibres and blocks on 05/07/08 | Photorealism, but the self-audit puts a fourth batch at only 2–3 points and it needs about 9.5 h of renders | 3 + 9.5 render | All set 01 |
| 9 | Per-frame JSON (gaze vector, pupil 2D, lid aperture) beside each required video | Makes the videos usable as a dataset; low score impact unless asked | 2 | Re-run labels only, if derivable from the motion script without rendering |

- **Reword-or-rebuild fork (needs a team decision):** the direction check can be (a) reworded in the README as "computed from projected geometry", about 5 min, or (b) rebuilt as an image-based check (item 3), about 2–3 h. Recommendation: (b). It is the claim a perception jury is most likely to test, and the current version shares its generating function with the thing it measures.
- A downstream "train a gaze estimator on our renders, test on real MPIIGaze" experiment is the gold standard in this field (UnityEyes lineage). It cannot be done properly by 22 Nov with 10 frames and a few videos, so it should not be claimed. At most, list it as future work.
- Photorealism carries the most points, but each further batch has bought less (33 → 38 → 40 for about 27 h of rendering, per the self-audit). Items 1–4 cost under a day of non-render time and protect against zero-score outcomes. Do them before any further look batch.

### Gaps
- The look scores are the team's own estimate (one reviewer, the same one who made the changes). No external person has viewed the renders against the reference videos.
- Not checked whether `wrapper/eyes.py` runs from an unzipped bundle outside the repo (it may import `truegaze/`). Test this as part of item 2.
- Not checked whether the organizers' form accepts a release asset or only the repo link.
