# Plan 014: Migrate `google-generativeai` → `google-genai`

> **Executor instructions**: Follow this plan step by step. This is a
> breaking SDK change — the new `google-genai` package has a different API.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: none
- **Category**: migration
- **Planned at**: commit `d4e8731`, 2026-06-16

## Why this matters

`providers/adapters/api.py` uses `google.generativeai` (the legacy SDK) with `genai.configure()` + `genai.GenerativeModel()` + `model.generate_content()`. This SDK has been deprecated since mid-2025. Future Gemini API features and model access will only be available through the new `google-genai` package.

## Current state

- `providers/adapters/api.py:27-29`:
  ```python
  def _load_google():
      import google.generativeai as genai
      return genai
  ```
- `providers/adapters/api.py:120-125`:
  ```python
  class GoogleApi(_ApiProvider):
      def _call(self, prompt: str) -> str:
          genai = _load_google()
          genai.configure(api_key=self.api_key)
          model = genai.GenerativeModel(self.model)
          resp = model.generate_content(prompt)
          return resp.text.strip()
  ```
- `providers/registry.py:87-90`:
  ```python
  if name == "google_api":
      import google.generativeai as genai
      genai.configure(api_key=key)
      return [m.name for m in genai.list_models()]
  ```

## Scope

**In scope:**
- `providers/adapters/api.py` — rewrite `GoogleApi._call()` and `_load_google()`
- `providers/registry.py` — rewrite `_list_api_models` for Google
- `requirements.txt` — update comment

**Out of scope:**
- Other API adapters (Anthropic, OpenAI) — working fine
- CLI adapters — no changes

## Steps

### Step 1: Update `_load_google` and `GoogleApi._call`

Replace in `providers/adapters/api.py`:
```python
def _load_google():
    from google import genai
    return genai

class GoogleApi(_ApiProvider):
    name = "google_api"
    display_name = "Google Gemini (API key)"
    sdk_pkg = "google-genai"

    def _call(self, prompt: str) -> str:
        genai = _load_google()
        client = genai.Client(api_key=self.api_key)
        resp = client.models.generate_content(model=self.model, contents=prompt)
        return resp.text.strip()
```

### Step 2: Update `_list_api_models` for Google

In `providers/registry.py`, replace the Google block:
```python
if name == "google_api":
    from google import genai
    client = genai.Client(api_key=key)
    return [m.name for m in client.models.list()]
```

### Step 3: Update `requirements.txt`

Change the comment from `pip install google-generativeai` to `pip install google-genai`.

### Step 4: Verify import

**Verify**: `python -c "from providers.adapters.api import GoogleApi; print('ok')"` → `ok` (will fail without SDK installed, but syntax should be valid)

### Step 5: Run tests

**Verify**: `source venv/bin/activate && pytest tests/ -v` → 38 pass (tests mock the LLM, so SDK absence doesn't matter)

## Done criteria

- [ ] `GoogleApi._call` uses `google.genai.Client` instead of `genai.configure` + `GenerativeModel`
- [ ] `_list_api_models` for Google uses new client
- [ ] `requirements.txt` says `google-genai`
- [ ] `pytest tests/ -v` exits 0
