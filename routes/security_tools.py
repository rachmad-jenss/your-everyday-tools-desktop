import hashlib
from flask import Blueprint, render_template, request, jsonify

bp = Blueprint("security", __name__)

HASH_ALGOS = ["md5", "sha1", "sha256", "sha512"]


@bp.route("/password-generator")
def password_generator():
    return render_template("tools/password_generator.html")


@bp.route("/hash-generator")
def hash_generator():
    return render_template("tools/hash_generator.html")


@bp.route("/file-hash", methods=["GET", "POST"])
def file_hash():
    if request.method == "GET":
        return render_template(
            "upload_tool.html",
            title="File Hash",
            description="Compute MD5, SHA-1, SHA-256, and SHA-512 hashes of an uploaded file.",
            endpoint="/security/file-hash",
            accept="*",
            multiple=False,
            button_text="Compute",
        )

    f = request.files.get("files")
    if not f:
        return jsonify({"error": "No file uploaded."}), 400

    hashers = {name: hashlib.new(name) for name in HASH_ALGOS}
    total = 0
    chunk_size = 1024 * 1024  # 1 MB
    while True:
        chunk = f.stream.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        for h in hashers.values():
            h.update(chunk)

    lines = [f"File:      {f.filename}", f"Size:      {total:,} bytes", ""]
    for name in HASH_ALGOS:
        lines.append(f"{name.upper():<8}   {hashers[name].hexdigest()}")

    return jsonify({"text": "\n".join(lines)})
