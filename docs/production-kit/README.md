# Production Kit — Systems-Focus Workflow

A single-file web app that implements `Production_Kit.md` as an interactive,
per-video pipeline. No backend, no build step — open `index.html` in a browser.
Data is saved to your browser's `localStorage`.

## What it enforces (the safety model)

> "If the top half isn't complete, the video doesn't get made."

- **Part 0** — Source-Tier rubric (T1–T4) shown as collapsible reference.
- **Part 1** — Research / Defence File: working title, pillar, core mechanism,
  claims ledger (claim · tier · source · fact-vs-allegation), on-screen docs,
  denials, and the 6-point legal self-check.
- **Gating** — Parts 2 & 3 stay **locked** until Part 1 is complete. A **T4
  claim blocks the script** (T4 may only be used to *find* a T1–T3 source).
- **Part 2** — Script template (3 acts) generated from Part 1.
- **Part 3** — Pre-publish gate (7 checks). "Cleared for upload" only when the
  gate is fully ticked *and* Part 1 is complete.
- **Export** — produces a Markdown defence file mirroring the original template.

## Test it

- **Locally:** open `docs/production-kit/index.html` in any browser.
- **Live (GitHub Pages):** the workflow in `.github/workflows/pages.yml`
  publishes `docs/` to Pages. Enable it once at
  **Settings → Pages → Source: GitHub Actions**, then visit
  `https://<owner>.github.io/<repo>/production-kit/`.
