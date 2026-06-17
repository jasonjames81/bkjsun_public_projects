# Plan D1: Implement interactive interview practice

> **Executor instructions**: Follow this plan step by step. This is a new
> feature — build it incrementally and verify each layer before moving on.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: MED
- **Depends on**: none
- **Category**: direction
- **Planned at**: commit `d4e8731`, 2026-06-16

## Why this matters

`project-instructions.md:82-83` documents "Option B — Interactive practice" where the LLM asks interview questions one at a time, the user answers, and the LLM provides follow-ups and coaching feedback. The README (step 7) promises this. But the backend only has a static `/coaching` route that generates a one-shot block. The interactive mode has no route, no conversation state, and no UI.

## Current state

- `project-instructions.md:82-83` — documents the feature
- `generator.py:606-663` — `_build_coaching_prompt` generates static résumé tips + interview talking points
- `app.py:333-349` — `/coaching` route returns static content
- `templates/index.html:282-290` — coaching card has only a "Copy" button, no chat UI

## Scope

**In scope:**
- `generator.py` — add `generate_interview_followup()` function
- `app.py` — add `/interview-practice` POST route
- `templates/index.html` — add chat-bubble UI section in coaching card

**Out of scope:**
- Server-side session state (keep it client-side to match the stateless design)
- Modifying the existing `/coaching` route

## Steps

### Step 1: Add `generate_interview_followup` in `generator.py`

Add after `generate_coaching` (around line 765):
```python
def generate_interview_followup(
    profile: dict,
    question: str,
    user_answer: str,
    prior_qa: list[dict],
    job_title: str,
    org_name: str,
    job_description: str,
    org_about: str = "",
) -> dict:
    """Generate a coaching follow-up for an interview practice answer."""
    name = profile_mod.applicant_name(profile)
    voice_block = profile_mod.build_voice_fingerprint(profile)
    profile_block = profile_mod.build_profile_summary(profile)

    prior_section = ""
    if prior_qa:
        prior_section = "\n=== PREVIOUS Q&A IN THIS SESSION ===\n"
        for qa in prior_qa:
            prior_section += f"\nQ: {qa['question']}\nA: {qa['answer']}\n"

    prompt = f"""You are coaching {name} in a mock interview. They just answered a question.
Provide brief, specific feedback on their answer, then ask the next likely interview question.

{voice_block}

{profile_block}

=== TARGET JOB ===
Job Title: {job_title}
Organization: {org_name}

Job Description:
{job_description}

About the Organization:
{org_about if org_about else "Not provided"}
{prior_section}
=== CURRENT QUESTION & ANSWER ===
Q: {question}
A: {user_answer}

=== YOUR TASK ===

1. Give 1-2 sentences of coaching feedback on the answer (what worked, what to improve).
2. Ask the next likely interview question for this role.

Output ONLY a JSON object:
{{"feedback": "<coaching feedback>", "next_question": "<next interview question>"}}

No prose outside the JSON. No markdown fences."""

    try:
        response = call_llm(prompt)
        data = _extract_json(response, array=False)
        return {"success": True, "feedback": data.get("feedback", ""), "next_question": data.get("next_question", "")}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Step 2: Add `/interview-practice` route in `app.py`

Add after the `/coaching` route:
```python
@app.route("/interview-practice", methods=["POST"])
def interview_practice():
    data = request.json or {}
    question = data.get("question", "").strip()
    user_answer = data.get("user_answer", "").strip()
    prior_qa = data.get("prior_qa", [])
    job_title, org_name, job_description, org_about = _job_fields(data)
    if not question or not user_answer:
        return jsonify({"success": False, "error": "Need both question and user_answer"}), 400
    if not job_title or not org_name or not job_description:
        return _missing_job()
    return jsonify(
        generate_interview_followup(
            _profile_from(data),
            question=question,
            user_answer=user_answer,
            prior_qa=prior_qa,
            job_title=job_title,
            org_name=org_name,
            job_description=job_description,
            org_about=org_about,
        )
    )
```

Add `generate_interview_followup` to the imports from `generator`.

### Step 3: Add chat-bubble UI in `templates/index.html`

Replace the coaching card content (lines 282-290) with a chat-style interface:
- A "Start interview practice" button that generates the first question
- A text input for the user's answer + "Submit" button
- A chat log showing Q/A pairs with coaching feedback
- State tracked in a JS array (`interviewHistory`)

### Step 4: Run tests

**Verify**: `source venv/bin/activate && pytest tests/ -v` → 38 pass

## Test plan

- Add a test for `generate_interview_followup` in `test_smoke.py` similar to the existing coaching test
- Verify the route returns JSON with `feedback` and `next_question` keys

## Done criteria

- [ ] `generate_interview_followup` function exists in `generator.py`
- [ ] `/interview-practice` POST route exists in `app.py`
- [ ] Chat-bubble UI exists in the coaching card
- [ ] `pytest tests/ -v` exits 0
