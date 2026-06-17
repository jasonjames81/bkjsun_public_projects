# Plan 011: Add CI/CD pipeline

> **Executor instructions**: Follow this plan step by step.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: 010 (ruff config)
- **Category**: dx
- **Planned at**: commit `d4e8731`, 2026-06-16

## Why this matters

No automated gate catches regressions before they reach users. A contributor can push a change that breaks the `/generate` route or the docx download, and neither the contributor nor the maintainer finds out until a user reports a failure.

## Current state

- No `.github/workflows/`, `Makefile`, `tox.ini`, or CI config
- 38 tests exist but run only manually
- `ruff check .` works but has no config (plan 010 adds one)

## Steps

### Step 1: Create workflow directory

```bash
mkdir -p .github/workflows
```

### Step 2: Create `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -r requirements.txt pytest
      - run: pytest tests/ -v

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install ruff
      - run: ruff check .
```

### Step 3: Verify

**Verify**: `cat .github/workflows/ci.yml` → valid YAML

## Done criteria

- [ ] `.github/workflows/ci.yml` exists
- [ ] Workflow runs pytest and ruff on push/PR to main
- [ ] Matrix covers Python 3.11, 3.12, 3.13
