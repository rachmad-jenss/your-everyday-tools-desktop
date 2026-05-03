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
    if HAS_PYZBAR:
        status = (
            '<p><i class="bi bi-check-circle-fill" style="color:#2ec4b6"></i> '
            '<strong>QR reading is ready.</strong> Uses <code>pyzbar</code> + the ZBar binary.</p>'
        )
    else:
        status = (
            '<p><i class="bi bi-exclamation-triangle-fill" style="color:#ffb703"></i> '
            '<strong>QR reading is unavailable.</strong> Two things to install:</p>'
            '<ol style="margin:.4rem 0 .6rem 1.2rem">'
            '<li><code>pip install pyzbar</code></li>'
            '<li>The ZBar shared library: '
            '<a href="https://github.com/NaturalHistoryMuseum/pyzbar#installation" target="_blank">install instructions</a> '
            '(Windows DLLs ship with pyzbar; <code>brew install zbar</code> on macOS; '
            '<code>apt install libzbar0</code> on Linux)</li>'
            '</ol>'
            '<p>Then restart the server.</p>'
        )
    return render_template("upload_tool.html",
        title="Read QR Code",
        description="Decode QR codes from uploaded images",
        notes=(
            f'{status}'
            '<p><strong>Best results on:</strong> sharp, well-lit images of QR codes that '
            'fill at least a quarter of the frame. Blurry, tilted, or partially obscured QRs '
            'may not decode. Multiple QRs in one image are all decoded.</p>'
        ),
        endpoint="/qr/read",
        accept=".jpg,.jpeg,.png,.bmp,.webp,.gif",
        multiple=False,
        options=[])


@bp.route("/wifi")
def wifi_page():
    return render_template("upload_tool.html",
        title="WiFi QR Code",
        description="Generate a QR code that joins a WiFi network when scanned",
        notes=(
            '<p>iOS, Android, and most modern phones can join a WiFi network by simply '
            'scanning a QR code formatted with the standard <code>WIFI:</code> URI. '
            'Print and stick on the wall, share on a guest sheet, etc.</p>'
            '<p style="font-size:.9em;color:var(--muted)">Encoding format: '
            '<code>WIFI:T:&lt;type&gt;;S:&lt;ssid&gt;;P:&lt;password&gt;;H:&lt;hidden&gt;;;</code></p>'
        ),
        endpoint="/qr/wifi",
        accept="",
        multiple=False,
        options=[
            {"type": "text", "name": "ssid", "label": "Network name (SSID)",
             "placeholder": "MyHomeWiFi"},
            {"type": "password", "name": "password", "label": "Password",
             "placeholder": "(leave empty if open network)"},
            {"type": "select", "name": "security", "label": "Security", "default": "WPA",
             "choices": [
                 {"value": "WPA",  "label": "WPA / WPA2 / WPA3"},
                 {"value": "WEP",  "label": "WEP (legacy)"},
                 {"value": "nopass", "label": "Open (no password)"},
             ]},
            {"type": "checkbox", "name": "hidden", "label": "Hidden network",
             "check_label": "Network does not broadcast its SSID",
             "default": False},
            {"type": "number", "name": "size", "label": "Module size (pixels)",
             "default": 10, "min": 1, "max": 50},
            {"type": "number", "name": "border", "label": "Border (modules)",
             "default": 4, "min": 0, "max": 20},
        ],
        button_text="Generate WiFi QR")


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


def _wifi_escape(s: str) -> str:
    """Escape special characters per the WIFI: URI scheme: \\, ;, ,, : and "."""
    return (s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
              .replace(":", "\\:").replace('"', '\\"'))


@bp.route("/wifi", methods=["POST"])
def wifi_generate():
    ssid = request.form.get("ssid", "").strip()
    if not ssid:
        return jsonify(error="Please enter a network name (SSID)."), 400

    password = request.form.get("password", "")
    security = request.form.get("security", "WPA").upper()
    if security not in ("WPA", "WEP", "NOPASS"):
        security = "WPA"
    if security == "NOPASS":
        security = "nopass"
        password = ""
    hidden = request.form.get("hidden") == "on"

    if security != "nopass" and not password:
        return jsonify(error="Password is required for WPA/WEP networks. Switch to 'Open' if the network has no password."), 400

    # Build the standard WIFI: URI string
    parts = [f"T:{security}", f"S:{_wifi_escape(ssid)}"]
    if security != "nopass":
        parts.append(f"P:{_wifi_escape(password)}")
    if hidden:
        parts.append("H:true")
    payload = "WIFI:" + ";".join(parts) + ";;"

    box_size = safe_int(request.form.get("size"), 10, min_val=1, max_val=50)
    border = safe_int(request.form.get("border"), 4, min_val=0, max_val=20)

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # higher correction for printed labels
        box_size=box_size,
        border=border,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    safe_ssid = re.sub(r"[^A-Za-z0-9_.-]", "_", ssid)[:40] or "wifi"
    return send_file(buf, mimetype="image/png",
                     as_attachment=True, download_name=f"wifi_{safe_ssid}.png")


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
    if HAS_BARCODE:
        status = (
            '<p><i class="bi bi-check-circle-fill" style="color:#2ec4b6"></i> '
            '<strong>Barcode generation is ready.</strong></p>'
        )
    else:
        status = (
            '<p><i class="bi bi-exclamation-triangle-fill" style="color:#ffb703"></i> '
            '<strong>Barcode generation is unavailable.</strong> Install with '
            '<code>pip install python-barcode</code> and restart the server.</p>'
        )
    return render_template("upload_tool.html",
        title="Generate Barcode",
        description="Create 1D barcodes (Code128, EAN13, UPC, ISBN, and more)",
        notes=(
            f'{status}'
            '<p><strong>Per-format input requirements:</strong></p>'
            '<ul style="margin:.4rem 0 .6rem 1.2rem">'
            '<li><strong>Code 128</strong> — any printable ASCII (general-purpose, recommended for free text).</li>'
            '<li><strong>Code 39</strong> — uppercase A–Z, 0–9, and a few symbols (<code>- . $ / + % space</code>).</li>'
            '<li><strong>EAN-13</strong> — exactly 12 digits (the 13th is computed as a checksum).</li>'
            '<li><strong>EAN-8</strong> — exactly 7 digits.</li>'
            '<li><strong>UPC-A</strong> — exactly 11 digits.</li>'
            '<li><strong>ISBN-13</strong> — 12 digits (without dashes); 978/979 prefix expected.</li>'
            '<li><strong>ISBN-10</strong> — 9 digits.</li>'
            '<li><strong>ISSN</strong> — 7 digits.</li>'
            '</ul>'
            '<p style="font-size:.9em;color:var(--muted)">PNG output for general use; SVG for '
            'high-resolution print or to scale without quality loss.</p>'
        ),
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
