"""Offline end-to-end smoke tests — no network, no real provider.

Monkeypatches generator.call_llm so the full prompt-build → parse → response path is
exercised against a canned model reply. Verifies the public app is de-personalized
(profile threads through) and the Flask routes wire up.
"""

import json
import sys
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

import generator  # noqa: E402
import profile as profile_mod  # noqa: E402
from app import app  # noqa: E402

SAMPLE_PROFILE = {
    "applicant_name": "Ada Lovelace",
    "contact": {
        "name": "Ada Lovelace",
        "city_state": "London, UK",
        "email": "ada@example.com",
    },
    "background": (
        "Mathematician and writer. Built the first published algorithm intended for a "
        "machine. Collaborated with Charles Babbage on the Analytical Engine, translating "
        "and extending Menabrea's memoir with extensive original notes."
    ),
    "writing_samples": "I believe the engine might act upon other things besides number.\n\n"
    "During my time studying the machine, I saw how symbols could be woven like a loom.",
    "stories": "Wrote Note G, the algorithm to compute Bernoulli numbers on the Analytical Engine.",
}

JOB = {
    "job_title": "Research Engineer",
    "org_name": "Analytical Engines Ltd",
    "job_description": "Seeking someone to design algorithms for novel computing machines.",
    "org_about": "We build mechanical computers.",
}


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_profile_blocks_are_depersonalized():
    summary = profile_mod.build_profile_summary(SAMPLE_PROFILE)
    assert "ADA LOVELACE" in summary
    assert "Jason" not in summary
    voice = profile_mod.build_voice_fingerprint(SAMPLE_PROFILE)
    assert "Jason" not in voice
    assert profile_mod.applicant_name(SAMPLE_PROFILE) == "Ada Lovelace"


def test_voice_fingerprint_without_samples():
    block = profile_mod.build_voice_fingerprint({"background": "x" * 50})
    assert "No writing samples" in block
    assert "Do NOT use" in block


def test_generate_route_threads_profile(client, monkeypatch):
    captured = {}
    canned = (
        "## 1. TAILORED COVER LETTER\n\n"
        "Dear Hiring Manager,\n\nI am applying for the Research Engineer role.\n\n"
        "Sincerely,\nAda Lovelace\n\n"
        "## 2. RESUME TAILORING SUGGESTIONS\n- emphasize algorithms\n\n"
        "## 3. JOB FIT ANALYSIS\nMatch score: 90\n"
    )

    def fake_call(prompt, **kw):
        captured["prompt"] = prompt
        return canned

    monkeypatch.setattr(generator, "call_llm", fake_call)

    res = client.post("/generate", json={**JOB, "profile": SAMPLE_PROFILE})
    body = res.get_json()
    assert body["success"], body
    assert "Research Engineer" in body["content"]
    # the applicant name, not Jason, reached the prompt
    assert "Ada Lovelace" in captured["prompt"]
    assert "Jason" not in captured["prompt"]


def test_analyze_fit_route(client, monkeypatch):
    monkeypatch.setattr(
        generator,
        "call_llm",
        lambda prompt, **kw: json.dumps(
            {
                "match_score": 88,
                "recommendation": "proceed",
                "rationale": "strong fit",
                "keywords_matched": ["algorithms"],
                "keywords_missing": [],
                "strengths": ["pioneering work"],
                "concerns": ["era gap"],
            }
        ),
    )
    res = client.post("/analyze-fit", json={**JOB, "profile": SAMPLE_PROFILE})
    body = res.get_json()
    assert body["success"] and body["recommendation"] == "proceed"


def test_generate_requires_background(client):
    res = client.post("/generate", json={**JOB, "profile": {"background": "too short"}})
    # job fields present, but downstream still runs; guard is on the client.
    # Here we assert the server doesn't crash and returns JSON.
    assert res.get_json() is not None


def test_download_docx_uses_profile_contact(client):
    content = (
        "## 1. TAILORED COVER LETTER\n\nDear Hiring Manager,\n\nBody paragraph.\n\n"
        "Sincerely,\nAda Lovelace\n\n## 2. RESUME TAILORING SUGGESTIONS\n- x\n"
    )
    res = client.post(
        "/download-docx",
        json={
            "content": content,
            "profile": SAMPLE_PROFILE,
            "job_title": "Research Engineer",
            "org_name": "Analytical Engines Ltd",
        },
    )
    assert res.status_code == 200
    assert res.data[:2] == b"PK"  # .docx is a zip
