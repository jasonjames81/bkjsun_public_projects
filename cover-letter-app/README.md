# Cover Letter AI Helper

A Flask web app that turns a job posting into a tailored, voice-matched cover letter —
using **whatever LLM access you have**: a bring-your-own API key (Anthropic / OpenAI /
Google), a logged-in AI CLI (Claude / Gemini / Codex), or a local Ollama model. Pick your
provider in the UI.

**Your data stays in your browser.** You paste your background once; it's saved in
`localStorage` and sent with each request. The server keeps no per-user files — only your
chosen provider + API key (stored locally, file permissions `0600`).

## Quick start

```bash
./start.sh
```

Then open <http://localhost:5000>. The script creates a `venv`, installs dependencies, and
launches the app.

Manual setup:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## How it works

```
Your profile (once)  +  a job posting
        │
        ▼
  Check fit ──► Generate (2-pass: draft + voice polish) ──► Refine ──► Download .docx
```

1. **Set up a provider** — open *AI provider*, pick one, and paste an API key if needed.
   Keys are stored locally (`platformdirs` config dir, `0600`), or read from
   `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GOOGLE_API_KEY` env vars.
2. **Your profile** — name, optional contact fields, and your background (paste your resume
   or LinkedIn text). Optionally add writing samples (to match your voice) and story notes
   (specific accomplishments with numbers). Saved in your browser.
3. **The job** — title, organization, job description, optional "about the org".
4. **Check fit** — a traffic-light recommendation (proceed / caution / skip) with match
   score, strengths, concerns, and keyword overlap — before you spend a generation.
5. **Generate** — a two-pass cover letter (draft from your profile, then a voice-polish pass
   that scrubs AI tells), plus resume-tailoring suggestions and interview talking points.
6. **Refine** — preset chips (tighter, warmer, more confident, different opening) or a
   free-form instruction.
7. **Download** — a formatted `.docx` with your contact header, date, body, and signature.

## Providers

| Kind | Examples | Notes |
|---|---|---|
| API key | Anthropic, OpenAI, Google | Works on any machine. Bring your own key. |
| CLI | Claude, Gemini, Codex | Used if the CLI is installed and logged in. |
| Local | Ollama | Runs fully offline against a local model. |

## Configuration

`config.py` only tunes the default Claude-CLI model (`CLAUDE_MODEL`) and the CLI subprocess
timeout. There are **no document paths** — the profile is supplied at runtime by the browser.

## Architecture

```
app.py            Flask routes; stateless, profile carried per-request
generator.py      LLM prompts (parameterized by applicant profile) + provider routing
profile.py        Builds prompt blocks from the user's pasted profile; voice fingerprint
docx_writer.py    Renders the .docx (contact header from the profile)
providers/        Provider abstraction: API / CLI / Ollama adapters, key storage, detection
templates/        Single-page, mobile-first UI (localStorage-backed profile)
config.py         Default CLI model + timeout
tests/            Offline smoke tests (mock provider; no network)
```

## Tests

```bash
source venv/bin/activate
pip install pytest
python -m pytest tests/ -v
```

The smoke tests mock the LLM call, so they run offline and make no API requests.

## Privacy

- Your profile lives in your browser's `localStorage`; "Clear" removes it.
- API keys are stored locally with `0600` permissions and are never logged or exported.
- The server stores no resumes, letters, or job postings.

## License

[GPL-3.0](../LICENSE).
