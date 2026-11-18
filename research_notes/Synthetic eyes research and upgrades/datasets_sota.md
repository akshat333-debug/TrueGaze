# Synthetic eye and face data generation: state of the art (notes as of 18 Nov 2026)

Scope: major synthetic eye/face pipelines and datasets for gaze estimation / eye tracking / XR, how they are evaluated, open-source tools, and what a 3-day Blender + GNM-head project can borrow. About 16 tool calls; several primary PDFs (CVF GazeGene PDF, UnityEyes Stuttgart page) were blocked or unreachable, and gaps below record what is missing.

## Major pipelines and datasets: pipeline, eye model, randomization, scale, evaluation

### Takeaway
The field has two families. One is near-eye IR renders for headset eye tracking (Swirski EyeRender 2014, NVGaze 2019, RIT-Eyes 2020, LEyes 2023/25, GazePrior 2026). The other is RGB eye-region or full-face renders for remote gaze and landmarks (SynthesEyes 2015, UnityEyes 2016, Microsoft Face Synthetics 2021, GazeGene CVPR 2025). The pipelines that report strong real-world results combine five things: anatomically grounded eye optics (refractive cornea, eyelids that follow gaze), many identities and HDRI environments, heavy augmentation, exact per-pixel/3D labels, and an evaluation on real data held out from anything that was tuned.

### Cited Findings
**Swirski & Dodgson EyeRender (2014, Cambridge): the closest prior art to our setup (Blender + Python).**
- The eye and surrounding face were modelled and rendered in Blender, with photorealistic lighting, reflections and refractions. The project ships a Blender model plus a Python module on GitHub. — [EyeRender project](https://www.cl.cam.ac.uk/research/rainbow/projects/eyerender/); [poster](https://www.cl.cam.ac.uk/research/rainbow/projects/eyerender/files/Swirski,%20Dodgson%20-%202014%20-%20Poster%20-%20Rendering%20ground%20truth%20eye%20images.pdf)
- Exposed parameters: pupil size, cornea refractive index, eye radius, eye position and orientation, eyelid position. To get the true pupil outline as the camera sees it through the cornea, the module ray-casts each pupil-border point through the cornea with a 1D root finder. — [same sources](https://www.cl.cam.ac.uk/research/rainbow/projects/eyerender/)

**SynthesEyes (Wood et al., ICCV 2015)**
- Dynamic eye-region models built from head-scan geometry, randomly posed across head pose, gaze and lighting to produce "perfectly labelled" photorealistic close-up eye images. The authors used the model's controllability to test how much realistic illumination and shape variation matter. They report beating state-of-the-art methods on eye-shape registration and on cross-dataset appearance-based gaze estimation in the wild. — [arXiv 1505.05916](https://arxiv.org/abs/1505.05916)

**UnityEyes (Wood et al., ETRA 2016)**
- A generative 3D eye-region model built from high-resolution face scans, with real-time approximations of eyeball materials and structures. Eyelids are animated by anatomically inspired procedural geometry. 1,000,000 eye images were rendered, and a nearest-neighbour gaze estimator reached competitive in-the-wild results. The tool is a free download (Windows; Linux untested) that outputs labelled images with gaze and landmark data. — [UnityEyes project](https://www.cl.cam.ac.uk/research/rainbow/projects/unityeyes/); [tutorial](https://www.cl.cam.ac.uk/research/rainbow/projects/unityeyes/tutorial.html)
- **UnityEyes 2** (Smith, Muthumanickam, Feng, Ding, Hauser): "open source robust synthetic eye generation for camera-based eye tracking with machine learning", ETRA 2025, Tokyo, 26–29 May 2025. — [researchr listing](https://researchr.org/publication/SmithMFDH25)

**SimGAN (Shrivastava et al., Apple, CVPR 2017): learned refinement of UnityEyes images**
- Adversarial refinement of synthetic images using unlabelled real images. The paper claims state-of-the-art MPIIGaze results without any labelled real data, and assessed realism with a user study. — [arXiv 1612.07828](https://arxiv.org/abs/1612.07828)
- The ICCV 2019 OpenEDS Synthetic Eye Generation Challenge was won by an image-refinement method. — [search summary of OpenEDS papers](https://arxiv.org/pdf/2005.03876); related: [Content-Consistent Generation of Realistic Eyes with Style](https://ar5iv.labs.arxiv.org/html/1911.03346)

**NVGaze (Kim et al., ACM CHI 2019, NVIDIA)**
- About 2M synthetic infrared near-eye images at 1280×960, from anatomically informed eye and face models that extend SynthesEyes. Randomized: face shape, gaze, pupil, iris, skin tone, external lighting. A companion real set has 2.5M images at 640×480 from 35 subjects in a matching on-axis setup. — [NVGaze project page](https://sites.google.com/nvidia.com/nvgaze); [NVIDIA Research](https://research.nvidia.com/publication/2019-05_nvgaze-anatomically-informed-dataset-low-latency-near-eye-gaze-estimation); [paper PDF](https://users.aalto.fi/~laines9/publications/kim2019sigchi_paper.pdf)
- Result: 2.06° (±0.44°) accuracy over a 30×40° field of view on real subjects held out from training, with sub-millisecond inference. The page links the dataset (via a request form) and code. — [NVGaze project page](https://sites.google.com/nvidia.com/nvgaze)

**RIT-Eyes (Nair et al., 2020): Blender near-eye renderer, the best-documented eye model**
- Built in Blender 2.8 and path-traced in Cycles (200 rays/pixel for the S-NVGaze set). — [RIT-Eyes paper](https://ar5iv.labs.arxiv.org/html/2006.03642)
- Eye model: a modified reduced optical eye with corneal radius 7.8 mm and refractive index 1.3375. It has an aspherical cornea, a tear film, a deformable iris with a 1–4 mm pupil aperture, eyelids that conform to the cornea and close with vertical gaze, a retroreflective retina (for bright-pupil effects) and a caruncle. Iris textures are IR photographs plus 2 artificial ones; there is 1 sclera texture. — [same](https://ar5iv.labs.arxiv.org/html/2006.03642)
- Randomization: 24 head models (18 train / 6 test, split by identity), 25 HDR environment maps with random rotation and intensity, eyeglasses in 50% of images, eye pose within ±30°, camera jitter ±5 mm (±1 mm for the general set), and 7 augmentations each applied with probability 14%. — [same](https://ar5iv.labs.arxiv.org/html/2006.03642)
- Labels: per-pixel pupil/iris/sclera masks (with and without skin occlusion), 2D and 3D feature centres in camera coordinates, eye pose in degrees, camera intrinsics. Scale: 51,600 images per set, 154,800 in total. — [same](https://ar5iv.labs.arxiv.org/html/2006.03642)
- Evaluation: segmentation mIoU with SegNet and RITnet. Same-domain mIoU is about 95–96. Sim-to-real drops: RITnet trained on S-OpenEDS scores 73.94 on real OpenEDS, and trained on S-NVGaze scores 73.38 on real NVGaze. Sclera is the weakest class. Stated limits: glasses reflect but do not refract, no makeup, little sclera variety. — [same](https://ar5iv.labs.arxiv.org/html/2006.03642)

**Microsoft "Fake It Till You Make It" / Face Synthetics (Wood et al., ICCV 2021)**
- 100,000 images at 512×512, rendered with Cycles. Rendering took 48 h on 150 NVIDIA M60 GPUs (about $7,200, roughly 4.3 GPU-min per image). — [arXiv HTML](https://arxiv.org/html/2109.15102v2)
- Randomized: identity (a blendshape model built from 511 scans), expression (a library of 27,000 expression parameters), 200 scanned albedo/displacement texture sets, 512 hairstyles, 162 eyebrows, 142 beards, 42 eyelash sets, 30 outfits, 36 headwear, 7 facewear, 11 eyewear, 448 HDRIs, and random camera position, focal length and depth of field. Gaze is random and eyelids are posed procedurally (two eye joints). The paper does not detail the eyeball optics. — [same](https://arxiv.org/html/2109.15102v2)
- Labels: 68 2D landmarks (679 dense landmarks in the follow-up), per-pixel face-parsing classes, plus albedo, normals, depth, mask, UVs and vertices. — [same](https://arxiv.org/html/2109.15102v2)
- Results from synthetic data alone vs the same network trained on real data: 300W NME common 3.09 vs 3.37, challenging 4.86 vs 5.77. Helen F1 92.0 vs 91.6; LaPa F1 90.1 vs 90.9. Ablations: removing augmentation raises 300W NME to 4.25, and removing label adaptation raises it to 5.61. **Label adaptation** is a small network that maps synthetic-convention predictions onto the human-annotation convention, and it never sees real images. — [same](https://arxiv.org/html/2109.15102v2)
- Dataset is for non-commercial research only (LICENSE.txt); the official repo hosts a 100-image sample, and a mirror lists the full 100k (32 GB). Paper text is CC BY-NC-SA 4.0. Related Microsoft releases: DigiFace-1M (face recognition). — [microsoft/FaceSynthetics](https://github.com/microsoft/FaceSynthetics); [project page](https://microsoft.github.io/FaceSynthetics); [arXiv 2109.15102](https://arxiv.org/abs/2109.15102); [DigiFace-1M](https://microsoft.github.io/DigiFace1M)

**OpenEDS (Meta/Facebook Reality Labs), the main real XR benchmarks**
- OpenEDS2019: VR HMD with two synchronized eye cameras at 200 Hz under controlled illumination. The segmentation baseline (pupil/iris/sclera/background) reached 98.3% mIoU. OpenEDS2019 has 152 participants and 12,759 images. — [OpenEDS2020 paper](https://arxiv.org/pdf/2005.03876); [LEyes paper](https://arxiv.org/html/2309.06129v4)
- OpenEDS2020: a gaze-prediction set (550,400 images, 66,560 sequences, with gaze vectors) and a segmentation set (200 sequences, about 29,500 images, 5% labelled); 80 participants. Baselines: 5.37° error predicting 1–5 frames ahead, and 84.1% segmentation mIoU. — [arXiv 2005.03876](https://arxiv.org/pdf/2005.03876)

**LEyes (Byrne, Nieho et al., arXiv 2309.06129, v4 dated 30 Apr 2025): the "minimal realism" counterpoint**
- Images are only 2D Gaussians: a dark pupil and bright corneal reflections (CRs), plus iris/background luminance and noise, quantized to 8-bit. No photorealism. — [arXiv HTML](https://arxiv.org/html/2309.06129v4)
- Results: pupil localization within 2 px on OpenEDS2019 was 75.8%, against EllSeg 71.8%, PuRe 65.6%, DeepVOG 60.9% and Pistol 55.4%. Mean CR error was 1.59 px. On co-recorded data its precision beat the EyeLink 1000 Plus with no loss of accuracy. Code: [dcnieho/Byrneetal_LEyes](https://github.com/dcnieho/Byrneetal_LEyes); no code licence was stated on the paper page. — [same](https://arxiv.org/html/2309.06129v4)

**GazeGene (Bao, Wang, Lu, CVPR 2025)**
- Built from MetaHuman characters in Unreal Engine, animated with Control Rig. Meshes were exported to Blender to compute the eyeball, pupil and iris geometry. — [Lacuna summary](https://lacuna.tiptreesystems.com/work/gazegene-large-scale-synthetic-gaze-dataset-with-3d-eyeball-annotations/wrk_80ab6ce68e4a5bcfbe2340b03874b349) (secondary source); [CVPR open access](https://openaccess.thecvf.com/content/CVPR2025/html/Bao_GazeGene_Large-scale_Synthetic_Gaze_Dataset_with_3D_Eyeball_Annotations_CVPR_2025_paper.html)
- Scale: 56 subjects × 9 cameras × 2,000 frames, about 1,008,000 face crops. Suggested split: subjects 1–46 train, 47–56 test. — [HF dataset card](https://huggingface.co/datasets/vigil1917/GazeGene)
- Per-frame labels: unit gaze vector in camera coordinates, left/right visual **and** optic axes, 3D gaze target and gaze depth, head rotation and translation, 2D/3D eyeball centres, 2D/3D pupil centres, 100-point 2D/3D iris contours, and cropped intrinsics. Per-subject labels: kappa angle; eyeball, iris and cornea radii; pupil-size parameter. Units are cm. Licence is CC BY-NC-SA 4.0 plus extra terms. — [HF dataset card](https://huggingface.co/datasets/vigil1917/GazeGene)
- Motivation: existing real datasets carry annotation errors and give only one gaze vector per sample. The paper claims quality and generalization comparable to real datasets. — [CVPR poster](https://cvpr.thecvf.com/virtual/2025/poster/33261); [HF card](https://huggingface.co/datasets/vigil1917/GazeGene)

**2026 work**
- **GazePrior** (Dumery, Colmenares, Fix, Fua, Behrooz, Kundu; arXiv 2605.22359, 21 May 2026). A learned 3D prior over eye identity, gaze and lighting is used to reconstruct annotated data captured on older AR/VR devices, then re-render it through a new device's cameras. The aim is zero-shot eye tracking on new hardware; it claims to beat earlier zero-shot methods (no numbers on the abstract page). — [arXiv](https://arxiv.org/abs/2605.22359); [project](https://corentindumery.github.io/projects/gazeprior.html)
- **Reconstructing Realistic and Relightable Eyes** (Khademi et al., WACV 2026). — [CVF PDF](https://openaccess.thecvf.com/content/WACV2026/papers/Khademi_Reconstructing_Realistic_and_Relightable_Eyes_WACV_2026_paper.pdf) (not read; title only)
- **MPSGaze360** (CVPR 2026, within the GazeOnce360 paper): a multi-person fisheye gaze dataset rendered with UE5 + MetaHuman. — [CVF PDF](https://openaccess.thecvf.com/content/CVPR2026/papers/Cai_GazeOnce360_Fisheye-Based_360deg_Multi-Person_Gaze_Estimation_with_Global-Local_Feature_Fusion_CVPR_2026_paper.pdf)

### Inferences
- The direction since 2025 is from "eye crop + one gaze vector" toward **full 3D eye-structure labels**: optic vs visual axis, kappa, iris contour, eyeball centre and radius (GazeGene), and toward re-rendering existing data for new devices (GazePrior). A procedural Blender rig that already knows its eyeball centre, cornea and iris geometry can export GazeGene-style labels at almost no cost. This lines us up with the 2025 CVPR state of the art at label level, though not at image-quality level.
- RIT-Eyes and EyeRender show that a scripted Blender/Cycles pipeline with a refractive cornea is a recognized, published way to do this. Our approach (procedural eyes on a GNM head in Blender) sits in this lineage and can cite it.
- LEyes is a useful honesty check: for near-eye pupil/CR tracking, task-relevant features matter more than photorealism. Realism claims should be tied to a downstream metric, not to looks.

### Gaps
- Exact UnityEyes / SimGAN MPIIGaze error numbers: the Stuttgart perceptualui page was unreachable and the abstract pages give no numbers. From memory (unverified, do not cite): UnityEyes kNN ~9.9° on MPIIGaze, SimGAN-refined ~7.8°. Check the PDFs before using them.
- GazeGene quantitative cross-dataset numbers: the CVF PDF returned 403 and the HF card shows them only as figures.
- UnityEyes 2 (ETRA 2025): no abstract, repo or licence found. Search the ETRA 2025 proceedings / Hauser lab GitHub.
- NVGaze renderer details and code licence were not retrieved.
- No reliable source found on Apple Vision Pro or Samsung/Google (Android XR) internal synthetic-eye pipelines; Meta's public output is OpenEDS plus GazePrior.

## Metrics papers use to show synthetic realism or usefulness

### Takeaway
Credible papers show usefulness through a **downstream task on real held-out data**: gaze angular error in degrees, landmark NME, segmentation mIoU/F1, or pupil localization within N px. They compare training on synthetic only, real only, and mixed, often with ablations that remove one realism component. Perceptual realism metrics (user studies, FID) are secondary and rarer in this field.

### Cited Findings
- Gaze angular error in degrees on held-out real subjects: NVGaze reports 2.06° ± 0.44°. — [NVGaze](https://sites.google.com/nvidia.com/nvgaze). OpenEDS2020 reports 5.37° for future-gaze prediction. — [arXiv 2005.03876](https://arxiv.org/pdf/2005.03876)
- Segmentation mIoU per class (pupil/iris/sclera), synthetic→real: RIT-Eyes gives about 74 on real data vs about 95 same-domain. — [RIT-Eyes](https://ar5iv.labs.arxiv.org/html/2006.03642). OpenEDS baselines: 98.3 (2019), 84.1 (2020). — [arXiv 2005.03876](https://arxiv.org/pdf/2005.03876)
- Landmark NME (300W) and face-parsing F1 (Helen, LaPa), synthetic vs real-trained, plus ablations (no augmentation, no label adaptation). — [Fake It Till You Make It](https://arxiv.org/html/2109.15102v2)
- Pupil detection rate within 2 px, CR error in px, and precision (RMS-S2S, STD) against a reference tracker. — [LEyes](https://arxiv.org/html/2309.06129v4)
- Human user study / visual Turing test for realism. — [SimGAN](https://arxiv.org/abs/1612.07828)
- "Controllability" ablations: render with and without realistic illumination or shape variation and measure the downstream change. — [SynthesEyes](https://arxiv.org/abs/1505.05916)

### Inferences
- A hackathon-scale, defensible usefulness check with no network training: run an off-the-shelf pupil/iris detector or segmenter (e.g. a RITnet- or EllSeg-type model, or MediaPipe Face Mesh iris landmarks) on our renders and report error against our exact ground truth (pupil centre px error, iris-landmark NME). This is a frozen scorer, so it is not tuned against our generator, and it measures "does a real-trained model see our eyes as eyes" (a reverse sim-to-real test).
- FID against a real eye set (e.g. an OpenEDS or UnityEyes sample) is cheap to compute, but it is not a standard result in this subfield. If used, frame it only as a distribution-distance signal, alongside a texture-variety measure.

### Gaps
- I found no eye-specific paper that uses FID/KID as its headline realism metric. This may exist in GAN eye-synthesis work (OpenEDS 2019 challenge entries) but was not verified.

## Open-source repos / tools for synthetic eye generation

### Takeaway
There are few maintained open Blender eye generators. EyeRender (Cambridge, Blender + Python) and RIT-Eyes (Blender 2.8; images and models released) are the closest; UnityEyes is a free binary; LEyes ships code; the large datasets (Face Synthetics, GazeGene) are non-commercial. A public Apache-2.0 procedural Blender eye pipeline on an open head (GNM) appears to fill a real gap.

### Cited Findings
- **EyeRender**: Blender model plus Python module on GitHub (pupil size, cornea refractive index, eye radius, eyelid position). The exact repo URL and licence were not retrieved. — [project](https://www.cl.cam.ac.uk/research/rainbow/projects/eyerender/)
- **RIT-Eyes**: Blender 2.8 / Cycles. The paper says rendered images and trained models are public; code licence not stated in what I read. A follow-up, "Temporal RIT-Eyes", is a Blender pipeline driven by real eye videos for natural gaze dynamics. — [RIT-Eyes](https://ar5iv.labs.arxiv.org/html/2006.03642); [search result for Temporal RIT-Eyes](https://unpaywall.org/10.1109%2FTVCG.2022.3203100)
- **UnityEyes**: free Windows/Linux binary (about 226 MB), outputs images plus gaze/landmark labels; © University of Cambridge, licence not stated on the page. — [project](https://www.cl.cam.ac.uk/research/rainbow/projects/unityeyes/)
- **LEyes**: [github.com/dcnieho/Byrneetal_LEyes](https://github.com/dcnieho/Byrneetal_LEyes) (code, models, evaluation). — [arXiv](https://arxiv.org/html/2309.06129v4)
- **microsoft/FaceSynthetics**: dataset plus sample, non-commercial research licence. — [GitHub](https://github.com/microsoft/FaceSynthetics)
- **iperov/SSHG**: Simple Synthetic Head Generator in Blender; outputs landmark labels, no gaze labels. — [GitHub](https://github.com/iperov/sshg)
- **gkaModelEye**: MATLAB ray-traced model eye (refraction through cornea, useful for checking pupil appearance). — [GitHub](https://www.github.com/gkaguirrelab/gkaModelEye)
- **GazeGene**: data on Hugging Face (gated, CC BY-NC-SA 4.0); no code repo found. — [HF](https://huggingface.co/datasets/vigil1917/GazeGene); [project](https://phi-ai.buaa.edu.cn/project/GazeGene/index.htm)
- Commercial Blender eye shaders exist (e.g. "Real Eye Customizable Shaders"); these are not redistributable, which matters for a public repo. — [Superhive docs](https://superhivemarket.com/products/real-eye-customizable-shaders/docs)

### Inferences
- Do not vendor any of these assets. EyeRender and RIT-Eyes geometry and licences are unverified, and FaceSynthetics and GazeGene are NC. Cite them only, and re-implement constants from the papers (corneal radius 7.8 mm, n = 1.3375, pupil 1–4 mm). Physical constants are facts, not copyrighted assets.

### Gaps
- GitHub star counts were not collected (search results did not include them, and the call budget ran out). If the deck needs them, check with `gh api repos/<owner>/<repo>`.
- UnityEyes 2 open-source repo URL not found.

## Ideas cheap to adopt in about 3 days (Blender, scripted, GNM head)

### Takeaway
The highest-value, lowest-cost borrowings are, in order: (1) per-frame GazeGene/RIT-Eyes-style **label export** computed from the rig, which needs no new rendering cost; (2) **segmentation masks** via Blender object/material index passes; (3) a seeded **domain-randomization manifest** (HDRI, iris texture, pupil size, gaze, camera jitter) with an identity-disjoint train/test split; (4) a cheap **near-IR render mode**; (5) a frozen off-the-shelf detector as a **realism/usefulness check**. A refractive cornea is worth checking only if it is not already in place.

### Cited Findings
- Label set worth matching, per frame: unit gaze vector (camera coordinates), optic and visual axes per eye, 3D gaze target, eyeball centre, pupil centre (2D + 3D), iris contour (GazeGene uses 100 points), head pose, intrinsics; per subject: kappa and eyeball/iris/cornea radii. — [GazeGene HF card](https://huggingface.co/datasets/vigil1917/GazeGene)
- Mask set worth matching: pupil / iris / sclera / skin, with and without eyelid occlusion, plus 2D/3D feature centres, eye pose and the K matrix. — [RIT-Eyes](https://ar5iv.labs.arxiv.org/html/2006.03642)
- Extra passes that are free from Cycles: albedo, normals, depth, foreground mask, UVs. — [Fake It Till You Make It](https://arxiv.org/html/2109.15102v2)
- Randomization knobs with published value ranges: HDRI with random rotation and intensity (RIT-Eyes 25 maps; Face Synthetics 448), eye pose ±30°, camera jitter ±1–5 mm, pupil aperture 1–4 mm, eyeglasses 50%, 7 augmentations at 14% each, eyelids closing with vertical gaze. — [RIT-Eyes](https://ar5iv.labs.arxiv.org/html/2006.03642)
- Hold out by **identity** (RIT-Eyes 18/6 heads; GazeGene 46/10 subjects). — [RIT-Eyes](https://ar5iv.labs.arxiv.org/html/2006.03642); [GazeGene](https://huggingface.co/datasets/vigil1917/GazeGene)
- Augmentation was what moved Face Synthetics from 4.25 to 3.09 NME. — [Fake It Till You Make It](https://arxiv.org/html/2109.15102v2)
- IR/near-eye mode: NVGaze, RIT-Eyes and OpenEDS are all IR, and the headset-relevant cues are a dark (or bright, via retroreflective retina) pupil plus corneal glints from point LEDs. — [NVGaze](https://sites.google.com/nvidia.com/nvgaze); [RIT-Eyes](https://ar5iv.labs.arxiv.org/html/2006.03642); [LEyes](https://arxiv.org/html/2309.06129v4)
- Refractive cornea: radius 7.8 mm, n = 1.3375, aspherical, with a tear film. The pupil seen through the cornea is shifted and magnified, so the 2D pupil label must be the refracted projection, not the raw 3D pupil projected. — [RIT-Eyes](https://ar5iv.labs.arxiv.org/html/2006.03642); [EyeRender](https://www.cl.cam.ac.uk/research/rainbow/projects/eyerender/)

### Inferences (concrete Blender recipes, not verified in our repo)
- **Labels (about half a day):** in the render loop, read the eye bone/empty world matrices, write a JSON per frame with gaze_dir_cam, eyeball_center_3d/2d, pupil_center_3d/2d (from `bpy_extras.object_utils.world_to_camera_view`), iris ring vertices projected to 2D, head pose and K. Also write a per-subject block with kappa, radii and a seed. This matches GazeGene's schema at no render cost.
- **Masks (about half a day):** set `pass_index` per object or material (pupil, iris, sclera, skin, eyelash) and enable the IndexOB/IndexMA passes plus a Cryptomatte or ID-mask compositor node to write PNG masks. Rendering with and without eyelids (holdout) gives the RIT-Eyes "with/without skin" variant.
- **Domain randomization (about 1 day):** one seeded `manifest.json` drives HDRI choice, rotation and strength, iris texture ID, pupil radius 1–4 mm, gaze ±30°, camera jitter, and optional exposure/blur/noise augmentation applied in post (OpenCV), so frames re-render deterministically. Split by texture/identity seed, never by frame.
- **IR mode (about half a day):** a scene variant that drops colour (grayscale emission or a single-channel compositor), uses 1–N small point/area "LED" lights near the camera for glints, a dark pupil, low iris contrast (iris texture desaturated, raised in value), and Filmic/Standard view transform with no HDRI colour. Bright-pupil mode: emissive or retroreflective retina with a coaxial light.
- **Frozen-scorer check (about half a day):** run MediaPipe Face Landmarker iris points (or an open pupil segmenter) on renders and report pixel error against our exact labels, split by condition (gaze angle, HDRI, iris texture). This becomes a reproducible table in the README and follows the CLAUDE.md rule against oracle advantage.
- **Do not attempt in 3 days:** GAN refinement (SimGAN), training a gaze network to sim-to-real convergence, or MetaHuman/Unreal porting.

### Gaps
- I did not check which of these the TrueGaze repo already does (cornea refraction, label export, masks). Map them against `truegaze/` before planning.
- Whether the hackathon rubric (`docs/hackathondetails.md`) rewards labels, masks or IR mode was not checked here; another researcher or the coordinator should match these ideas against the rubric.
