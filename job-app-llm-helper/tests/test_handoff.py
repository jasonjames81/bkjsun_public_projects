"""Pure unit tests for the browser-chat handoff prompt packager (no network)."""

import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

import handoff  # noqa: E402
import pytest  # noqa: E402

from providers.base import ProviderError  # noqa: E402
from providers.config import ProviderConfig  # noqa: E402
from providers.detect import detect_providers  # noqa: E402
from providers.registry import get_provider, list_models  # noqa: E402

PROFILE = {
    "applicant_name": "Ada Lovelace",
    "contact": {"name": "Ada Lovelace", "email": "ada@example.com"},
    "background": "Mathematician. Wrote the first published algorithm for a machine.",
    "writing_samples": "",
}


def _build(**overrides):
    kwargs = dict(
        profile=PROFILE,
        job_title="Research Engineer",
        org_name="Analytical Engines Ltd",
        job_description="Build numerical methods for the Analytical Engine.",
        org_about="We advance mechanical computation for the public good.",
        samples=[],
        sample_chars=2000,
        num_samples=3,
    )
    kwargs.update(overrides)
    return handoff.build_handoff_prompt(**kwargs)


def test_prompt_includes_core_materials():
    out = _build()
    assert "Research Engineer" in out
    assert "Analytical Engines Ltd" in out
    assert "Build numerical methods" in out
    assert "advance mechanical computation" in out
    assert "Ada Lovelace" in out


def test_prompt_includes_interactive_steps():
    out = _build()
    assert "one at a time" in out.lower()
    assert "fit" in out.lower()
    assert "clarifying question" in out.lower()
    assert "draft" in out.lower()
    assert "interview" in out.lower()


def test_prompt_includes_ai_tells_review():
    out = _build()
    assert "AI" in out
    assert "I am excited to" in out
    assert "leverage" in out


def test_prompt_includes_optional_coverage_review():
    out = _build()
    assert "key requirement" in out.lower()
    assert "gap" in out.lower()


def test_samples_respect_count_and_length():
    samples = ["A" * 5000, "B" * 5000, "C" * 5000, "D" * 5000]
    out = _build(samples=samples, num_samples=2, sample_chars=100)
    assert "A" * 100 in out
    assert "B" * 100 in out
    assert "C" * 100 not in out
    assert "A" * 101 not in out


def test_no_samples_omits_voice_samples_block_without_error():
    out = _build(samples=[])
    assert "MY WRITING SAMPLES (match this voice)" not in out
    assert "--- WRITING SAMPLE" not in out


def test_empty_org_emits_ask_user_fallback():
    out = _build(org_about="")
    assert "paste" in out.lower()


def test_caps_bound_oversized_job_and_org():
    out = _build(
        job_description="J" * 20000,
        org_about="O" * 20000,
    )
    assert "J" * 8000 in out
    assert "J" * 8001 not in out
    assert "O" * 6000 in out
    assert "O" * 6001 not in out


def test_browser_chat_is_detected_and_available():
    infos = {i.name: i for i in detect_providers(ProviderConfig())}
    assert "browser_chat" in infos
    bc = infos["browser_chat"]
    assert bc.available is True
    assert bc.kind == "manual"


def test_get_provider_browser_chat_raises():
    with pytest.raises(ProviderError):
        get_provider("browser_chat", ProviderConfig())


def test_list_models_browser_chat_empty():
    assert list_models("browser_chat", ProviderConfig()) == []
