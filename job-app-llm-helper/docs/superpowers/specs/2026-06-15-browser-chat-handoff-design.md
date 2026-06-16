# Browser-chat handoff ("Browser AI") provider — design

**Date:** 2026-06-15
**Status:** Approved (design); pending implementation plan

## Problem

A user with only a consumer chat subscription (claude.ai, ChatGPT web, etc.) and
no API key or supported CLI cannot generate in-app today. The only supported
bridges are an installed CLI or an API key. This design adds a keyless,
install-free path: the app does all the deterministic work locally and hands the
user **one self-contained prompt** to paste into their own logged-in chat tab,
where the chat LLM runs the rest of the application flow interactively.

This is the "guided manual" direction from `docs/provider-roadmap.md` §B, refined
into a single interactive handoff prompt rather than per-step paste round-trips.

## Goals

- Offer "Browser AI (paste prompt)" as a peer option in the existing provider
  select box, alongside CLI / API / Ollama.
- Require no API key, no CLI install, no browser automation, no extension.
- Do **all** LLM-free steps locally (file parsing, regex extraction, website
  crawl, prompt assembly, `.docx` writing) so the user's chat usage/limits are
  spent only on irreducible generation.
- Produce one compact, interactive prompt the user pastes once; the chat then
  walks them through fit check, clarifying questions, draft, AI-tells rewrite,
  résumé/interview coaching, refine, and an optional coverage review.
- Let the user trade voice fidelity against prompt size (sample count / length)
  with the tradeoff shown.
- Keep the `.docx` download perk via an optional paste-back box.

## Non-goals

- No scripting/injection of claude.ai or ChatGPT (ToS, anti-bot, fragility).
- No browser extension (tracked as later research in roadmap §B; not this work).
- No reverse-engineered internal chat APIs / session-cookie reuse.
- This mode does not implement the synchronous `Provider.generate()` protocol; it
  never routes through `call_llm`.

## What is local (free) vs handed to the chat

| Step | Needs LLM? | Keyless path |
|---|---|---|
| Ingest résumé / LinkedIn / writing samples (`sources.py`) | no | parse to text locally |
| Regex contact fields (email/phone/LinkedIn) | no | already regex |
| Crawl org website (`sources.py` light crawl, `_strip_html`) | no | fetch + strip raw text locally |
| Assemble the handoff prompt | no | the feature itself |
| `.docx` writer (`docx_writer.py`) | no | from pasted-back letter |
| Job-posting structuring, org summary, fit, questions, answers, letter, coaching, refine, reviews | **yes** | done by the chat from the embedded raw/cleaned materials |

Intermediate artifacts (structured job, org summary) are **not** pre-generated;
the chat distills them inline while drafting, saving round-trips and chat tokens.

## Architecture

### 1. Provider entry & detection

- New provider **id** `browser_chat`, **display** `"Browser AI (paste prompt —
  claude.ai, ChatGPT, etc.)"`.
- New provider **kind** `"manual"` in `providers/base.py` (`ProviderInfo.kind`).
- `providers/detect.py`: always `available=True`,
  `detail="no key or install needed — you paste into your own chat tab"`. Tier
  shown as not-applicable (depends on the site the user chooses).
- `providers/registry.py` `get_provider("browser_chat", ...)` raises
  `ProviderError("this provider builds a prompt to paste; it doesn't generate
  in-app")`. This guards against any code path wrongly routing `browser_chat`
  through `call_llm`. The app branches earlier (see §3) so this path is only a
  safety net.
- `list_models("browser_chat", ...)` returns `[]` (no model selection).

### 2. The prompt packager — `handoff.py`

One pure module, no network/subprocess/filesystem I/O (the caller passes in what
`sources.py`/regex already produced):

```
build_handoff_prompt(
    profile, job_title, org_name, job_description,
    org_about, samples, *, sample_chars, num_samples
) -> str
```

Assembles one self-contained prompt with these sections:

1. **Role + interactive instructions.** "You are helping me tailor a job
   application. Work through these steps one at a time, waiting for my reply
   between each:"
   1. confirm you've understood my background and the role
   2. fit assessment
   3. ask me clarifying questions
   4. draft the cover letter
   5. **AI-tells rewrite** — review the draft for AI giveaway phrasing (generic
      openers, "I am excited to", "leverage", "passionate about", em-dash
      overuse, hollow superlatives) and rewrite anything that reads
      machine-generated into plain, specific language
   6. résumé-tailoring tips + interview prep
   7. refine on request
   8. **optional coverage review** — ask whether I want a final check; if yes,
      list the job posting's key requirements and show how the letter addresses
      each, flagging any gaps
2. **Candidate.** Cleaned résumé text + regex'd contact facts.
3. **Voice.** `num_samples` writing samples, each capped to `sample_chars`,
   clearly delimited.
4. **Role/employer.** Raw job text + **raw `_strip_html`-cleaned org crawl**
   (not summarized), each capped to a sane ceiling (job ~8k, org ~6k chars,
   matching existing snippet caps in `generator.py`). Instruction: "Below is raw
   text crawled from the employer's website. Use it to infer their mission,
   values, and any recent news, and weave relevant points into the letter." If
   the crawl is empty/failed, the prompt tells the chat to ask the user to paste
   the org's About text or proceed without it.
5. **Voice rules.** The application-voice guidance baked in as instructions,
   including the `voice_core.md` AI-blacklist patterns (seed for step 5 above).

Reuses existing context-assembly helpers from `generator.py` (e.g. the
profile-formatting used by `_build_cover_letter_prompt`) so the keyless and
provider paths don't drift.

### 3. UI flow — `templates/index.html`

Single-page app; add one branch and one panel, no new page.

- When the selected provider is `browser_chat`, the main action button switches
  from "Generate" → **"Build prompt for browser AI"**; API-key/model rows hide.
- **New endpoint** `POST /build-handoff-prompt`: takes the same intake payload
  `/generate` receives, plus `{num_samples, sample_chars}`; calls
  `handoff.build_handoff_prompt(...)`; returns `{prompt}`. No provider call.
- **Panel shown after build:**
  - Read-only prompt box + **Copy** button.
  - A short "1 → 2 → 3" line: open claude.ai / ChatGPT → paste → follow its
    questions.
  - **Sample controls:** number of samples (up to 4) and length per sample, with
    a live tradeoff hint, e.g. "3 samples × ~1 page is usually enough; 4 × 1–2
    pages matches your voice better but makes a longer prompt that uses more of
    your chat's limits." Changing either re-calls `/build-handoff-prompt`.
  - Estimated size readout (chars / approx words) so the tradeoff is visible
    before pasting.
  - Collapsible **paste-back** textarea: "Got your letter? Paste it here to
    download as .docx" (see §4).

### 4. Paste-back to `.docx`

`/download-docx` (app.py) is already provider-independent — it takes
`{content, org_name, job_title, profile}`, runs `extract_cover_letter_section`
+ `build_cover_letter_docx`, returns the file. The paste-back textarea POSTs the
user-pasted letter (plus org/job/profile already in app state) to the **existing**
`/download-docx`. `extract_cover_letter_section` tolerates surrounding text, so a
pasted chat reply with preamble still yields a clean letter. No new backend.

### 5. Error handling & edges

- **Empty intake:** `/build-handoff-prompt` requires at least a résumé or job
  description; else 400 "add your résumé or the job posting first" (matches
  existing route validation style).
- **No samples uploaded:** prompt embeds voice-rules block only; sample controls
  hide. No error.
- **Empty/failed org crawl:** handled in the prompt text (§2.4); no server error.
- **Oversized materials:** per-section char caps in `handoff.py` bound the prompt
  regardless of input size.
- **`get_provider("browser_chat")`:** raises `ProviderError` (safety net, §1).

### 6. Testing

- `tests/test_handoff.py` (pure, no network): prompt contains résumé, job, org,
  the step list, the AI-tells and coverage-review instructions; respects
  `num_samples`/`sample_chars`; org-empty path emits the ask-user fallback line;
  per-section caps enforced.
- `detect.py` test: `browser_chat` present, `available=True`, kind `manual`.
- Route tests: `/build-handoff-prompt` happy path + empty-intake 400;
  `get_provider("browser_chat")` raises.

## Files touched

- `providers/base.py` — allow `"manual"` kind.
- `providers/detect.py` — add `browser_chat` entry.
- `providers/registry.py` — `get_provider` guard + `list_models` empty.
- `handoff.py` — **new**, the prompt packager.
- `app.py` — `/build-handoff-prompt` route; reuse `/download-docx`.
- `templates/index.html` — provider branch, build panel, sample controls,
  paste-back box.
- `tests/test_handoff.py` — **new**; small additions to detect/route tests.
- `docs/provider-roadmap.md` — mark §B "guided manual" as implemented (this
  design), note the interactive-handoff refinement.
