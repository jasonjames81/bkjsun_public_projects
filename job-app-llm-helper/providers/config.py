"""User selection + key storage for providers.

Storage decision (from the spec): plaintext JSON, chmod 600. No OS keyring —
its Linux backend is too unreliable for a "runs anywhere" app. Env vars take
precedence over stored keys and can be used without storing.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from platformdirs import user_config_dir

_APP_DIRNAME = "job-app-llm-helper"

ENV_VARS: dict[str, str] = {
    "anthropic_api": "ANTHROPIC_API_KEY",
    "openai_api": "OPENAI_API_KEY",
    "google_api": "GOOGLE_API_KEY",
}


def default_config_path() -> Path:
    return Path(user_config_dir(_APP_DIRNAME)) / "config.json"


def _consent_message(path: Path) -> str:
    return (
        f"This key will be stored in plaintext at {path}, readable only by your "
        "account (file permissions 0600). It is never logged or included in exports."
    )


class ProviderConfig:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path is not None else default_config_path()
        self._selected: str | None = None
        self._models: dict[str, str] = {}
        self._api_keys: dict[str, str] = {}

    def load(self) -> "ProviderConfig":
        if self.path.exists():
            data = json.loads(self.path.read_text())
            self._selected = data.get("selected_provider")
            self._models = dict(data.get("selected_models", {}))
            self._api_keys = dict(data.get("api_keys", {}))
        return self

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "selected_provider": self._selected,
            "selected_models": self._models,
            "api_keys": self._api_keys,
        }
        self.path.write_text(json.dumps(payload, indent=2))
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    def selected(self) -> str | None:
        return self._selected

    def set_selected(self, name: str) -> None:
        self._selected = name

    def get_model(self, provider: str) -> str | None:
        return self._models.get(provider)

    def set_model(self, provider: str, model: str) -> None:
        self._models[provider] = model

    def get_key(self, provider: str) -> str | None:
        return self._api_keys.get(provider)

    def set_key(self, provider: str, key: str, *, on_consent=None) -> None:
        if on_consent is not None:
            on_consent(_consent_message(self.path))
        self._api_keys[provider] = key

    def has_env_key(self, provider: str) -> bool:
        env_var = ENV_VARS.get(provider)
        return bool(env_var and os.environ.get(env_var))

    def resolve_key(self, provider: str) -> str | None:
        env_var = ENV_VARS.get(provider)
        if env_var and os.environ.get(env_var):
            return os.environ[env_var]
        return self._api_keys.get(provider)
