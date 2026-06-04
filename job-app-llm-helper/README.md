# Job App LLM Helper

A Flask web app that turns a job posting into a tailored, voice-matched cover letter —
using **whatever LLM access you have**: a bring-your-own API key (Anthropic / OpenAI /
Google), a logged-in AI CLI (Claude / Gemini / Codex), or a local Ollama model. Pick your
provider in the UI.

**Your data stays in your browser.** You paste your background once; it's saved in
`localStorage` and sent with each request. The server keeps no per-user files — only your
chosen provider + API key (stored locally, file permissions `0600`).

## Download & run on a Mac (no terminal commands)

1. Go to the [**Releases**](https://github.com/jasonjames81/public_projects/releases) page and
   download `job-app-llm-helper.zip`.
2. Double-click the zip to unzip it, then open the `job-app-llm-helper` folder.
3. **Right-click** `start-mac.command` → **Open** → **Open**. (macOS asks the first time
   because the file was downloaded — you only approve it once. After that, double-click works.)
4. A Terminal window opens, sets things up the first time (~1 minute), and your browser opens
   to the app. Keep that Terminal window open while you use it; close it to stop.
5. In the app, open **AI provider**, pick one, and paste an API key.

**You need two things:** Python 3 (the launcher tells you where to get it if it's missing) and
an LLM API key. The simplest key is from Anthropic — create one at
<https://console.anthropic.com> → *API keys*, then paste it into the app's *AI provider* box.
(OpenAI and Google keys also work, as does a logged-in `claude` CLI or a local Ollama model.)

> Everything runs on your own computer. Your profile stays in your browser; your key is stored
> locally. Nothing is uploaded except your request to the LLM provider you choose.

## Quick start (developers)

```bash
./start.sh            # macOS/Linux: creates a venv, installs deps, runs the app
```

Then open <http://localhost:5000>.

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
  Check fit ──► (optional) recall experiences ──► (optional) employer questions
            ──► Generate (2-pass: draft + voice polish) ──► Refine ──► Download .docx
```

1. **Set up a provider** — open *AI provider*, pick one, and paste an API key if needed.
   Keys are stored locally (`platformdirs` config dir, `0600`), or read from
   `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GOOGLE_API_KEY` env vars. The app auto-selects
   the first available provider; *Generate* is blocked until one is ready.
2. **Your profile** — name, optional contact fields, and your background. Type/paste it, or
   **import from a file or link** (see below). Optionally add writing samples (to match your
   voice) and story notes (accomplishments with numbers). Saved in your browser.
3. **The job** — title, organization, job description, optional "about the org".
4. **Check fit** — a traffic-light recommendation (proceed / caution / skip) with match
   score, strengths, concerns, and keyword overlap — before you spend a generation.
5. **Recall your experiences** *(optional)* — get questions tailored to the role; your
   answers feed the cover letter.
6. **Employer application questions** *(optional)* — paste the supplemental questions (with
   optional limits like `(150 words)`), get clarifying prompts where your profile falls
   short, then draft grounded answers. These won't be duplicated in the cover letter.
7. **Generate** — a two-pass cover letter (draft from your profile, then a voice-polish pass
   that scrubs AI tells), plus resume-tailoring suggestions and interview talking points.
8. **Refine** — preset chips (tighter, warmer, more confident, different opening) or a
   free-form instruction.
9. **Download** — a formatted `.docx` with your contact header, date, body, and signature.

## Importing your background from a file or link

Instead of pasting, point the **import** box (under *Background*) at:

- a **local file** — `~/Documents/resume.docx`, a `.pdf`, `.txt`, `.md`, or `.html`;
- a **web link** — a Google Doc **published to the web** (File → Share → Publish to web), a
  personal site, or any public page.

The text is extracted and appended to *Background*. `.docx` needs `pandoc`; `.pdf` needs
`pdftotext` (poppler) — both optional, with a clear message if missing. LinkedIn profile
URLs generally require login and won't extract — paste that text or use a public link.

> Importing reads local files and fetches URLs **on the machine running the app**. That's
> fine for the intended single-user, self-hosted setup. Do not expose this app as a shared
> public server (see *Deploying*).

## Providers

| Kind | Examples | Notes |
|---|---|---|
| API key | Anthropic, OpenAI, Google | Works on any machine. Bring your own key. |
| CLI | Claude, Gemini, Codex | Used if the CLI is installed and logged in. |
| Local | Ollama | Runs fully offline against a local model. |

## Configuration

`config.py` only tunes the default Claude-CLI model (`CLAUDE_MODEL`) and the CLI subprocess
timeout. There are **no document paths** — the profile is supplied at runtime by the browser.

## Deploying

This app is built to be **self-hosted, one user per instance** — run your own copy with
your own key. It is *not* a multi-tenant service: the API key and provider choice are stored
on the server, so one shared public instance would let every visitor spend the host's key,
and the *import* feature would read the host's files. Run it locally (or on your own box).

**Run it (production-safe defaults):**

```bash
python app.py            # binds 127.0.0.1:5000, debug OFF
```

Environment overrides:

| Var | Default | Purpose |
|---|---|---|
| `JALLM_HOST` | `127.0.0.1` | Set `0.0.0.0` to reach it from other devices on your network |
| `JALLM_PORT` | `5000` | Port |
| `JALLM_DEBUG` | off | `1` enables Flask debug — **never** on an exposed host (RCE risk) |

**Use it from your phone (same Wi-Fi):**

```bash
JALLM_HOST=0.0.0.0 python app.py
# then on your phone open  http://<your-computer-ip>:5000
```

Find your computer's IP with `ip addr` (Linux), `ipconfig` (Windows), or `ifconfig` (macOS).
Only do this on a network you trust.

## Architecture

```
app.py            Flask routes; stateless, profile carried per-request
generator.py      LLM prompts (parameterized by applicant profile) + provider routing
profile.py        Builds prompt blocks from the user's profile; voice fingerprint
sources.py        Import background from a local file path or web URL (self-host only)
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
- Imported files/links are read on your own machine (self-host model) and only their
  extracted text is added to your profile — nothing is uploaded anywhere except to the LLM
  provider you chose, at generation time.

## License

[GPL-3.0](../LICENSE).
