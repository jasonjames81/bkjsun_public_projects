# sources.py
"""Load applicant background text from a local file path or a web URL.

Self-host model: the app runs on the user's own machine, so reading their local
files (a resume in Documents) and fetching public web links (a published Google Doc,
a personal site) is expected and safe.

SECURITY: do NOT expose this app as a shared multi-tenant server. Server-side URL
fetch would become an SSRF vector and local-path loading would read the host's
filesystem. This feature is intended for the single-user self-host model only.

Supported:
- Local .docx / .pdf via `pandoc` / `pdftotext` if installed; .txt / .md / .html read directly.
- http(s) URLs: fetched and reduced to readable text. A Google Doc must be
  "Published to the web" (or link-viewable) for its text to come through; private
  docs and most of LinkedIn require login and will not extract.
"""

from __future__ import annotations

import html as html_mod
import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

_TIMEOUT = 20
_MAX_BYTES = 5_000_000  # 5 MB cap on loaded/fetched content

# Google Docs "published to the web" page scaffolding to drop.
_GDOCS_BOILERPLATE = (
    "Published using Google Docs",
    "Report abuse",
    "Updated automatically every",
)


class SourceError(Exception):
    """Raised for any expected failure (missing file, bad URL, no text)."""


def _strip_html(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", raw)
    raw = re.sub(r"(?is)<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?is)</(p|div|li|h[1-6]|tr)>", "\n", raw)
    text = re.sub(r"(?s)<[^>]+>", " ", raw)
    text = html_mod.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _strip_gdocs_boilerplate(text: str) -> str:
    lines = text.splitlines()
    last = -1
    for i, line in enumerate(lines[:30]):
        if any(m in line for m in _GDOCS_BOILERPLATE):
            last = i
    return "\n".join(lines[last + 1 :]).lstrip() if last >= 0 else text.lstrip()


def _pdftotext(data: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
        tmp.write(data)
        tmp.flush()
        try:
            r = subprocess.run(
                ["pdftotext", "-layout", tmp.name, "-"],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
        except FileNotFoundError as e:
            raise SourceError("PDF support needs `pdftotext` (install poppler).") from e
        except subprocess.CalledProcessError as e:
            raise SourceError(f"pdftotext failed: {e.stderr.strip()}") from e
    return r.stdout


def load_path(path: str) -> str:
    p = Path(path).expanduser()
    if not p.exists() or not p.is_file():
        raise SourceError(f"file not found: {p}")
    if p.stat().st_size > _MAX_BYTES:
        raise SourceError("file is too large (over 5 MB)")
    suffix = p.suffix.lower()

    if suffix == ".docx":
        try:
            r = subprocess.run(
                ["pandoc", str(p), "-t", "plain", "--wrap=none"],
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
        except FileNotFoundError as e:
            raise SourceError("DOCX support needs `pandoc` (install it).") from e
        except subprocess.CalledProcessError as e:
            raise SourceError(f"pandoc failed: {e.stderr.strip()}") from e
        return r.stdout
    if suffix == ".pdf":
        return _pdftotext(p.read_bytes())
    if suffix in (".txt", ".md"):
        return p.read_text(encoding="utf-8", errors="replace")
    if suffix in (".html", ".htm"):
        return _strip_html(p.read_text(encoding="utf-8", errors="replace"))
    raise SourceError(
        f"unsupported file type '{suffix}'. Use .docx, .pdf, .txt, .md, or .html"
    )


def load_url(url: str) -> str:
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (job-app-llm-helper)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:  # noqa: S310 (self-host only)
            ctype = (resp.headers.get("Content-Type") or "").lower()
            raw = resp.read(_MAX_BYTES + 1)
    except Exception as e:
        raise SourceError(f"could not fetch URL: {e}") from e
    if len(raw) > _MAX_BYTES:
        raise SourceError("remote file is too large (over 5 MB)")

    if "pdf" in ctype or url.lower().split("?")[0].endswith(".pdf"):
        return _pdftotext(raw)
    text = raw.decode("utf-8", errors="replace")
    if "html" in ctype or "<html" in text[:2000].lower():
        text = _strip_gdocs_boilerplate(_strip_html(text))
    return text


def load_source(ref: str) -> dict:
    """Load text from a file path or URL. Returns {"kind", "text"}; raises SourceError."""
    ref = (ref or "").strip()
    if not ref:
        raise SourceError("provide a file path or URL")
    scheme = urlparse(ref).scheme.lower()
    if scheme in ("http", "https"):
        kind, text = "url", load_url(ref)
    elif scheme in ("file",):
        kind, text = "file", load_path(urlparse(ref).path)
    else:
        kind, text = "file", load_path(ref)
    text = (text or "").strip()
    if not text:
        raise SourceError("no readable text found in that source")
    return {"kind": kind, "text": text}
