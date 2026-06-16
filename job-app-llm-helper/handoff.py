"""Browser-chat handoff: assemble one self-contained, interactive prompt the user
pastes into their own logged-in chat tab (claude.ai, ChatGPT, etc.).

Pure module — no network, subprocess, or filesystem I/O. The caller supplies the
already-parsed materials (sources.py / regex / profile blocks have run upstream).
This keeps the keyless path and the provider path from drifting on context format.
"""

from __future__ import annotations

import profile as profile_mod

# Per-section caps mirror generator.py's snippet cap (text[:6000]); keep the prompt
# bounded no matter how large the pasted inputs are.
_JOB_CAP = 8000
_ORG_CAP = 6000

# AI-tells the chat must catch and rewrite in step 5. Named explicitly so the chat
# has concrete targets rather than a vague "sound human" instruction.
_AI_TELLS = [
    'generic openers like "I am writing to express my interest"',
    '"I am excited to"',
    '"leverage"',
    '"passionate about"',
    '"in today\'s fast-paced world"',
    '"hollow superlatives" (world-class, cutting-edge, seamless)',
    "em-dash overuse and tidy three-part lists",
]

_STEPS = """\
Work through these steps one at a time. After each step, stop and wait for my reply
before moving to the next:

1. Confirm you understand my background and the role (one short paragraph).
2. Give a brief fit assessment: where I match the role and where I am light.
3. Ask me any clarifying questions you need before drafting.
4. Draft the cover letter (about one page, four paragraphs, plain prose).
5. AI-TELLS REWRITE: review your own draft for phrasing that reads machine-generated
   and rewrite it into plain, specific language. Watch especially for:
{ai_tells}
6. Give résumé-tailoring tips and interview-prep talking points grounded only in my
   real background above.
7. Refine the letter on my request.
8. OPTIONAL COVERAGE REVIEW: ask whether I want a final check. If I say yes, list the
   job posting's key requirements and show how the letter addresses each, flagging any
   gaps."""


def _cap(text: str, limit: int) -> str:
    text = (text or "").strip()
    return text[:limit]


def _samples_block(samples: list[str], num_samples: int, sample_chars: int) -> str:
    chosen = [(s or "").strip()[:sample_chars] for s in (samples or [])[:num_samples]]
    chosen = [s for s in chosen if s]
    if not chosen:
        return ""
    parts = ["=== MY WRITING SAMPLES (match this voice) ==="]
    for i, s in enumerate(chosen, 1):
        parts.append(f"\n--- WRITING SAMPLE {i} ---\n{s}")
    return "\n".join(parts)


def _org_block(org_name: str, org_about: str) -> str:
    cleaned = _cap(org_about, _ORG_CAP)
    if not cleaned:
        return (
            f"=== EMPLOYER: {org_name} ===\n"
            "No website text was captured. Ask me to paste the organization's About / "
            "mission text, or proceed without it if I prefer."
        )
    return (
        f"=== EMPLOYER: {org_name} ===\n"
        "Below is raw text crawled from the employer's website. Use it to infer their "
        "mission, values, and any recent news, and weave relevant points into the "
        "letter. It is raw — ignore navigation and boilerplate.\n\n"
        f"{cleaned}"
    )


def build_handoff_prompt(
    profile: dict,
    job_title: str,
    org_name: str,
    job_description: str,
    org_about: str,
    samples: list[str],
    *,
    sample_chars: int,
    num_samples: int,
) -> str:
    """Assemble one interactive prompt the user pastes into their own chat tab.

    ``samples`` is a pre-split list of writing-sample chunks; the first
    ``num_samples`` are used, each capped to ``sample_chars`` characters.
    """
    name = profile_mod.applicant_name(profile)
    profile_block = profile_mod.build_profile_summary(profile)
    voice_block = profile_mod.build_voice_fingerprint(profile)
    samples_block = _samples_block(samples, num_samples, sample_chars)
    steps = _STEPS.format(ai_tells="\n".join(f"   - {t}" for t in _AI_TELLS))

    sections = [
        f"You are helping me tailor a job application. I am {name}. {steps}",
        profile_block,
    ]
    if samples_block:
        sections.append(samples_block)
    sections.append(voice_block)
    sections.append(
        f"=== TARGET ROLE ===\nJob Title: {job_title}\nOrganization: {org_name}\n\n"
        f"Job Description:\n{_cap(job_description, _JOB_CAP)}"
    )
    sections.append(_org_block(org_name, org_about))
    return "\n\n".join(s for s in sections if s.strip())
