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

## B. Browser walkthrough package — IMPLEMENTED (interactive handoff)

**Status (2026-06-15):** Shipped as the `browser_chat` provider. Refined from
per-step paste round-trips into a single self-contained interactive prompt: the app
does all deterministic work locally (parsing, regex contact, org crawl, prompt
assembly, `.docx`) and emits one prompt the user pastes once; the chat then walks
them through fit → questions → draft → AI-tells rewrite → coaching → refine →
optional coverage review. Design: `docs/superpowers/specs/2026-06-15-browser-chat-handoff-design.md`.
Modules: `handoff.py`, `providers/detect.py` (`browser_chat`), `app.py`
(`/build-handoff-prompt`), `templates/index.html`.

The original per-step "guided manual" sketch below is kept for history.

### Problem

Today a user with only a consumer chat subscription (claude.ai, ChatGPT web) and
no API key / supported CLI cannot generate in-app. The supported bridge is the
official CLI; a web tab alone can't be driven. For those users the app should be
able to **walk them through doing it by hand in their own chat tab**, assembling
the right prompt locally and guiding paste-in/paste-back.

### Approach: "guided manual" mode (no automation of the chat site)

Do **not** attempt to script or inject into claude.ai / ChatGPT. Their ToS forbids
automation, anti-bot defenses break it, and it is fragile. Instead add a provider
kind `manual` that turns the app into a copy/paste coach:

1. The app builds the exact prompt locally (it already does, in `generator.py`).
2. Instead of calling a provider, it shows the prompt in a copy box plus a
   "1 → 2 → 3" walkthrough: *Open your chat tab → paste this → paste the reply
   back here.*
3. A "paste the model's response here" textarea feeds the response back into the
   same parse path (`_extract_json`, section split, polish-skip) the providers use.
4. Each step (fit check, questions, draft answers, generate, refine) gets the same
   build-prompt → copy → paste-back loop. State stays client-side.

This needs no new dependency and no browser extension. It is the honest version of
"walk the person interactively through the steps."

### Optional later: a browser-extension helper

If true one-click injection is ever wanted, the only defensible form is a
**user-installed browser extension** the user explicitly adds (not a server-side
injection). It would:

- expose a "send to active chat tab" button via the extension's content script;
- read the assembled prompt from the local app (same-origin message or copy);
- paste it into the chat composer and read back the response DOM.

Risks to weigh before building: chat-site ToS on automation, DOM churn breaking the
content script, and the maintenance burden of per-site selectors. Treat as research,
not a near-term feature. The guided-manual mode (above) covers the same user need
with none of these risks and should ship first.

### Interactive intake idea (from notes)

The notes also asked for an LLM-driven interactive intake that walks the user
through pasting resume/LinkedIn/job links and then offers letter / answers /
interview prep. The current import-first UI already covers the *intake* half
(upload resume, samples, job, org). The *conversational* half — a chat-style
guide that asks "what do you want help with next?" — could sit on top of the
`manual` mode above, or any configured provider, as a thin scripted wizard. Spec
it separately if pursued.
