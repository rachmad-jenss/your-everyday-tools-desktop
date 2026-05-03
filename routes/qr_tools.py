import io
import re
import qrcode
from flask import Blueprint, render_template, request, send_file, jsonify

from routes._helpers import safe_int, safe_float, log_error, NO_FILE_SINGLE

try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    from PIL import Image
    HAS_PYZBAR = True
except (ImportError, FileNotFoundError, OSError):
    HAS_PYZBAR = False

try:
    import barcode as pybarcode
    from barcode.writer import ImageWriter, SVGWriter
    HAS_BARCODE = True
except ImportError:
    HAS_BARCODE = False

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

    box_size = safe_int(request.form.get("size"), 10, min_val=1, max_val=50)
    border = safe_int(request.form.get("border"), 4, min_val=0, max_val=20)
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
        return jsonify(error=NO_FILE_SINGLE), 400

    try:
        img = Image.open(io.BytesIO(files[0].read()))
    except Exception as e:
        log_error(e, "qr-read")
        return jsonify(error="Could not read image (file may be corrupted or not an image)."), 400
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


BARCODE_TYPES = [
    {"value": "code128", "label": "Code 128 (general text)"},
    {"value": "code39", "label": "Code 39 (uppercase/digits)"},
    {"value": "ean13", "label": "EAN-13 (12 digits)"},
    {"value": "ean8", "label": "EAN-8 (7 digits)"},
    {"value": "upca", "label": "UPC-A (11 digits)"},
    {"value": "isbn13", "label": "ISBN-13 (12 digits)"},
    {"value": "isbn10", "label": "ISBN-10 (9 digits)"},
    {"value": "issn", "label": "ISSN (7 digits)"},
    {"value": "jan", "label": "JAN (12 digits)"},
    {"value": "pzn", "label": "PZN (6 digits)"},
]


@bp.route("/barcode")
def barcode_page():
    return render_template("upload_tool.html",
        title="Generate Barcode",
        description="Create 1D barcodes (Code128, EAN13, UPC, ISBN, and more)",
        endpoint="/qr/barcode",
        text_input=True,
        text_label="Barcode value",
        text_placeholder="Enter digits or text (see selected type's requirements)...",
        accept="",
        multiple=False,
        options=[
            {"type": "select", "name": "btype", "label": "Barcode type",
             "choices": BARCODE_TYPES},
            {"type": "select", "name": "format", "label": "Output format",
             "choices": [
                 {"value": "png", "label": "PNG"},
                 {"value": "svg", "label": "SVG (vector)"},
             ]},
            {"type": "checkbox", "name": "show_text", "label": "Show value below bars", "default": True},
            {"type": "number", "name": "module_width", "label": "Bar width (mm)", "default": 0.2, "min": 0.1, "max": 1.0, "step": 0.1},
            {"type": "number", "name": "module_height", "label": "Bar height (mm)", "default": 15, "min": 5, "max": 50},
        ],
        button_text="Generate Barcode")


@bp.route("/barcode", methods=["POST"])
def barcode_generate():
    if not HAS_BARCODE:
        return jsonify(error="Barcode generation requires 'python-barcode'. Install with: pip install python-barcode"), 400

    text = request.form.get("text", "").strip()
    if not text:
        return jsonify(error="Please enter a value for the barcode."), 400

    btype = request.form.get("btype", "code128").lower()
    fmt = request.form.get("format", "png").lower()
    show_text = request.form.get("show_text") in ("on", "true", "1")

    module_width = safe_float(request.form.get("module_width"), 0.2,
                              min_val=0.1, max_val=1.0)
    module_height = safe_float(request.form.get("module_height"), 15.0,
                               min_val=5.0, max_val=50.0)

    valid = {k: v for k, v in [(c["value"], c["label"]) for c in BARCODE_TYPES]}
    if btype not in valid:
        return jsonify(error=f"Unknown barcode type: {btype}"), 400

    try:
        cls = pybarcode.get_barcode_class(btype)
    except pybarcode.errors.BarcodeNotFoundError:
        return jsonify(error=f"Barcode type {btype} not supported."), 400

    writer = SVGWriter() if fmt == "svg" else ImageWriter()
    options = {
        "module_width": module_width,
        "module_height": module_height,
        "write_text": show_text,
        "quiet_zone": 2.0,
        "font_size": 8 if show_text else 0,
        "text_distance": 3.0,
    }

    try:
        bc = cls(text, writer=writer)
    except (pybarcode.errors.IllegalCharacterError,
            pybarcode.errors.NumberOfDigitsError) as e:
        return jsonify(error=f"Invalid value for {valid[btype]}: {e}"), 400
    except Exception as e:
        return jsonify(error=f"Could not create barcode: {e}"), 400

    buf = io.BytesIO()
    try:
        bc.write(buf, options=options)
    except Exception as e:
        return jsonify(error=f"Render failed: {e}"), 400

    buf.seek(0)

    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", text)[:40] or "barcode"
    if fmt == "svg":
        return send_file(buf, mimetype="image/svg+xml",
                         as_attachment=True, download_name=f"{safe}.svg")
    return send_file(buf, mimetype="image/png",
                     as_attachment=True, download_name=f"{safe}.png")
