# Plan 002: Unify JSON parsing in generator.py

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step.
>
> **Drift check**: `git diff --stat d4e8731..HEAD -- generator.py`

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `d4e8731`, 2026-06-16

## Why this matters

`generator.py` defines a robust `_extract_json()` helper that strips markdown fences, tries a clean parse, then falls back to regex. But `analyze_fit()` (line 282) and `generate_questions()` (line 490) bypass it with raw `re.search` + `json.loads`. When an LLM wraps its JSON in `` ```json `` fences (common behavior), these two functions fail to parse, returning `{"success": false}` to the user. The other 4 functions that use `_extract_json` handle this correctly. This causes intermittent user-facing failures depending on which provider/model is used.

## Current state

- `generator.py:59-74` — `_extract_json()` helper:
  ```python
  def _extract_json(response: str, *, array: bool = False):
      stripped = re.sub(r"^```(?:json)?\s*\n?", "", response.strip(), flags=re.IGNORECASE)
      stripped = re.sub(r"\n?```\s*$", "", stripped)
      try:
          return json.loads(stripped)
      except json.JSONDecodeError:
          pass
      pattern = r"\[[\s\S]*\]" if array else r"\{[\s\S]*\}"
      match = re.search(pattern, response)
      ...
  ```
- `generator.py:280-286` — `analyze_fit` bypasses it:
  ```python
  response = call_llm(prompt)
  match = re.search(r"\{[\s\S]*\}", response)
  if not match:
      raise ValueError("no JSON object in response")
  data = json.loads(match.group(0))
  ```
- `generator.py:488-493` — `generate_questions` bypasses it:
  ```python
  response = call_llm(prompt)
  json_match = re.search(r"\[[\s\S]*\]", response)
  if not json_match:
      raise ValueError("No JSON array found in response")
  questions = json.loads(json_match.group())
  ```

## Scope

**In scope:**
- `generator.py` — replace ad-hoc parsing in `analyze_fit` and `generate_questions` with `_extract_json`

**Out of scope:**
- `_extract_json` itself — already correct
- Other functions that already use `_extract_json` — no changes needed

## Steps

### Step 1: Fix `analyze_fit` (line 280-286)

Replace the manual regex+loads block with:
```python
response = call_llm(prompt)
data = _extract_json(response, array=False)
data["success"] = True
return data
```

Remove the `try/except` around the old regex block (the existing outer `try/except` at line 280 already catches `_extract_json` failures).

**Verify**: `python -c "import generator; print('ok')"` → `ok`

### Step 2: Fix `generate_questions` (line 488-493)

Replace the manual regex+loads block with:
```python
response = call_llm(prompt)
questions = _extract_json(response, array=True)
return {"success": True, "questions": questions}
```

**Verify**: `python -c "import generator; print('ok')"` → `ok`

### Step 3: Run tests

**Verify**: `source venv/bin/activate && pytest tests/ -v` → 38 pass

## Done criteria

- [ ] `analyze_fit` uses `_extract_json(response, array=False)` instead of raw regex
- [ ] `generate_questions` uses `_extract_json(response, array=True)` instead of raw regex
- [ ] No manual `re.search(r"\{[\s\S]*\}"` or `re.search(r"\[[\s\S]*\]"` remains in generator.py (grep confirms)
- [ ] `pytest tests/ -v` exits 0

## STOP conditions

- If `_extract_json` doesn't handle a case the old code handled (check error paths)
