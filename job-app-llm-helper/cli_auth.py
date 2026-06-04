# cli_auth.py
"""Help the user connect a subscription-backed CLI (Claude Code / Codex / Gemini).

These CLIs authenticate with the user's *subscription account* through their own
browser OAuth flow — there is no third-party API to a consumer subscription, so the
official CLI is the supported bridge. This module:

  * checks whether a CLI is installed and actually logged in (an authoritative probe
    — it runs a one-token generation, since "on PATH" does not mean "authenticated");
  * best-effort launches the CLI's login in a visible terminal so the browser sign-in
    opens (always falling back to a copyable manual command);
  * exposes install metadata.

SELF-HOST ONLY: launching a terminal + browser and running the CLI happens on the
machine running this app. Do not expose this app as a shared server.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile

# name -> binary on PATH
BINARY = {
    "claude_cli": "claude",
    "gemini_cli": "gemini",
    "codex_cli": "codex",
}

# Authoritative login probe: a minimal non-interactive generation. Returncode 0 with
# output ⇒ authenticated. Mirrors providers/adapters/cli.py invocation styles; Claude
# pins a cheap model to keep the probe fast/inexpensive.
_PROBE_CMD = {
    "claude_cli": ["claude", "--print", "--no-session-persistence", "--model", "haiku"],
    "gemini_cli": ["gemini", "-p", "-"],
    "codex_cli": ["codex", "exec", "-"],
}
_PROBE_INPUT = "Reply with the single word: ok"
_PROBE_TIMEOUT = 30

# Command the user runs to authenticate. Running the bare CLI the first time triggers
# its login (which opens the browser sign-in for the subscription account).
LOGIN_COMMAND = {
    "claude_cli": "claude",
    "gemini_cli": "gemini",
    "codex_cli": "codex",
}

# (display, docs URL, npm package) — npm install works cross-platform (needs Node.js).
INSTALL = {
    "claude_cli": (
        "Claude Code",
        "https://docs.anthropic.com/en/docs/claude-code",
        "@anthropic-ai/claude-code",
    ),
    "gemini_cli": (
        "Gemini CLI",
        "https://github.com/google-gemini/gemini-cli",
        "@google/gemini-cli",
    ),
    "codex_cli": ("Codex CLI", "https://github.com/openai/codex", "@openai/codex"),
}


def is_installed(name: str) -> bool:
    binary = BINARY.get(name)
    return bool(binary and shutil.which(binary))


def is_logged_in(name: str) -> bool:
    """Authoritatively test whether the CLI can generate (i.e. is logged in).

    Runs a tiny generation with a short timeout. Any non-zero exit, empty output, or
    timeout ⇒ not usable yet (not installed, not logged in, or rate-limited).
    """
    if not is_installed(name):
        return False
    cmd = _PROBE_CMD.get(name)
    if not cmd:
        return False
    try:
        result = subprocess.run(
            cmd,
            input=_PROBE_INPUT,
            capture_output=True,
            text=True,
            timeout=_PROBE_TIMEOUT,
            cwd=tempfile.gettempdir(),
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


def status(name: str) -> dict:
    """Return {installed, logged_in, login_command, install:{...}} for the UI."""
    display, url, pkg = INSTALL.get(name, ("", "", ""))
    installed = is_installed(name)
    return {
        "name": name,
        "installed": installed,
        # Skip the (paid) probe when the binary is absent — it can't be logged in.
        "logged_in": is_logged_in(name) if installed else False,
        "login_command": LOGIN_COMMAND.get(name, ""),
        "install": {"display": display, "url": url, "npm": pkg},
    }


def _terminal_launch(command: str) -> bool:
    """Best-effort: open a visible terminal running `command`. Returns success.

    `command` is built only from our fixed LOGIN_COMMAND constants — never user input
    — so embedding it in the platform launchers below is safe.
    """
    try:
        if sys.platform == "darwin":
            script = f'tell application "Terminal" to do script "{command}"'
            subprocess.Popen(["osascript", "-e", script])
            subprocess.Popen(
                ["osascript", "-e", 'tell application "Terminal" to activate']
            )
            return True
        if sys.platform.startswith("win"):
            subprocess.Popen(["cmd", "/c", "start", "cmd", "/k", command])
            return True
        # Linux/other: try common terminal emulators in order.
        for term, args in (
            ("x-terminal-emulator", ["-e"]),
            ("gnome-terminal", ["--"]),
            ("konsole", ["-e"]),
            ("xterm", ["-e"]),
        ):
            if shutil.which(term):
                subprocess.Popen(
                    [
                        term,
                        *args,
                        "bash",
                        "-lc",
                        f"{command}; echo; read -p 'Press Enter to close.'",
                    ]
                )
                return True
        return False
    except OSError:
        return False


def launch_login(name: str) -> dict:
    """Try to open the CLI's login in a terminal. Always returns the manual command too."""
    if name not in LOGIN_COMMAND:
        return {
            "launched": False,
            "login_command": "",
            "error": f"unknown provider {name!r}",
        }
    if not is_installed(name):
        display, url, pkg = INSTALL.get(name, ("", "", ""))
        return {
            "launched": False,
            "login_command": LOGIN_COMMAND[name],
            "error": f"{display or name} is not installed",
            "install": {"display": display, "url": url, "npm": pkg},
        }
    command = LOGIN_COMMAND[name]
    launched = _terminal_launch(command)
    return {"launched": launched, "login_command": command}
