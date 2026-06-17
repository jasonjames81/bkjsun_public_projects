# Plan 012: Parallelize `crawl_site` HTTP fetches

> **Executor instructions**: Follow this plan step by step.

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED
- **Depends on**: none
- **Category**: perf
- **Planned at**: commit `d4e8731`, 2026-06-16

## Why this matters

`crawl_site()` in `sources.py:216-252` makes up to 8 sequential HTTP requests (7 `_ORG_PATHS` + user-given path), each with a 20-second timeout. Worst case: 160 seconds of blocking I/O on a single Flask request thread. Even the happy path (4-5 successful fetches) takes 5-10 seconds, freezing the UI.

## Current state

- `sources.py:237-249`:
  ```python
  for cand in candidates:
      if cand in seen or total >= _CRAWL_MAX_CHARS:
          continue
      seen.add(cand)
      try:
          text = load_url(cand).strip()
      except SourceError:
          continue
      ...
  ```

## Scope

**In scope:**
- `sources.py` — parallelize the fetch loop using `concurrent.futures.ThreadPoolExecutor`

**Out of scope:**
- `load_url` — no changes needed
- `app.py` route handling — no changes needed

## Steps

### Step 1: Add import

At top of `sources.py`, add:
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
```

### Step 2: Replace sequential loop

Replace the `for cand in candidates` loop (lines 237-249) with:

```python
def _fetch_one(cand: str) -> str | None:
    try:
        text = load_url(cand).strip()
    except SourceError:
        return None
    if len(text) < 80:
        return None
    return text

with ThreadPoolExecutor(max_workers=4) as pool:
    futures = {pool.submit(_fetch_one, c): c for c in candidates}
    for future in as_completed(futures):
        cand = futures[future]
        if total >= _CRAWL_MAX_CHARS:
            break
        try:
            text = future.result()
        except Exception:
            continue
        if text is None:
            continue
        chunk = text[: _CRAWL_MAX_CHARS - total]
        sections.append(f"--- {cand} ---\n{chunk}")
        total += len(chunk)
```

### Step 3: Run tests

**Verify**: `source venv/bin/activate && pytest tests/test_sources.py -v` → all pass

### Step 4: Run full suite

**Verify**: `source venv/bin/activate && pytest tests/ -v` → all pass

## Test plan

- Existing `test_sources.py` tests cover `load_url` and `load_source` — they should still pass
- The crawl integration is not unit-tested (it hits real URLs); verify by running the app and testing manually if possible

## Done criteria

- [ ] `crawl_site` uses `ThreadPoolExecutor(max_workers=4)` instead of sequential loop
- [ ] Results are still collected in order (sections list preserves candidate order)
- [ ] Partial failures still skipped silently
- [ ] `pytest tests/ -v` exits 0

## STOP conditions

- If parallelization changes the ordering of sections (must preserve candidate order)
- If `load_url` is not thread-safe (it uses `urllib.request` which is thread-safe)
