# Setting Up with Claude Projects

One-time setup (~10 minutes). Free tier works.

## Steps

1. Go to [claude.ai](https://claude.ai) and sign up or log in
2. Click **Projects** in the left sidebar → **Create Project**
3. Name it something like "Job Applications"
4. Under **Project Knowledge**, upload:
   - Your resume/CV (PDF or DOCX)
   - LinkedIn profile (URL or exported text)
   - 2-4 writing samples (emails, reports, essays — anything in your natural voice)
   - The voice fingerprint block (paste as text — generate it first using the [voice fingerprint prompt](voice-fingerprint-prompt.md))
5. Under **Project Instructions**, paste the contents of [project-instructions.md](project-instructions.md) — replace `[YOUR NAME — replace this]` with your actual name
6. Pick the strongest model your plan offers (see below)
7. Start a new chat → paste the [kickoff message](kickoff-template.md) for your first application

[Screenshot: Projects sidebar with "Create Project" button highlighted]

[Screenshot: Project Knowledge section with uploaded files visible]

[Screenshot: Project Instructions text area with content pasted]

[Screenshot: Model picker dropdown showing available models]

## Model notes

| Plan | Model | Notes |
|---|---|---|
| Free | Sonnet | Good for cover letters and voice matching. |
| Pro ($20/mo) | Opus | Best for nuanced voice matching and long-form writing. Recommended for frequent applicants. |

## Free tier limits

- 5 projects, 20 files per project (30 MB each), Sonnet only
- Project Knowledge persists across conversations

## Tips

- **First run:** The LLM will ask you to upload any missing materials and generate your voice fingerprint from your writing samples.
- The voice fingerprint makes cover letters sound like *you* instead of AI. Generate once, reuse forever.
- Start a **new chat** for each application to keep context clean.
