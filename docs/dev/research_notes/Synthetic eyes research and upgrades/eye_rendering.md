# Photoreal eye rendering (Blender 4.5 Cycles focus)

Scope note: about 16 tool calls. Primary sources reached: the Pixar RenderMan "Making of a Samurai" breakdown, Reallusion CC Blender Tools docs, Universal Human (Blender) eye shader docs, the Blender 4.5 manual (Principled BSDF, Light Paths), Unity HDRP eye docs, and iris-synthesis papers (via search snippets). Epic's English MetaHuman eye-material page and Jimenez's eye slides did not return usable text; those are listed as gaps.

## 1. Eye anatomy layers and how pros build them (cornea, anterior chamber, iris depth, limbus, meniscus, occlusion)

### Takeaway
Every production eye found uses **separate geometry layers**: an outer cornea/sclera shell (one mesh, masked material), a recessed or concave iris inside it, a thin **tear-meniscus / tearline strip** along the lid margin, and an **eye-occlusion ("eye AO") shell** for lid shadowing. Refraction comes either from a real dielectric cornea (offline: Pixar, Universal Human) or a parallax/depth offset (real-time: CC Tools, MetaHuman, HDRP). In Cycles the real-refraction route works but needs shadow and caustic handling.

### Cited Findings
- Pixar's Samurai (built from a MetaHuman base) remodelled the eyes as five pieces: **cornea, limbus, lens, iris, meniscus**, modelled from physical eye data. **Cornea and sclera share one mesh**, with a mask blending the cornea dielectric into the sclera material. — [RenderMan: Making of a Samurai](https://renderman.pixar.com/the-making-of-a-samurai)
- Pixar values: sclera is built like skin SSS but with **IOR 1**. Limbus is SSS blended with a dielectric at **IOR 0.976, roughness 0.01** ("below 1 to avoid stacked refraction behind the cornea"). Iris is the skin shader with **SSS scale 3**. Meniscus is a dielectric at **IOR 1.37, roughness 0.09**, with a noise bump. Lens is a dielectric at **IOR 1.1, roughness 0.3**, with exterior IOR **1.334**. — [RenderMan Samurai](https://renderman.pixar.com/the-making-of-a-samurai)
- Pixar sclera DMFP (SSS distance) is **about 1.3 at the edges, rising to 6 toward the centre**. A radial **"limbus backlight" mask raises DMFP to 8 around the limbus, with warmer tones**. — [RenderMan Samurai](https://renderman.pixar.com/the-making-of-a-samurai)
- Pixar cornea **thin-film look**: three dielectrics with Reflection Tint set to pure R, G and B, each with transmission tint 0.333, added together and offset in roughness by 0.01 per channel. — [RenderMan Samurai](https://renderman.pixar.com/the-making-of-a-samurai)
- Pixar trace depth: **at least 4 for specular and diffuse, up to 8**, with diminishing returns. Iris displacement dicing was 0.5 instead of 1 (4x geometry resolution). Bump handles high frequencies and displacement handles low ones, with veins as sclera displacement. — [RenderMan Samurai](https://renderman.pixar.com/the-making-of-a-samurai)
- Physical IORs for Cycles: **cornea about 1.376, aqueous humour 1.336**. One suggestion models the cornea's inner surface with relative IOR 1.376/1.336 ≈ **1.0299** and fills the inside with aqueous at 1.336. — [BlenderArtists: physically correct eye](https://blenderartists.org/t/modeling-a-physically-correct-human-eye/620146). The Auto Eye add-on recommends **about 1.38** for realism and about 1.3 for stylized eyes. — [Auto Eye docs](https://superhivemarket.com/products/auto-eye/docs)
- Universal Human (Blender Cycles) uses an exterior **Eye** object (sclera and cornea material) and an interior **Iris** object (iris and pupil materials), with **pupil dilation and offset shape keys** (the offset shifts the pupil slightly up and toward the nose). Its iris colour stacks **Melanin over Fibres over Base**, with Limbal Ring, Grain and Displacement inputs. — [Universal Human eye shader docs](https://sites.google.com/view/universalhuman/documentation/eye-shader-docs)
- CC Blender Tools (Reallusion to Blender) eyeball parameters: Iris Radius; **Limbus Width, Limbus Dark Radius/Width, Limbus Color**; Sclera Scale (blood-vessel visibility); **Corner Shadow (Shadow Radius, Hardness, Color)**; separate Cornea, Iris and Sclera roughness and specular; a per-channel Subsurface Radius times Scale; **Iris Depth, Depth Radius, Pupil Scale, IOR, Refraction Depth**; Sclera normal tiling, Blood Vessel Height, Iris Bump Height. — [CC Blender Tools: Eyes](https://soupday.github.io/cc_blender_tools/eyes.html)
- CC Blender Tools has two Eevee refraction modes. **Parallax** (default) uses one cornea material and keeps SSS and shadow reception. **SSR** puts a transmissive cornea over an opaque iris but loses SSS and full shadows. — [CC Blender Tools: Eyes](https://soupday.github.io/cc_blender_tools/eyes.html)
- CC **Eye Occlusion** shell parameters: Strength, Hardness (alpha exponent), Top/Bottom/Inner/Outer gradients each with Range and Curve, a secondary top-down mask, **Tear Duct Position/Width**, and per-edge displacement. **TearLine** mesh: Specular, Roughness, Alpha, and Displace/Inner Displace. — [CC Blender Tools: Eyes](https://soupday.github.io/cc_blender_tools/eyes.html)
- Reallusion manual: Eye Occlusion represents **"shadows cast from the eyelids"**, and the Tear Line handles reflection where the tear film meets the lid. — [Reallusion CC4 Tear Line shader](https://manual.reallusion.com/character-creator-4/Content/ENU/4.0/15_Digital_Human_Shader/Eyes/Digital-Human-Tearline-Shader.htm); [Reallusion Eye & Eye Occlusion (Unreal)](https://manual.reallusion.com/CC_and_IC_Auto_Setup_Plugin/ENU/CC_and_iC_Auto_Setup/1.2/02_for_Unreal/Eye-and-Eye-Occlusion.htm)
- MetaHuman's eye-occlusion shader is **unlit and uses emissive output** so it does not go black. Users report artifacts under strong side light. — [UE forum: MetaHuman Eye Occlusion shader](https://forums.unrealengine.com/t/metahuman-eye-occlusion-shader/541004). The MetaHuman eye material exposes **Limbal Ring Size, Softness and Color**. — [Epic MetaHuman eye material controls (JA)](https://dev.epicgames.com/documentation/metahuman/eye-material-controls?lang=ja)
- Unity HDRP treats the eye as a **two-layer material**: layer one is the cornea plus surface fluids, layer two is the sclera and iris seen through it. It supports cornea refraction, caustics, pupil dilation, limbal darkening and SSS. — [Unity HDRP: Understand eyes](https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.0/manual/understand-eyes.html). Its limbal ring has separate size-on-iris, size-on-sclera, fade and intensity controls. — [Unity HDRP Eye shader](https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@15.0/manual/eye-shader.html)
- Digital Ira (USC ICT/Activision) listed **eye refraction and caustics** plus a two-lobe specular with microstructure among its rendering features. — [Digital Ira poster](https://vgl.ict.usc.edu/Research/DigitalIra/digitalIraPoster.pdf); [Digital Ira and Beyond course](https://vgl.ict.usc.edu/Publications/2014/Digital%20Ira%20and%20Beyond%20Creating%20Photoreal%20Real-Time%20Digital%20Characters.pdf)

### Inferences
- **Minimum credible Cycles eye stack, all buildable by script:**
  1. An outer shell sphere with a slight corneal bulge. Use a masked material: Principled at IOR about 1.376, roughness about 0.0–0.02 and transmission 1 inside the cornea mask, and sclera Principled with SSS outside it. Pixar's IOR-1 trick for the sclera means the sclera gets no refractive offset of its own.
  2. A concave or recessed iris disc about 2–3 mm behind the cornea apex, so real parallax happens.
  3. An optional aqueous volume at IOR 1.336. It is usually skipped: a single 1.376 cornea over an air gap is the common simplification.
  4. A tear-meniscus strip along the lower lid: a glossy dielectric at IOR about 1.37, roughness about 0.05–0.1, with a noise bump.
  5. An eye-occlusion shell slightly in front of the eyeball, using a transparent and black mix whose alpha comes from a UV gradient (strongest at the top lid and corners). It should not cast shadows itself.
- The Pixar "limbus backlight" (warmer, deeper SSS ring around the limbus) is cheap to copy in Blender. Drive Principled **Subsurface Scale** or radius with a radial mask (a gradient texture over object-space distance from the eye axis) so it is larger near the limbus.
- Blender 4.x Principled has a native **Thin Film** input (Cycles only, thickness in nm; strongest between about 100 and 1000 nm, UI range 400–800). It can stand in for Pixar's RGB-split thin-film cornea trick, for example 300–500 nm at very low visibility. That is untested, so keep the effect subtle. — [Blender 4.5 Principled BSDF manual](https://docs.blender.org/manual/en/4.5/render/shader_nodes/shader/principled.html)

### Gaps
- Epic's English MetaHuman eye-material page returned no body text, so exact MetaHuman parameter names and defaults (for example IrisUVRadius, LimbusUVWidth, Depth Scale) are unconfirmed.
- Jimenez's 2012 "Photorealistic Eyes Rendering" and GDC 2013 slides were not readable (a 323 MB pptx), so his exact sclera/iris SSS and refraction formulas are not captured here.

## 2. Failure modes: "dead" or "painted" eyes, dark far-side sclera, pink sclera on inward rotation, bright crescent on iris

### Takeaway
Most "dead" or "painted" reads come from four causes: no lid/lash shadowing (no eye AO), no wet high-frequency specular or tear meniscus, a flat iris without parallax or depth, and over-bright or hard highlights. The Cycles-specific artefacts (a darkened iris, a dark sclera, crescents) mostly come from the **glass cornea blocking or caustic-starving light** and from **SSS or reflection interactions with the eye socket**.

### Cited Findings
- Without AO and the right shading, eyes read as **"bright, bug-eyed and uncanny"**, especially at distance. — [Polycount discussion](https://polycount.com/discussion/comment/1569350)
- Without parallax you cannot get the lens-like look where the highlight sits on the cornea while the iris is seen offset from the side. — [Polycount](https://polycount.com/discussion/comment/2664363)
- Pixar: the eyes are "the most complex and important part" of a character, and if they look fake the whole character reads fake. The key fixes were correct light response, the limbus backlight, the thin-film cornea, and **removing dark lines where the meniscus meets skin**. To do that, the meniscus is excluded from the skin's SSS trace and from shadow/transmission casting. — [RenderMan Samurai](https://renderman.pixar.com/the-making-of-a-samurai)
- In Cycles, a refracting cornea **casts a shadow onto the iris**, and a common fix is a separate cornea mesh that does not cast shadows. Some artists make the cornea and tears **invisible to shadows**, using them only for reflection. — [BlenderArtists: transparency issue](https://blenderartists.org/t/transparency-issue/534183); [Renderosity thread](https://api.renderosity.com/forums/threads/2875274/print); [BlenderArtists: eye glass transparency shadows problem](https://blenderartists.org/t/eye-glass-trancparancy-shadows-problem/1510333)
- With refractive caustics on, **the iris renders much darker, especially with denoising**, and needs hundreds of samples. Turning caustics off changes the light path; compensate by raising iris Melanin, Tint and Base. **Path Guiding** (Blender 3.4+) reduces the caustic cost, but **only on CPU**. Larger lights speed up caustics but soften them. — [Universal Human eye shader docs](https://sites.google.com/view/universalhuman/documentation/eye-shader-docs)
- A commercial photoreal Blender eye states it needs **>1000 samples with caustics**, and far fewer with them off. — [Human Eye Photorealistic docs](https://superhivemarket.com/products/human-eye-photorealistic/docs)
- Blender's Light Paths panel has **Caustics > Reflective / Refractive** checkboxes and **Filter Glossy** (1.0 is the suggested start), which blurs glossy reflections after blurry bounces to cut caustic noise. — [Blender 4.5 manual: Light Paths](https://docs.blender.org/manual/en/4.5/render/cycles/render_settings/light_paths.html)
- The "white ring" around the iris (DAZ Genesis 8) is tied to **sclera specular highlights**. Refraction also requires the cornea and moisture surfaces **not to be thin-walled**. — [DAZ forum: G8 white ring syndrome](https://www.daz3d.com/forums/discussion/comment/2949441/)
- Reallusion's **Iris UV Radius** setting fixes "an unnatural ring" at the iris edge, and the Limbus setting controls the dark ring. — [Reallusion Eye & Eye Occlusion](https://manual.reallusion.com/CC_and_IC_Auto_Setup_Plugin/ENU/CC_and_iC_Auto_Setup/1.2/02_for_Unreal/Eye-and-Eye-Occlusion.htm)
- Use a small, sharp highlight on the cornea and a much softer, broader one on the iris. Avoid "burnt-in" (painted) highlights in textures. — [Poser uncanny-valley article](https://www.posersoftware.com/article/1078/how-to-avoid-the-uncanny-valley-in-poser-portraits); [scienceinsights how-to](https://scienceinsights.org/how-to-render-realistic-eyes-step-by-step/) (secondary, lower confidence)
- Pixar noted the **denoiser struggled with eyes at low sample counts**, so they rendered as long as practical before denoising. — [RenderMan Samurai](https://renderman.pixar.com/the-making-of-a-samurai)

### Inferences (diagnoses for the specific symptoms asked; derived from the above plus Cycles behaviour, not individually sourced)
- **Flat, dark sclera on the far-side eye in 3/4 view.** Likely causes, in order:
  - (a) The far eye sits in the nose's shadow and the sclera has no SSS, so it has nothing to fill it.
  - (b) An eye-occlusion or AO shell that is too strong or too wide, applied evenly to both eyes.
  - (c) The cornea/outer shell casts shadows onto the sclera and iris.

  Fixes:
  - Turn off **Object > Visibility > Ray Visibility > Shadow** on the cornea shell, tearline and occlusion shell (`obj.visible_shadow = False` in the 4.x API).
  - Give the sclera Principled SSS (Random Walk, weight 1, a small scale around 1–3 mm, a slightly warm radius).
  - Cap the occlusion alpha at about 0.4–0.6, and build it from lid-distance gradients rather than a uniform darkening.
  - Add a soft fill or rim light from the far side, or a large softbox, since larger lights also help caustics.
- **Pink or red sclera when the eye rotates inward.** The inner sclera is near the caruncle and socket skin, so probable causes are:
  - (a) The sclera's random-walk SSS shares geometry with, or overlaps, the skin, so red skin scatter bleeds in.
  - (b) A skin-like red-dominant SSS radius on the sclera itself.
  - (c) Glossy and diffuse bounce off the red caruncle and inner lid; a real effect, but exaggerated if the sclera is too diffuse or white-bright.
  - (d) An eye texture whose UVs wrap a vessel-heavy or red corner region into view under rotation.

  Fixes:
  - Make the eyeball a separate closed mesh, so it never shares random-walk SSS with skin.
  - Use a near-neutral sclera radius (for example R 1.0, G 0.9, B 0.8 times a small scale) instead of skin's (1.0, 0.2, 0.1)-style radius.
  - Keep vessel density concentrated at the corners, but desaturate it.
  - Check that the socket/caruncle mesh does not intersect the eyeball.
- **Bright crescent on the iris.** Most likely one of these:
  - (a) A caustic: the cornea focusing a key light onto the iris rim. It is physically real, but noisy and exaggerated with a small, hard light.
  - (b) Light leaking through the gap between the iris disc and the sclera shell (the limbus not sealed), or the iris edge poking past the limbus. Compare Reallusion's "Iris UV Radius fixes unnatural ring".
  - (c) Total internal reflection or the back face of a double-sided cornea, if the cornea is a closed solid with a back face hitting the iris.
  - (d) Sclera specular bleeding over the limbus (DAZ "white ring").

  Fixes:
  - Seal the iris-to-sclera boundary with a dark limbal ring in both the shader and the geometry.
  - Make the cornea a single-sided shell or a properly closed volume; do not mix the two.
  - Turn off Refractive Caustics, or use Filter Glossy about 1.0, and compensate the iris albedo.
  - Use a larger key light.
- **"Painted" iris.** This comes from a flat albedo texture with baked highlights and shadows, no depth, and no fibre normal. Fixes:
  - Put the iris in real recessed or concave geometry behind a refracting cornea.
  - Add a fibre/crypt bump (see section 3).
  - Remove any baked specular from the texture.
  - Give the iris a little SSS (Pixar uses scale 3 relative to skin).
  - Darken the limbus ring and the pupil edge.
- **"Dead" eye overall.** Fixes:
  - Add a tear meniscus along the lower lid with a sharp glossy highlight.
  - Make the cornea roughness near 0, so it gives a crisp environment reflection. An HDRI with a window or softbox is far better than a point light here.
  - Add an eye-occlusion shell, so the top lid and lashes shadow the upper iris and sclera.
  - Leave some sclera vessel and colour variation instead of pure white.
  - Add small micro-saccades and blinks in motion. That last point is general practice and not sourced here.

### Gaps
- No primary source was found that specifically diagnoses "pink sclera on inward rotation" or "bright iris crescent". The diagnoses above are reasoned inferences and should be verified by A/B renders: toggle cornea shadow visibility, toggle refractive caustics, and swap the sclera SSS radius.
- The Blender 4.5 Object Visibility and Cycles object-settings pages did not return body text, so the exact wording of "Ray Visibility > Shadow" and the MNEE "Cast/Receive Shadow Caustics" limitations is not quoted. The headings exist on the Cycles object page: "Ray Visibility … Caustics … Shadow Linking". — [Blender 4.5 Cycles object settings](https://docs.blender.org/manual/en/4.5/render/cycles/object_settings/object_data.html)

## 3. Procedural iris texture generation (fibres, crypts, collarette)

### Takeaway
The iris-synthesis literature converges on layered generation: radial **fibres**, then a **collarette** ring at about one-third to one-half of the radius, then **crypts** (dark lacunae) concentrated near the collarette, plus **concentric furrows** at the periphery, **pigment spots (naevi)**, a dark limbal ring and a pupillary ruff. All of these map directly onto Blender shader nodes in polar coordinates.

### Cited Findings
- Lefohn et al. (2003, ocularist-inspired) build the iris in painted layers as an ocularist would. They describe the **collarette** as confined to the inner half of the iris, containing radial spokes or dots, and note that crypts and naevi patterns "could be produced procedurally or could be captured" from images. — [Lefohn et al., escholarship PDF](https://escholarship.org/content/qt8d88d3qc/qt8d88d3qc.pdf?t=ptt3cv)
- Shah & Ross: a **Markov Random Field** background texture, then embedded radial and concentric furrows, the collarette and crypts. This is the basis of the WVU synthetic iris dataset. — [WVU synthetic iris dataset](https://biic.wvu.edu/data-sets/synthetic-iris-dataset); [Clarkson synthetic iris](https://citer.clarkson.edu/?p=187)
- Zuo & Schmid model the iris as **continuous 3D fibres in cylindrical coordinates**, project them to 2D, then add the collarette, a semi-transparent top layer, and random eyelids and lashes. — [Zuo/Schmid, via core.ac.uk](https://core.ac.uk/download/50367538.pdf)
- A 2025 survey warns that synthetic irises can carry **generation artefacts that make them look synthetic**. — [arXiv 2506.02626](https://arxiv.org/pdf/2506.02626); see also [arXiv 2503.11930](https://arxiv.org/pdf/2503.11930)
- Universal Human's practical shader layering is **Base, then Fibres (image and alpha), then Melanin (ColorRamp), then Grain, then Limbal Ring**, with the colour also driving displacement. — [Universal Human docs](https://sites.google.com/view/universalhuman/documentation/eye-shader-docs)

### Inferences (Blender node recipe, scriptable)
- **Polar coordinates:** from the iris UV centred at (0.5, 0.5), compute `r = length(uv - 0.5) / R_iris` and `θ = atan2`. Use Separate XYZ, Vector Math and Math nodes, or the Gradient texture in Spherical/Radial mode for θ.
- **Fibres:** a Noise or Wave texture sampled at (θ·k, r·small), so it is stretched radially; for example a Wave texture in Bands mode along X with distortion 5–10, fed with θ·60 and r·2. Use the result as both an albedo multiplier (about ±15%) and a Bump height.
- **Collarette:** a smooth bump ring at r ≈ 0.35–0.45, built as a Map Range of r and then a ColorRamp. Modulate its radius with low-frequency noise in θ so it is jagged, and make it lighter or more saturated than the outer stroma.
- **Crypts:** a Voronoi texture (F1 or Distance to Edge) in (θ, r) space. Threshold it to sparse dark lens-shaped holes, masked to r ∈ [0.3, 0.6], and give them negative bump.
- **Contraction furrows:** a sine of r·N (N ≈ 6–10) masked to r > 0.65, as a faint bump.
- **Pupillary ruff:** a thin dark-brown ring at r ≈ pupil + 0.02.
- **Limbal ring:** darken smoothly over r ∈ [0.9, 1.0] and blend into the sclera over about 2–5% of the eye radius.
- **Colour:** two ColorRamps (inner zone and outer zone) blended by r. That gives the common central-heterochromia look, for example an amber collarette inside a grey-green outer zone. Melanin maps to brown via a ramp.
- **Per-eye variation:** seed the noise W-coordinate (4D Noise) differently per eye, so the L and R irises are distinct but share palette parameters. This satisfies a "distinct L/R iris" requirement procedurally.

### Gaps
- Full PDFs of Lefohn, Shah/Ross and Zuo/Schmid were not opened. The proportions above (collarette at 0.35–0.45 of the radius, and so on) are artistic estimates consistent with "inner half", not measured values from the papers.

## 4. Sclera vessels, SSS, wet specular, caustics: Cycles parameters

### Takeaway
Use Principled BSDF Random Walk SSS on the sclera and iris, a near-zero-roughness clear dielectric cornea that does **not** cast shadows, refractive caustics off (or Filter Glossy) unless you can afford 1000+ samples, and vessels as low-frequency displacement plus colour concentrated at the canthi.

### Cited Findings
- Blender 4.5 Principled SSS methods:
  - **Christensen-Burley** is faster but less accurate.
  - **Random Walk** (Cycles only) uses true volumetric scattering, best for **closed meshes**; overlapping faces and holes cause problems.
  - **Random Walk (Skin)** auto-adjusts the radius from the colour texture and uses mixed diffuse/specular entry with a custom IOR.

  Other inputs:
  - **Weight** should typically be 0 or 1.
  - **Radius** is per RGB channel, and **Scale** applies to the radius.
  - **SSS IOR** (Cycles) is 1.0–2.0.
  - **Anisotropy**: skin is measured at about 0.8.
  - Specular **Distribution** is GGX or Multiscatter GGX, the latter more energy-conserving.

  — [Blender 4.5 Principled BSDF](https://docs.blender.org/manual/en/4.5/render/shader_nodes/shader/principled.html)
- Cycles **Caustics: Reflective / Refractive** toggles, and **Filter Glossy** (start at 1.0) to reduce fireflies. — [Blender 4.5 Light Paths](https://docs.blender.org/manual/en/4.5/render/cycles/render_settings/light_paths.html)
- Pixar keeps sclera veins as **displacement** and lower-frequency detail as bump, and iris high frequency as bump. — [RenderMan Samurai](https://renderman.pixar.com/the-making-of-a-samurai)
- CC Tools exposes **Sclera Scale (vessel visibility), Blood Vessel Height**, sclera normal tiling and a **Corner Shadow** radius/hardness/colour, which darkens the eyeball near the canthi. — [CC Blender Tools: Eyes](https://soupday.github.io/cc_blender_tools/eyes.html)
- Shadow-caustic route: a Daz-to-Blender issue notes that, in Cycles, a partially transmissive cornea still has a minor effect on shading even when made "invisible". — [Diffeomorphic import_daz issue 336](https://bitbucket.org/Diffeomorphic/import_daz/issues/336/eevee-principled-method-the-current)

### Inferences (concrete starting values to A/B, not sourced presets)
- **Cornea:** Principled with Base White, Roughness 0.0–0.02, IOR 1.376, Transmission Weight 1.0. `visible_shadow = False`; keep glossy and transmission visibility on.
- **Sclera:**
  - Base about (0.80, 0.76, 0.72) sRGB, not pure white.
  - SSS Random Walk, Weight 1, Radius (1.0, 0.85, 0.75), Scale 0.002–0.004 m (adjust to scene units).
  - Roughness 0.15–0.25 under a near-zero-roughness wet layer. Use Coat Weight 1, Coat Roughness 0.02, Coat IOR 1.33, or rely on the cornea/tear shell if it covers the eyeball.
- **Vessels:** a Noise texture (high Detail, Distortion) through a thin ColorRamp band gives dark-red lines. Mask it by a gradient from the canthi (object-space X), so the corners are vesselly and the centre is clean. Feed a little into Bump.
- **Iris:** Principled with SSS weight about 0.3–1 at a tiny scale (Pixar uses 3 times its skin SSS scale), roughness about 0.4, and Bump from the fibre pattern.
- **Lights and samples:** use a large area light or an HDRI (window reflections sell wetness). Refractive caustics off by default, with the iris albedo raised to compensate. If they are on, use CPU Path Guiding and 1000+ samples per Universal Human. Max bounces: glossy and transmission at least 8 (Pixar: 4–8).
- **Tear meniscus and caruncle:**
  - Meniscus: a thin tube or strip mesh along the lower lid margin. Principled, transmission 1, IOR 1.37, roughness 0.05–0.09 (Pixar), noise bump, shadow visibility off.
  - Caruncle and plica: a small pink, SSS-heavy, high-gloss lump at the inner canthus, with roughness about 0.2 plus a wet coat. It is not covered by the sources found here.

### Gaps
- No source covered **lash shadows** specifically. In Cycles, real lash geometry (curves or cards) casts real shadows, so it needs no fake. In real-time engines the occlusion shell fakes it, and its top-lid gradient is the stand-in.
- The **caruncle and plica semilunaris** were not described in any source reached.

## 5. Cheap skin pores and micro detail in Blender

### Takeaway
The standard cheap approach is a **Voronoi texture (distorted by Noise) into a Bump node** in the Principled Normal. Alone it looks artificial ("leather" is closer than plain cells), so layer two or three scales and mask by face region.

### Cited Findings
- The basic chain is Voronoi into Bump Height into Principled Normal. Add a Noise texture into the Mapping vector to distort the Voronoi so the cells are not regular. — [ArtStation blog: procedural bark in Blender 5.1](https://jsabbott.artstation.com/blog/3ZXjq/how-do-you-create-a-procedural-tree-bark-material-in-blender-5-1) (same building blocks applied to bark)
- Real skin bump "is not just a simple noise bump", and looks more like a leather pattern. — [BlenderArtists: procedural skin texturing](https://blenderartists.org/t/procedural-skin-texturing/1167816)
- There is an Eevee procedural pore thread. Commercial procedural skin shaders (Easy Skin Shader, Procedural Skin Details) offer pores, freckles and micro-wrinkles as node groups. — [BlenderArtists: procedural skin pore texture in Eevee](https://blenderartists.org/t/procedural-skin-pore-texture-in-eevee/1289021); [Easy Skin Shader docs](https://www.blendermarket.com/products/easy-skin-shader/docs); [Procedural Skin Details](https://superhivemarket.com/products/procedural-skin-details)
- A baked normal map can be combined with procedural Voronoi or noise bump. — [BlenderArtists: mixing normal maps on procedural materials](https://blenderartists.org/t/mixing-normal-maps-on-procedural-materials/1388690)

### Inferences (scriptable recipe)
- **Pores:** Voronoi in F1 mode, Smooth F1 or Distance, with Scale set so cells are about 0.2–0.5 mm on the face (object or UV coordinates distorted by Noise at strength about 0.1–0.3). Pass it through a ColorRamp so only small dark pits remain, then into Bump (Strength 0.1–0.3, Distance about 0.0005 m).
- **Leather cross-hatching (micro-wrinkles):** two stretched Wave or Noise textures at ±45°, multiplied, into a second Bump chained via that Bump's Normal input.
- **Region mask:** pore strength high on the nose, cheeks and forehead, low on the lids and lips. Use a painted or UV-region mask, or vertex groups to an Attribute node.
- **Roughness variation:** feed the pore mask lightly into Roughness, so pits are rougher and oilier ridges are shinier. That gives the specular break-up that sells skin at portrait distance.
- **Eyelids:** keep the pores very low there. Lid skin is thin and smooth, and strong pores near the eyes compete with the eye detail.

### Gaps
- No primary source gave a verified pore recipe with exact values. The numbers above are starting points to test.
