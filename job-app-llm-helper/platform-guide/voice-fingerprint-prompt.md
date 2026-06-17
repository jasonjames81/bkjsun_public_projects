# Voice Fingerprint Prompt

> v0.1 — test and refine. Run this once with your writing samples. The output goes into your Project's Knowledge section.

## What this does

This prompt analyzes your writing samples and produces a "Voice Fingerprint" — a summary of your writing style that the LLM uses to match your voice in cover letters and application materials.

## How to use it

1. Start a new conversation (not your job-application Project)
2. Upload 2-4 writing samples: emails, reports, essays, blog posts — anything in your natural voice
3. Paste the prompt below
4. Copy the output block and paste it into your Project's Knowledge section

## The prompt

---

Please analyze the writing samples I've uploaded and create a Voice Fingerprint that captures my natural writing style. Examine these dimensions:

**Sentence-level:**
- Average sentence length (word count)
- Sentence structure patterns (simple, compound, complex)
- Preferred sentence openings

**Paragraph-level:**
- Average paragraph length (sentences and words)
- How you structure paragraphs (topic sentence → detail, anecdote → lesson, etc.)

**Vocabulary:**
- Formality level (casual, professional, formal)
- Characteristic words or phrases you use (and ones you never use)
- Technical vs plain language preferences

**Tone:**
- Overall tone (warm, direct, analytical, narrative, etc.)
- How tone shifts across contexts (formal email vs blog post)

**Transitions:**
- How you connect ideas between sentences and paragraphs
- Favorite transition words or structures

**AI tells to avoid:**
- List any patterns in my writing that differ from typical AI-generated text
- Note phrases I use that AI would never generate naturally
- Identify my "voice signatures" — the things that make my writing recognizably mine

Output your analysis as a single markdown block labeled `## Voice Fingerprint`. Format each dimension as a bullet point or short paragraph. Keep it concise — this will be pasted into a Project's Knowledge section, so aim for 200-400 words total.

---

## What you'll get back

A markdown block like this (yours will be different):

## Voice Fingerprint

- **Sentence length:** Averages 18-22 words. Mix of short punchy sentences (under 10 words) with longer explanatory ones. Rarely uses questions.
- **Paragraph length:** 2-4 sentences. Leads with the main point, then supports with specifics.
- **Vocabulary:** Professional but not stiff. Uses "figure out" instead of "determine," "use" instead of "utilize." Avoids jargon unless technical audience is clear.
- **Tone:** Direct and warm. Conversational without being casual. Confident but not arrogant. Uses "I" naturally.
- **Transitions:** Minimal. Lets paragraphs do the work. When transitions are needed, uses "Here's the thing:" or "That said:" rather than "Furthermore" or "Moreover."
- **AI tells to avoid:** Never starts with "I'm writing to express..." Never uses "leverage," "synergy," "passionate about," or "in today's fast-paced world." Doesn't hedge with "I think perhaps." Specificity is the signature — always names the project, the number, the outcome.
