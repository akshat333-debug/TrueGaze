# TrueGaze — agent rules (every team member's Claude reads this first)

Samsung PRISM XR Hackathon 2026, **Track 1: Synthetic Eyes**. Team Zero Drift (VIT Vellore).
Final submission **22 Nov 2026** via Google form; everything must be in this repo, made **public** before submitting.
Rules and rubric: `docs/hackathondetails.md`. Plan: `docs/PLAN.md`.

## Before any work
1. `git pull --rebase` on `main`.
2. Read `TASKS.md` (Next up + latest handoff note), then `DECISIONS.md`. Don't contradict a logged decision without a new entry.
3. Claim the task in `TASKS.md` (owner + `in progress`), commit and push the claim.

## While working
- Small branch per task, merged to `main` the same day. Never leave work unpushed overnight.
- **Licences:** this repo goes public. Never commit a head model, texture or scan whose licence forbids redistribution (FLAME does). Record every asset's source and licence in `docs/ASSETS.md` before committing it.
- Required outputs (all must exist; extras only after): 5–10 UV maps (face + distinct L/R iris), Python script with `Left` / `Right` / `Generate Motion` inputs rendering a video each (≤15 s), 5–10 renders with different textures, `.blend` with a timeline-animated expression.
- Every claim in the deck/README must be reproducible from a script in this repo.

## After every unit of work (same commit)
- Update `TASKS.md` with a handoff note (done / next / gotchas / how to run).
- New decision → `DECISIONS.md`. Plan changed → `docs/PLAN.md`.
- Commit message `<area>: <what>`. Push.
