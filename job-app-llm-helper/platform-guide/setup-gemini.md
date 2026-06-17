# Setting Up with Gemini Notebooks

One-time setup (~10 minutes). Free tier works great.

## Steps

1. Go to [gemini.google.com](https://gemini.google.com) and sign up or log in
2. Click **Notebooks** in the left sidebar → **Create Notebook**
3. Name it something like "Job Applications"
4. Upload your core assets as **Sources**:
   - Your resume/CV (PDF or DOCX)
   - LinkedIn profile (URL or exported text)
   - 2-4 writing samples (emails, reports, essays — anything in your natural voice)
   - The voice fingerprint block (paste as text or upload a .md file — the LLM can also generate this from your writing samples on first run)
5. Start a new chat within the notebook and paste the contents of [project-instructions.md](project-instructions.md) — replace `[YOUR NAME — replace this]` with your actual name
6. For each new application, start a **new chat** within the notebook and paste the [kickoff message](kickoff-template.md)

[Screenshot: Notebooks sidebar with "Create Notebook" button highlighted]

[Screenshot: Notebook with uploaded Sources visible]

[Screenshot: Notebook chat with kickoff message]

## How it works

Gemini Notebooks are a structured workspace — you upload core assets (resume, LinkedIn, writing samples, voice fingerprint) as permanent Sources, then start a new chat for each application. The Sources stay loaded across chats, so you don't re-upload everything each time.

Notebooks sync with NotebookLM, so you can also access your materials there.

## Free tier limits

- 100 notebooks, 50 sources per notebook
- 50 chat queries per day (resets the next day)
- 32k context window
- Works across web, Android, and iOS

## Model notes

Gemini uses the latest available model — no selection needed.

## Tips

- If Gemini can't fetch a URL you paste, it'll ask you to paste the text instead. This is normal.
- Start a **new chat** for each application to keep context clean.
- You can add or replace sources later if you update your resume or voice fingerprint.
