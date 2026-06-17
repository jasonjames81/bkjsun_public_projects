# Setting Up with Claude Projects

One-time setup (~10 minutes). Free tier works great.

## Steps

1. Go to [claude.ai](https://claude.ai) and sign up or log in
2. Click **Projects** in the left sidebar → **Create Project**
3. Name it something like "Job Applications"
4. Under **Project Knowledge**, upload:
   - Your resume/CV (PDF or DOCX)
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
| Free | Sonnet | Works well for cover letters. Handles voice matching adequately. |
| Pro ($20/mo) | Opus | Best for nuanced voice matching and long-form writing. Recommended if you write a lot of applications. |

## Free tier limits

- Up to 5 projects, 20 files per project (30 MB each)
- Sonnet only (no Opus)
- Memory across conversations is enabled — your Project Knowledge persists

## Tips

- The voice fingerprint is what makes cover letters sound like *you* instead of AI. Generate it once, reuse it forever.
- If Claude can't fetch a URL you paste, it'll ask you to paste the text instead. This is normal.
- Start a **new chat** for each application to keep context clean.
