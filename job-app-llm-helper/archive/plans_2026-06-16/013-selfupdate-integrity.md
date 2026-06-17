# Plan 013: Add selfupdate tarball integrity check

> **Executor instructions**: Follow this plan step by step.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: MED
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `d4e8731`, 2026-06-16

## Why this matters

`selfupdate.py:177-188` downloads a tarball from GitHub and extracts it over the install directory with no checksum or signature verification. If the download is tampered with (MITM, compromised release asset), arbitrary code would be written into the user's install directory. The real-world risk is low (HTTPS + GitHub infrastructure), but it's a gap versus best practice for self-updaters.

## Current state

- `selfupdate.py:93-99` — `find_tarball_url` only looks for `.tar.gz`, ignores `.sha256` files
- `selfupdate.py:177-188` — downloads, extracts, copies with no verification
- `selfupdate.py:125-128` — `_download` writes raw bytes

## Steps

### Step 1: Add `find_checksum_url` helper

After `find_tarball_url` (line 99), add:
```python
def find_checksum_url(assets: list[dict]) -> str | None:
    """Look for a .sha256 checksum file alongside the tarball."""
    for a in assets or []:
        name = a.get("name", "")
        if name.endswith(".sha256"):
            return a.get("browser_download_url")
    return None
```

### Step 2: Add verification step in `run()`

After downloading the tarball (line 180), before extraction:
```python
import hashlib

sha_url = find_checksum_url(assets)
if sha_url:
    try:
        sha_raw = _fetch_json(sha_url)  # .sha256 files are text
        expected = sha_raw.strip().split()[0]  # format: "hash  filename"
        actual = hashlib.sha256(tarball.read_bytes()).hexdigest()
        if actual != expected:
            print(f"Checksum mismatch — skipping update. Expected {expected[:12]}…, got {actual[:12]}…")
            return 1
    except Exception:
        pass  # If checksum fetch fails, proceed without verification (graceful degradation)
```

Note: `_fetch_json` is designed for GitHub API responses. For a plain `.sha256` file, use `_download` to fetch it as text instead:
```python
import io
sha_data = io.BytesIO()
_req = urllib.request.Request(sha_url, headers={"User-Agent": "job-app-llm-helper"})
with urllib.request.urlopen(_req, timeout=_TIMEOUT) as resp:
    sha_data.write(resp.read())
expected = sha_data.getvalue().decode("utf-8").strip().split()[0]
```

### Step 3: Run tests

**Verify**: `source venv/bin/activate && pytest tests/test_selfupdate.py -v` → all pass (9 existing + 1 new for `find_checksum_url`)

## Done criteria

- [ ] `find_checksum_url` helper exists
- [ ] `run()` fetches `.sha256` if available and verifies hash before extraction
- [ ] Graceful degradation if checksum fetch fails
- [ ] `pytest tests/ -v` exits 0
