# Plan 005: Remove dead `resolve_default_model`

> **Executor instructions**: Follow this plan step by step.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: tech-debt
- **Planned at**: commit `d4e8731`, 2026-06-16

## Why this matters

`registry.py:96-105` defines `resolve_default_model()` as a public function but it has zero call sites anywhere in the codebase. Dead code adds maintenance surface and misleads contributors into thinking it's used.

## Current state

- `registry.py:96-105`:
  ```python
  def resolve_default_model(name: str, available: list[str]) -> str | None:
      """Pick a sensible default from a live model list using the family keyword."""
      if not available:
          return None
      family = PREFERRED_FAMILY.get(name)
      if family:
          preferred = [m for m in available if family in m.lower()]
          if preferred:
              return preferred[0]
      return available[0]
  ```
- Grep confirms: only the definition, no callers.

## Steps

### Step 1: Delete the function

Remove `resolve_default_model` from `registry.py:96-105`.

**Verify**: `python -c "from providers.registry import get_provider, list_models; print('ok')"` → `ok`

### Step 2: Run tests

**Verify**: `source venv/bin/activate && pytest tests/ -v` → 38 pass

## Done criteria

- [ ] `resolve_default_model` does not exist in `registry.py`
- [ ] `pytest tests/ -v` exits 0
