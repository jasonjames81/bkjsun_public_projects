# Plan 010: Add ruff lint config

> **Executor instructions**: Follow this plan step by step.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `d4e8731`, 2026-06-16

## Why this matters

`.ruff_cache/` exists on disk proving ruff has been run ad-hoc, but there's no config file. Each developer (or AI agent) runs ruff with different defaults. The `# noqa: BLE001` and `# noqa: S310` suppressions in `app.py` and `selfupdate.py` are undocumented — a future contributor may add more broad catches without realizing the pattern is intentional.

## Current state

- `.ruff_cache/` exists (ruff used ad-hoc)
- No `ruff.toml`, `pyproject.toml`, or `.pre-commit-config.yaml`
- `# noqa: BLE001` in `app.py:129,156,173,193,219` and `selfupdate.py:197`
- `# noqa: S310` in `sources.py:194` and `selfupdate.py:121,127`
- `# noqa: E402` in `tests/test_smoke.py:17-19`

## Steps

### Step 1: Create `ruff.toml`

Create `job-app-llm-helper/ruff.toml`:
```toml
line-length = 100

[lint]
select = ["E", "F", "W", "I", "B", "S"]
ignore = [
    "BLE001",  # broad exception catches — intentional in route error handlers
    "S310",    # urllib audit URL — self-host only, fixed GitHub/localhost URLs
]

[lint.per-file-ignores]
"tests/*" = ["E402"]  # sys.path manipulation in test files
```

### Step 2: Verify ruff passes

**Verify**: `ruff check .` → clean (or only pre-existing issues)

### Step 3: Commit

Single commit: `chore: add ruff.toml lint config`

## Done criteria

- [ ] `ruff.toml` exists in project root
- [ ] `ruff check .` exits 0 (or matches pre-existing baseline)
