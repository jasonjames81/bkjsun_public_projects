# Plan 004: Add `.gitignore`

> **Executor instructions**: Follow this plan step by step.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `d4e8731`, 2026-06-16

## Why this matters

No `.gitignore` exists. `venv/`, `__pycache__/`, `.ruff_cache/`, `.pytest_cache/` are all present on disk. Any `git add .` or IDE "commit all" stages 50+ MB of venv plus caches into the public repo. If a user ever drops a `.env` file in the project root, there's no guardrail preventing it from being committed.

## Current state

- Glob confirms no `.gitignore` in `job-app-llm-helper/`
- Directories on disk that should be ignored: `venv/`, `__pycache__/`, `.ruff_cache/`, `.pytest_cache/`

## Steps

### Step 1: Create `.gitignore`

Create `job-app-llm-helper/.gitignore` with:
```
# Python
venv/
__pycache__/
*.pyc
*.pyo
*.egg-info/
dist/
build/

# Tool caches
.ruff_cache/
.pytest_cache/

# Environment / secrets
.env
*.env
*.pickle

# OS
.DS_Store
Thumbs.db

# IDE
.idea/
.vscode/
*.swp
```

### Step 2: Verify no currently-tracked files match

**Verify**: `git status --short` → only shows `.gitignore` as new, no deletions of existing tracked files

### Step 3: Commit

Single commit: `chore: add .gitignore`

## Done criteria

- [ ] `.gitignore` exists in `job-app-llm-helper/`
- [ ] `venv/`, `__pycache__/`, `.ruff_cache/`, `.pytest_cache/` are all listed
- [ ] No existing tracked files are affected
