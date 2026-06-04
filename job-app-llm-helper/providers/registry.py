"""The one place that maps a provider name to a concrete adapter instance.

get_provider() builds the selected adapter from ProviderConfig (resolving keys,
models, and timeouts). list_models() fetches the live model list for the UI
dropdown — live so new releases need no code change. Default model resolution
prefers a family keyword, else the first listed model; never a pinned version.
"""

from __future__ import annotations

import config as app_config
from providers.adapters.api import AnthropicApi, GoogleApi, OpenAiApi
from providers.adapters.cli import ClaudeCli, CodexCli, GeminiCli
from providers.adapters.ollama import OllamaProvider, list_local_models
from providers.base import Provider, ProviderError
from providers.config import ProviderConfig

PREFERRED_FAMILY = {
    "anthropic_api": "sonnet",
    "openai_api": "gpt",
    "google_api": "pro",
}


def _cli_timeout() -> int:
    return getattr(app_config, "CLAUDE_TIMEOUT_SECONDS", 300)


def get_provider(name: str | None, config: ProviderConfig) -> Provider:
    if not name:
        raise ProviderError("No provider selected. Open settings and choose one.")

    if name == "claude_cli":
        model = config.get_model("claude_cli") or app_config.CLAUDE_MODEL
        return ClaudeCli(model=model, timeout=_cli_timeout())
    if name == "gemini_cli":
        return GeminiCli(model=config.get_model("gemini_cli"), timeout=_cli_timeout())
    if name == "codex_cli":
        return CodexCli(model=config.get_model("codex_cli"), timeout=_cli_timeout())

    if name == "anthropic_api":
        return AnthropicApi(
            api_key=config.resolve_key(name), model=config.get_model(name)
        )
    if name == "openai_api":
        return OpenAiApi(api_key=config.resolve_key(name), model=config.get_model(name))
    if name == "google_api":
        return GoogleApi(api_key=config.resolve_key(name), model=config.get_model(name))

    if name == "ollama":
        model = config.get_model("ollama")
        if model is None:
            local = list_local_models()
            model = local[0] if local else None
        return OllamaProvider(model=model)

    raise ProviderError(f"Unknown provider: {name!r}")


def list_models(name: str, config: ProviderConfig) -> list[str]:
    """Live model list for the UI dropdown. Empty list = none / not fetchable.

    CLI providers return [] (their model set is opaque; user types a model or
    uses the CLI default). API providers query their list endpoint lazily.
    """
    if name == "ollama":
        return list_local_models()
    if name in PREFERRED_FAMILY:
        return _list_api_models(name, config)
    return []


def _list_api_models(name: str, config: ProviderConfig) -> list[str]:
    key = config.resolve_key(name)
    if not key:
        return []
    try:
        if name == "anthropic_api":
            from anthropic import Anthropic

            return [m.id for m in Anthropic(api_key=key).models.list()]
        if name == "openai_api":
            from openai import OpenAI

            return [m.id for m in OpenAI(api_key=key).models.list()]
        if name == "google_api":
            import google.generativeai as genai

            genai.configure(api_key=key)
            return [m.name for m in genai.list_models()]
    except Exception:
        return []
    return []


def resolve_default_model(name: str, available: list[str]) -> str | None:
    """Pick a sensible default from a live model list using the family keyword."""
    if not available:
        return None
    family = PREFERRED_FAMILY.get(name)
    if family:
        preferred = [m for m in available if family in m.lower()]
        if preferred:
            return preferred[0]
    return available[0]
