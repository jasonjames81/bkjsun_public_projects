# Plan 003: Remove stale ProviderConfig singleton

> **Executor instructions**: Follow this plan step by step.
>
> **Drift check**: `git diff --stat d4e8731..HEAD -- app.py`

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug
- **Planned at**: commit `d4e8731`, 2026-06-16

## Why this matters

`app.py:64-71` caches `ProviderConfig` in a module-level singleton (`_PROVIDER_CONFIG`). Once loaded on the first request, it never refreshes. If the user changes their provider selection via the UI, subsequent requests to `/providers`, `/providers/cli-status`, and `/providers/select` serve stale state. Meanwhile, `generator.py:50` explicitly re-reads from disk on every LLM call ("Re-reads from disk each call so a provider selection saved by the web UI takes effect"), and `/test-api` also reads fresh. The inconsistency means some routes see the new selection and others don't.

## Current state

- `app.py:64-71`:
  ```python
  _PROVIDER_CONFIG = None

  def _provider_config_for_request():
      global _PROVIDER_CONFIG
      if _PROVIDER_CONFIG is None:
          _PROVIDER_CONFIG = ProviderConfig().load()
      return _PROVIDER_CONFIG
  ```
- Call sites using the singleton: `list_providers_route` (line 415), `provider_models_route` (line 439), `select_provider_route` (line 469), `set_provider_key_route` (line 488)
- `/test-api` (line 397) creates its own `ProviderConfig().load()` — already fresh

## Scope

**In scope:**
- `app.py` — remove `_PROVIDER_CONFIG` singleton and `_provider_config_for_request()`, replace call sites with `ProviderConfig().load()`

**Out of scope:**
- `generator.py` — already reads fresh per call, no changes needed
- `providers/config.py` — the config class is fine, the issue is the caching in app.py

## Steps

### Step 1: Remove the singleton

Delete `_PROVIDER_CONFIG = None` (line 64) and `_provider_config_for_request()` (lines 67-71).

### Step 2: Replace call sites

Replace every `_provider_config_for_request()` call with `ProviderConfig().load()`:
- `list_providers_route` (line 415)
- `provider_models_route` (line 439)
- `select_provider_route` (line 469)
- `set_provider_key_route` (line 488)

**Verify**: `python -c "from app import app; print('ok')"` → `ok`

### Step 3: Run tests

**Verify**: `source venv/bin/activate && pytest tests/ -v` → 38 pass

## Done criteria

- [ ] No `_PROVIDER_CONFIG` global or `_provider_config_for_request` in app.py
- [ ] All provider routes use `ProviderConfig().load()` directly
- [ ] `pytest tests/ -v` exits 0
