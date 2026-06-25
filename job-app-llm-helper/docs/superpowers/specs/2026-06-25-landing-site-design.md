# Landing Site — Design Spec

**Date:** 2026-06-25
**Status:** Approved (design), pending implementation plan

## Problem

The project lives on a public GitHub repo. Non-technical users — the target
audience — land on the code-tree repo page, feel intimidated, and bounce before
they reach the setup guides. We want a polished, friendly, shareable front door
(LinkedIn / Reddit / forums / friends) that walks a newcomer into either the
**Use in Browser** path or the **Download the App** path, with guided
copy-to-clipboard for the long paste blocks.

## Goals

- A single shareable URL that does not read as "GitHub" to a nervous user.
- Easy navigation for both usage paths (browser-based projects, self-hosted app).
- Copy-to-clipboard buttons for the project-instructions, kickoff, and
  interview-prep paste blocks.
- **Low maintenance**: no framework, no dependency rot, no build server. The
  content freezes after a few more debug runs.

## Non-Goals (YAGNI)

- No search, analytics, CMS, multi-page router, or SSG framework.
- No backend. The site is fully static.
- No redesign of the self-hosted Flask app UI (`templates/index.html`).

## Architecture

A new `site/` directory in the repo:

- **`site/index.html`** — the entire page. Inline `<style>` and a small inline
  `<script>` (vanilla JS, ~50 lines) for platform-tab switching and
  copy-to-clipboard. Zero external dependencies, zero build output to serve.
- **`site/build_site.py`** — a local generator (~40-60 lines, stdlib only,
  runs under `~/projects/venv` or system python). Reads the canonical markdown
  and injects the current paste-block text into `index.html` between marker
  comments. Run manually whenever the source markdown changes; the **rendered
  `index.html` is committed** and is what Vercel serves.
- **`vercel.json`** — static hosting config. Root output = `site/`, no build
  command (Vercel just serves the committed HTML).

Rationale: a single hand-authored HTML file has nothing to rot (contrast Astro
Starlight's `node_modules` + the Node-22 deploy issues seen on my-wiki). The
only sync risk — the paste blocks drifting from what the repo/app ships — is
handled by `build_site.py` + a CI drift test, not by a runtime framework.

## Page Layout

Single scrolling page with anchor navigation.

1. **Hero** — project title, one-line pitch, two large buttons:
   *Use in Browser* and *Download the App*, each scrolling to its section.
2. **Use in Browser** —
   - Short intro paragraph.
   - Free-vs-paid comparison table (sourced from `README.md`).
   - **Platform tabs**: Claude / ChatGPT / Gemini. Each tab shows that
     platform's numbered setup steps (sourced from
     `platform-guide/setup-{claude,chatgpt,gemini}.md`).
   - Three **copy buttons**, each showing the block and a "Copy" control that
     flips to "Copied ✓" on click:
     - Project Instructions (the content below the divider in
       `platform-guide/project-instructions.md`)
     - Kickoff Message (`platform-guide/kickoff-template.md`)
     - Interview-Prep Message (`platform-guide/interview-prep-template.md`)
3. **Download the App** — concise steps (download → run start script → connect
   an LLM), the privacy note, and links to the GitHub repo + releases.
4. **Footer** — GitHub repo link, license.

Styling reuses the app's existing palette (`--accent: #2b6cb0`, etc. from
`templates/index.html`) so the site and app read as one product. Layout is
mobile-responsive with large touch targets.

## Content Injection (drift control)

`build_site.py` is the single bridge between canonical markdown and the site:

- `index.html` contains marker pairs, e.g.
  `<!-- INJECT:project-instructions -->` … `<!-- /INJECT:project-instructions -->`.
- For each marker, the script reads the corresponding source:
  - `project-instructions` → everything **below the `---` divider** in
    `platform-guide/project-instructions.md`.
  - `kickoff` → the message body of `platform-guide/kickoff-template.md`
    (the text between the first `---` and the trailing `## Tips`).
  - `interview-prep` → the message body of
    `platform-guide/interview-prep-template.md` (same fence convention).
- The extracted text is HTML-escaped and written into the injection region in a
  form the copy JS reads (a hidden `<textarea>` or `data-` attribute paired with
  a visible `<pre>` preview).
- The script is idempotent: re-running replaces the region between markers, never
  appends.

Markdown stays canonical for content; the rendered HTML is the committed
artifact. Setup-step prose in each tab is authored directly in `index.html`
(short, stable) — only the three machine-pasted blocks are injected, because
those must match the repo/app exactly.

## Testing

- **pytest** (in existing `tests/`, run by `ci.yml`): execute `build_site.py`
  against the repo, then assert each injected block in `index.html` equals the
  text extracted from its source markdown. CI fails if the committed HTML has
  drifted from the markdown (i.e. someone edited a `.md` without re-running the
  build).
- **Manual**: open `site/index.html` in a browser; verify platform tabs switch,
  all three copy buttons place correct text on the clipboard and show
  "Copied ✓", and the layout holds at mobile width.

## Deploy

- New Vercel project pointing at the repo, root directory `site/`, framework
  "Other", no build command (serves the committed static files).
- After first deploy, add the live URL to the top of `README.md` and optionally
  point the setup-guide links at the site.
- Custom domain optional, later.

## Files Touched

- New: `site/index.html`, `site/build_site.py`, `vercel.json`,
  `tests/test_build_site.py`.
- Edited (post-deploy): `README.md` (add live URL).
