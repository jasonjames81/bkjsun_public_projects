# Implementation Plan: Platform-Native Job App Assistant Guide

## Context

**Working directory**: `/home/jsun/projects` (agent memory, instructions, AAMM)
**Target repo**: `/home/jsun/public_projects` → `github.com:jasonjames81/bkjsun_public_projects`
**Target subfolder**: `job-app-llm-helper/`

The browser-chat handoff feature (code + `/build-handoff-prompt` route) was already removed in commit `6d8e20c`. Only the design docs and implementation plan remain. This project replaces that approach with a platform-native guide.

---

## Part A: New files to create

All new files go in `job-app-llm-helper/platform-guide/`.

### A1. `platform-guide/voice-fingerprint-prompt.md`

A one-time prompt the user feeds to their LLM along with writing samples. The LLM analyzes the samples and emits a reusable voice fingerprint block that the user pastes into Project Knowledge.

**Structure:**
- Header explaining this is a one-time setup step
- The prompt itself (copy-pasteable)
- What the LLM will output (a markdown block)
- Instructions: paste the output into Project Knowledge alongside your resume and writing samples

**Key content decisions:**
- The prompt should instruct the LLM to analyze writing samples for: sentence length, paragraph length, vocabulary level, tone, structural patterns, transition style, and AI-tell markers to avoid
- Output format: a single fenced markdown block labeled `## Voice Fingerprint` that can be pasted directly into Project Knowledge
- Should work the same across Claude/ChatGPT/Gemini (no platform-specific syntax)

### A2. `platform-guide/project-instructions.md`

The custom instructions to paste into Project Instructions (the system prompt for the Project).

**Structure:**
- **Persona**: You are a job-application writing assistant. Your user is [NAME]. You have their resume, writing samples, and voice fingerprint in Project Knowledge.
- **Process**:
  1. On first run: Walk the user through uploading resume/CV + writing samples + running the voice-fingerprint prompt. Confirm what's saved.
  2. On returning runs: Check what's in Project Knowledge. "I see your resume and writing samples are already here. Do you want to replace any, or should I use what's here?"
  3. Per application: User pastes kickoff message → you guide them through the full workflow (fit check → recall experiences → employer questions → draft → voice polish → refine)
- **AI-tells scrubbing**: After drafting, rewrite to remove common AI tells (e.g., "I'm excited about", "leverage", "synergy", "in today's fast-paced world", excessive hedging). Use the voice fingerprint as the target.
- **Workflow steps**: Numbered steps matching the app's flow (fit → recall → questions → draft → polish → refine → optional coaching)
- **Link-fetch guidance**: When a URL fails to fetch, tell the user to paste the text or upload a PDF. Don't fabricate content from a failed fetch.
- **Output format**: Cover letter in a copy box, then offer to refine. Download as .docx when ready (if the platform supports it).

**Key content decisions:**
- The instructions should be platform-agnostic (no Claude/ChatGPT/Gemini-specific syntax)
- The "first run vs returning" logic is handled by the LLM's own reasoning — it checks Project Knowledge and asks
- Should reference the voice fingerprint block by name so the LLM knows to look for it

### A3. `platform-guide/kickoff-template.md`

The per-application message the user pastes to start a new job application.

**Structure:**
```
New role. 

Job posting: [paste the job description or link]
Org website: [link to the organization's about/mission page, optional]

Walk me through it.
```

**Key content decisions:**
- Keep it minimal — the LLM has everything else in Project Knowledge
- The "Walk me through it" triggers the process defined in project-instructions.md
- Optional org website link — the LLM will try to fetch it, fall back to asking the user to paste if it fails

### A4. `platform-guide/setup-claude.md`

Concise Claude Projects setup guide.

**Structure:**
1. Go to [claude.ai](https://claude.ai) → sign up / log in (free tier works)
2. Click **Projects** in the left sidebar → **Create Project**
3. Name it (e.g., "Job Applications")
4. **Project Knowledge**: Upload your resume/CV, writing samples (up to 4), and the voice fingerprint block (paste as text or upload a .md file)
5. **Project Instructions**: Paste the contents of `project-instructions.md`
6. Model: Pick the strongest model your plan offers (Sonnet on free, Opus on Pro)
7. Start a new chat → paste the kickoff message for your first application

**Free tier notes:**
- Up to 5 projects, 20 files per project (30 MB each)
- Sonnet only (no Opus)
- Memory across conversations is enabled

**Screenshot placeholders**: Note where screenshots should go (Projects sidebar, Create Project button, Knowledge section, Instructions section, Model picker)

### A5. `platform-guide/setup-chatgpt.md`

Same structure as setup-claude.md, adapted for ChatGPT Projects.

**Key differences:**
- Projects are unlimited on free tier, but only 5 files per project
- Default model is GPT-5.3 (free) or GPT-5.5 (Plus)
- No explicit model selection within Projects (uses plan default)
- Available on web, iOS, Android

**Screenshot placeholders**: Note where screenshots should go

### A6. `platform-guide/setup-gemini.md`

Same structure, adapted for Gemini Notebooks.

**Key differences:**
- Gems can only be **created** on desktop (gemini.google.com), but used on mobile
- File uploads happen during Gem creation
- Free tier includes Gems (since March 2025)
- No explicit model selection (uses Gemini latest)

**Screenshot placeholders**: Note where screenshots should go ( Gems Manager, Create Gem, Instructions field, File upload)

---

## Part B: Files to modify

### B1. `job-app-llm-helper/README.md` — Restructure

**New structure:**

```markdown
# Job App LLM Helper

[Updated intro — two ways to use: browser-native (no install) or downloadable app]

## Use it in your browser (no install needed)

[2-3 sentence overview: You can set up a reusable job-application assistant 
using Claude Projects, ChatGPT Projects, or Gemini Notebooks — no download, 
no API key. The LLM handles the full workflow using your resume, writing 
samples, and voice fingerprint stored in the Project.]

### Free vs paid

| | Claude | ChatGPT | Gemini |
|---|---|---|---|
| Free tier | Yes (5 projects, Sonnet) | Yes (unlimited, 5 files) | Yes (unlimited) |
| Paid tier | Pro $20/mo (Opus, unlimited) | Plus $20/mo (25 files) | Advanced $20/mo |
| Best for | Long-form writing, nuanced voice matching | Broad tool integration, fastest iteration | Google ecosystem users |

[Note: all three work great on free tier. Paid adds more files and better models.]

### Setup (one-time, ~10 min)

1. Pick your platform → [Claude](platform-guide/setup-claude.md) | [ChatGPT](platform-guide/setup-chatgpt.md) | [Gemini](platform-guide/setup-gemini.md)
2. Create a Project/Gem with the [project instructions](platform-guide/project-instructions.md)
3. Upload your resume + writing samples
4. Run the [voice fingerprint prompt](platform-guide/voice-fingerprint-prompt.md) once, paste the output into Project Knowledge

### Per-application (each time)

Paste the [kickoff message](platform-guide/kickoff-template.md) with the job posting and optional org site link. The LLM walks you through the rest.

[Note about link-fetch unreliability — if a link fails, paste the text]

[Note about privacy — materials live with the provider; consumer tiers may train unless opted out]

---

## Download the app

[Existing content from current README, with minor trimming:
- Download & run
- Connect an LLM
- How it works
- Run from source
- Architecture
- Tests
- License]
```

**Key decisions:**
- The browser-native guide is the first and primary section
- The downloadable app is §2, positioned as the alternative for CLI/API/Ollama users
- Platform guides are linked, not inlined (keeps README clean)
- The project-instructions.md and voice-fingerprint-prompt.md are linked directly (the user copies from them)

### B2. `docs/provider-roadmap.md` — Update §B

Replace the current §B content with a note:

```markdown
## B. Browser walkthrough package — REMOVED (replaced by platform-native guide)

The browser-chat handoff feature (code + `/build-handoff-prompt` route) was 
removed in v0.3.0 (commit `6d8e20c`). It was replaced by a simpler, 
maintenance-free approach: a guide that teaches users to set up platform-native 
assistants using Claude Projects, ChatGPT Projects, or Gemini Notebooks — no app 
code needed. See `platform-guide/` and the README §1.

The original design docs are archived:
- `docs/superpowers/specs/2026-06-15-browser-chat-handoff-design.md`
- `docs/superpowers/plans/2026-06-15-browser-chat-handoff.md`
```

### B3. `public_projects/README.md` — Update description

Update the job-app-llm-helper row in the table:

```markdown
| [job-app-llm-helper/](job-app-llm-helper/) | Write cover letters, answer application questions, and prep for interviews with LLM help — via browser-native Projects (Claude/ChatGPT/Gemini, no install) or a self-hosted Flask app (API key, CLI, or local Ollama). |
```

---

## Part C: Files to remove

### C1. `docs/superpowers/specs/2026-06-15-browser-chat-handoff-design.md`
Replaced by `platform-guide/`. The design was for a feature that was built and then removed.

### C2. `docs/superpowers/plans/2026-06-15-browser-chat-handoff.md`
Same — implementation plan for the removed feature.

---

## Part D: Execution order

1. **Create `platform-guide/` directory**
2. **Write `project-instructions.md`** — this is the core content; everything else references it
3. **Write `voice-fingerprint-prompt.md`** — standalone prompt, no dependencies
4. **Write `kickoff-template.md`** — tiny, depends on project-instructions
5. **Write `setup-claude.md`, `setup-chatgpt.md`, `setup-gemini.md`** — reference project-instructions and voice-fingerprint-prompt
6. **Rewrite `job-app-llm-helper/README.md`** — link to all new files
7. **Update `docs/provider-roadmap.md`** — note §B removal
8. **Update `public_projects/README.md`** — update description
9. **Delete `docs/superpowers/specs/2026-06-15-browser-chat-handoff-design.md`**
10. **Delete `docs/superpowers/plans/2026-06-15-browser-chat-handoff.md`**
11. **Export this plan** → `docs/platform-guide-implementation.md`
12. **Commit and push**

---

## Part E: Key content principles

1. **The prompt is the stable core.** Setup steps rot (platform UIs churn). The project-instructions.md and voice-fingerprint-prompt.md are platform-agnostic and durable.
2. **Three equal platforms.** No second-class. Claude, ChatGPT, and Gemini all work on free tiers with comparable features.
3. **First-run vs returning flow.** The LLM handles this through its own reasoning — no app code needed. First run: walk through setup. Returning: "what's changed?"
4. **Link-fetch is unreliable.** One sentence in the guide, not a detailed fallback table. The LLM will suggest pasting text when links fail.
5. **Privacy is stated plainly.** Materials live with the provider. Consumer tiers may train unless opted out. This is the trade-off vs the app's local-only storage.
6. **Free tier is the default.** The guide works on free tiers. Paid tiers add more files and better models — mentioned but not required.

---

## Part F: Risks and open questions

1. **Screenshots**: Plan calls for screenshot placeholders. Finding and adding real screenshots is a separate task. Should we ship with placeholders first, or block on screenshots?
2. **Project-instructions.md content**: The exact wording of the project instructions will need iteration. Should we write a first draft and mark it as "v0.1 — test and refine"?
3. **Voice-fingerprint-prompt.md**: Same — the prompt needs testing across all three platforms to ensure consistent output. Mark as v0.1?
4. **Gemini file upload**: Gems allow file uploads during creation, but the UX for "paste as text" (for the voice fingerprint block) may differ from Claude/ChatGPT. Need to verify the exact flow.
5. **Commit strategy**: One commit for all files, or separate commits for creation vs cleanup?
