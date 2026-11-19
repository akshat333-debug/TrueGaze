# Physiologically plausible eye and eyelid motion for animation

Scope: numbers and models (primary sources where reachable) for saccades, fixational motion, blinks, lid-eye coupling, eye-head, vergence, pupil; how graphics papers validated eye motion; open datasets to compare against.

Research limits (read first): about 17 tool calls. PMC (pmc.ncbi.nlm.nih.gov) returned a reCAPTCHA page, and the Eyes Alive and Ruhland STAR PDFs redirected or came back empty, so several classic numbers below come from abstracts or from later reviews that cite the primary source. Each bullet says which. Anything I could not source is in Gaps, labelled "unverified".

## 1. Saccades: main sequence, velocity profile, glissades/PSO, microsaccades, drift/tremor, smooth pursuit

### Takeaway
Saccade duration grows roughly linearly with amplitude (about 2.7 ms/deg in Baloh 1975). Peak velocity rises with amplitude but saturates, and fits an exponential or an S-shaped (logistic) curve. Use Vpk = Vmax·(1 − e^(−A/C)) for peak velocity and D = D0 + d·A for duration. Fixation should not be static: microsaccades at 1–3/s, under about 0.5°, plus tremor at about 70–103 Hz. Post-saccadic oscillation (PSO) is real, but in video trackers it is partly a pupil-relative-to-iris wobble rather than rotation of the globe.

### Cited Findings
- Bahill, Clark & Stark (1975) named the "main sequence": peak velocity and duration both increase systematically with saccade amplitude. Mathematical Biosciences 24(3):191–204. Seen via citing papers; full text not retrieved. — [Gibaldi & Sabatini 2021, BRM (citing)](https://pmc.ncbi.nlm.nih.gov/articles/PMC7880984); [preprint PDF](https://iris.unige.it/retrieve/e268c4ce-65fa-a6b7-e053-3a05fe0adea1/Main_Sequence_BRM%20%28revised%29.pdf)
- Companion 1975 papers by the same group cover glissades and dynamic overshoot: Bahill & Stark, "Overlapping saccades and glissades", Exp. Neurology 48(1):95–106, and "Dynamic overshoot in saccadic eye movements", Exp. Neurology 48(1):107–122. — [search result citing them](https://pmc.ncbi.nlm.nih.gov/articles/PMC7880984)
- Baloh, Sills, Kumley & Honrubia (1975), Neurology 25(11):1065–1070, measured 25 normal subjects. Amplitude and duration were linearly correlated, with a mean slope of **2.7 ms per degree**. Amplitude and peak velocity were nonlinear and best fit by a **2-constant exponential equation**. The constants are not in the abstract. — [Scilit abstract record](https://scilit.com/publications/db6853d9de9d3c9a2d9c9b4fa59245a4)
- Duchowski & Krejtz (JEMR 2017) proposed an inverse-linear **logistic** main-sequence model. It is an S curve, flat at very small and very large amplitudes, offered as an alternative to the exponential. — [JEMR article](https://bop.unibe.ch/JEMR/article/download/3603/Duchowski_JEMR_10-3-4/13042)
- Collewijn, Erkelens & Steinman (1988), J Physiol 404:157–182, recorded with scleral coils. Human horizontal saccades are **not strictly conjugate**: there is a transient divergence-then-convergence whose size and speed scale with saccade size, and post-saccadic drift has both version and vergence components. The abducting eye shows less net drift than the adducting eye. The companion vertical-saccade paper is J Physiol 404:183–197. — [PMC1190820](https://pmc.ncbi.nlm.nih.gov/articles/PMC1190820), [PMC1190821](https://pmc.ncbi.nlm.nih.gov/articles/PMC1190821/)
- In the eye-tracker signal, post-saccadic oscillations **decrease with increasing saccade size** (Hooge, Cornelissen & Holmqvist 2015, Vision Research 112:55–67). — [Utrecht record](https://research-portal.uu.nl/en/publications/the-art-of-braking-post-saccadic-oscillations-in-the-eye-tracker-/)
- In pupil-based trackers the pupil moves relative to the iris after a saccade, so part of the PSO is the pupil and iris wobbling rather than the eyeball rotating (Nyström, Hooge & Holmqvist 2013). Nyström et al. (2015, Vision Research 107:1–14) tested whether crystalline-lens accommodation drives PSO. — [Lund record](https://lup.lub.lu.se/record/4909556); [Nyström 2015 record](https://utrecht-main-test.atmire.com/items/f19cd24c-b7e2-4aa9-9a9b-95e15251d1e8)
- Microsaccades occur **1–3 times per second** during attempted fixation. They are usually **under 0.5°** but can reach 1° or more. Drift parameters have less consensus. — [Otero-Millan, Macknik & Martinez-Conde 2014, Frontiers Integr. Neurosci.](https://www.frontiersin.org/journals/integrative-neuroscience/articles/10.3389/fnint.2014.00052/full); [PMC4083562](https://pmc.ncbi.nlm.nih.gov/articles/PMC4083562)
- Ocular tremor amplitude is about one photoreceptor width, with dominant frequencies **averaging about 84 Hz (range 70–103 Hz)**. This is from a later Martinez-Conde & Macknik review, which cites other primary work. — [par.nsf.gov 10429897](https://par.nsf.gov/servlets/purl/10429897)
- A secondary wiki warns that some numbers commonly attributed to Martinez-Conde et al. 2004 (Nat Rev Neurosci 5:229–240), such as tremor "< 1 arcmin", are not actually in that paper. — [search result](https://zerca.tail8f5ad8.ts.net/wiki/eye-tracking-research-kb/fixational-eye-movements)

### Inferences
- For a script, D = D0 + 2.7·A ms is defensible, citing Baloh 1975 for the slope only. An intercept needs a source we can quote (see Gaps).
- Driving peak velocity from a saturating exponential, and checking that synthetic saccades fall on that curve, is the standard "main-sequence check". It is a cheap, reproducible validation plot for the deck.
- Fixation jitter should be pink (1/f) noise plus occasional microsaccades, not white noise. Duchowski's perceptual study shows unfiltered jitter is rated least natural (see section 3).
- If we render an iris and pupil, a small damped pupil-relative-to-iris overshoot after each saccade is physiologically grounded (Nyström 2013) and decreases for larger saccades (Hooge 2015).

### Gaps
- Exact Bahill 1975 and Baloh 1975 exponential constants (Vmax, C) were not retrieved, because the full texts were paywalled and PMC returned a CAPTCHA. Unverified training-knowledge values that need checking before citing: Baloh-type Vmax of about 500–700 °/s and C of about 7–15°; Carpenter (1988) D ≈ 2.2·A + 21 ms.
- Velocity-profile skew was not sourced. Unverified: the acceleration phase is shorter than deceleration, and the profile becomes more skewed as amplitude grows (Van Opstal & Van Gisbergen 1987).
- Glissade and PSO amplitudes and durations in degrees and ms were not retrieved.
- No smooth-pursuit numbers were sourced. Unverified: pursuit gain near 1 up to about 30 °/s, with catch-up saccades above that.

## 2. Blinks, lid-saccade coupling, gaze-evoked blinks, eye-head/VOR, vergence, pupil

### Takeaway
A blink is strongly asymmetric. Closing is fast (about 75–100 ms) and opening roughly half as fast. The whole blink lasts about 250–450 ms, and spontaneous rate is about 15/min with wide individual spread (6.6–27/min in Trutoiu's actors). The upper lid tracks vertical gaze through "lid saccades" (Becker & Fuchs 1988). Lifting is active (levator) and lowering is passive. During a blink the eye rotates down and toward the nose. Blinks synchronise with large gaze shifts.

### Cited Findings
- Spontaneous blink rate is **about 15 per minute** (Riggs 1981; Volkmann 1982; Evinger 1995; Ousler 2014; Van Opstal 2016). — [Frontiers Syst. Neurosci. 2023 review](https://www.frontiersin.org/journals/systems-neuroscience/articles/10.3389/fnsys.2023.1242654/full)
- Trutoiu et al. 2011 (300 fps, 3 actors) measured individual blink rates of **8.2, 27.0 and 6.6 blinks/min**. They attribute the 27.0 to contact lenses, and all three fall within the bounds in Doughty 2001. — [Trutoiu et al. 2011, ACM TAP 8(3)](https://la.disneyresearch.com/wp-content/uploads/Modeling-and-Animating-Eye-Blinks-Paper.pdf)
- The whole blink lasts **250–450 ms** (Volkmann 1982). Visual occlusion ("blackout") lasts **about 40–200 ms**. Full lid closure is held for **10–50 ms** (Ousler 2014), longer for voluntary blinks or dry eyes. — [Frontiers 2023](https://www.frontiersin.org/journals/systems-neuroscience/articles/10.3389/fnsys.2023.1242654/full)
- The down (closing) phase lasts about **75–100 ms** (Evinger et al. 1991), or 50–130 ms per Stern 1984. The lid starts moving about **10 ms after orbicularis oculi activation**. Peak lid velocity is **16–19 cm/s** as the lid crosses the visual axis (Doane 1980). — [Frontiers 2023](https://www.frontiersin.org/journals/systems-neuroscience/articles/10.3389/fnsys.2023.1242654/full)
- The up (opening) phase is about **half as fast** as the down phase. Reflex blinks have the fastest down phase and spontaneous blinks the slowest, while up-phase velocity barely differs between blink types (Evinger et al. 1991, IOVS 32:387–400). — [Frontiers 2023](https://www.frontiersin.org/journals/systems-neuroscience/articles/10.3389/fnsys.2023.1242654/full); [Stony Brook record of Evinger 1991](https://researchconnect.stonybrook.edu/en/publications/eyelid-movements-mechanisms-and-normal-data/)
- Blink amplitude vs peak velocity is **linear and positive** (Evinger 1991; Costela 2014). Amplitude vs duration is more variable. — [Frontiers 2023](https://www.frontiersin.org/journals/systems-neuroscience/articles/10.3389/fnsys.2023.1242654/full)
- Mechanism (Evinger 1991): the **levator palpebrae** drives upward lid movement both in upward saccades and in the blink up-phase. Lid movement in downward saccades comes almost entirely from **passive forces plus levator relaxation**. Blink closure adds active orbicularis contraction. Downward lid saccades often **overshoot**, and for most amplitudes they are faster than upward ones. — [search summary of Evinger 1991 and citing papers](https://researchconnect.stonybrook.edu/en/publications/eyelid-movements-mechanisms-and-normal-data/); [core.ac.uk thesis](https://core.ac.uk/download/18513071.pdf)
- Becker & Fuchs (1988), J Neurophysiol 60:1227–1252, used search coils in humans and monkeys and coined the term **"lid saccades"**. Downward lid saccades match eye-saccade velocities, while upward lid saccades are slower than the eye. This is from a thesis summary; abstract not retrieved. — [core.ac.uk thesis](https://core.ac.uk/download/18513071.pdf)
- When a blink starts, the eye moves **down and nasally** and returns before blink offset. The lower lid moves **3–5 mm nasally** (Doane 1980). — [Frontiers 2023](https://www.frontiersin.org/journals/systems-neuroscience/articles/10.3389/fnsys.2023.1242654/full)
- Blinks **synchronise with saccades and combined eye-head gaze shifts** (Zee 1983; Evinger 1994; Goossens & Van Opstal 2000), and blinks can initiate vergence. The review gives no probability-versus-amplitude numbers. — [Frontiers 2023](https://www.frontiersin.org/journals/systems-neuroscience/articles/10.3389/fnsys.2023.1242654/full)
- Trutoiu 2011 adopts VanderWerf et al. (2003)'s definition of blink end: the moment inter-eyelid distance reaches **95% of the original value**. Opening converges asymptotically, so the end point is otherwise ill-defined. — [Trutoiu 2011](https://la.disneyresearch.com/wp-content/uploads/Modeling-and-Animating-Eye-Blinks-Paper.pdf)
- Pupil: macaque minimum mean constriction latency was **136 ms** at the brightest flash. Human latencies are reported as about **70 ms longer** (so about 200 ms; this is my arithmetic). Pupil oscillations of **0.9–1.6 Hz** occurred in monkeys under long bright stimuli, and the source likens these to human hippus. — [Utah collection record (macaque PLR metrics)](https://collections.lib.utah.edu/details?id=225584)
- Human constriction velocity falls with age and constriction latency rises with age (90 healthy adults, Korea). No values were given in the snippet. — [KoreaMed](https://synapse.koreamed.org/articles/1010793)

### Inferences
- Blink keyframes: close in about 3 frames at 30 fps (about 100 ms), hold 0–1 frame, open in about 6–8 frames, with an ease-out tail. Add an eye rotation down and in during the blink. Trigger blinks on a Poisson-like process at about 15/min (range 6–27), with an extra chance of a blink when a gaze shift is large.
- Lid coupling: drive upper-lid height from eye pitch every frame. Make the downward lid snappier, with slight overshoot, and the upward lid slightly lagging the eye.
- Pupil: a first-order lag of about 0.2 s latency for light changes, plus a slow oscillation under 2 Hz, is defensible. Present the human hippus band as unverified.

### Gaps
- Exact gain of upper-lid position against vertical eye position (Becker & Fuchs 1988) was not retrieved. Unverified: roughly proportional, around 1 mm of lid per few degrees of gaze.
- No sourced probability-versus-amplitude curve for gaze-evoked blinks. Unverified: Evinger 1994 reports blinks become very likely for gaze shifts above about 30–40°.
- Eye-head coordination: no sourced numbers. Unverified: head contribution becomes significant beyond about 15–20° gaze shifts, and VOR gain is about 1 (Guitton & Volle 1987; Freedman & Sparks).
- Vergence dynamics: only Collewijn's transient-vergence finding was sourced. Unverified: vergence takes several hundred ms, much slower than saccades.
- No human normative pupil table was retrieved: latency, constriction velocity in mm/s, re-dilation time, and hippus frequency.

## 3. Graphics and animation papers on eye motion, and how they validated it

### Takeaway
The field validates eye motion almost entirely through **perceptual naturalness user studies** (Likert ratings or preference), sometimes with recorded human motion as a reference stimulus. Only a few recent works add **quantitative comparison against recorded eye-tracking statistics**, such as StyGazeTalk's fixation-ratio and gaze-head metrics. A main-sequence plot of synthetic against literature values would be both cheap and distinctive.

### Cited Findings
- **Lee, Badler & Badler, "Eyes Alive" (SIGGRAPH 2002, doi 10.1145/566570.566629).** Saccade model built on empirical saccade models plus statistics from eye-tracking data. Parameters cover magnitude, direction, duration, velocity and inter-saccadic interval, with separate talking and listening modes. Evaluation was a subjective comparison of **three conditions**: static eyes, random saccades, and statistically derived saccades. Participant count was not retrieved. — [SIGGRAPH history](https://history.siggraph.org/?p=118454); [UPenn repository](https://repository.upenn.edu/hms/51)
- Critique of Eyes Alive: it uses only first-order statistics and has no gaze-eyelid coupling or vergence (Deng, Lewis & Neumann). Their SIGGRAPH 2003 sketch, a texture-synthesis eye model, ran an **informal 8-person test** in which 7 preferred their model over Eyes Alive. — [Deng et al. sketch PDF](https://graphics.cs.uh.edu/wp-content/uploads/papers/2003/sig03_eyemotion.pdf); [CGA 2005 version](https://graphics.cs.uh.edu/wp-content/uploads/papers/2005/CGA_eyemotion.pdf)
- **Ruhland et al. 2015**, "A Review of Eye Gaze in Virtual Agents, Social Robotics and HCI", Computer Graphics Forum 34(6):299–326, doi 10.1111/cgf.12603. It starts from eyeball, eyelid and head physiology and ends with **guidelines for animators**. I could not extract its specific numbers. — [Eurographics DL](https://diglib.eg.org:443/xmlui/handle/10.1111/cgf12603); [TCD open copy](https://edepositireland.ie/handle/2262/75245)
- **Trutoiu, Carter, Matthews & Hodgins 2011**, "Modeling and Animating Eye Blinks", ACM TAP 8(3):17. Three actors were filmed at **300 fps** (over 400,000 frames each) and tracked with Active Appearance Models (42-point eye model). Closing and opening were each fit with a spline, and a PCA model generates blinks.
  - **Exp. 1:** 32 participants rated naturalness on a 7-point scale. The design was 2 (character: photoreal or cartoon) × 2 (profile) × 2 (motion blur) × 2 (closing amplitude) repeated-measures. Model blinks were rated more natural than the real ones, F(1,31)=39.07, p<0.001, and motion blur had no main effect.
  - **Exp. 2:** 43 participants, 400 trials, comparing 5 profiles (data-driven against textbook linear and ease-in/out, symmetric and asymmetric) × 4 durations × 2 characters. All pairwise profile differences were significant (Bonferroni, p<0.05).
  - Conclusion: data-derived blinks with full closure are consistently rated more natural than textbook animation curves. The asymmetric profile (fast close, slow asymptotic open) matters.
  - [Trutoiu 2011 PDF](https://la.disneyresearch.com/wp-content/uploads/Modeling-and-Animating-Eye-Blinks-Paper.pdf); [CMU RI](https://www.ri.cmu.edu/publications/modeling-and-animating-eye-blinks)
- **Duchowski et al.**, "Eye movement synthesis" (ETRA 2016), preceded by "Eye movement synthesis with 1/f pink noise" (MIG 2015). Procedural model: rotations obey **Donders' and Listing's laws**, saccades follow the **main sequence**, and gaze jitter and **pupil unrest** use **1/f^α (pink) noise**. — [CAV paper (zendy)](https://zendy.io/title/10.1002/cav.1745)
- Krejtz, Duchowski et al. (Computer Animation and Virtual Worlds 2017) ran a perceptual test of that model, with **recorded eye movements as reference**, at extreme close-up and close-up distances. Pink-noise jitter was rated highly natural. **No jitter, or unfiltered (white) jitter, was rated least natural.** — [CAV 10.1002/cav.1745](https://zendy.io/title/10.1002/cav.1745)
- Recent work:
  - **Canales, Jain & Jörg (MIG 2023)**, real-time conversational gaze synthesis from speech and head motion, evaluated with a user study against other eye-animation methods. — [PDF](https://www.uni-bamberg.de/fileadmin/cg/publications/canales23/Canales23_Gaze.pdf)
  - **Melgare et al. (CGF 2024)**, eye and head gaze during locomotion. — [Eurographics PDF](https://diglib.eg.org/bitstream/handle/10.1111/cgf15168/v43i8_cgf15168.pdf)
  - **StyGazeTalk (arXiv 2509.17168)**, gaze plus head from speech, with a dataset (HAGE) recorded with a professional eye tracker. It introduces pattern-level metrics, a **fixation ratio** and a **gaze-head compensation score**, rather than frame-wise error. — [arXiv](https://arxiv.org/html/2509.17168v2)
  - **Kullmann & Botsch (CHI EA 2023)**, evaluation of other-avatar facial animation in social VR, covering naturalness and latency. — [PDF](https://downloads.hci.informatik.uni-wuerzburg.de/2023-chi-Kullmann-An-Evaluation-of-Other-Avatar-Facial-Animation-Methods-for-Social-VR.pdf)

### Inferences
- A defensible validation for our project, reproducible by script with no user study:
  - Plot the synthetic saccades' peak velocity and duration against amplitude, overlaid on the literature main sequence.
  - Plot the lid-closure time profile against Trutoiu's asymmetric shape and Evinger's durations.
  - Show the blink-interval histogram against about 15/min.
  - Show the fixation-jitter spectrum (1/f) against a white-noise control.

  This directly mirrors how Duchowski and Trutoiu argue for naturalness.
- To avoid an "oracle" critique: if we tune parameters to literature constants, then the validation should compare against an **independent** recorded dataset (for example GazeBase), not against the same constants we coded in.

### Gaps
- Eyes Alive participant count and statistics were not retrieved; the PDF URL redirects.
- No graphics paper found that quantitatively scores **blink timing** against recorded tracker data.

## 4. Open eye-movement datasets for comparison

### Takeaway
GazeBase is the strongest open option. It has 322 participants recorded at 1000 Hz on an EyeLink 1000, with fixation, saccade, reading and game tasks, and a ready loader in pymovements. That makes it practical to extract a real main sequence and microsaccade statistics as an independent reference.

### Cited Findings
- **GazeBase** (Griffith, Lohr, Abdulin & Komogortsev, Scientific Data 8:184, 2021) contains **12,334 monocular (left-eye) recordings** from **322 college-aged participants** (151 F and 171 M in Round 1). It was recorded at **1,000 Hz** on an **EyeLink 1000** (desktop mount) over **37 months and 9 rounds**, with 7 tasks: fixation, saccade tasks, reading, video and a gaze-driven game. — [Nature Sci Data](https://www.nature.com/articles/s41597-021-00959-y.pdf); [PMC8285447](https://pmc.ncbi.nlm.nih.gov/articles/PMC8285447); [arXiv 2009.06171](https://arxiv.org/pdf/2009.06171)
- GazeBase has a **pymovements** loader. — [pymovements docs](https://pymovements.readthedocs.io/en/v0.4.0/reference/pymovements.datasets.gazebase.GazeBase.html)
- The StyGazeTalk HAGE dataset contains professional eye-tracker recordings with head motion during unscripted conversation. Release status was not checked. — [arXiv 2509.17168](https://arxiv.org/html/2509.17168v2)

### Inferences
- GazeBase's "random saccade" task is the natural source for an independent main-sequence fit (Vmax, C, duration slope) to validate our synthetic saccades against.
- GazeBase does not contain eyelid or blink kinematics beyond tracker dropouts, so blink validation still rests on the literature (Evinger, Trutoiu).

### Gaps
- GazeBase licence terms were not checked; check before redistributing any derived data in the public repo.
- Other datasets were not researched in this pass: EyeLink-based saccade sets, GazeBaseVR, the Gaze-in-Wild eye-plus-head dataset, and blink video datasets.
