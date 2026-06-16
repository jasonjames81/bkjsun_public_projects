"""Browser-chat handoff: assemble one self-contained, interactive prompt the user
pastes into their own logged-in chat tab (claude.ai, ChatGPT, etc.).

Pure module — no network, subprocess, or filesystem I/O. The caller supplies the
already-parsed materials (sources.py / regex / profile blocks have run upstream).
This keeps the keyless path and the provider path from drifting on context format.
"""

from __future__ import annotations

import profile as profile_mod

# Cap the job description so an oversized paste can't blow past the chat's context.
# The employer's website is NOT inlined — we hand the chat the URL and let it fetch
# the page itself, so there's no crawled-text cap to apply.
_JOB_CAP = 8000

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
Work through these steps in order, one at a time. After each step, stop and wait for
my reply before the next. Keep every reply tight: no preamble, no recap of my
materials, no "here is what I'll do" — just do the step. Brief is better.

1. In 2-3 sentences, give your read of my fit for the role: where I match and where
   I am light.
2. Ask only the clarifying questions you actually need before drafting (skip this if
   you have none).
3. Research the employer (see EMPLOYER below) and draft the cover letter: about one
   page, four paragraphs, plain prose.
4. AI-TELLS REWRITE: review your own draft for phrasing that reads machine-generated
   and rewrite it into plain, specific language. Watch especially for:
{ai_tells}
5. Give résumé-tailoring tips and interview-prep talking points grounded only in my
   real background above — as short bullets, not prose.
6. Refine the letter on my request.
7. OPTIONAL COVERAGE REVIEW: ask whether I want a final check. If I say yes, list the
   job posting's key requirements and show how the letter addresses each, flagging any
   gaps."""


def _cap(text: str, limit: int) -> str:
    text = (text or "").strip()
    return text[:limit]


def _org_block(org_name: str, org_url: str) -> str:
    """Tell the chat to research the employer ITSELF rather than inlining crawled text.

    Consumer chats (claude.ai, ChatGPT) can browse, so handing over the URL yields
    cleaner grounding than pasting disorganized site text — and keeps the prompt short.
    """
    org_name = (org_name or "").strip()
    url = (org_url or "").strip()
    header = f"=== EMPLOYER: {org_name} ===" if org_name else "=== EMPLOYER ==="
    if url:
        return (
            f"{header}\n"
            f"Research this employer yourself before drafting: open {url} (and its "
            "about / mission / news pages) with your web browsing and use what you find "
            "to ground the letter. If you can't browse, say so and I'll paste the text."
        )
    return (
        f"{header}\n"
        "Use what you reliably know about this organization; if you need more, ask me "
        "for their website link or mission text rather than guessing."
    )


def _samples_block(samples: list[str], num_samples: int, sample_chars: int) -> str:
    chosen = [(s or "").strip()[:sample_chars] for s in (samples or [])[:num_samples]]
    chosen = [s for s in chosen if s]
    if not chosen:
        return ""
    parts = ["=== MY WRITING SAMPLES (match this voice) ==="]
    for i, s in enumerate(chosen, 1):
        parts.append(f"\n--- WRITING SAMPLE {i} ---\n{s}")
    return "\n".join(parts)


def build_handoff_prompt(
    profile: dict,
    job_title: str,
    org_name: str,
    job_description: str,
    org_url: str,
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
    sections.append(_org_block(org_name, org_url))
    return "\n\n".join(s for s in sections if s.strip())
