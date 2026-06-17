# Plan 001: Fix drifted `_CLOSING_RE` regex

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise.
>
> **Drift check**: `git diff --stat d4e8731..HEAD -- docx_writer.py profile.py`
> If either file changed, compare the "Current state" excerpts against the
> live code before proceeding.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `d4e8731`, 2026-06-16

## Why this matters

`profile.py` defines `_CLOSING_RE` with `Thanks|Thank you` in the alternation, but `docx_writer.py` defines its own `_CLOSING_RE` without them. If a cover letter closes with "Thanks,\nAda", the voice fingerprint extraction (`profile.py`) recognizes it as a closing but the docx renderer (`docx_writer.py`) does not — the closing bleeds into the body paragraphs of the downloaded `.docx`. This is an active correctness bug, not just duplication.

## Current state

- `profile.py:102-106` — the more complete regex:
  ```python
  _CLOSING_RE = re.compile(
      r"^\s*(Sincerely|Best regards|Best,|Warm regards|Warmly|Kind regards|Thanks|"
      r"Thank you|Yours truly|Cordially)",
      re.IGNORECASE,
  )
  ```
- `docx_writer.py:19-21` — missing `Thanks|Thank you`:
  ```python
  _CLOSING_RE = re.compile(
      r"^\s*(Sincerely|Best regards|Best,|Warm regards|Warmly|Kind regards|Yours truly|Cordially)",
      re.IGNORECASE,
  )
  ```
- `_SALUTATION_RE` is identical in both files (no drift).

## Commands you will need

| Purpose | Command | Expected |
|---------|---------|----------|
| Tests | `source venv/bin/activate && pytest tests/ -v` | 38 pass |
| Lint | `ruff check docx_writer.py profile.py` | clean |

## Scope

**In scope:**
- `docx_writer.py` — remove local `_CLOSING_RE`, import from `profile.py`

**Out of scope:**
- `profile.py` — the regex is correct here, no changes needed
- `_SALUTATION_RE` — already identical, no changes needed

## Git workflow

- Branch: `advisor/001-fix-closing-regex`
- Single commit: `fix: unify _CLOSING_RE regex across profile.py and docx_writer.py`
- Do NOT push unless instructed.

## Steps

### Step 1: Import the canonical regex

In `docx_writer.py`, add an import from `profile`:
```python
from profile import _CLOSING_RE, _SALUTATION_RE
```

Delete the local `_CLOSING_RE` and `_SALUTATION_RE` definitions (lines 18-22).

**Verify**: `python -c "from docx_writer import _CLOSING_RE; print('ok')"` → `ok`

### Step 2: Run tests

**Verify**: `source venv/bin/activate && pytest tests/ -v` → 38 pass

### Step 3: Run lint

**Verify**: `ruff check docx_writer.py profile.py` → clean

## Test plan

- No new tests needed — the existing `test_download_docx_uses_profile_contact` and `test_generate_cover_letter_excludes_coaching_sections` cover the docx path
- The regex change is verified by the import succeeding and existing tests passing

## Done criteria

- [ ] `docx_writer.py` imports `_CLOSING_RE` and `_SALUTATION_RE` from `profile.py`
- [ ] No local `_CLOSING_RE` or `_SALUTATION_RE` in `docx_writer.py`
- [ ] `pytest tests/ -v` exits 0 (38 pass)
- [ ] `ruff check docx_writer.py profile.py` exits 0

## STOP conditions

- If importing from `profile.py` causes a circular import (it won't — `docx_writer` doesn't import `profile` currently, and `profile` doesn't import `docx_writer`)
- If tests fail after the change
