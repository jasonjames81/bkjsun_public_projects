# Provider roadmap

Design notes for expanding how the app reaches an LLM. Two threads: (A) the
proposed `agy` / Antigravity CLI provider, and (B) a browser-side walkthrough
package for users who only have a chat subscription (claude.ai / ChatGPT) and no
API key or supported CLI.

---

## A. Antigravity CLI (`agy`) — NOT wired (blocked)

Antigravity's CLI (`agy`) was proposed as a replacement for the Gemini CLI
provider. Empirical testing on 2026-06-15 shows it is **unsuitable as a drop-in
text-generation provider**, and the swap is on hold.

What was found running `agy` locally:

- **It is an agent, not a generator.** `agy --print "<prompt>"` does not just answer
  — it autonomously runs tools first: it listed the working directory, read files
  across `/home/jsun` (CLAUDE.md, AGENTS.md, `.remember/now.md`, `~/.gemini`,
  `~/.codex/hooks.json`), and ran `git status`, all before producing the reply.
- **`--sandbox` does not contain it.** With `--sandbox` and an empty working
  directory, it still roamed the home directory and read arbitrary files.
- **No flag disables tool use.** Available flags: `--print/-p`, `--model`,
  `--print-timeout`, `--sandbox`, `--dangerously-skip-permissions`,
  `--continue`, `--conversation`, `--prompt-interactive`, `--add-dir`,
  `--log-file`. None turn off the agent loop.
- **Prompt is an argv value, not stdin.** `agy --print` takes the prompt as the
  flag argument (`flag needs an argument: -print` when piped). The existing CLI
  adapter pipes via stdin, so `agy` would need a custom code path.
- **Slow.** Many tool round-trips per call; far slower than a single generation.

Why this matters for a **public, self-hosted** tool: a provider that reads
arbitrary files on the host during a routine cover-letter generation is a privacy
and safety problem, and the latency is poor. Shipping it as a default-looking
"(CLI login)" option would surprise users.

**Recommendation:** keep `gemini_cli` as-is; do not add `agy` as a generation
provider until Antigravity exposes a non-agentic "generate only" mode (no tools,
stdin or arg prompt, bounded latency). If/when it does, wiring is small: a new
`AgyCli` adapter (`binary = "agy"`, prompt passed as `--print <prompt>` arg,
`model_flag = "--model"`, `neutral_cwd = True`) plus entries in
`cli_auth.py` (`BINARY`/`_PROBE_CMD`/`LOGIN_COMMAND`/`INSTALL`),
`providers/detect.py` (`_CLIS`), and `providers/registry.py` (`get_provider`).

**Decision (2026-06-15):** keep `gemini_cli`; do not wire `agy` until it offers a
non-agentic generate-only mode. No code change made.

---

## B. Browser walkthrough package — REMOVED (replaced by platform-native guide)

The browser-chat handoff feature (code + `/build-handoff-prompt` route) was
removed in v0.3.0 (commit `6d8e20c`). It was replaced by a simpler,
maintenance-free approach: a guide that teaches users to set up platform-native
assistants using Claude Projects, ChatGPT Projects, or Gemini Gems — no app
code needed. See `platform-guide/` and the README §1.

The original design docs are archived:
- `docs/superpowers/specs/2026-06-15-browser-chat-handoff-design.md`
- `docs/superpowers/plans/2026-06-15-browser-chat-handoff.md`
