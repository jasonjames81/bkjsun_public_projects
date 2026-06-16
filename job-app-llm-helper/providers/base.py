"""Core provider types: the Provider protocol, value objects, error, and tier heuristic.

Pure data + logic only — no subprocess, network, or filesystem I/O lives here.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


class QualityTier(enum.Enum):
    BEST = "best"
    GOOD = "good"
    BASIC = "basic"


@dataclass
class ProviderInfo:
    name: str  # stable id, e.g. "anthropic_api"
    display_name: str  # human label, e.g. "Anthropic (API key)"
    kind: str  # "cli" | "api" | "local" | "manual"
    available: bool
    detail: str  # e.g. "found on PATH — may require login"
    tier: QualityTier
    model: str | None  # selected/default model; "(CLI default)" for opaque CLIs
    tier_verified: bool = True  # False when tier was guessed for an unknown model


class ProviderError(Exception):
    """Raised by any adapter when generation cannot complete.

    The message is user-facing (e.g. shown in the UI) and MUST never contain
    secrets — adapters redact keys before constructing it.
    """


@runtime_checkable
class Provider(Protocol):
    info: ProviderInfo

    def generate(self, prompt: str) -> str: ...


# Keyword heuristics — NO full version strings, so new model releases need no code change.
_BEST_KEYWORDS = ("opus", "sonnet", "gpt-5", "pro")
_GOOD_KEYWORDS = ("haiku", "mini", "nano", "flash", "lite")


def estimate_tier(model: str | None, kind: str) -> tuple[QualityTier, bool]:
    """Estimate a model's quality tier from its name.

    Returns (tier, verified). ``verified`` is False when the name matched no
    keyword and we fell back to GOOD — the UI flags that as "unverified".
    Local models are always BASIC (and considered verified — it's a known floor).
    """
    if kind == "local":
        return QualityTier.BASIC, True
    name = (model or "").lower()
    if any(kw in name for kw in _BEST_KEYWORDS):
        return QualityTier.BEST, True
    if any(kw in name for kw in _GOOD_KEYWORDS):
        return QualityTier.GOOD, True
    return QualityTier.GOOD, False
