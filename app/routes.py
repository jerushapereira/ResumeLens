import json
from pathlib import Path

from flask import Blueprint, Response, current_app, jsonify, render_template, request
from werkzeug.utils import secure_filename

from .services.report_service import build_report
from .services.resume_analyzer import ResumeAnalyzer
from .utils.text_extractor import extract_resume_text, is_allowed_file


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    return render_template("index.html")


@main_bp.get("/api/health")
def health_check():
    return jsonify({"status": "ok"})


@main_bp.post("/api/analyze")
def analyze_resume():
    if "resume" not in request.files:
        return jsonify({"error": "Please upload a PDF or DOCX resume."}), 400

    uploaded_file = request.files["resume"]
    desired_role = request.form.get("role", "").strip()

    if uploaded_file.filename == "":
        return jsonify({"error": "No file was selected."}), 400

    if not is_allowed_file(uploaded_file.filename, current_app.config["ALLOWED_EXTENSIONS"]):
        return jsonify({"error": "Only PDF and DOCX resumes are supported."}), 400

    upload_dir = Path(current_app.config["UPLOAD_FOLDER"])
    upload_dir.mkdir(exist_ok=True)

    safe_name = secure_filename(uploaded_file.filename)
    saved_path = upload_dir / safe_name

    try:
        uploaded_file.save(saved_path)
        resume_text = extract_resume_text(saved_path)

        if len(resume_text.strip()) < 80:
            return jsonify({
                "error": "Could not extract enough readable text from this resume. Try a text-based PDF or DOCX file."
            }), 422

        analyzer = ResumeAnalyzer(
            api_key=current_app.config["GROQ_API_KEY"],
            model=current_app.config["GROQ_MODEL"],
            api_url=current_app.config["GROQ_API_URL"],
        )
        analysis = analyzer.analyze(resume_text=resume_text, desired_role=desired_role)

        return jsonify({
            "filename": safe_name,
            "desired_role": desired_role or "General internship / entry-level role",
            "resume_text_preview": resume_text[:700],
            "analysis": analysis,
        })
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 422
    except Exception:
        current_app.logger.exception("Resume analysis failed")
        return jsonify({"error": "Resume analysis failed. Please check the file and try again."}), 500
    finally:
        if saved_path.exists():
            saved_path.unlink()


@main_bp.post("/api/download-report")
def download_report():
    payload = request.get_json(silent=True) or {}
    analysis = payload.get("analysis")

    if not isinstance(analysis, dict):
        return jsonify({"error": "Missing analysis data for the report."}), 400

    filename = secure_filename(payload.get("filename", "resume-analysis")) or "resume-analysis"
    role = payload.get("desired_role", "General internship / entry-level role")
    report_text = build_report(filename=filename, desired_role=role, analysis=analysis)

    return Response(
        report_text,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}-analysis-report.txt"},
    )
