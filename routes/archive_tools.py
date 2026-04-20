import io
import zipfile
from datetime import datetime
from flask import Blueprint, render_template, request, send_file, jsonify

from utils.file_utils import make_zip

bp = Blueprint("archive", __name__)

MAX_ENTRIES = 2000
MAX_EXTRACT_BYTES = 500 * 1024 * 1024  # 500 MB total extracted size (zip bomb guard)


@bp.route("/zip", methods=["GET", "POST"])
def zip_create():
    if request.method == "GET":
        return render_template(
            "upload_tool.html",
            title="Create ZIP",
            description="Bundle multiple files into a single .zip archive.",
            endpoint="/archive/zip",
            accept="*",
            multiple=True,
            options=[
                {
                    "name": "compression",
                    "label": "Compression",
                    "type": "select",
                    "default": "deflated",
                    "choices": [
                        {"value": "deflated", "label": "Deflate (smaller)"},
                        {"value": "stored", "label": "Store (no compression)"},
                    ],
                },
                {
                    "name": "archive_name",
                    "label": "Output name (without .zip)",
                    "type": "text",
                    "default": "archive",
                },
            ],
            button_text="Create ZIP",
        )

    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files uploaded."}), 400

    method = zipfile.ZIP_DEFLATED if request.form.get("compression", "deflated") == "deflated" else zipfile.ZIP_STORED
    name = (request.form.get("archive_name") or "archive").strip() or "archive"
    if name.lower().endswith(".zip"):
        name = name[:-4]

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", method) as zf:
        for f in files:
            data = f.read()
            zf.writestr(f.filename, data)
    buf.seek(0)

    return send_file(buf, mimetype="application/zip", as_attachment=True, download_name=f"{name}.zip")


@bp.route("/unzip", methods=["GET", "POST"])
def zip_extract():
    if request.method == "GET":
        return render_template(
            "upload_tool.html",
            title="Extract ZIP",
            description="Extract a .zip archive and repackage the contents as a flat download.",
            notes="<strong>Note:</strong> extracted contents are returned as a new ZIP (preserving directory layout). "
                  "Encrypted archives are not supported. Max total extracted size: 500 MB.",
            endpoint="/archive/unzip",
            accept=".zip",
            multiple=False,
            button_text="Extract",
        )

    if "files" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    f = request.files["files"]
    if not f.filename.lower().endswith(".zip"):
        return jsonify({"error": "Please upload a .zip file."}), 400

    try:
        data = f.read()
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            total = 0
            out = []
            for info in zf.infolist():
                if info.is_dir():
                    continue
                if info.file_size > MAX_EXTRACT_BYTES:
                    return jsonify({"error": "File in archive exceeds size limit."}), 400
                total += info.file_size
                if total > MAX_EXTRACT_BYTES:
                    return jsonify({"error": "Total extracted size exceeds 500 MB limit."}), 400
                out.append((info.filename, zf.read(info)))
    except zipfile.BadZipFile:
        return jsonify({"error": "Not a valid ZIP archive."}), 400
    except RuntimeError as e:
        if "password" in str(e).lower() or "encrypted" in str(e).lower():
            return jsonify({"error": "Password-protected ZIPs are not supported."}), 400
        return jsonify({"error": f"Extraction failed: {e}"}), 400

    if not out:
        return jsonify({"error": "Archive is empty."}), 400

    buf = make_zip(out)
    base = f.filename.rsplit(".", 1)[0]
    return send_file(buf, mimetype="application/zip", as_attachment=True, download_name=f"{base}_extracted.zip")


@bp.route("/zip-info", methods=["GET", "POST"])
def zip_info():
    if request.method == "GET":
        return render_template(
            "upload_tool.html",
            title="ZIP Info",
            description="Inspect a ZIP archive: list files, sizes, and compression ratios.",
            endpoint="/archive/zip-info",
            accept=".zip",
            multiple=False,
            button_text="Inspect",
        )

    if "files" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    f = request.files["files"]
    if not f.filename.lower().endswith(".zip"):
        return jsonify({"error": "Please upload a .zip file."}), 400

    try:
        data = f.read()
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            entries = []
            total_uncompressed = 0
            total_compressed = 0
            for info in zf.infolist()[:MAX_ENTRIES]:
                dt = "-"
                try:
                    dt = datetime(*info.date_time).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass
                entries.append(
                    f"{_format_size(info.file_size):>10}  "
                    f"{_format_size(info.compress_size):>10}  "
                    f"{dt}  "
                    f"{info.filename}"
                )
                total_uncompressed += info.file_size
                total_compressed += info.compress_size

            ratio = (1 - total_compressed / total_uncompressed) * 100 if total_uncompressed else 0
            header = (
                f"{'Uncompr.':>10}  {'Compr.':>10}  {'Modified':<16}  Name\n"
                f"{'-' * 10}  {'-' * 10}  {'-' * 16}  {'-' * 30}"
            )
            footer = (
                f"\n{'-' * 10}  {'-' * 10}\n"
                f"{_format_size(total_uncompressed):>10}  {_format_size(total_compressed):>10}  "
                f"({len(zf.infolist())} entries, {ratio:.1f}% saved)"
            )
            return jsonify({"text": header + "\n" + "\n".join(entries) + footer})
    except zipfile.BadZipFile:
        return jsonify({"error": "Not a valid ZIP archive."}), 400


def _format_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} TB"
