# Deck outline (draft, 13 Nov; superseded by `tools/make_deck.py`, which follows the organizers' template)

Ten slides, ordered by the rubric: textures 60, kinematics 20, portability 20, brownie points. Every number below comes from a script in this repo; the slide names the script.

1. **Title.** TrueGaze: photoreal animated eyes on Google's GNM head. Team Zero Drift, VIT Vellore. Hero still (`outputs/renders/0N_hero.png`).
2. **The brief in one line, and our answer.** Eight texture sets with distinct left/right irises that wrap onto any GNM head; one command renders Left / Right / Generate Motion with physiologically timed eyes, lids, lashes and brows. Table: required output → where it is in the repo.
3. **Textures: eight people.** `docs/texture_sets.jpg` and `docs/hero_sets.jpg`. Light and dark skin, young to old, six eye colours. Left and right iris always differ.
4. **Textures: how the skin was made.** GNM ships no texture. MakeHuman's public-domain skins are fitted onto GNM in 3D: median fit error 0.5 mm, eyelid edges and lip line pinned (`tools/transfer_skin.py`). UV sheet from `uv_maps/`.
5. **Textures: the eye itself.** Iris fibres, collarette, furrows, freckles, limbal ring; refracting cornea; veined sclera; wet lid edge and tear line; about 7,500 hair strands (lashes, brows, facial down; `tools/make_hair.py` prints 7,458). Close-up crops.
6. **No seams, measured.** `tools/seam_audit.py`: 142 seam edges checked on every set, front-of-face colour step ≤ 6 of 255. The audit caught two real regressions during the build.
7. **Kinematics.** Table from `tools/evaluate_motion.py`: saccade duration, blink timing and rate, vergence, each against its published range. Direction check 5/5 from projected pupil positions (`wrapper/eyes.py`).
8. **Soft tissue (brownie points).** The eye sits in a socket; lids lift over the cornea (lifted up to 1.6 mm); skin near the lid drags up to 2.7 mm with the eye; lashes follow. Wire / clay / final strip (`docs/breakdown.jpg`), frames from the wireframe video.
9. **Portability and reproducibility.** Stock and random-identity GNM heads wearing our sets (`apply_textures.py`); textures named by GNM UDIM tile; `./reproduce.sh` rebuilds everything from a fresh clone; model and skin downloads pinned by SHA-256; `.blend` plays without script permissions.
10. **Honest limits and next steps.** No caustic light in the iris, no fleshy inner-corner tissue (GNM has none), upper lid does not fold into itself, one head shape for the videos. Licences: GNM Apache 2.0, MakeHuman CC0, everything else generated here.

Demo video (1–2 min): hero-view Generate Motion → front-view Left / Right / Generate Motion → wireframe version → eight sets → one terminal command running.
