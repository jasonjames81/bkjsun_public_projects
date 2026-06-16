# Browser-Chat Handoff ("Browser AI") Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a keyless "Browser AI" provider that does all deterministic work locally and emits one self-contained, interactive prompt the user pastes into their own logged-in chat tab (claude.ai, ChatGPT, etc.).

**Architecture:** A new pure module `handoff.py` assembles the prompt from already-parsed materials. A new provider id `browser_chat` (kind `"manual"`) appears in the existing select box but never routes through `call_llm` — the app branches earlier into a new `POST /build-handoff-prompt` route. `.docx` capture reuses the existing provider-independent `/download-docx` via an optional paste-back box. No new dependency, no browser automation.

**Tech Stack:** Python 3 / Flask, vanilla JS single-page UI, pytest. Reuses `profile.py` (profile/voice/contact blocks), `sources.py` (parsing/crawl — already done upstream of this feature), `docx_writer.py` (paste-back).

---

## File Structure

- `handoff.py` — **new.** Pure prompt packager. No network/subprocess/filesystem I/O. One public function `build_handoff_prompt(...)` plus private section helpers and the AI-tells pattern list.
- `providers/base.py` — **modify.** Document `"manual"` as a valid `ProviderInfo.kind` (comment only; `kind` is a free `str`).
- `providers/detect.py` — **modify.** Append a `browser_chat` `ProviderInfo` (always `available=True`).
- `providers/registry.py` — **modify.** `get_provider("browser_chat")` raises `ProviderError` (safety net); `list_models` returns `[]` for it (already the default branch — add a test).
- `app.py` — **modify.** New `POST /build-handoff-prompt` route; reuse existing `/download-docx`.
- `templates/index.html` — **modify.** Provider branch (button relabel + hide key/model rows), build panel (prompt box, copy, 1→2→3, sample controls, size readout, paste-back box).
- `tests/test_handoff.py` — **new.** Pure unit tests for `handoff.build_handoff_prompt` + the registry guard.
- `tests/test_smoke.py` — **modify.** Add route tests for `/build-handoff-prompt` and a `detect_providers` assertion for `browser_chat`.
- `docs/provider-roadmap.md` — **modify.** Mark §B guided-manual implemented; note interactive-handoff refinement.

---

## Task 1: The prompt packager — `handoff.py`

**Files:**
- Create: `handoff.py`
- Test: `tests/test_handoff.py`

Design notes (read before coding):
- The function is **pure**: caller passes already-parsed strings + a pre-split list of samples. No I/O here.
- Per-section caps mirror existing snippet caps in `generator.py` (`text[:6000]`): job text cap **8000**, org text cap **6000**, each sample cap = `sample_chars`.
- `samples` arrives already split into chunks by the caller; `build_handoff_prompt` takes the first `num_samples`, caps each to `sample_chars`. If `samples` is empty, the samples block is omitted (no error).
- AI-tells list is a module-level constant so the test can assert specific phrases.

- [ ] **Step 1: Write the failing test**

Create `tests/test_handoff.py`:

```python
"""Pure unit tests for the browser-chat handoff prompt packager (no network)."""

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

import handoff  # noqa: E402

PROFILE = {
    "applicant_name": "Ada Lovelace",
    "contact": {"name": "Ada Lovelace", "email": "ada@example.com"},
    "background": "Mathematician. Wrote the first published algorithm for a machine.",
    "writing_samples": "",
}


def _build(**overrides):
    kwargs = dict(
        profile=PROFILE,
        job_title="Research Engineer",
        org_name="Analytical Engines Ltd",
        job_description="Build numerical methods for the Analytical Engine.",
        org_about="We advance mechanical computation for the public good.",
        samples=[],
        sample_chars=2000,
        num_samples=3,
    )
    kwargs.update(overrides)
    return handoff.build_handoff_prompt(**kwargs)


def test_prompt_includes_core_materials():
    out = _build()
    assert "Research Engineer" in out
    assert "Analytical Engines Ltd" in out
    assert "Build numerical methods" in out
    assert "advance mechanical computation" in out
    assert "Ada Lovelace" in out


def test_prompt_includes_interactive_steps():
    out = _build()
    # the 8-step interactive instruction block
    assert "one at a time" in out.lower()
    assert "fit" in out.lower()
    assert "clarifying question" in out.lower()
    assert "draft" in out.lower()
    assert "interview" in out.lower()


def test_prompt_includes_ai_tells_review():
    out = _build()
    assert "AI" in out  # AI-tells rewrite step present
    # a couple of representative blacklist phrases must be named for the chat to catch
    assert "I am excited to" in out
    assert "leverage" in out


def test_prompt_includes_optional_coverage_review():
    out = _build()
    assert "key requirement" in out.lower() or "key point" in out.lower()
    assert "gap" in out.lower()


def test_samples_respect_count_and_length():
    samples = ["A" * 5000, "B" * 5000, "C" * 5000, "D" * 5000]
    out = _build(samples=samples, num_samples=2, sample_chars=100)
    assert "A" * 100 in out
    assert "B" * 100 in out
    assert "C" * 100 not in out  # 3rd sample dropped (num_samples=2)
    assert "A" * 101 not in out  # capped at sample_chars


def test_no_samples_omits_voice_samples_block_without_error():
    out = _build(samples=[])
    assert "WRITING SAMPLE" not in out.upper()


def test_empty_org_emits_ask_user_fallback():
    out = _build(org_about="")
    assert "paste" in out.lower()  # tells chat to ask user to paste About text


def test_caps_bound_oversized_job_and_org():
    out = _build(
        job_description="J" * 20000,
        org_about="O" * 20000,
    )
    assert "J" * 8000 in out
    assert "J" * 8001 not in out
    assert "O" * 6000 in out
    assert "O" * 6001 not in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /home/jsun/public_projects/job-app-llm-helper && python -m pytest tests/test_handoff.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'handoff'`.

- [ ] **Step 3: Write minimal implementation**

Create `handoff.py`:

```python
"""Browser-chat handoff: assemble one self-contained, interactive prompt the user
pastes into their own logged-in chat tab (claude.ai, ChatGPT, etc.).

Pure module — no network, subprocess, or filesystem I/O. The caller supplies the
already-parsed materials (sources.py / regex / profile blocks have run upstream).
This keeps the keyless path and the provider path from drifting on context format.
"""

from __future__ import annotations

import profile as profile_mod

# Per-section caps mirror generator.py's snippet cap (text[:6000]); keep the prompt
# bounded no matter how large the pasted inputs are.
_JOB_CAP = 8000
_ORG_CAP = 6000

# AI-tells the chat must catch and rewrite in step 5. Named explicitly so the chat
# has concrete targets rather than a vague "sound human" instruction.
_AI_TELLS = [
    'generic openers like "I am writing to express my interest"',
    '"I am excited to"',
    '"leverage"',
    '"passionate about"',
    '"in today\'s fast-paced world"',
    '"hollow superlatives" (world-class, cutting-edge, seamless)',
    "em-dash overuse and tidy three-part lists",
]

_STEPS = """\
Work through these steps one at a time. After each step, stop and wait for my reply
before moving to the next:

1. Confirm you understand my background and the role (one short paragraph).
2. Give a brief fit assessment: where I match the role and where I am light.
3. Ask me any clarifying questions you need before drafting.
4. Draft the cover letter (about one page, four paragraphs, plain prose).
5. AI-TELLS REWRITE: review your own draft for phrasing that reads machine-generated
   and rewrite it into plain, specific language. Watch especially for:
{ai_tells}
6. Give résumé-tailoring tips and interview-prep talking points grounded only in my
   real background above.
7. Refine the letter on my request.
8. OPTIONAL COVERAGE REVIEW: ask whether I want a final check. If I say yes, list the
   job posting's key requirements and show how the letter addresses each, flagging any
   gaps."""


def _cap(text: str, limit: int) -> str:
    text = (text or "").strip()
    return text[:limit]


def _samples_block(samples: list[str], num_samples: int, sample_chars: int) -> str:
    chosen = [(s or "").strip()[:sample_chars] for s in (samples or [])[:num_samples]]
    chosen = [s for s in chosen if s]
    if not chosen:
        return ""
    parts = ["=== MY WRITING SAMPLES (match this voice) ==="]
    for i, s in enumerate(chosen, 1):
        parts.append(f"\n--- WRITING SAMPLE {i} ---\n{s}")
    return "\n".join(parts)


def _org_block(org_name: str, org_about: str) -> str:
    cleaned = _cap(org_about, _ORG_CAP)
    if not cleaned:
        return (
            f"=== EMPLOYER: {org_name} ===\n"
            "No website text was captured. Ask me to paste the organization's About / "
            "mission text, or proceed without it if I prefer."
        )
    return (
        f"=== EMPLOYER: {org_name} ===\n"
        "Below is raw text crawled from the employer's website. Use it to infer their "
        "mission, values, and any recent news, and weave relevant points into the "
        "letter. It is raw — ignore navigation and boilerplate.\n\n"
        f"{cleaned}"
    )


def build_handoff_prompt(
    profile: dict,
    job_title: str,
    org_name: str,
    job_description: str,
    org_about: str,
    samples: list[str],
    *,
    sample_chars: int,
    num_samples: int,
) -> str:
    """Assemble one interactive prompt the user pastes into their own chat tab.

    ``samples`` is a pre-split list of writing-sample chunks; the first
    ``num_samples`` are used, each capped to ``sample_chars`` characters.
    """
    name = profile_mod.applicant_name(profile)
    profile_block = profile_mod.build_profile_summary(profile)
    voice_block = profile_mod.build_voice_fingerprint(profile)
    samples_block = _samples_block(samples, num_samples, sample_chars)
    steps = _STEPS.format(ai_tells="\n".join(f"   - {t}" for t in _AI_TELLS))

    sections = [
        f"You are helping me tailor a job application. I am {name}. {steps}",
        profile_block,
    ]
    if samples_block:
        sections.append(samples_block)
    sections.append(voice_block)
    sections.append(
        f"=== TARGET ROLE ===\nJob Title: {job_title}\nOrganization: {org_name}\n\n"
        f"Job Description:\n{_cap(job_description, _JOB_CAP)}"
    )
    sections.append(_org_block(org_name, org_about))
    return "\n\n".join(s for s in sections if s.strip())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /home/jsun/public_projects/job-app-llm-helper && python -m pytest tests/test_handoff.py -v`
Expected: PASS (8 tests).

Note: `test_prompt_includes_ai_tells_review` asserts `"leverage"` and `"I am excited to"` — both are in `_AI_TELLS`. `test_no_samples_omits_voice_samples_block_without_error` asserts `"WRITING SAMPLE"` absent — the samples block (the only place that string appears) is skipped when empty; `build_voice_fingerprint` with no samples emits "VOICE GUIDANCE", not "WRITING SAMPLE".

- [ ] **Step 5: Lint**

Run: `cd /home/jsun/public_projects/job-app-llm-helper && ruff check handoff.py tests/test_handoff.py && ruff format handoff.py tests/test_handoff.py`
Expected: no errors.

- [ ] **Step 6: Commit**

```bash
cd /home/jsun/public_projects/job-app-llm-helper
git add handoff.py tests/test_handoff.py
git commit -m "feat(handoff): pure browser-chat prompt packager

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Provider detection + registry guard

**Files:**
- Modify: `providers/base.py:26` (the `kind` field comment)
- Modify: `providers/detect.py` (append `browser_chat` entry)
- Modify: `providers/registry.py:29-57` (`get_provider` guard)
- Test: `tests/test_handoff.py` (registry guard), `tests/test_smoke.py` (detect entry)

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_handoff.py`:

```python
import pytest  # noqa: E402

from providers.base import ProviderError  # noqa: E402
from providers.config import ProviderConfig  # noqa: E402
from providers.detect import detect_providers  # noqa: E402
from providers.registry import get_provider, list_models  # noqa: E402


def test_browser_chat_is_detected_and_available():
    infos = {i.name: i for i in detect_providers(ProviderConfig())}
    assert "browser_chat" in infos
    bc = infos["browser_chat"]
    assert bc.available is True
    assert bc.kind == "manual"


def test_get_provider_browser_chat_raises():
    with pytest.raises(ProviderError):
        get_provider("browser_chat", ProviderConfig())


def test_list_models_browser_chat_empty():
    assert list_models("browser_chat", ProviderConfig()) == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/jsun/public_projects/job-app-llm-helper && python -m pytest tests/test_handoff.py -k browser_chat -v`
Expected: FAIL — `browser_chat` not in detected infos; `get_provider` raises "Unknown provider" (acceptable, but make it explicit) — assertion on `kind == "manual"` fails first.

- [ ] **Step 3: Update `providers/base.py` comment**

Edit `providers/base.py` line 26:

```python
    kind: str  # "cli" | "api" | "local" | "manual"
```

- [ ] **Step 4: Add the `browser_chat` entry in `providers/detect.py`**

At the end of `detect_providers`, just before `return infos`, insert:

```python
    infos.append(
        ProviderInfo(
            name="browser_chat",
            display_name="Browser AI (paste prompt — claude.ai, ChatGPT, etc.)",
            kind="manual",
            available=True,
            detail="no key or install needed — you paste into your own chat tab",
            tier=QualityTier.BEST,
            model=None,
            tier_verified=False,
        )
    )
```

Rationale for tier: the quality depends on whichever site the user pastes into; `tier_verified=False` flags it as not-app-determined, matching how the UI already renders unverified tiers.

- [ ] **Step 5: Add the `get_provider` guard in `providers/registry.py`**

In `get_provider`, immediately before the final `raise ProviderError(f"Unknown provider: {name!r}")`, insert:

```python
    if name == "browser_chat":
        raise ProviderError(
            "this provider builds a prompt to paste; it doesn't generate in-app"
        )
```

(`list_models("browser_chat", ...)` already returns `[]` via the function's default branch — the new test locks that in; no code change needed there.)

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd /home/jsun/public_projects/job-app-llm-helper && python -m pytest tests/test_handoff.py -v`
Expected: PASS (all, including the 3 new).

- [ ] **Step 7: Lint**

Run: `cd /home/jsun/public_projects/job-app-llm-helper && ruff check providers/ tests/test_handoff.py && ruff format providers/`
Expected: no errors.

- [ ] **Step 8: Commit**

```bash
cd /home/jsun/public_projects/job-app-llm-helper
git add providers/base.py providers/detect.py providers/registry.py tests/test_handoff.py
git commit -m "feat(providers): browser_chat manual provider (detect + guard)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: `POST /build-handoff-prompt` route

**Files:**
- Modify: `app.py` (new route; import `handoff`; sample-splitting helper)
- Test: `tests/test_smoke.py`

Design notes:
- The route accepts the same intake payload `/generate` gets, plus `{num_samples, sample_chars}`.
- It splits `profile["writing_samples"]` into chunks (same 3+-blank-line rule `build_voice_fingerprint` uses), then delegates to `handoff.build_handoff_prompt`.
- Validation: require at least a résumé/background OR a job description; else 400. (Looser than `/generate`, which needs all job fields — a handoff prompt is still useful with just one side filled.)
- No provider call. Returns `{"success": True, "prompt": ..., "chars": len, "words": approx}`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_smoke.py` (reuses module-level `SAMPLE_PROFILE` and `JOB`):

```python
def test_build_handoff_prompt_route(client):
    resp = client.post(
        "/build-handoff-prompt",
        json={
            "profile": SAMPLE_PROFILE,
            **JOB,
            "job_description": "Design numerical methods.",
            "org_about": "We build engines for the public good.",
            "num_samples": 3,
            "sample_chars": 2000,
        },
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert "Research Engineer" in body["prompt"]
    assert "Design numerical methods" in body["prompt"]
    assert body["chars"] == len(body["prompt"])
    assert body["words"] > 0


def test_build_handoff_prompt_requires_some_input(client):
    resp = client.post(
        "/build-handoff-prompt",
        json={"profile": {}, "job_description": ""},
    )
    assert resp.status_code == 400
    assert resp.get_json()["success"] is False
```

(`JOB` in `test_smoke.py` already defines `job_title`/`org_name`/`job_description`; the test overrides `job_description`/`org_about` after spreading `JOB`, so the later keys win.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /home/jsun/public_projects/job-app-llm-helper && python -m pytest tests/test_smoke.py -k handoff -v`
Expected: FAIL — 404 (route not registered).

- [ ] **Step 3: Add the import in `app.py`**

`re` is already imported at `app.py:19` — do not re-import it. After the
`from generator import (...)` block (around line 32), add only:

```python
import handoff
```

- [ ] **Step 4: Add a sample-splitting helper + the route in `app.py`**

Insert before the `/generate` route (around line 310):

```python
_SAMPLE_SPLIT = re.compile(r"\n\s*\n\s*\n+")


def _split_samples(profile: dict) -> list[str]:
    """Split the pasted writing_samples blob into chunks (same rule as the voice fingerprint)."""
    raw = (profile.get("writing_samples") or "").strip()
    if not raw:
        return []
    return [c.strip() for c in _SAMPLE_SPLIT.split(raw) if c.strip()]


@app.route("/build-handoff-prompt", methods=["POST"])
def build_handoff_prompt_route():
    """Assemble the browser-chat handoff prompt locally — no provider call.

    Looser validation than /generate: a prompt is useful with just a background or
    just a job posting, so require at least one of the two.
    """
    data = request.json or {}
    job_title, org_name, job_description, org_about = _job_fields(data)
    profile = _profile_from(data)
    has_background = bool((profile.get("background") or "").strip())
    if not has_background and not job_description:
        return jsonify(
            {
                "success": False,
                "error": "Add your background/résumé or the job posting first",
            }
        ), 400
    try:
        num_samples = int(data.get("num_samples", 3))
    except (TypeError, ValueError):
        num_samples = 3
    try:
        sample_chars = int(data.get("sample_chars", 2000))
    except (TypeError, ValueError):
        sample_chars = 2000
    num_samples = max(0, min(num_samples, 4))
    sample_chars = max(200, min(sample_chars, 8000))

    prompt = handoff.build_handoff_prompt(
        profile,
        job_title=job_title,
        org_name=org_name,
        job_description=job_description,
        org_about=org_about,
        samples=_split_samples(profile),
        sample_chars=sample_chars,
        num_samples=num_samples,
    )
    return jsonify(
        {
            "success": True,
            "prompt": prompt,
            "chars": len(prompt),
            "words": len(prompt.split()),
        }
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /home/jsun/public_projects/job-app-llm-helper && python -m pytest tests/test_smoke.py -k handoff -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Full test suite + lint**

Run: `cd /home/jsun/public_projects/job-app-llm-helper && python -m pytest -q && ruff check app.py && ruff format app.py`
Expected: all pass, no lint errors.

- [ ] **Step 7: Commit**

```bash
cd /home/jsun/public_projects/job-app-llm-helper
git add app.py tests/test_smoke.py
git commit -m "feat(app): /build-handoff-prompt route for browser-chat mode

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: UI — provider branch, build panel, paste-back

**Files:**
- Modify: `templates/index.html`

Design notes:
- The provider select already populates from `GET /providers` (Task 2 makes `browser_chat` appear automatically).
- Add a JS branch keyed on the selected provider's `kind === "manual"` (the `/providers` payload already returns `kind`).
- When manual: relabel the main action button to "Build prompt for browser AI", hide the API-key and model rows, and on click POST the intake to `/build-handoff-prompt` instead of `/generate`.
- Render a panel: read-only `<textarea>` with the prompt, a **Copy** button, a "1 → 2 → 3" line, sample controls (count 0–4, length per sample) with a live tradeoff hint + size readout, and a collapsible paste-back `<textarea>` that POSTs to the existing `/download-docx`.

Because `index.html` is one large vanilla-JS file, follow its existing patterns (no framework, `fetch` + DOM updates). Locate the current provider-select handler and the Generate button handler before editing.

- [ ] **Step 1: Locate the integration points**

Run: `cd /home/jsun/public_projects/job-app-llm-helper && rg -n "providers|/generate|/download-docx|provider.kind|action button|Generate" templates/index.html | head -40`
Identify: (a) where `/providers` is fetched and the select is built, (b) the main Generate button + its click handler, (c) the existing download-docx call. Note their IDs/function names for the edits below.

- [ ] **Step 2: Add the manual-mode state + panel markup**

In the HTML where the generate/result area lives, add a hidden panel (use the file's existing class conventions for spacing/buttons):

```html
<div id="handoff-panel" style="display:none">
  <p class="hint">1 → open claude.ai or ChatGPT &nbsp; 2 → paste this prompt &nbsp; 3 → follow its questions</p>
  <div class="row">
    <label>Writing samples to include:
      <select id="handoff-num-samples">
        <option value="0">none</option>
        <option value="2">2</option>
        <option value="3" selected>3</option>
        <option value="4">4</option>
      </select>
    </label>
    <label>Length each:
      <select id="handoff-sample-chars">
        <option value="1500">~½ page</option>
        <option value="3000" selected>~1 page</option>
        <option value="6000">~2 pages</option>
      </select>
    </label>
  </div>
  <p class="hint" id="handoff-tradeoff">
    3 samples × ~1 page is usually enough. More/longer matches your voice better
    but makes a longer prompt that uses more of your chat's limits.
  </p>
  <textarea id="handoff-prompt" rows="14" readonly></textarea>
  <p class="hint" id="handoff-size"></p>
  <button id="handoff-copy" type="button">Copy prompt</button>

  <details id="handoff-pasteback">
    <summary>Got your letter back? Paste it here to download as .docx</summary>
    <textarea id="handoff-letter" rows="10"
      placeholder="Paste the cover letter the chat gave you"></textarea>
    <button id="handoff-download" type="button">Download .docx</button>
  </details>
</div>
```

- [ ] **Step 3: Branch the provider-change handler**

In the function that runs when the provider select changes (and once on initial load after `/providers` resolves), add:

```javascript
function applyProviderMode(info) {
  const manual = info && info.kind === "manual";
  // hide key/model rows in manual mode (use the IDs found in Step 1)
  document.getElementById("api-key-row")?.classList.toggle("hidden", manual);
  document.getElementById("model-row")?.classList.toggle("hidden", manual);
  // relabel the main action button
  const btn = document.getElementById("generate-btn"); // id from Step 1
  if (btn) btn.textContent = manual ? "Build prompt for browser AI" : "Generate";
  btn?.setAttribute("data-mode", manual ? "handoff" : "generate");
}
```

Call `applyProviderMode(selectedInfo)` wherever the selection is resolved. Use the actual element IDs discovered in Step 1; if the key/model rows have different IDs/classes, adapt the selectors (the `?.` guards no-op when an element is absent).

- [ ] **Step 4: Branch the main action button**

In the main button's click handler, branch on the mode set in Step 3:

```javascript
if (btn.getAttribute("data-mode") === "handoff") {
  await buildHandoffPrompt();
  return;
}
// ...existing /generate path unchanged...
```

Add the builder:

```javascript
async function buildHandoffPrompt() {
  const payload = collectIntakePayload(); // the same object the /generate call builds (from Step 1)
  payload.num_samples = parseInt(document.getElementById("handoff-num-samples").value, 10);
  payload.sample_chars = parseInt(document.getElementById("handoff-sample-chars").value, 10);
  const resp = await fetch("/build-handoff-prompt", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await resp.json();
  if (!data.success) {
    showError(data.error); // reuse the file's existing error display
    return;
  }
  document.getElementById("handoff-prompt").value = data.prompt;
  document.getElementById("handoff-size").textContent =
    `${data.chars.toLocaleString()} characters · ~${data.words.toLocaleString()} words`;
  document.getElementById("handoff-panel").style.display = "";
}
```

Reuse the existing intake-collecting code from the `/generate` handler (Step 1) for `collectIntakePayload`; if `/generate` builds its body inline, extract that into a small helper so both paths share it (DRY).

- [ ] **Step 5: Wire copy, sample-control rebuild, and paste-back**

```javascript
document.getElementById("handoff-copy").addEventListener("click", () => {
  const ta = document.getElementById("handoff-prompt");
  navigator.clipboard.writeText(ta.value);
});

// Re-build when the user changes sample count/length.
["handoff-num-samples", "handoff-sample-chars"].forEach((id) => {
  document.getElementById(id).addEventListener("change", buildHandoffPrompt);
});

document.getElementById("handoff-download").addEventListener("click", async () => {
  const content = document.getElementById("handoff-letter").value.trim();
  if (!content) return;
  const payload = collectIntakePayload();
  const resp = await fetch("/download-docx", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      content,
      org_name: payload.org_name,
      job_title: payload.job_title,
      profile: payload.profile,
    }),
  });
  if (!resp.ok) { showError("could not build .docx"); return; }
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "CoverLetter.docx";
  a.click();
  URL.revokeObjectURL(url);
});
```

(If the existing `/generate` download path already has a blob-download helper, call it instead of duplicating — DRY.)

- [ ] **Step 6: Manual verification**

Run: `cd /home/jsun/public_projects/job-app-llm-helper && JALLM_NO_BROWSER=1 python app.py` (then open http://localhost:5000 in a browser).
Verify:
- Select "Browser AI" → button relabels to "Build prompt for browser AI", key/model rows hide.
- Fill background + job, click → prompt panel appears, size readout shows, Copy works.
- Change sample count/length → prompt rebuilds, size updates.
- Paste a letter into paste-back → Download .docx downloads a file.
- Switch back to another provider → button reverts to "Generate", panel logic doesn't interfere.

Stop the server (Ctrl-C) when done.

- [ ] **Step 7: Commit**

```bash
cd /home/jsun/public_projects/job-app-llm-helper
git add templates/index.html
git commit -m "feat(ui): browser-chat handoff panel, sample controls, paste-back

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Docs — mark roadmap §B implemented

**Files:**
- Modify: `docs/provider-roadmap.md`

- [ ] **Step 1: Update §B**

Edit the §B heading and add a status note at the top of the section:

```markdown
## B. Browser walkthrough package — IMPLEMENTED (interactive handoff)

**Status (2026-06-15):** Shipped as the `browser_chat` provider. Refined from
per-step paste round-trips into a single self-contained interactive prompt: the app
does all deterministic work locally (parsing, regex contact, org crawl, prompt
assembly, `.docx`) and emits one prompt the user pastes once; the chat then walks
them through fit → questions → draft → AI-tells rewrite → coaching → refine →
optional coverage review. Design: `docs/superpowers/specs/2026-06-15-browser-chat-handoff-design.md`.
Modules: `handoff.py`, `providers/detect.py` (`browser_chat`), `app.py`
(`/build-handoff-prompt`), `templates/index.html`.

The original per-step "guided manual" sketch below is kept for history.
```

Leave the "Optional later: a browser-extension helper" and "Interactive intake idea" subsections unchanged (still future work).

- [ ] **Step 2: Commit**

```bash
cd /home/jsun/public_projects/job-app-llm-helper
git add docs/provider-roadmap.md
git commit -m "docs(roadmap): mark browser-chat handoff implemented

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Final verification

- [ ] **Run the full suite + lint**

Run: `cd /home/jsun/public_projects/job-app-llm-helper && python -m pytest -q && ruff check . && ruff format --check .`
Expected: all tests pass; no lint errors.

- [ ] **Review the branch**

Run: `cd /home/jsun/public_projects/job-app-llm-helper && git log --oneline main..HEAD`
Expected: spec commit + the 5 task commits.
