# Implementation Plan — Job App LLM Helper Updates

**Date:** 2026-06-16 (revised)

---

## Overview

8 files to change across documentation, prompts, UI, and LLM-facing text. Internal variable names (`experience_answers`, `stories`) stay stable — only user-facing labels, prompt text, and documentation change. 5 files confirmed unchanged.

### Key decisions

- LLM generates voice fingerprint from writing samples on first run (preferred over guiding user to run prompt separately)
- Interview prep (step 7): ask user which mode — generate likely Qs only, or interactive Q→answer→follow-up coaching loop
- Export format preference: LLM asks after generating cover letter (not in kickoff template, not in project-instructions setup)
- Gemini Notebooks free tier caps verified: 100 notebooks, 50 sources/notebook, 50 chats/day, 32k context. Google Docs export on free tier: unverified (omit claim or mark uncertain)
- Lint: `ruff check .` (no config, ad-hoc only). Test: `python -m pytest tests/ -v`

---

## File-by-file changes

### 1. `platform-guide/project-instructions.md` (rewrite)

Core file — everything references it. Rewrite to avoid bullet-heavy formatting (bullets don't copy cleanly); use numbered steps and short paragraphs.

**Top of file:**
- Add `> ⚠️ Before copying: replace [YOUR NAME] below with your actual name.` at the very top

**Who you are section:**
- Add LinkedIn to materials: "You have their resume, LinkedIn profile, writing samples, and voice fingerprint"
- Update "saved in Project Knowledge" to cover all platforms (not just Claude Projects)

**First run vs returning:**
- First run: LLM asks user to provide/paste: resume/CV, LinkedIn URL or public profile text, 2-4 writing samples
- Voice fingerprint: LLM generates it from the writing samples directly (preferred). If platform can't do this, guide user to run the voice-fingerprint-prompt.md
- For platforms that support file uploads, guide user through uploading
- Returning: confirm loaded materials, offer to replace

**Workflow steps:**

1. **Fit check** — unchanged
2. **Useful details** (renamed from "Recall experiences") — ask 2-4 targeted questions to surface relevant stories/accomplishments. framing: "gather useful details, specific accomplishments, and relevant stories"
3. **Employer application questions** (clarified) — this is for supplemental application questions FROM the employer (e.g. "Why do you want to work here?", "Describe a time you led under pressure"). LLM asks: "Do you have any actual or potential additional application questions for this job?" Distinguish from interview questions the user might ask (those are in step 7)
4. **Draft cover letter** — unchanged logic
5. **Voice polish** — unchanged
6. **Refine** — unchanged
7. **Interview prep** (new) — generate likely interview questions and let the user practice. Ask user which mode, or offer to skip for now:
   - **Option A:** Generate a list of likely interview questions with talking points (quick reference)
   - **Option B:** Interactive practice — LLM asks questions one at a time, user answers verbally or types, LLM gives follow-ups and coaching feedback
   - **Option C:** Skip for now — "No problem. Come back to this when you land an interview and I'll be ready."

**Output format section:**
- After generating the cover letter, ask user what export format they want: `.docx` or `.pdf`
- Note: `.pdf` export is only available through browser-native platforms (Claude/ChatGPT/Gemini can create PDFs directly); the self-hosted app exports `.docx` only
- Update to reflect the new 7-step workflow

### 2. `platform-guide/kickoff-template.md` (minor edits)

- Add tip at top: "Start a **new chat** within your project/notebook for each new application."
- Add optional LinkedIn field: "LinkedIn profile: [link, optional]"
- Keep the template minimal

### 3. `platform-guide/setup-claude.md` (simplify + update)

- Tighten all prose — clear and concise, essential info only
- Add LinkedIn to upload list: "Your resume/CV, LinkedIn profile (URL or exported text), 2-4 writing samples, voice fingerprint"
- Add first-run guidance: "On first run, the LLM will ask you to upload any missing materials and generate your voice fingerprint from your writing samples."
- Tip: start a **new chat** for each application

### 4. `platform-guide/setup-chatgpt.md` (simplify + update)

Same treatment as Claude.

### 5. `platform-guide/setup-gemini.md` (full rewrite: Gems → Notebooks)

- **Replace Gems with Notebooks** — Gemini Notebooks are free for all users (April 2026), synced with NotebookLM
- Structure the setup around Notebooks:
  1. Go to gemini.google.com → Notebooks in sidebar → Create Notebook
  2. Name it "Job Applications"
  3. Upload core assets as Sources: resume/CV, LinkedIn, writing samples, voice fingerprint
  4. Paste project instructions as a chat prompt (Notebooks don't have a separate instructions field — user starts a chat and pastes)
  5. Start a new chat per application
- Include verified free tier details:
  - 100 notebooks, 50 sources per notebook, 50 chats/day, 32k context window
  - Google Docs export on free tier: status uncertain (don't make a claim we can't verify)
  - If you hit the 50-chat daily limit, it resets the next day
- Note: structured workspace approach — upload core assets as permanent sources, keep prompts grounded, track output

### 6. `templates/index.html` (UI label changes)

- Line 226: `"Recall your experiences"` → `"Useful details"`
- Line 243 hint text: clarify that employer questions are supplemental application questions from the employer (e.g. "Why do you want to work here?"), not interview questions to ask the employer
- Leave internal HTML `id` names (`experienceCard`, `experienceQs`, `experienceErr`) unchanged — they're JS-internal, not user-facing

### 7. `generator.py` (prompt wording)

- `generate_questions()` docstring (line 439): `"help the applicant recall relevant experiences"` → `"help the applicant surface useful details for the cover letter"`
- `generate_questions()` prompt (lines 451-486): Update framing from "gather specific stories and experiences" to "gather useful details, specific accomplishments, and relevant stories". Change "applicant recall and articulate relevant experiences" → "applicant surface useful details for the cover letter"
- `_build_cover_letter_prompt()` section header (line 554): `f"\n=== {name.upper()}'S RELEVANT EXPERIENCES & STORIES FOR THIS ROLE (USE THESE) ===\n"` → `f"\n=== {name.upper()}'S USEFUL DETAILS FOR THIS ROLE (USE THESE) ===\n"`
- `_build_coaching_prompt()` section header (line 620): `f"\n=== {name.upper()}'S RELEVANT EXPERIENCES & STORIES FOR THIS ROLE ===\n"` → `f"\n=== {name.upper()}'S USEFUL DETAILS FOR THIS ROLE ===\n"`
- `_build_cover_letter_prompt()` prompt text (line 598): `"USE the specific stories and answers shared above"` — keep as-is (this is about using what was gathered, not about the label)

### 8. `README.md` (restructure + simplify)

**Browser section:**
- Line 5: "Gemini Gems" → "Gemini Notebooks"
- Simplify Setup to 3 steps: pick platform → follow setup guide → paste kickoff message
- Remove per-application subsection (folded into step 3)
- Update free-vs-paid table for Gemini: Notebooks (free, 100 notebooks, 50 sources, 50 chats/day, 32k context)
- Add ⚠️ icon to macOS section, tighten wording
- Line 14: "Gemini Gems" → "Gemini Notebooks"

**Download section:**
- Fix stale pandoc/pdftotext claim (line 128) — replace with pure-Python deps: `python-docx` and `pypdf`
- Update workflow diagram (line 109): "recall experiences" → "useful details"
- Step 5 (line 122): rename "Recall experiences" → "Useful details"
- All prose tightened

**Consistency check:** Ensure all references to workflow steps, features, and platform capabilities match the updated prompts and UI.

### 9. `tests/test_smoke.py` (update test names/descriptions)

- `test_generate_includes_experience_and_application_answers` (line 242): rename to `test_generate_includes_useful_details_and_application_answers`
- Comment updates: "experience answer threaded" → "useful details answer threaded" (lines 116, 263)
- Keep internal variable references (`experience_answers`) as-is — they match the API contract

### 10. `docs/provider-roadmap.md` (no change needed)

Already clean — handoff removal noted.

### 11. `docs/platform-guide-implementation.md` (no change needed)

Already documents the plan. Left as historical reference.

### 12. `app.py` (no changes)

Internal variable names (`experience_answers`) stay. API contract unchanged.

### 13. `profile.py` (no changes)

`build_stories_block()` is internal. User-facing labels are in the UI and prompts.

---

## Implementation order

1. **project-instructions.md** — core content, everything references it
2. **setup-gemini.md** — full rewrite (Gems → Notebooks)
3. **setup-claude.md, setup-chatgpt.md** — simplify + update (parallelizable)
4. **kickoff-template.md** — minor tweaks
5. **generator.py** — prompt wording changes
6. **templates/index.html** — UI label changes
7. **README.md** — restructure + simplify + consistency pass
8. **tests/test_smoke.py** — update test names/descriptions
9. **Run tests** — `python -m pytest tests/ -v` to verify nothing broke
10. **Run lint** — `ruff check .` (no config, ad-hoc)

## Not changed (by design)

- `app.py` — internal API contract unchanged
- `profile.py` — internal variable names unchanged
- `voice-fingerprint-prompt.md` — prompt is solid as-is
- `docs/provider-roadmap.md` — already clean
- Internal variable names (`experience_answers`, `stories`, `experienceCard`) — backward-compatible, not user-facing

## Subagent dispatch plan

- **Parallel batch 1** (independent doc changes): setup-claude.md, setup-chatgpt.md, kickoff-template.md
- **Sequential**: project-instructions.md (core, must be right first), setup-gemini.md (full rewrite, depends on project-instructions.md for consistency)
- **Sequential**: generator.py → templates/index.html → README.md → tests/test_smoke.py
- **Final**: run pytest + ruff
