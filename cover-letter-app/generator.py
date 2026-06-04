# generator.py
"""LLM generation for the public cover-letter app.

Forked from the personal edition's claude_generator.py and de-personalized: every
prompt is parameterized by the runtime ``profile`` dict (see profile.py) instead of a
hardcoded applicant and disk-loaded documents. Provider routing is unchanged — it
flows through providers/ and works with any configured CLI, API key, or local model.
"""

from __future__ import annotations

import json
import re

import profile as profile_mod
from providers.base import ProviderError
from providers.config import ProviderConfig
from providers.registry import get_provider

# Default word cap used when a question carries no explicit length limit.
_DEFAULT_ANSWER_LIMIT = "~150 words"


def _hard_constraints(name: str) -> str:
    """Shared hard constraints, parameterized by applicant name."""
    return f"""\
=== HARD CONSTRAINTS ===

1. QUANTIFIED CLAIMS: Use only numbers, percentages, dates, dollar amounts, durations, team
   sizes, or other quantities that appear verbatim in {name}'s background, story notes, or
   answers above. Do not infer, estimate, round, or extrapolate. If a number would be helpful
   but is not provided, write the qualitative claim without a number rather than fabricating one.

2. STORY USE: Only deploy accomplishments whose subject matter matches the JD. Do not invent
   specifics, quotes, or numbers beyond what {name} wrote. Do not combine details across
   separate stories into a single anecdote.

3. VOICE: Match the voice fingerprint above — sentence length distribution, paragraph rhythm,
   characteristic openers/transitions/closers. Avoid every phrase in the "Do NOT use" list.

4. NO AI TELLS: Do not write meta-language about being thrilled, excited to apply, writing
   to express interest, finding the role compelling, or being a perfect fit. Do not use
   triadic flourishes ("I bring rigor, empathy, and vision"). Do not write a closing line
   that summarizes the letter you just wrote."""


def _load_provider_config() -> ProviderConfig:
    # Re-reads from disk each call so a provider selection saved by the web UI
    # takes effect on the next generation — no module-level cache.
    return ProviderConfig().load()


def _selected_provider_name(cfg: ProviderConfig) -> str:
    # Default to the Claude CLI when nothing is selected, so a machine with `claude`
    # logged in works out of the box; public users instead pick an API-key provider.
    return cfg.selected() or "claude_cli"


def _extract_json(response: str, *, array: bool = False):
    """Extract and parse a JSON value from an LLM response string."""
    stripped = re.sub(r"^```(?:json)?\s*\n?", "", response.strip(), flags=re.IGNORECASE)
    stripped = re.sub(r"\n?```\s*$", "", stripped)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass
    pattern = r"\[[\s\S]*\]" if array else r"\{[\s\S]*\}"
    match = re.search(pattern, response)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError(f"no JSON {'array' if array else 'object'} found in response")


def call_llm(prompt: str, *, retries: int = 1) -> str:
    """Generate text from the user's selected LLM provider and return it stripped."""
    cfg = _load_provider_config()
    name = _selected_provider_name(cfg)
    try:
        provider = get_provider(name, cfg)
        result = provider.generate(prompt)
    except ProviderError as exc:
        raise RuntimeError(str(exc)) from exc
    return result.strip()


def refine_letter(
    current_letter: str,
    instruction: str,
    profile: dict,
    job_title: str = "",
    org_name: str = "",
):
    """Revise an existing cover letter per a free-form instruction."""
    if not current_letter.strip():
        return {"success": False, "error": "current_letter is empty"}
    if not instruction.strip():
        return {"success": False, "error": "instruction is empty"}

    name = profile_mod.applicant_name(profile)
    voice_block = profile_mod.build_voice_fingerprint(profile)

    prompt = f"""You are revising {name}'s cover letter based on a specific instruction.
Maintain the writer's voice and preserve every factual claim. Output ONLY the revised letter — no
preamble, no explanation, no markdown fences, no after-notes.

{voice_block}

=== JOB CONTEXT ===
{f"Role: {job_title}" if job_title else ""}
{f"Organization: {org_name}" if org_name else ""}

=== CURRENT LETTER ===
{current_letter.strip()}

=== INSTRUCTION ===
{instruction.strip()}

=== CONSTRAINTS ===
- Preserve every factual claim. Do not invent new numbers, organizations, dates, or stories.
- Match the voice fingerprint above; avoid the "Do NOT use" phrases.
- Keep the contact block, date, salutation, and signature unless the instruction says otherwise.
- Output the full revised letter only."""

    try:
        revised = call_llm(prompt).strip()
        if not revised:
            return {"success": False, "error": "the model returned an empty letter"}
        return {"success": True, "letter": revised}
    except Exception as e:
        return {"success": False, "error": str(e)}


def analyze_fit(profile: dict, job_title, org_name, job_description, org_about=""):
    """Pre-flight fit analysis with a traffic-light recommendation."""
    name = profile_mod.applicant_name(profile)
    profile_block = profile_mod.build_profile_summary(profile)
    stories_block = profile_mod.build_stories_block(profile)

    prompt = f"""You are screening a job posting against {name}'s full profile to decide
whether they should apply. Be honest — flag mismatches the applicant should know about, but
base every judgment on ALL of the materials below.

{profile_block}

{stories_block}

=== TARGET JOB ===
Job Title: {job_title}
Organization: {org_name}

Job Description:
{job_description}

About the Organization:
{org_about if org_about else "Not provided"}

=== YOUR TASK ===

Output ONLY a JSON object with these exact keys:

{{
  "match_score": <int 0-100>,
  "recommendation": "proceed" | "caution" | "skip",
  "rationale": "<one sentence summary of the recommendation>",
  "keywords_matched": ["<3-7 JD requirements/keywords clearly satisfied by the profile>"],
  "keywords_missing": ["<3-7 JD requirements/keywords NOT clearly evidenced in the profile>"],
  "strengths": ["<3-4 specific strengths the applicant brings to THIS role; reference concrete experience>"],
  "concerns": ["<2-4 specific concerns the hiring side will likely raise>"]
}}

GUIDELINES:
- Assess fit against the FULL background and story notes above, not a single headline line.
- Before placing anything in "keywords_missing" or "concerns", confirm it is genuinely absent
  from every input above. Never assert the applicant lacks experience that a document or story shows.
- "proceed" when score >= 70 AND no fatal mismatches (location ineligibility, missing required certifications, etc.)
- "caution" when score 50-69 OR there is a meaningful mismatch worth addressing in the cover letter
- "skip" when score < 50 OR there is a fatal mismatch
- For "keywords_missing", list things the JD explicitly requires that the profile doesn't evidence — these matter for ATS / hiring screens
- For "concerns", be specific and constructive.
- No prose outside the JSON. No markdown fences."""

    try:
        response = call_llm(prompt)
        match = re.search(r"\{[\s\S]*\}", response)
        if not match:
            raise ValueError("no JSON object in response")
        data = json.loads(match.group(0))
        data["success"] = True
        return data
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_clarifying_questions(
    profile: dict,
    questions: list[str],
    job_title: str,
    org_name: str,
    job_description: str,
    org_about: str = "",
) -> dict:
    """Decide which pasted employer questions need more detail and ask for it."""
    name = profile_mod.applicant_name(profile)
    profile_block = profile_mod.build_profile_summary(profile)
    stories_block = profile_mod.build_stories_block(profile)
    questions_block = "\n".join(f"- {q}" for q in questions)

    prompt = f"""You are helping {name} prepare answers to supplemental application questions
for a job. Review the profile and the pasted questions, then decide whether the existing
materials already provide enough detail to answer each question fully.

{profile_block}

{stories_block}

=== TARGET JOB ===
Job Title: {job_title}
Organization: {org_name}

Job Description:
{job_description}

About the Organization:
{org_about if org_about else "Not provided"}

=== APPLICATION QUESTIONS TO REVIEW ===
{questions_block}

=== YOUR TASK ===

For each question, determine whether the profile and story notes already supply sufficient
detail to write a strong, specific answer. For any question where important details are
missing, generate 1–2 targeted clarifying questions the applicant can answer to fill the gap.
Deduplicate across questions. When the materials already suffice, return an empty list.

Output ONLY a JSON object with this exact key:

{{"clarifying_questions": ["<clarifying question>", ...]}}

No prose, no markdown fences."""

    try:
        response = call_llm(prompt)
        data = _extract_json(response, array=False)
        return {
            "success": True,
            "clarifying_questions": data.get("clarifying_questions", []),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def answer_application_questions(
    profile: dict,
    questions: list[dict],
    clarifying_answers: list[dict],
    job_title: str,
    org_name: str,
    job_description: str,
    org_about: str = "",
) -> dict:
    """Draft answers to each employer application question, honouring length caps."""
    name = profile_mod.applicant_name(profile)
    profile_block = profile_mod.build_profile_summary(profile)
    stories_block = profile_mod.build_stories_block(profile)
    voice_block = profile_mod.build_voice_fingerprint(profile)

    questions_block_lines = []
    for i, q in enumerate(questions, 1):
        limit = q.get("limit")
        if limit:
            cap_str = (
                f"  [LIMIT: {limit.get('value', '?')} {limit.get('unit', 'words')}]"
            )
        else:
            cap_str = f"  [LIMIT: {_DEFAULT_ANSWER_LIMIT}]"
        questions_block_lines.append(f"{i}. {q['question']}{cap_str}")
    questions_block = "\n".join(questions_block_lines)

    if clarifying_answers:
        clarifying_section = "\n=== ADDITIONAL CONTEXT THE APPLICANT PROVIDED ===\n"
        for qa in clarifying_answers:
            clarifying_section += f"\nQ: {qa['question']}\nA: {qa['answer']}\n"
    else:
        clarifying_section = ""

    prompt = f"""You are drafting {name}'s answers to supplemental application questions
for a specific job. Match the voice precisely and rely only on facts present in the inputs below.

{voice_block}

{stories_block}

{profile_block}
{clarifying_section}

=== TARGET JOB ===
Job Title: {job_title}
Organization: {org_name}

Job Description:
{job_description}

About the Organization:
{org_about if org_about else "Not provided"}

=== APPLICATION QUESTIONS (answer each in order) ===
{questions_block}

{_hard_constraints(name)}

5. LENGTH: Honour the per-question limit shown above. When the limit is in words, stay within
   that word count. When in characters, stay within that character count. Default ({_DEFAULT_ANSWER_LIMIT})
   applies when no explicit limit is given.

=== YOUR TASK ===

Write a direct, specific answer to each question in the applicant's voice and only verified facts.
Output ONLY a JSON array preserving the original question order:

[{{"question": "<question text>", "answer": "<drafted answer>"}}, ...]

No prose outside the JSON. No markdown fences."""

    try:
        response = call_llm(prompt)
        answers = _extract_json(response, array=True)
        return {"success": True, "answers": answers}
    except Exception as e:
        return {"success": False, "error": str(e)}


def generate_questions(
    profile: dict,
    job_title,
    org_name,
    job_description,
    org_about="",
    prior_qa: list[dict] | None = None,
):
    """Generate targeted questions to help the applicant recall relevant experiences."""
    name = profile_mod.applicant_name(profile)
    prior_qa_section = ""
    if prior_qa:
        prior_qa_section = (
            "\n=== QUESTIONS ALREADY ANSWERED — do NOT ask these again ==="
            "\nThe applicant has ALREADY answered the following. Do NOT ask about them again;"
            " ask only about remaining gaps. If nothing meaningful remains, return an empty array [].\n"
        )
        for qa in prior_qa:
            prior_qa_section += f"\nQ: {qa['question']}\nA: {qa['answer']}\n"

    prompt = f"""You are helping {name} prepare to apply for a job. Before writing the cover letter,
gather specific stories and experiences that relate to this position.

=== TARGET JOB ===
Job Title: {job_title}
Organization: {org_name}

Job Description:
{job_description}

About the Organization:
{org_about if org_about else "Not provided"}
{prior_qa_section}
=== YOUR TASK ===

Analyze this job description and generate 4-5 specific, targeted questions that will help the
applicant recall and articulate relevant experiences for the cover letter.

GUIDELINES:
- Ask about SPECIFIC experiences, projects, or accomplishments (not general questions)
- Each question should tie directly to a key requirement or skill in the job description
- Questions should prompt storytelling with details, numbers, and outcomes
- Focus on experiences that may NOT be fully detailed in a resume
- Ask about situations, challenges overcome, or impact created

EXAMPLE GOOD QUESTIONS:
- "Can you describe a time when you designed or improved a system? What metrics did you track and what decisions did the data inform?"
- "Tell me about a project where you built capacity in a team with limited resources. How did you approach it and what was the outcome?"

EXAMPLE BAD QUESTIONS:
- "Do you have experience with this?" (too general, yes/no)
- "What are your strengths?" (too generic, not job-specific)

Respond with ONLY a JSON array of 4-5 question strings, no other text:
["Question 1", "Question 2", "Question 3", "Question 4", "Question 5"]
"""

    try:
        response = call_llm(prompt)
        json_match = re.search(r"\[[\s\S]*\]", response)
        if not json_match:
            raise ValueError("No JSON array found in response")
        questions = json.loads(json_match.group())
        return {"success": True, "questions": questions}
    except Exception as e:
        return {"success": False, "error": str(e)}


_COVER_LETTER_SPLIT = re.compile(
    r"(##\s*1\.\s*TAILORED COVER LETTER\s*\n)(.*?)(\n##\s*2\.)",
    re.DOTALL | re.IGNORECASE,
)


def polish_cover_letter_section(draft: str, profile: dict) -> str:
    """Second pass: scrub AI tells and tighten voice on the cover-letter section only."""
    match = _COVER_LETTER_SPLIT.search(draft)
    if not match:
        return draft

    header, cover_letter, tail_marker = (
        match.group(1),
        match.group(2).strip(),
        match.group(3),
    )
    voice_block = profile_mod.build_voice_fingerprint(profile)

    polish_prompt = f"""You are revising a draft cover letter to remove AI tells and tighten the
voice match. Here is the writer's voice fingerprint:

{voice_block}

Here is the draft cover letter to revise:

---DRAFT---
{cover_letter}
---END DRAFT---

Your task: rewrite the cover letter to fix any of the following, while preserving substance,
structure, and every factual claim:
1. Phrases on the "Do NOT use" list — replace with voice-matching alternatives.
2. Generic AI cadence — triadic flourishes, hollow superlatives, meta-statements about being thrilled or excited.
3. Sentences that don't sound like the voice exemplars — adjust rhythm, register, and connective phrasing.
4. Closing lines that summarize the letter — replace with a characteristic closer.

Constraints:
- Do not invent new facts, numbers, organizations, or stories. Every concrete claim must already be in the draft.
- Keep the same paragraphs and overall flow; this is a voice pass, not a structural rewrite.
- Output ONLY the revised cover letter — no preamble, no explanation, no markdown fences, no after-notes."""

    polished = call_llm(polish_prompt).strip()
    if not polished:
        return draft
    return f"{draft[: match.start()]}{header}{polished}\n{tail_marker}{draft[match.end() :]}"


def _build_generation_prompt(
    profile: dict,
    job_title: str,
    org_name: str,
    job_description: str,
    org_about: str,
    additional_notes: str,
    experience_answers,
    application_answers: list[dict] | None = None,
) -> str:
    name = profile_mod.applicant_name(profile)
    profile_block = profile_mod.build_profile_summary(profile)
    voice_block = profile_mod.build_voice_fingerprint(profile)
    stories_block = profile_mod.build_stories_block(profile)

    experience_section = ""
    if experience_answers:
        experience_section = f"\n=== {name.upper()}'S RELEVANT EXPERIENCES & STORIES FOR THIS ROLE (USE THESE) ===\n"
        for qa in experience_answers:
            experience_section += f"\nQ: {qa['question']}\nA: {qa['answer']}\n"

    application_answers_section = ""
    if application_answers:
        application_answers_section = (
            "\n=== APPLICATION ANSWERS THE APPLICANT IS ALREADY SUBMITTING FOR THIS ROLE ===\n"
            "The cover letter must NOT duplicate this content; cover different ground.\n"
        )
        for qa in application_answers:
            application_answers_section += f"\nQ: {qa['question']}\nA: {qa['answer']}\n"

    return f"""You are helping {name} write a tailored cover letter and prepare an application
package for a specific job. Match {name}'s voice precisely and rely only on facts present in the
inputs below.

{voice_block}

{stories_block}

{profile_block}
{experience_section}

=== TARGET JOB ===
Job Title: {job_title}
Organization: {org_name}

Job Description:
{job_description}

About the Organization:
{org_about if org_about else "Not provided"}

Additional Notes from the applicant:
{additional_notes if additional_notes else "None"}
{application_answers_section}
{_hard_constraints(name)}

=== YOUR TASK ===

Generate three sections, in this order, with the headers exactly as shown:

## 1. TAILORED COVER LETTER

Write a complete cover letter for {name} applying to this position.

- DO NOT simply repeat or rephrase content from the resume
- USE the specific stories and answers shared above; add details and context not already in the resume
- Reference the organization's mission/values if provided
- Keep it to one page (about 4 paragraphs of substantive prose)
- Use today's date
- Address to "Dear Hiring Manager" unless a name is known
- Close with the applicant's standard pattern (see voice fingerprint)

## 2. RESUME TAILORING SUGGESTIONS

Based on the job requirements, suggest:
- Which points from the background to emphasize or move to the top
- Any bullets that should be reworded to better match job keywords (give the rewrite verbatim)
- Skills to highlight
- Any gaps to address in the cover letter

## 3. JOB FIT ANALYSIS

Provide:
- Match score (0-100) with one-sentence explanation
- Top 3 strengths the applicant brings to this role
- Top 2-3 potential concerns and concrete reframes
- 3-4 talking points for an interview

Format your response with clear headers using ## for main sections and --- for subsections."""


def generate_cover_letter(
    profile: dict,
    job_title,
    org_name,
    job_description,
    org_about="",
    additional_notes="",
    experience_answers=None,
    application_answers: list[dict] | None = None,
    polish: bool = True,
) -> dict:
    """Generate a tailored cover letter and resume suggestions via the selected provider."""
    prompt = _build_generation_prompt(
        profile,
        job_title,
        org_name,
        job_description,
        org_about,
        additional_notes,
        experience_answers,
        application_answers,
    )
    try:
        draft = call_llm(prompt)
        final = polish_cover_letter_section(draft, profile) if polish else draft
        return {
            "success": True,
            "content": final,
            "polished": polish,
            "job_title": job_title,
            "org_name": org_name,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "job_title": job_title,
            "org_name": org_name,
        }
