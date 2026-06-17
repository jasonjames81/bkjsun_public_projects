# Plan 009: Add `docx_writer.py` parsing tests

> **Executor instructions**: Follow this plan step by step.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: 004 (.gitignore)
- **Category**: tests
- **Planned at**: commit `d4e8731`, 2026-06-16

## Why this matters

`extract_cover_letter_section` and `_split_letter_parts` are the sole gateway between the LLM's raw output and the user's downloaded `.docx`. If the regex fails to strip the employer Q&A appendix, it leaks into the cover-letter document. If `_split_letter_parts` misidentifies the closing, the body gets swallowed. None of these failure modes are caught by tests.

## Current state

- `docx_writer.py:29-40` — `extract_cover_letter_section`: two regex paths (legacy header match, fallback split)
- `docx_writer.py:43-72` — `_split_letter_parts`: four branches (no salutation, no closing, normal, closing before salutation)
- `tests/test_smoke.py:267-282` — only checks status code and PK header, not content correctness

## Steps

### Step 1: Create `tests/test_docx_writer.py`

Write tests covering:

1. **`extract_cover_letter_section`** — legacy multi-section output with `## 1. TAILORED COVER LETTER` header, modern letter-only output, letter + employer Q&A appendix (`## 4. EMPLOYER APPLICATION QUESTIONS`), bare text with no headers
2. **`_split_letter_parts`** — normal letter with salutation + closing, letter with no salutation, letter with no closing, letter where a body line contains "Sincerely" (not the closing)
3. **`_paragraphs_from_lines`** — blank-line-separated paragraphs, single paragraph, lines with only whitespace
4. **`build_cover_letter_docx`** — full integration: letter text + contact dict → bytes, verify PK header (zip), verify contact name appears in output

### Step 2: Run tests

**Verify**: `source venv/bin/activate && pytest tests/test_docx_writer.py -v` → all pass

### Step 3: Run full suite

**Verify**: `source venv/bin/activate && pytest tests/ -v` → all pass

## Done criteria

- [ ] `tests/test_docx_writer.py` exists
- [ ] Tests cover `extract_cover_letter_section`, `_split_letter_parts`, `_paragraphs_from_lines`, `build_cover_letter_docx`
- [ ] `pytest tests/ -v` exits 0
