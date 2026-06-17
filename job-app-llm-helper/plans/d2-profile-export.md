# Plan D2: Add profile export/import

> **Executor instructions**: Follow this plan step by step.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `d4e8731`, 2026-06-16

## Why this matters

All profile data lives in `localStorage`. Users who invest time building a rich profile (2 resume uploads, 4 writing samples, stories) lose everything on browser clear, incognito switch, or device change. There is no backup or transfer path. The only data management option is "Clear".

## Current state

- `templates/index.html:377-390` — save/clear profile, no export
- `templates/index.html:496-562` — import buttons fill localStorage, no export
- `app.py` — no `/export-profile` route (backend doesn't need one; data is client-side)

## Steps

### Step 1: Add "Download profile" button

In `templates/index.html`, after the "Save profile" / "Clear" buttons (around line 191), add:
```html
<button type="button" id="exportProfileBtn" class="ghost">Download profile</button>
```

### Step 2: Add JS handler

In the `<script>` block, add:
```javascript
$("exportProfileBtn").addEventListener("click", () => {
  const data = readProfileForm();
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "job-app-profile.json";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
});
```

### Step 3: Add "Import profile" file picker

After the export button, add:
```html
<input type="file" id="importProfileFile" accept=".json" style="display:none">
<button type="button" id="importProfileBtn" class="ghost">Import profile</button>
```

JS handler:
```javascript
$("importProfileBtn").addEventListener("click", () => $("importProfileFile").click());
$("importProfileFile").addEventListener("change", () => {
  const file = $("importProfileFile").files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const data = JSON.parse(reader.result);
      PROFILE_FIELDS.forEach((f) => { if (data[f] != null) $(f).value = data[f]; });
      saveProfile();
      $("profileSaved").textContent = "Imported ✓";
      setTimeout(() => ($("profileSaved").textContent = ""), 2000);
    } catch {
      alert("Invalid profile file.");
    }
  };
  reader.readAsText(file);
  $("importProfileFile").value = "";
});
```

### Step 4: Verify

Load the app in a browser. Export profile → verify JSON file downloads. Import it back → verify fields populate.

## Done criteria

- [ ] "Download profile" button exists next to "Save profile"
- [ ] "Import profile" button exists
- [ ] Export downloads a `.json` file with all profile fields
- [ ] Import loads the JSON back into the form and saves to localStorage
