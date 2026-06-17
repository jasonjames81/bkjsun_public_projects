# Plan 006: Fix stale "Gemini Gems" doc references

> **Executor instructions**: Follow this plan step by step.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: docs
- **Planned at**: commit `d4e8731`, 2026-06-16

## Why this matters

The Gemini feature was renamed from "Gems" to "Notebooks" (2026-06-16). The platform guide and setup docs were updated, but two docs files still reference "Gemini Gems". Contributors reading these docs will reference the wrong product name.

## Current state

- `docs/platform-guide-implementation.md:105` — "adapted for Gemini Gems"
- `docs/platform-guide-implementation.md:131` — "Gemini Gems"
- `docs/platform-guide-implementation.md:190` — "Gemini Gems"
- `docs/provider-roadmap.md:56` — "Gemini Gems"

## Steps

### Step 1: Update `docs/platform-guide-implementation.md`

Find-and-replace all 3 occurrences of "Gemini Gems" → "Gemini Notebooks".

### Step 2: Update `docs/provider-roadmap.md`

Replace "Gemini Gems" with "Gemini Notebooks" on line 56.

### Step 3: Verify

**Verify**: `grep -rn "Gemini Gems" docs/` → no matches

## Done criteria

- [ ] `grep -rn "Gemini Gems" docs/` returns no matches
- [ ] All references now say "Gemini Notebooks"
