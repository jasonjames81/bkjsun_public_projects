# app.py
"""Flask app for Job App LLM Helper (public, self-hosted edition).

Stateless by design: the applicant profile (name, background, contact, optional
writing samples and story notes) is supplied by the browser with each request and
remembered client-side in localStorage. The server reads and writes no per-user
files — only the provider config (API-key selection) lives on disk, via platformdirs.

Self-host only: the import (sources.py) and CLI-login (cli_auth.py) routes read local
files / launch local processes, so this must not run as a shared multi-tenant server.
"""

from datetime import date

from flask import Flask, Response, jsonify, render_template, request

import profile as profile_mod
from docx_writer import build_cover_letter_docx, extract_cover_letter_section
from generator import (
    analyze_fit,
    answer_application_questions,
    generate_clarifying_questions,
    generate_cover_letter,
    generate_questions,
    refine_letter,
)
import cli_auth
from providers.config import ProviderConfig
from providers.detect import detect_providers
from providers.registry import list_models
from sources import SourceError, load_source

app = Flask(__name__)

_PROVIDER_CONFIG = None


def _provider_config_for_request():
    global _PROVIDER_CONFIG
    if _PROVIDER_CONFIG is None:
        _PROVIDER_CONFIG = ProviderConfig().load()
    return _PROVIDER_CONFIG


def _profile_from(data: dict) -> dict:
    """Pull the applicant profile out of a request body, defaulting to empty."""
    profile = data.get("profile")
    return profile if isinstance(profile, dict) else {}


def _job_fields(data: dict) -> tuple[str, str, str, str]:
    return (
        data.get("job_title", "").strip(),
        data.get("org_name", "").strip(),
        data.get("job_description", "").strip(),
        data.get("org_about", "").strip(),
    )


def _missing_job():
    return (
        jsonify(
            {
                "success": False,
                "error": "Please fill in Job Title, Organization Name, and Job Description",
            }
        ),
        400,
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/profile-status", methods=["POST"])
def profile_status():
    """Report whether the supplied profile has enough background to generate from."""
    profile = _profile_from(request.get_json(silent=True) or {})
    return jsonify(
        {
            "ready": profile_mod.has_minimum_profile(profile),
            "name": profile_mod.applicant_name(profile),
        }
    )


@app.route("/load-source", methods=["POST"])
def load_source_route():
    """Extract text from a local file path or web URL (self-host only — see sources.py)."""
    data = request.get_json(silent=True) or {}
    ref = (data.get("ref") or "").strip()
    if not ref:
        return jsonify({"ok": False, "error": "provide a file path or URL"}), 400
    try:
        result = load_source(ref)
    except SourceError as e:
        return jsonify({"ok": False, "error": str(e)})
    except Exception as e:  # noqa: BLE001 — surface any unexpected failure to the UI
        return jsonify({"ok": False, "error": f"could not load source: {e}"})
    return jsonify(
        {
            "ok": True,
            "kind": result["kind"],
            "text": result["text"],
            "chars": len(result["text"]),
        }
    )


@app.route("/analyze-fit", methods=["POST"])
def analyze_fit_route():
    data = request.json or {}
    job_title, org_name, job_description, org_about = _job_fields(data)
    if not job_title or not org_name or not job_description:
        return _missing_job()
    return jsonify(
        analyze_fit(
            _profile_from(data), job_title, org_name, job_description, org_about
        )
    )


@app.route("/clarify-application-questions", methods=["POST"])
def clarify_application_questions():
    data = request.json or {}
    job_title, org_name, job_description, org_about = _job_fields(data)
    questions = data.get("questions", [])
    if (
        not job_title
        or not org_name
        or not job_description
        or not isinstance(questions, list)
        or not questions
    ):
        return _missing_job()
    return jsonify(
        generate_clarifying_questions(
            _profile_from(data),
            questions=questions,
            job_title=job_title,
            org_name=org_name,
            job_description=job_description,
            org_about=org_about,
        )
    )


@app.route("/answer-application-questions", methods=["POST"])
def answer_application_questions_route():
    data = request.json or {}
    job_title, org_name, job_description, org_about = _job_fields(data)
    questions = data.get("questions", [])
    clarifying_answers = data.get("clarifying_answers", [])
    if (
        not job_title
        or not org_name
        or not job_description
        or not isinstance(questions, list)
        or not questions
    ):
        return _missing_job()
    return jsonify(
        answer_application_questions(
            _profile_from(data),
            questions=questions,
            clarifying_answers=clarifying_answers,
            job_title=job_title,
            org_name=org_name,
            job_description=job_description,
            org_about=org_about,
        )
    )


@app.route("/get-questions", methods=["POST"])
def get_questions():
    data = request.json or {}
    job_title, org_name, job_description, org_about = _job_fields(data)
    prior_qa = data.get("prior_qa", [])
    if not job_title or not org_name or not job_description:
        return _missing_job()
    return jsonify(
        generate_questions(
            _profile_from(data),
            job_title=job_title,
            org_name=org_name,
            job_description=job_description,
            org_about=org_about,
            prior_qa=prior_qa,
        )
    )


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json or {}
    job_title, org_name, job_description, org_about = _job_fields(data)
    additional_notes = data.get("additional_notes", "").strip()
    experience_answers = data.get("experience_answers", [])
    application_answers = data.get("application_answers", [])
    if not job_title or not org_name or not job_description:
        return _missing_job()
    return jsonify(
        generate_cover_letter(
            _profile_from(data),
            job_title=job_title,
            org_name=org_name,
            job_description=job_description,
            org_about=org_about,
            additional_notes=additional_notes,
            experience_answers=experience_answers or None,
            application_answers=application_answers or None,
        )
    )


@app.route("/refine", methods=["POST"])
def refine():
    data = request.json or {}
    current_letter = data.get("current_letter", "").strip()
    instruction = data.get("instruction", "").strip()
    job_title = data.get("job_title", "").strip()
    org_name = data.get("org_name", "").strip()
    if not current_letter or not instruction:
        return jsonify(
            {"success": False, "error": "Need both current_letter and instruction"}
        ), 400
    return jsonify(
        refine_letter(
            current_letter, instruction, _profile_from(data), job_title, org_name
        )
    )


@app.route("/download-docx", methods=["POST"])
def download_docx():
    data = request.json or {}
    content = data.get("content", "").strip()
    org_name = data.get("org_name", "").strip()
    job_title = data.get("job_title", "").strip()
    if not content:
        return jsonify({"success": False, "error": "content is required"}), 400

    contact = profile_mod.contact_from_profile(_profile_from(data))
    letter_text = extract_cover_letter_section(content)
    docx_bytes = build_cover_letter_docx(
        letter_text, contact=contact, today=date.today()
    )

    safe_org = org_name.replace(" ", "_").replace("/", "_") or "Application"
    safe_role = job_title.replace(" ", "_").replace("/", "_") or "CoverLetter"
    filename = f"CoverLetter_{safe_org}_{safe_role}.docx"
    return Response(
        docx_bytes,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.route("/test-api")
def test_api():
    cfg = ProviderConfig().load()
    selected = cfg.selected() or "claude_cli"
    infos = {i.name: i for i in detect_providers(cfg)}
    info = infos.get(selected)
    if info is None or not info.available:
        return jsonify(
            {
                "configured": False,
                "message": f"selected provider '{selected}' is not available",
            }
        )
    return jsonify(
        {"configured": True, "message": f"{info.display_name} ready — {info.detail}"}
    )


@app.route("/providers")
def list_providers_route():
    cfg = _provider_config_for_request()
    infos = detect_providers(cfg)
    return jsonify(
        {
            "selected": cfg.selected(),
            "providers": [
                {
                    "name": i.name,
                    "display_name": i.display_name,
                    "kind": i.kind,
                    "available": i.available,
                    "detail": i.detail,
                    "tier": i.tier.value,
                    "tier_verified": i.tier_verified,
                    "model": i.model,
                }
                for i in infos
            ],
        }
    )


@app.route("/providers/models")
def provider_models_route():
    cfg = _provider_config_for_request()
    name = (request.args.get("name") or "").strip()
    return jsonify({"models": list_models(name, cfg)})


@app.route("/providers/cli-status")
def cli_status_route():
    """Installed + logged-in state for a subscription CLI provider (self-host only)."""
    name = (request.args.get("name") or "").strip()
    if name not in cli_auth.BINARY:
        return jsonify({"error": f"not a CLI provider: {name!r}"}), 400
    return jsonify(cli_auth.status(name))


@app.route("/providers/cli-login", methods=["POST"])
def cli_login_route():
    """Open the CLI's browser login in a terminal (self-host only). Falls back to a manual command."""
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if name not in cli_auth.BINARY:
        return jsonify(
            {"launched": False, "error": f"not a CLI provider: {name!r}"}
        ), 400
    return jsonify(cli_auth.launch_login(name))


@app.route("/providers/select", methods=["POST"])
def select_provider_route():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    cfg = _provider_config_for_request()
    known = {i.name for i in detect_providers(cfg)}
    if name not in known:
        return jsonify({"success": False, "error": f"unknown provider '{name}'"}), 400
    cfg.set_selected(name)
    model = (data.get("model") or "").strip()
    if model:
        cfg.set_model(name, model)
    cfg.save()
    return jsonify({"success": True})


@app.route("/providers/key", methods=["POST"])
def set_provider_key_route():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    key = (data.get("key") or "").strip()
    if not name or not key:
        return jsonify({"success": False, "error": "name and key are required"}), 400
    cfg = _provider_config_for_request()
    captured = {}
    cfg.set_key(name, key, on_consent=lambda msg: captured.setdefault("msg", msg))
    cfg.save()
    return jsonify({"success": True, "consent": captured.get("msg", "")})


if __name__ == "__main__":
    import os

    # Prod-safe defaults: debug OFF, bound to localhost. Override via env when you
    # self-host. Set JALLM_HOST=0.0.0.0 to reach it from your phone on the same
    # network. Never enable debug on an exposed host (Werkzeug console is an RCE).
    debug = os.environ.get("JALLM_DEBUG", "").lower() in ("1", "true", "yes")
    host = os.environ.get("JALLM_HOST", "127.0.0.1")
    port = int(os.environ.get("JALLM_PORT", "5000"))

    print("\n" + "=" * 60)
    print("  JOB APP LLM HELPER")
    print("=" * 60)
    _selected = ProviderConfig().load().selected() or "claude_cli"
    print(f"\nGenerating via provider: {_selected} (change it in the web UI)")
    print(
        f"Open http://{'localhost' if host in ('127.0.0.1', '0.0.0.0') else host}:{port} in your browser"
    )
    if host == "0.0.0.0":
        print(
            "Reachable on your LAN — open http://<this-machine-ip>:%d on your phone"
            % port
        )
    print()
    app.run(debug=debug, host=host, port=port)
