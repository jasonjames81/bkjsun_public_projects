# Plan D3: Add coaching `.docx` download

> **Executor instructions**: Follow this plan step by step.

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `d4e8731`, 2026-06-16

## Why this matters

The cover letter result card has a "Download .docx" button. The coaching result card (résumé tailoring + interview talking points) has only a "Copy" button. The coaching content — which includes specific resume rewordings and interview talking points — is arguably more actionable than the cover letter, yet has no polished download.

## Current state

- `templates/index.html:268-279` — cover letter card: has "Download .docx" button
- `templates/index.html:282-290` — coaching card: has only "Copy" button
- `app.py:370-392` — `/download-docx` route: builds formatted `.docx` from letter content
- `docx_writer.py:91-156` — `build_cover_letter_docx` renders letter + contact header

## Scope

**In scope:**
- `docx_writer.py` — add `build_coaching_docx()` function
- `app.py` — add `/download-coaching-docx` route (or generalize existing route)
- `templates/index.html` — add download button to coaching card

**Out of scope:**
- Modifying the existing `/download-docx` route (keep it letter-specific)

## Steps

### Step 1: Add `build_coaching_docx` in `docx_writer.py`

After `build_cover_letter_docx`:
```python
def build_coaching_docx(content: str, *, job_title: str = "", org_name: str = "") -> bytes:
    """Build a formatted .docx from coaching markdown content."""
    document = Document()
    style = document.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)

    # Title
    title = document.add_paragraph()
    run = title.add_run("Résumé & Interview Tips")
    run.bold = True
    run.font.size = Pt(14)

    if job_title or org_name:
        sub = document.add_paragraph()
        parts = [f for f in [job_title, org_name] if f]
        run = sub.add_run(" for " + " at ".join(parts))
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)

    document.add_paragraph()

    # Content — split by markdown headers
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("## ") or stripped.startswith("# "):
            document.add_paragraph()  # spacer
            p = document.add_paragraph()
            run = p.add_run(stripped.lstrip("#").strip())
            run.bold = True
            run.font.size = Pt(12)
        elif stripped.startswith("- "):
            document.add_paragraph(stripped[2:], style="List Bullet")
        elif stripped:
            document.add_paragraph(stripped)

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()
```

### Step 2: Add `/download-coaching-docx` route in `app.py`

```python
@app.route("/download-coaching-docx", methods=["POST"])
def download_coaching_docx():
    data = request.json or {}
    content = data.get("content", "").strip()
    job_title = data.get("job_title", "").strip()
    org_name = data.get("org_name", "").strip()
    if not content:
        return jsonify({"success": False, "error": "content is required"}), 400

    docx_bytes = build_coaching_docx(content, job_title=job_title, org_name=org_name)

    safe_org = org_name.replace(" ", "_").replace("/", "_") or "Application"
    safe_role = job_title.replace(" ", "_").replace("/", "_") or "Tips"
    filename = f"CoachingTips_{safe_org}_{safe_role}.docx"
    return Response(
        docx_bytes,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

Import `build_coaching_docx` from `docx_writer`.

### Step 3: Add download button in coaching card

In `templates/index.html`, after the "Copy" button (line 287), add:
```html
<button type="button" id="downloadCoachingBtn">Download .docx</button>
```

JS handler:
```javascript
$("downloadCoachingBtn").addEventListener("click", async () => {
  const content = $("coachingOut").textContent;
  if (!content) return;
  busy($("downloadCoachingBtn"), true, "Building…");
  await downloadDocx(content, $("coachingErr"));  // reuse existing helper
  busy($("downloadCoachingBtn"), false, "Download .docx");
});
```

Wait — `downloadDocx` posts to `/download-docx`. Need a separate function:
```javascript
async function downloadCoachingDocx(content, errorEl) {
  try {
    const res = await fetch("/download-coaching-docx", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content, job_title: $("jobTitle").value.trim(), org_name: $("orgName").value.trim(),
      }),
    });
    if (!res.ok) { if (errorEl) errorEl.textContent = "Download failed."; return; }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "CoachingTips.docx";
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  } catch (e) {
    if (errorEl) errorEl.textContent = "Download failed.";
  }
}
```

### Step 4: Run tests

**Verify**: `source venv/bin/activate && pytest tests/ -v` → 38 pass

## Done criteria

- [ ] `build_coaching_docx` function exists in `docx_writer.py`
- [ ] `/download-coaching-docx` route exists in `app.py`
- [ ] "Download .docx" button exists in coaching card
- [ ] `pytest tests/ -v` exits 0
