# config.py
"""App-wide settings for the public cover-letter helper.

Unlike the personal edition, there are no local document paths here — the applicant
profile is supplied at runtime by the browser (see profile.py). These settings only
tune the default Claude-CLI model and subprocess timeout used by the provider layer.
Users who pick an API key or Ollama provider in the UI are unaffected by CLAUDE_MODEL.
"""

# Default model for the Claude CLI provider when the user hasn't chosen one.
# "haiku" (fastest), "sonnet" (default), "opus" (highest quality), or None for CLI default.
CLAUDE_MODEL = "sonnet"

# Per-subprocess timeout (seconds) for CLI providers.
CLAUDE_TIMEOUT_SECONDS = 300
