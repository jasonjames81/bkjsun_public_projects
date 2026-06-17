# Plan D4: Surface voice fingerprint for export

> **Executor instructions**: Follow this plan step by step.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `d4e8731`, 2026-06-16

## Why this matters

The self-hosted app computes a voice fingerprint from writing samples (`profile.py:192-291`), but the result is only used internally in LLM prompts — it's never shown to the user. Browser-native users must run a separate voice-fingerprint prompt and manually paste the output into Project Knowledge. Surfacing the computed fingerprint as an exportable artifact would bridge both use cases and save browser-native users a step.

## Current state

- `profile.py:192-291` — `build_voice_fingerprint()` computes the fingerprint
- `templates/index.html` — no voice fingerprint section in the UI
- `platform-guide/project-instructions.md:14` — tells browser-native users to generate it manually

## Steps

### Step 1: Add voice fingerprint section in the UI

After the "Writing samples" textarea (around line 186), add:
```html
<details class="collapse" id="voiceBox">
  <summary id="voiceSummary">Voice fingerprint <span class="opt">(computed from writing samples)</span></summary>
  <div id="voiceFingerprint" style="min-height:80px; margin-top:8px; white-space:pre-wrap; font-size:0.9em; color:var(--muted);"></div>
  <div class="btns">
    <button type="button" id="copyVoiceBtn" class="ghost">Copy to clipboard</button>
  </div>
</details>
```

### Step 2: Add JS to compute and display

When the profile is saved or writing samples change, compute and display the fingerprint. Since the computation is in Python (`profile.py`), the app needs a route to compute it:

In `app.py`, add:
```python
@app.route("/compute-voice-fingerprint", methods=["POST"])
def compute_voice_fingerprint():
    profile = _profile_from(request.get_json(silent=True) or {})
    fingerprint = profile_mod.build_voice_fingerprint(profile)
    return jsonify({"ok": True, "fingerprint": fingerprint})
```

In `templates/index.html`, add JS:
```javascript
async function updateVoiceFingerprint() {
  const samples = $("writingSamples").value.trim();
  if (!samples) {
    $("voiceFingerprint").textContent = "No writing samples — add samples above to compute your voice fingerprint.";
    return;
  }
  $("voiceFingerprint").textContent = "Computing…";
  const res = await postJSON("/compute-voice-fingerprint", { profile: currentProfile() });
  if (res.ok) {
    $("voiceFingerprint").textContent = res.fingerprint;
  } else {
    $("voiceFingerprint").textContent = "Could not compute voice fingerprint.";
  }
}
```

Call `updateVoiceFingerprint()` after saving profile and when writing samples change.

### Step 3: Add copy button handler

```javascript
$("copyVoiceBtn").addEventListener("click", () => {
  navigator.clipboard && navigator.clipboard.writeText($("voiceFingerprint").textContent);
});
```

### Step 4: Run tests

**Verify**: `source venv/bin/activate && pytest tests/ -v` → 38 pass

## Done criteria

- [ ] Voice fingerprint section exists in the UI below writing samples
- [ ] `/compute-voice-fingerprint` route exists in `app.py`
- [ ] Fingerprint is computed and displayed when writing samples are present
- [ ] "Copy to clipboard" button works
- [ ] `pytest tests/ -v` exits 0
