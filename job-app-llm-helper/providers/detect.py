"""detect_providers(): report every known provider with availability + reason.

Detection is cheap and never blocks: CLIs are checked with shutil.which (presence
≠ logged in — auth failures surface at generate time); API keys are checked against
config/env (validated lazily on first use); Ollama is probed with a short-timeout
tags request.
"""

from __future__ import annotations

import shutil

from providers.adapters.ollama import list_local_models
from providers.base import ProviderInfo, QualityTier, estimate_tier
from providers.config import ENV_VARS, ProviderConfig

_CLIS = [
    ("claude_cli", "Claude Code (CLI login)", "claude"),
    ("gemini_cli", "Gemini (CLI login)", "gemini"),
    ("codex_cli", "Codex (CLI login)", "codex"),
]
_APIS = [
    ("anthropic_api", "Anthropic (API key)"),
    ("openai_api", "OpenAI (API key)"),
    ("google_api", "Google Gemini (API key)"),
]


def detect_providers(config: ProviderConfig) -> list[ProviderInfo]:
    infos: list[ProviderInfo] = []

    for name, display, binary in _CLIS:
        present = shutil.which(binary) is not None
        model = config.get_model(name)
        tier, verified = estimate_tier(model, "cli")
        infos.append(
            ProviderInfo(
                name=name,
                display_name=display,
                kind="cli",
                available=present,
                detail=(
                    f"found on PATH — may require `{binary}` login"
                    if present
                    else f"{binary} not found on PATH"
                ),
                tier=tier,
                model=model or "(CLI default)",
                tier_verified=verified,
            )
        )

    for name, display in _APIS:
        has_stored = config.get_key(name) is not None
        env_var = ENV_VARS.get(name)
        has_env = config.has_env_key(name)
        model = config.get_model(name)
        tier, verified = estimate_tier(model, "api")
        if has_env:
            detail = f"key in ${env_var} (used without storing)"
        elif has_stored:
            detail = "key stored"
        else:
            detail = "no API key — enter one to enable"
        infos.append(
            ProviderInfo(
                name=name,
                display_name=display,
                kind="api",
                available=has_stored or has_env,
                detail=detail,
                tier=tier,
                model=model,
                tier_verified=verified,
            )
        )

    local_models = list_local_models()
    infos.append(
        ProviderInfo(
            name="ollama",
            display_name="Ollama (local model)",
            kind="local",
            available=bool(local_models),
            detail=(
                f"running, {len(local_models)} model(s)"
                if local_models
                else "not running (start Ollama to enable)"
            ),
            tier=QualityTier.BASIC,
            model=config.get_model("ollama")
            or (local_models[0] if local_models else None),
            tier_verified=True,
        )
    )

    infos.append(
        ProviderInfo(
            name="browser_chat",
            display_name="Browser AI (paste prompt — claude.ai, ChatGPT, etc.)",
            kind="manual",
            available=True,
            detail="no key or install needed — you paste into your own chat tab",
            tier=QualityTier.BEST,
            model=None,
            tier_verified=False,
        )
    )

    return infos
