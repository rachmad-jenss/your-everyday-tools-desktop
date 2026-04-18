import io
import qrcode
from flask import Blueprint, render_template, request, send_file, jsonify

try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    from PIL import Image
    HAS_PYZBAR = True
except ImportError:
    HAS_PYZBAR = False

bp = Blueprint("qr", __name__)


@bp.route("/generate")
def generate_page():
    return render_template("upload_tool.html",
        title="Generate QR Code",
        description="Create QR codes from text or URLs",
        endpoint="/qr/generate",
        text_input=True,
        text_label="Text or URL",
        text_placeholder="Enter the text or URL for the QR code...",
        accept="",
        multiple=False,
        options=[
            {"type": "number", "name": "size", "label": "Module size (pixels)", "default": 10, "min": 1, "max": 50},
            {"type": "number", "name": "border", "label": "Border (modules)", "default": 4, "min": 0, "max": 20},
            {"type": "select", "name": "color", "label": "Color",
             "choices": [
                 {"value": "black", "label": "Black"},
                 {"value": "#4361ee", "label": "Blue"},
                 {"value": "#e63946", "label": "Red"},
                 {"value": "#2d6a4f", "label": "Green"},
             ]},
        ],
        button_text="Generate QR Code")


@bp.route("/read")
def read_page():
    return render_template("upload_tool.html",
        title="Read QR Code",
        description="Decode QR codes from uploaded images",
        endpoint="/qr/read",
        accept=".jpg,.jpeg,.png,.bmp,.webp,.gif",
        multiple=False,
        options=[])


@bp.route("/generate", methods=["POST"])
def generate():
    text = request.form.get("text", "").strip()
    if not text:
        return jsonify(error="Please enter text or a URL."), 400

    box_size = int(request.form.get("size", 10))
    border = int(request.form.get("border", 4))
    color = request.form.get("color", "black")

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(text)
    qr.make(fit=True)

    img = qr.make_image(fill_color=color, back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return send_file(buf, mimetype="image/png",
                     as_attachment=True, download_name="qrcode.png")


@bp.route("/read", methods=["POST"])
def read():
    if not HAS_PYZBAR:
        return jsonify(error="QR reading requires the 'pyzbar' package. Install with: pip install pyzbar"), 400

    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="No file uploaded."), 400

    img = Image.open(io.BytesIO(files[0].read()))
    results = pyzbar_decode(img)

    if not results:
        return jsonify(error="No QR code found in the image."), 400

    decoded = []
    for r in results:
        decoded.append({
            "type": r.type,
            "data": r.data.decode("utf-8", errors="replace"),
        })

    text = "\n".join(f"[{d['type']}] {d['data']}" for d in decoded)
    return jsonify(text=text)
