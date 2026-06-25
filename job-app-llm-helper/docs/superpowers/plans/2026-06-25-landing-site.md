# Landing Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a polished, low-maintenance static landing page for job-app-llm-helper that gives non-technical users an easy front door to both the "Use in Browser" and "Download the App" paths, with copy-to-clipboard for the paste blocks, deployed to Vercel.

**Architecture:** A single hand-authored `site/index.html` (inline CSS + vanilla JS) is the entire site. A stdlib-only `site/build_site.py` injects the canonical paste-block text from the `platform-guide/*.md` files into marker regions in the HTML; the rendered HTML is committed and served statically. A local pytest asserts the committed HTML matches the current markdown (drift guard).

**Tech Stack:** Plain HTML5 + CSS + vanilla JS; Python 3.11+ stdlib (`html`, `re`, `pathlib`) for the build script; pytest; Vercel static hosting.

## Global Constraints

- All paths below are relative to the project dir `job-app-llm-helper/` (git root is the parent `public_projects/`; remote `bkjsun_public_projects`).
- `build_site.py` is **stdlib only** — no third-party imports. It must pass `ruff check .` (config: `ruff.toml`, line-length 100, rules `E,F,W,I,B,S`).
- The rendered `site/index.html` is a **committed artifact**. Never hand-edit the text inside `<!-- INJECT:* -->` regions — edit the source `.md` and re-run `build_site.py`.
- Only THREE blocks are injected: `project-instructions`, `kickoff`, `interview-prep`. All other page prose (setup steps, tables, download steps) is authored directly in `index.html`.
- Brand palette (match the Flask app `templates/index.html`): `--bg:#f6f7f9; --card:#ffffff; --ink:#1c2230; --muted:#5b6472; --line:#e3e7ee; --accent:#2b6cb0; --accent-ink:#fff`.
- Run Python via `~/projects/venv/bin/python` locally; pytest via `./venv/bin/python -m pytest` (the project venv at `job-app-llm-helper/venv`).
- Markdown fence conventions (verified): `project-instructions.md` — content is everything **below the first `---` line**. `kickoff-template.md` and `interview-prep-template.md` — message body is the text **between the first and second `---` lines**.

---

### Task 1: Build script — extraction + injection logic

**Files:**
- Create: `site/build_site.py`
- Test: `tests/test_build_site.py`

**Interfaces:**
- Produces:
  - `extract_below_divider(md: str) -> str` — text after the first line equal to `---`, stripped.
  - `extract_message_body(md: str) -> str` — text between the first and second lines equal to `---`, stripped.
  - `render_block(text: str) -> str` — HTML-escaped text wrapped as `<pre class="paste-block">…</pre>`.
  - `inject(html: str, name: str, block_html: str) -> str` — replaces the content between `<!-- INJECT:name -->` and `<!-- /INJECT:name -->` (markers preserved), idempotent.
  - `build(project_dir: Path) -> str` — reads `site/index.html` + the three guides under `platform-guide/`, returns the fully rendered HTML string.
  - `main() -> None` — writes `build(...)` back to `site/index.html`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_build_site.py
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"
sys.path.insert(0, str(SITE))

import build_site as bs  # noqa: E402


def test_extract_below_divider():
    md = "# Title\n\nintro\n\n---\n\nreal body\nmore\n"
    assert bs.extract_below_divider(md) == "real body\nmore"


def test_extract_message_body():
    md = "# Title\n\ntip\n\n---\n\nbody line 1\nbody line 2\n\n---\n\n## Tips\n- x\n"
    assert bs.extract_message_body(md) == "body line 1\nbody line 2"


def test_render_block_escapes():
    out = bs.render_block('a < b & "c"')
    assert "&lt;" in out and "&amp;" in out and "&quot;" in out
    assert out.startswith('<pre class="paste-block">')
    assert out.endswith("</pre>")


def test_inject_replaces_region_and_is_idempotent():
    html = "X<!-- INJECT:foo -->OLD<!-- /INJECT:foo -->Y"
    once = bs.inject(html, "foo", "NEW")
    assert once == "X<!-- INJECT:foo -->NEW<!-- /INJECT:foo -->Y"
    twice = bs.inject(once, "foo", "NEW")
    assert twice == once
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `./venv/bin/python -m pytest tests/test_build_site.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'build_site'` (file not created yet).

- [ ] **Step 3: Write the build script**

```python
# site/build_site.py
"""Render site/index.html by injecting canonical paste-blocks from platform-guide/*.md.

Stdlib only. Run after editing any of the three source guides:
    python site/build_site.py
The rendered index.html is committed; do not hand-edit the INJECT regions.
"""

from __future__ import annotations

import html as html_mod
import re
from pathlib import Path

# (source markdown filename, marker name, extractor function name)
BLOCKS = [
    ("project-instructions.md", "project-instructions", "below_divider"),
    ("kickoff-template.md", "kickoff", "message_body"),
    ("interview-prep-template.md", "interview-prep", "message_body"),
]


def extract_below_divider(md: str) -> str:
    """Return everything after the first line that is exactly '---', stripped."""
    lines = md.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "---":
            return "\n".join(lines[i + 1 :]).strip()
    raise ValueError("no '---' divider found")


def extract_message_body(md: str) -> str:
    """Return the text between the first and second lines that are exactly '---'."""
    idx = [i for i, line in enumerate(md.splitlines()) if line.strip() == "---"]
    if len(idx) < 2:
        raise ValueError("expected two '---' fences")
    lines = md.splitlines()
    return "\n".join(lines[idx[0] + 1 : idx[1]]).strip()


def render_block(text: str) -> str:
    """Wrap escaped text in a <pre> the copy JS reads via innerText."""
    return f'<pre class="paste-block">{html_mod.escape(text)}</pre>'


def inject(html: str, name: str, block_html: str) -> str:
    """Replace the content between the named INJECT markers; idempotent."""
    pattern = re.compile(
        rf"(<!-- INJECT:{re.escape(name)} -->).*?(<!-- /INJECT:{re.escape(name)} -->)",
        re.DOTALL,
    )
    if not pattern.search(html):
        raise ValueError(f"marker for {name!r} not found in index.html")
    return pattern.sub(rf"\g<1>{block_html}\g<2>", html, count=1)


_EXTRACTORS = {
    "below_divider": extract_below_divider,
    "message_body": extract_message_body,
}


def build(project_dir: Path) -> str:
    """Read index.html + the three guides, return rendered HTML."""
    html = (project_dir / "site" / "index.html").read_text(encoding="utf-8")
    guide_dir = project_dir / "platform-guide"
    for filename, name, extractor in BLOCKS:
        md = (guide_dir / filename).read_text(encoding="utf-8")
        text = _EXTRACTORS[extractor](md)
        html = inject(html, name, render_block(text))
    return html


def main() -> None:
    project_dir = Path(__file__).resolve().parent.parent
    (project_dir / "site" / "index.html").write_text(build(project_dir), encoding="utf-8")
    print("rendered site/index.html")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `./venv/bin/python -m pytest tests/test_build_site.py -v`
Expected: PASS (4 passed). The `build`/`main` paths are exercised in Task 3.

- [ ] **Step 5: Lint**

Run: `ruff check site/build_site.py tests/test_build_site.py`
Expected: no errors (the `# noqa: E402` on the import keeps the path-insert pattern clean).

- [ ] **Step 6: Commit**

```bash
git add job-app-llm-helper/site/build_site.py job-app-llm-helper/tests/test_build_site.py
git commit -m "feat(site): markdown block extraction + injection for landing page"
```

---

### Task 2: Author `site/index.html`

**Files:**
- Create: `site/index.html`

**Interfaces:**
- Consumes: nothing (static authoring). Must contain the three marker pairs `<!-- INJECT:project-instructions -->…<!-- /INJECT:project-instructions -->`, `<!-- INJECT:kickoff -->…<!-- /INJECT:kickoff -->`, `<!-- INJECT:interview-prep -->…<!-- /INJECT:interview-prep -->` (regions may start empty).
- Produces: the page Task 3 injects into and the deploy serves.

> Source content to transcribe: free-vs-paid table from `README.md` (the "Free vs paid" table); setup steps from `platform-guide/setup-claude.md`, `setup-chatgpt.md`, `setup-gemini.md`; download steps from the `README.md` "Download the app" section. The GitHub repo URL is `https://github.com/jasonjames81/bkjsun_public_projects/tree/main/job-app-llm-helper`.

- [ ] **Step 1: Create the full page**

Create `site/index.html` with this complete content:

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Job App LLM Helper — write better cover letters with AI</title>
<meta name="description" content="Set up an AI job-application assistant in your browser, or run it locally. Free.">
<style>
  :root {
    --bg:#f6f7f9; --card:#ffffff; --ink:#1c2230; --muted:#5b6472;
    --line:#e3e7ee; --accent:#2b6cb0; --accent-ink:#fff; --radius:12px;
  }
  * { box-sizing: border-box; }
  body {
    margin:0; background:var(--bg); color:var(--ink);
    font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  }
  a { color:var(--accent); }
  .wrap { max-width:860px; margin:0 auto; padding:0 20px; }
  header.hero { text-align:center; padding:64px 20px 40px; }
  header.hero h1 { font-size:2.2rem; margin:0 0 12px; }
  header.hero p { font-size:1.15rem; color:var(--muted); max-width:620px; margin:0 auto 28px; }
  .cta { display:inline-flex; gap:12px; flex-wrap:wrap; justify-content:center; }
  .btn {
    display:inline-block; padding:12px 22px; border-radius:var(--radius);
    background:var(--accent); color:var(--accent-ink); text-decoration:none; font-weight:600;
  }
  .btn.secondary { background:var(--card); color:var(--accent); border:1px solid var(--line); }
  section { padding:36px 0; border-top:1px solid var(--line); }
  section h2 { font-size:1.6rem; margin:0 0 8px; }
  .lead { color:var(--muted); margin:0 0 20px; }
  .card { background:var(--card); border:1px solid var(--line); border-radius:var(--radius); padding:20px; margin:16px 0; }
  table { width:100%; border-collapse:collapse; margin:12px 0; }
  th,td { text-align:left; padding:8px 10px; border-bottom:1px solid var(--line); font-size:.95rem; }
  th { color:var(--muted); font-weight:600; }
  ol { padding-left:20px; }
  ol li { margin:6px 0; }
  .tabs { display:flex; gap:8px; margin:8px 0 0; flex-wrap:wrap; }
  .tab {
    padding:8px 16px; border:1px solid var(--line); border-radius:999px;
    background:var(--card); cursor:pointer; font-weight:600; color:var(--muted);
  }
  .tab[aria-selected="true"] { background:var(--accent); color:var(--accent-ink); border-color:var(--accent); }
  .panel { display:none; }
  .panel.active { display:block; }
  .copy-row { display:flex; align-items:center; gap:10px; margin:18px 0 6px; }
  .copy-row h3 { margin:0; font-size:1.05rem; }
  .copy-btn {
    margin-left:auto; padding:6px 14px; border:1px solid var(--accent); border-radius:8px;
    background:var(--accent); color:var(--accent-ink); cursor:pointer; font-weight:600; font-size:.9rem;
  }
  .copy-btn.done { background:#1f7a4d; border-color:#1f7a4d; }
  pre.paste-block {
    background:#0f1729; color:#e6edf7; border-radius:var(--radius); padding:14px;
    max-height:240px; overflow:auto; white-space:pre-wrap; word-break:break-word; font-size:.85rem;
  }
  footer { text-align:center; color:var(--muted); padding:32px 0 56px; font-size:.9rem; }
  @media (max-width:560px){ header.hero h1{font-size:1.7rem;} }
</style>
</head>
<body>
<header class="hero">
  <div class="wrap">
    <h1>Job App LLM Helper</h1>
    <p>Write sharper cover letters, answer application questions, and prep for interviews —
       with an AI assistant that sounds like <em>you</em>. Free to set up.</p>
    <div class="cta">
      <a class="btn" href="#browser">Use in your browser</a>
      <a class="btn secondary" href="#download">Download the app</a>
    </div>
  </div>
</header>

<main class="wrap">

<section id="browser">
  <h2>Use it in your browser</h2>
  <p class="lead">No install, no API key. Set up a reusable assistant in Claude, ChatGPT,
     or Gemini using your resume and writing samples — it builds a voice fingerprint from them.</p>

  <div class="card">
    <table>
      <thead><tr><th></th><th>Claude</th><th>ChatGPT</th><th>Gemini</th></tr></thead>
      <tbody>
        <tr><td>Free tier</td><td>Yes (5 projects, Sonnet)</td><td>Yes (5 files/project)</td><td>Yes (Notebooks)</td></tr>
        <tr><td>Paid</td><td>Pro $20/mo</td><td>Plus $20/mo</td><td>Advanced $20/mo</td></tr>
        <tr><td>Best for</td><td>Nuanced voice matching</td><td>Fastest iteration</td><td>Google ecosystem</td></tr>
      </tbody>
    </table>
  </div>

  <h3>1. Pick your platform &amp; set up the project</h3>
  <div class="tabs" role="tablist">
    <button class="tab" role="tab" aria-selected="true" data-tab="claude">Claude</button>
    <button class="tab" role="tab" aria-selected="false" data-tab="chatgpt">ChatGPT</button>
    <button class="tab" role="tab" aria-selected="false" data-tab="gemini">Gemini</button>
  </div>

  <div class="panel active" data-panel="claude">
    <ol>
      <li>Go to <a href="https://claude.ai">claude.ai</a> and log in.</li>
      <li>Click <strong>Projects</strong> &rarr; <strong>New Project</strong>; name it "Job Applications".</li>
      <li>Under <strong>Files</strong>, upload your resume, 2–4 writing samples, and (optional) your LinkedIn PDF.</li>
      <li>Under <strong>Project Instructions</strong>, paste the block below.</li>
      <li>Start a new chat and paste the Kickoff (or Interview-Prep) message below.</li>
    </ol>
  </div>
  <div class="panel" data-panel="chatgpt">
    <ol>
      <li>Go to <a href="https://chatgpt.com">chatgpt.com</a> and log in.</li>
      <li>Click <strong>Projects</strong> &rarr; <strong>New project</strong>; name it "Job Applications".</li>
      <li>Click <strong>Add files</strong> and upload your resume, 2–4 writing samples, and (optional) LinkedIn PDF.</li>
      <li>Under <strong>Project instructions</strong>, paste the block below.</li>
      <li>Start a new chat and paste the Kickoff (or Interview-Prep) message below.</li>
    </ol>
  </div>
  <div class="panel" data-panel="gemini">
    <ol>
      <li>Go to <a href="https://gemini.google.com">gemini.google.com</a> and log in.</li>
      <li>Click <strong>Notebooks</strong> &rarr; <strong>Create Notebook</strong>; name it "Job Applications".</li>
      <li>Upload your resume, 2–4 writing samples, and (optional) LinkedIn PDF as <strong>Sources</strong>.</li>
      <li>Open the <strong>⋮</strong> menu (top-right) &rarr; <strong>Notebook settings</strong> &rarr; <strong>Instructions</strong>, and paste the block below.</li>
      <li>Start a new chat in the notebook and paste the Kickoff (or Interview-Prep) message below.</li>
    </ol>
  </div>

  <div class="copy-row">
    <h3>2. Project Instructions</h3>
    <button class="copy-btn" data-copy="pi">Copy</button>
  </div>
  <div id="pi"><!-- INJECT:project-instructions --><!-- /INJECT:project-instructions --></div>

  <div class="copy-row">
    <h3>3. Kickoff message (new application)</h3>
    <button class="copy-btn" data-copy="kickoff">Copy</button>
  </div>
  <div id="kickoff"><!-- INJECT:kickoff --><!-- /INJECT:kickoff --></div>

  <div class="copy-row">
    <h3>Interview-prep message (role you applied to elsewhere)</h3>
    <button class="copy-btn" data-copy="iprep">Copy</button>
  </div>
  <div id="iprep"><!-- INJECT:interview-prep --><!-- /INJECT:interview-prep --></div>
</section>

<section id="download">
  <h2>Download the app</h2>
  <p class="lead">Prefer everything on your own machine? Run the self-hosted app with your own
     API key, a logged-in CLI, or a local Ollama model. Your data never leaves your computer.</p>
  <div class="card">
    <ol>
      <li><a href="https://github.com/jasonjames81/bkjsun_public_projects/tree/main/job-app-llm-helper">Download the project from GitHub</a> (green <strong>Code</strong> button &rarr; Download ZIP, then unzip).</li>
      <li>Run the start script for your OS: <code>start-mac.command</code> (macOS), <code>start-windows.bat</code> (Windows), or <code>start.sh</code> (Linux). It opens the app in your browser.</li>
      <li>Click <strong>Connect an LLM</strong> and choose an API key, CLI login, or local Ollama model.</li>
    </ol>
  </div>
</section>

</main>

<footer>
  <div class="wrap">
    <a href="https://github.com/jasonjames81/bkjsun_public_projects/tree/main/job-app-llm-helper">View on GitHub</a> · MIT License
  </div>
</footer>

<script>
  // Platform tabs
  document.querySelectorAll('.tab').forEach(function (tab) {
    tab.addEventListener('click', function () {
      var name = tab.getAttribute('data-tab');
      document.querySelectorAll('.tab').forEach(function (t) {
        t.setAttribute('aria-selected', t === tab ? 'true' : 'false');
      });
      document.querySelectorAll('.panel').forEach(function (p) {
        p.classList.toggle('active', p.getAttribute('data-panel') === name);
      });
    });
  });
  // Copy buttons
  document.querySelectorAll('.copy-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var target = document.getElementById(btn.getAttribute('data-copy'));
      var pre = target && target.querySelector('pre.paste-block');
      if (!pre) return;
      navigator.clipboard.writeText(pre.innerText).then(function () {
        var label = btn.textContent;
        btn.textContent = 'Copied ✓';
        btn.classList.add('done');
        setTimeout(function () { btn.textContent = label; btn.classList.remove('done'); }, 1600);
      });
    });
  });
</script>
</body>
</html>
```

- [ ] **Step 2: Verify markers are present**

Run: `grep -c "INJECT:" site/index.html`
Expected: `6` (three open + three close markers).

- [ ] **Step 3: Commit**

```bash
git add job-app-llm-helper/site/index.html
git commit -m "feat(site): author landing page (hero, browser tabs, download, copy buttons)"
```

---

### Task 3: Render blocks + drift guard test

**Files:**
- Modify: `site/index.html` (populated by the build script)
- Modify: `tests/test_build_site.py` (add drift test)

**Interfaces:**
- Consumes: `build_site.build(project_dir)` and the marker regions from Task 2.

- [ ] **Step 1: Add the drift test**

Append to `tests/test_build_site.py`:

```python
def test_committed_index_html_is_current():
    """The committed index.html must equal a fresh build from the source markdown."""
    project_dir = SITE.parent
    current = (SITE / "index.html").read_text(encoding="utf-8")
    assert bs.build(project_dir) == current, (
        "site/index.html is stale — run `python site/build_site.py` and commit the result"
    )
```

- [ ] **Step 2: Run the drift test to verify it fails**

Run: `./venv/bin/python -m pytest tests/test_build_site.py::test_committed_index_html_is_current -v`
Expected: FAIL — the marker regions are still empty, so `build()` output differs from the committed (empty) HTML.

- [ ] **Step 3: Run the build script**

Run: `~/projects/venv/bin/python site/build_site.py`
Expected: prints `rendered site/index.html`; the three `<div id="…">` regions now contain `<pre class="paste-block">` elements with the guide text.

- [ ] **Step 4: Run the full suite to verify it passes**

Run: `./venv/bin/python -m pytest tests/ -v`
Expected: PASS — all prior tests plus `test_committed_index_html_is_current` now green.

- [ ] **Step 5: Manual browser check**

Open `site/index.html` in a browser. Verify: the three platform tabs switch panels; each of the three Copy buttons flips to "Copied ✓" and places the correct full text on the clipboard; the layout holds when the window is narrowed to phone width.

- [ ] **Step 6: Commit**

```bash
git add job-app-llm-helper/site/index.html job-app-llm-helper/tests/test_build_site.py
git commit -m "feat(site): render paste-blocks + add drift guard test"
```

---

### Task 4: Vercel config, deploy, and README pointer

**Files:**
- Create: `site/vercel.json`
- Modify: `README.md` (add live URL — after deploy)

**Interfaces:**
- Consumes: the committed `site/` directory.

- [ ] **Step 1: Add minimal Vercel config**

Create `site/vercel.json`:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "cleanUrls": true
}
```

- [ ] **Step 2: Commit the config**

```bash
git add job-app-llm-helper/site/vercel.json
git commit -m "chore(site): add vercel static config"
git push
```

- [ ] **Step 3: Create the Vercel project (manual — user action)**

In the Vercel dashboard: **Add New… → Project → import `bkjsun_public_projects`**. Set **Root Directory** to `job-app-llm-helper/site`, **Framework Preset** to "Other", leave the build command empty (static). Deploy. Note the resulting `*.vercel.app` URL.

> This step needs the user's Vercel account; the agent cannot complete it. Pause and hand off the URL.

- [ ] **Step 4: Add the live URL to the README**

Once the URL is known, insert a line directly under the H1 in `README.md`:

```markdown
> 🌐 **New here? Start at the friendly setup page → <LIVE_URL>**
```

(Replace `<LIVE_URL>` with the real deployment URL.)

- [ ] **Step 5: Commit**

```bash
git add job-app-llm-helper/README.md
git commit -m "docs: link landing site from README"
git push
```

---

## Notes / Out of Scope

- **GitHub CI does not currently run** on this repo: the workflow lives at `job-app-llm-helper/.github/workflows/ci.yml`, but GitHub only executes workflows under the **repo-root** `.github/`. The drift test therefore runs locally via `pytest tests/`. Activating CI on GitHub (moving/duplicating the workflow to repo root with a `working-directory` default) is a separate, optional task — out of scope here.
- No custom domain in this plan; add later via Vercel if desired.
- `build_site.py` is run manually after editing the source guides — there is no auto-build on deploy (intentional: keeps Vercel a pure static serve with nothing to break).

## Self-Review

- **Spec coverage:** front door + two-path layout (Task 2), copy buttons (Tasks 2–3), markdown-injection drift control (Tasks 1, 3), pytest drift test (Task 3), Vercel deploy + README URL (Task 4), palette reuse + responsive (Task 2). All spec sections mapped.
- **Placeholder scan:** none — full code given for build script, tests, and HTML. `<LIVE_URL>` in Task 4 is a genuine runtime value the user supplies post-deploy, flagged explicitly.
- **Type consistency:** `extract_below_divider` / `extract_message_body` / `render_block` / `inject` / `build` / `main` names and signatures match across Tasks 1 and 3; marker names (`project-instructions`, `kickoff`, `interview-prep`) and DOM ids (`pi`, `kickoff`, `iprep`) are consistent between the HTML (Task 2) and the build mapping (Task 1).
