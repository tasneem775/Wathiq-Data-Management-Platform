"""Wathiq API Bridge.

The only HTTP-facing file in this project. It is a thin connector and
nothing else:

    Browser -> HTTP POST /api/assess -> this file
        -> src/dashboard/assessment_dashboard_adapter.py::prepare_dashboard_assessment()
        -> the existing, UNMODIFIED Assessment Pipeline
           (assessment_pipeline_service -> docx_evidence_reader ->
            evidence_assessment_orchestrator -> gap_analysis_engine ->
            compliance_recommendation_engine -> assessment_results_store ->
            word_report_generator)
        -> back to the browser as JSON, exactly the same Presentation Dict
           the pipeline already produces.

No assessment/scoring/gap-analysis/recommendation logic lives here. This
file only: receives the upload, writes it to a temp file OUTSIDE the repo,
calls the one existing entry point, deletes the temp file, and returns the
result as-is (plus a report_download_url convenience field).

Also serves wathiq_maturity_dashboard/ and data/ as static files, so the
whole app runs on a single origin -- no CORS needed, no second server.

Run:   python wathiq_api.py
Open:  http://localhost:8090/wathiq_maturity_dashboard/index.html
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_from_directory

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.assessment_dashboard_adapter import prepare_dashboard_assessment  # noqa: E402

REPORTS_DIR = PROJECT_ROOT / "reports"
FRONTEND_DIR = PROJECT_ROOT / "wathiq_maturity_dashboard"
DATA_DIR = PROJECT_ROOT / "data"
EVIDENCE_CATALOG_DIR = DATA_DIR / "evidence_catalog"

ALLOWED_EXTENSION = ".docx"

app = Flask(__name__)


def _load_valid_evidence_codes() -> set[str]:
    """Real evidence codes from data/evidence_catalog/*.json -- same source
    the frontend itself reads. Used only to reject a request whose
    evidence_code was never offered by the UI; never used to invent one."""
    codes: set[str] = set()
    if not EVIDENCE_CATALOG_DIR.exists():
        return codes
    for catalog_file in EVIDENCE_CATALOG_DIR.glob("*.json"):
        try:
            data = json.loads(catalog_file.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - a bad catalog file must not crash startup
            continue
        for item in data.get("evidence_items", []):
            code = item.get("code")
            if code:
                codes.add(code)
    return codes


VALID_EVIDENCE_CODES = _load_valid_evidence_codes()


# ---------------------------------------------------------------------
# Static frontend (same origin as the API -- no CORS needed)
# ---------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/wathiq_maturity_dashboard/<path:filename>")
def frontend_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


@app.route("/data/<path:filename>")
def data_files(filename):
    return send_from_directory(DATA_DIR, filename)


# ---------------------------------------------------------------------
# API
# ---------------------------------------------------------------------
@app.route("/api/assess", methods=["POST"])
def api_assess():
    evidence_code = (request.form.get("evidence_code") or "").strip()
    uploaded_file = request.files.get("file")

    if not evidence_code:
        return jsonify({"success": False, "message": "لم يتم إرسال رمز الدليل (evidence_code)."}), 400

    if VALID_EVIDENCE_CODES and evidence_code not in VALID_EVIDENCE_CODES:
        return jsonify({"success": False, "message": "رمز الدليل غير موجود في كتالوج الأدلة."}), 400

    if uploaded_file is None or not uploaded_file.filename:
        return jsonify({"success": False, "message": "لم يتم إرفاق ملف."}), 400

    if not uploaded_file.filename.lower().endswith(ALLOWED_EXTENSION):
        return jsonify({"success": False, "message": "صيغة الملف غير مدعومة. الرجاء رفع ملف DOCX."}), 400

    # ملف مؤقت خارج المستودع بالكامل (tempfile.gettempdir()) -- لا يُحفظ في
    # temp_uploads/ ولا أي مسار داخل المشروع، ويُحذف تلقائياً عند الخروج من
    # هذا الـ with بغض النظر عن نجاح التقييم أو فشله.
    with tempfile.TemporaryDirectory(prefix="wathiq_upload_") as tmp_dir:
        safe_name = re.sub(r'[\\/:*?"<>|]+', "_", uploaded_file.filename)
        tmp_path = Path(tmp_dir) / safe_name
        uploaded_file.save(tmp_path)

        try:
            result = prepare_dashboard_assessment(evidence_code=evidence_code, file_path=str(tmp_path))
        except Exception as error:  # noqa: BLE001 - the API must never 500 on a bad upload
            return jsonify({"success": False, "message": "حدث خطأ غير متوقع أثناء التقييم.", "error": str(error)}), 500

    result["success"] = bool(result.get("assessment_available"))
    word_report = result.get("word_report") or {}
    if word_report.get("generated") and word_report.get("file_name"):
        result["report_download_url"] = "/api/reports/" + word_report["file_name"]

    return jsonify(result)


@app.route("/api/reports/<path:file_name>")
def api_reports(file_name):
    # يمنع Path traversal: اسم ملف مباشر داخل reports/ فقط، بلا مسارات فرعية.
    if "/" in file_name or "\\" in file_name or not file_name.lower().endswith(ALLOWED_EXTENSION):
        abort(404)
    if not (REPORTS_DIR / file_name).exists():
        abort(404)
    return send_from_directory(REPORTS_DIR, file_name, as_attachment=True)


if __name__ == "__main__":
    print("Wathiq API + static frontend running.")
    print("Open: http://localhost:8090/wathiq_maturity_dashboard/index.html")
    app.run(host="127.0.0.1", port=8090, debug=False)
