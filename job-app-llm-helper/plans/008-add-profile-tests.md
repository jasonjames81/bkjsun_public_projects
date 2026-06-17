# Plan 008: Add `profile.py` voice-fingerprint tests

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: LOW
- **Depends on**: 004 (.gitignore)
- **Category**: tests
- **Planned at**: commit `d4e8731`, 2026-06-16

## Why this matters

The voice fingerprint is the core differentiator of this tool — it drives every LLM prompt via `generator.py`. The 200-line statistical engine in `profile.py:129-291` has zero test coverage. Regressions in sentence splitting, paragraph detection, opener/closer extraction, or statistics aggregation would silently degrade cover-letter quality.

## Current state

- `profile.py:129-291` — untested: `_paragraphs`, `_sentences`, `_words`, `_strip_letter_scaffolding`, `_opener_phrase`, `_closer_phrase`, `_ngrams`, `_transition_phrases`, full `build_voice_fingerprint` with samples
- `tests/test_smoke.py:52-64` — only two tests touch `profile.py`: depersonalization check and no-samples fallback

## Scope

**In scope:**
- Create `tests/test_profile.py` with unit tests for the pure helper functions and integration tests for `build_voice_fingerprint`

**Out of scope:**
- `profile.py` — no changes to source code
- `test_smoke.py` — existing tests stay as-is

## Steps

### Step 1: Create `tests/test_profile.py`

Write tests covering:

1. **`_strip_letter_scaffolding`** — letter with salutation + closing, letter with no salutation, letter with no closing, letter where body contains "Sincerely"
2. **`_paragraphs`** — text with blank-line-separated paragraphs, single paragraph, very short paragraphs filtered by 30-char threshold
3. **`_sentences`** — normal text, text with abbreviations (Mr., Dr.), single-sentence text
4. **`build_voice_fingerprint` with samples** — provide a realistic 3-paragraph writing sample, assert stats are present (avg sentence length, opener/closer counts, exemplar selection)
5. **`build_voice_fingerprint` with multi-sample input** — triple-newline-separated samples
6. **`build_voice_fingerprint` without samples** — assert fallback text (already tested in test_smoke.py, but include for completeness)

Use `SAMPLE_PROFILE` from `test_smoke.py` as the pattern for profile dicts.

### Step 2: Run tests

**Verify**: `source venv/bin/activate && pytest tests/test_profile.py -v` → all pass

### Step 3: Run full suite

**Verify**: `source venv/bin/activate && pytest tests/ -v` → all pass (38+ new tests)

## Test plan

- File: `tests/test_profile.py`
- Pattern: follow `tests/test_smoke.py` conventions (same imports, same sys.path setup)
- Tests: ~8-10 unit tests + 2-3 integration tests

## Done criteria

- [ ] `tests/test_profile.py` exists
- [ ] Tests cover `_strip_letter_scaffolding`, `_paragraphs`, `_sentences`, `build_voice_fingerprint` with samples
- [ ] `pytest tests/ -v` exits 0 with all tests passing
