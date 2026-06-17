# Plan 007: Extract `experience_section` helper

> **Executor instructions**: Follow this plan step by step.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: tech-debt
- **Planned at**: commit `d4e8731`, 2026-06-16

## Why this matters

`_build_cover_letter_prompt` (line 552-556) and `_build_coaching_prompt` (line 618-622) contain near-identical blocks building an `experience_section` string from `experience_answers`. The only difference: the cover-letter version appends `(USE THESE)` to the header. If the format ever changes, both sites must be updated in lockstep.

## Current state

- `generator.py:552-556`:
  ```python
  experience_section = ""
  if experience_answers:
      experience_section = f"\n=== {name.upper()}'S USEFUL DETAILS FOR THIS ROLE (USE THESE) ===\n"
      for qa in experience_answers:
          experience_section += f"\nQ: {qa['question']}\nA: {qa['answer']}\n"
  ```
- `generator.py:618-622`:
  ```python
  experience_section = ""
  if experience_answers:
      experience_section = f"\n=== {name.upper()}'S USEFUL DETAILS FOR THIS ROLE ===\n"
      for qa in experience_answers:
          experience_section += f"\nQ: {qa['question']}\nA: {qa['answer']}\n"
  ```

## Steps

### Step 1: Add helper function

Add before `_build_cover_letter_prompt` (around line 537):
```python
def _format_experience_section(name: str, experience_answers, *, add_use_prompt: bool = False) -> str:
    if not experience_answers:
        return ""
    suffix = " (USE THESE)" if add_use_prompt else ""
    section = f"\n=== {name.upper()}'S USEFUL DETAILS FOR THIS ROLE{suffix} ===\n"
    for qa in experience_answers:
        section += f"\nQ: {qa['question']}\nA: {qa['answer']}\n"
    return section
```

### Step 2: Replace both call sites

In `_build_cover_letter_prompt` (line 552-556), replace with:
```python
experience_section = _format_experience_section(name, experience_answers, add_use_prompt=True)
```

In `_build_coaching_prompt` (line 618-622), replace with:
```python
experience_section = _format_experience_section(name, experience_answers)
```

**Verify**: `python -c "import generator; print('ok')"` → `ok`

### Step 3: Run tests

**Verify**: `source venv/bin/activate && pytest tests/ -v` → 38 pass

## Done criteria

- [ ] `_format_experience_section` helper exists in `generator.py`
- [ ] Both `_build_cover_letter_prompt` and `_build_coaching_prompt` use the helper
- [ ] No duplicate `experience_section` building code remains
- [ ] `pytest tests/ -v` exits 0
