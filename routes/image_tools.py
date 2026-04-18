import io
from flask import Blueprint, render_template, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import TAGS

try:
    from rembg import remove as rembg_remove
    HAS_REMBG = True
except ImportError:
    HAS_REMBG = False

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

bp = Blueprint("image", __name__)

IMAGE_ACCEPT = ".jpg,.jpeg,.png,.bmp,.tiff,.webp"


def get_pil_image(file):
    return Image.open(io.BytesIO(file.read()))


def image_to_bytes(img, fmt, quality=85):
    buf = io.BytesIO()
    save_kwargs = {"format": fmt}

    if fmt.upper() == "JPEG":
        if img.mode in ("RGBA", "P", "LA"):
            img = img.convert("RGB")
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True
    elif fmt.upper() == "PNG":
        save_kwargs["optimize"] = True
    elif fmt.upper() == "WEBP":
        save_kwargs["quality"] = quality

    img.save(buf, **save_kwargs)
    buf.seek(0)
    return buf


FORMAT_MAP = {
    "jpg": ("JPEG", "image/jpeg", "jpg"),
    "jpeg": ("JPEG", "image/jpeg", "jpg"),
    "png": ("PNG", "image/png", "png"),
    "webp": ("WEBP", "image/webp", "webp"),
    "bmp": ("BMP", "image/bmp", "bmp"),
    "tiff": ("TIFF", "image/tiff", "tiff"),
}


# ── Page Routes ──────────────────────────────────

@bp.route("/resize")
def resize_page():
    return render_template("upload_tool.html",
        title="Resize Image",
        description="Resize images by percentage or specific dimensions",
        endpoint="/image/resize",
        accept=IMAGE_ACCEPT,
        multiple=False,
        options=[
            {"type": "select", "name": "mode", "label": "Resize Mode",
             "choices": [
                 {"value": "percentage", "label": "By Percentage"},
                 {"value": "dimensions", "label": "By Dimensions"},
             ]},
            {"type": "number", "name": "percentage", "label": "Scale (%)", "default": 50, "min": 1, "max": 1000,
             "depends_on": {"mode": "percentage"}},
            {"type": "number", "name": "width", "label": "Width (px)",
             "depends_on": {"mode": "dimensions"}},
            {"type": "number", "name": "height", "label": "Height (px)",
             "depends_on": {"mode": "dimensions"}},
            {"type": "checkbox", "name": "keep_ratio", "label": "Aspect Ratio",
             "check_label": "Maintain aspect ratio", "default": True,
             "depends_on": {"mode": "dimensions"}},
        ])


@bp.route("/compress")
def compress_page():
    return render_template("upload_tool.html",
        title="Compress Image",
        description="Reduce image file size while controlling quality",
        endpoint="/image/compress",
        accept=IMAGE_ACCEPT,
        multiple=False,
        options=[
            {"type": "range", "name": "quality", "label": "Quality",
             "default": 70, "min": 10, "max": 100, "step": 5, "suffix": "%"},
        ])


@bp.route("/convert")
def convert_page():
    return render_template("upload_tool.html",
        title="Convert Image Format",
        description="Convert images between different formats",
        endpoint="/image/convert",
        accept=IMAGE_ACCEPT,
        multiple=False,
        options=[
            {"type": "select", "name": "format", "label": "Convert to",
             "choices": [
                 {"value": "png", "label": "PNG"},
                 {"value": "jpg", "label": "JPG"},
                 {"value": "webp", "label": "WebP"},
                 {"value": "bmp", "label": "BMP"},
                 {"value": "tiff", "label": "TIFF"},
             ]},
        ])


@bp.route("/remove-bg")
def remove_bg_page():
    return render_template("upload_tool.html",
        title="Remove Background",
        description="Automatically remove the background from images",
        endpoint="/image/remove-bg",
        accept=IMAGE_ACCEPT,
        multiple=False,
        options=[])


@bp.route("/crop")
def crop_page():
    return render_template("upload_tool.html",
        title="Crop Image",
        description="Crop images using preset ratios or custom coordinates",
        endpoint="/image/crop",
        accept=IMAGE_ACCEPT,
        multiple=False,
        options=[
            {"type": "select", "name": "mode", "label": "Crop Mode",
             "choices": [
                 {"value": "ratio", "label": "Aspect Ratio (center crop)"},
                 {"value": "custom", "label": "Custom Coordinates"},
             ]},
            {"type": "select", "name": "ratio", "label": "Aspect Ratio",
             "choices": [
                 {"value": "1:1", "label": "1:1 (Square)"},
                 {"value": "4:3", "label": "4:3"},
                 {"value": "3:2", "label": "3:2"},
                 {"value": "16:9", "label": "16:9"},
                 {"value": "9:16", "label": "9:16 (Vertical)"},
             ],
             "depends_on": {"mode": "ratio"}},
            {"type": "number", "name": "left", "label": "Left (px)", "default": 0,
             "depends_on": {"mode": "custom"}},
            {"type": "number", "name": "top", "label": "Top (px)", "default": 0,
             "depends_on": {"mode": "custom"}},
            {"type": "number", "name": "right", "label": "Right (px)",
             "depends_on": {"mode": "custom"}},
            {"type": "number", "name": "bottom", "label": "Bottom (px)",
             "depends_on": {"mode": "custom"}},
        ])


@bp.route("/rotate")
def rotate_page():
    return render_template("upload_tool.html",
        title="Rotate / Flip Image",
        description="Rotate or flip images",
        endpoint="/image/rotate",
        accept=IMAGE_ACCEPT,
        multiple=False,
        options=[
            {"type": "select", "name": "action", "label": "Action",
             "choices": [
                 {"value": "90", "label": "Rotate 90° Clockwise"},
                 {"value": "180", "label": "Rotate 180°"},
                 {"value": "270", "label": "Rotate 90° Counter-clockwise"},
                 {"value": "flip_h", "label": "Flip Horizontal"},
                 {"value": "flip_v", "label": "Flip Vertical"},
             ]},
        ])


@bp.route("/exif")
def exif_page():
    return render_template("upload_tool.html",
        title="EXIF Viewer / Stripper",
        description="View or remove metadata (EXIF) from images",
        endpoint="/image/exif",
        accept=IMAGE_ACCEPT,
        multiple=False,
        options=[
            {"type": "select", "name": "action", "label": "Action",
             "choices": [
                 {"value": "view", "label": "View EXIF data"},
                 {"value": "strip", "label": "Strip EXIF data"},
             ]},
        ])


@bp.route("/favicon")
def favicon_page():
    return render_template("upload_tool.html",
        title="Favicon Generator",
        description="Create a .ico favicon from any image",
        endpoint="/image/favicon",
        accept=IMAGE_ACCEPT,
        multiple=False,
        options=[
            {"type": "select", "name": "sizes", "label": "Sizes to include",
             "choices": [
                 {"value": "all", "label": "All (16, 32, 48, 64, 128, 256)"},
                 {"value": "standard", "label": "Standard (16, 32, 48)"},
                 {"value": "16", "label": "16x16 only"},
                 {"value": "32", "label": "32x32 only"},
             ]},
        ],
        button_text="Generate Favicon")


@bp.route("/ocr")
def ocr_page():
    return render_template("upload_tool.html",
        title="Image to Text (OCR)",
        description="Extract text from images using optical character recognition",
        endpoint="/image/ocr",
        accept=IMAGE_ACCEPT,
        multiple=False,
        options=[])


@bp.route("/watermark")
def watermark_page():
    return render_template("upload_tool.html",
        title="Add Watermark",
        description="Add a text watermark to images",
        endpoint="/image/watermark",
        accept=IMAGE_ACCEPT,
        multiple=False,
        options=[
            {"type": "text", "name": "text", "label": "Watermark Text", "placeholder": "Your watermark text"},
            {"type": "select", "name": "position", "label": "Position",
             "choices": [
                 {"value": "center", "label": "Center"},
                 {"value": "bottom-right", "label": "Bottom Right"},
                 {"value": "bottom-left", "label": "Bottom Left"},
                 {"value": "top-right", "label": "Top Right"},
                 {"value": "top-left", "label": "Top Left"},
                 {"value": "tiled", "label": "Tiled (repeated)"},
             ]},
            {"type": "range", "name": "opacity", "label": "Opacity",
             "default": 40, "min": 10, "max": 100, "step": 5, "suffix": "%"},
            {"type": "number", "name": "fontsize", "label": "Font Size", "default": 36, "min": 10, "max": 200},
        ])


# ── Processing Routes ────────────────────────────

@bp.route("/resize", methods=["POST"])
def resize():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="No file uploaded."), 400

    img = get_pil_image(files[0])
    mode = request.form.get("mode", "percentage")

    if mode == "percentage":
        pct = float(request.form.get("percentage", 50)) / 100.0
        new_size = (int(img.width * pct), int(img.height * pct))
    else:
        w = request.form.get("width", "")
        h = request.form.get("height", "")
        keep_ratio = request.form.get("keep_ratio") == "on"

        if not w and not h:
            return jsonify(error="Enter at least width or height."), 400

        w = int(w) if w else None
        h = int(h) if h else None

        if keep_ratio:
            if w and h:
                ratio = min(w / img.width, h / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
            elif w:
                ratio = w / img.width
                new_size = (w, int(img.height * ratio))
            else:
                ratio = h / img.height
                new_size = (int(img.width * ratio), h)
        else:
            new_size = (w or img.width, h or img.height)

    img = img.resize(new_size, Image.LANCZOS)

    ext = files[0].filename.rsplit(".", 1)[1].lower() if "." in files[0].filename else "png"
    fmt_info = FORMAT_MAP.get(ext, FORMAT_MAP["png"])
    buf = image_to_bytes(img, fmt_info[0])

    name = files[0].filename.rsplit(".", 1)[0] + f"_resized.{fmt_info[2]}"
    return send_file(buf, mimetype=fmt_info[1], as_attachment=True, download_name=name)


@bp.route("/compress", methods=["POST"])
def compress():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="No file uploaded."), 400

    quality = int(request.form.get("quality", 70))
    img = get_pil_image(files[0])

    # Always output as JPEG for best compression
    buf = image_to_bytes(img, "JPEG", quality=quality)

    name = files[0].filename.rsplit(".", 1)[0] + "_compressed.jpg"
    return send_file(buf, mimetype="image/jpeg", as_attachment=True, download_name=name)


@bp.route("/convert", methods=["POST"])
def convert():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="No file uploaded."), 400

    target = request.form.get("format", "png")
    fmt_info = FORMAT_MAP.get(target, FORMAT_MAP["png"])

    img = get_pil_image(files[0])
    buf = image_to_bytes(img, fmt_info[0])

    name = files[0].filename.rsplit(".", 1)[0] + f".{fmt_info[2]}"
    return send_file(buf, mimetype=fmt_info[1], as_attachment=True, download_name=name)


@bp.route("/remove-bg", methods=["POST"])
def remove_bg():
    if not HAS_REMBG:
        return jsonify(error="Background removal requires the 'rembg' package. Install with: pip install rembg"), 400

    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="No file uploaded."), 400

    input_data = files[0].read()
    output_data = rembg_remove(input_data)

    name = files[0].filename.rsplit(".", 1)[0] + "_nobg.png"
    return send_file(io.BytesIO(output_data), mimetype="image/png",
                     as_attachment=True, download_name=name)


@bp.route("/crop", methods=["POST"])
def crop():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="No file uploaded."), 400

    img = get_pil_image(files[0])
    mode = request.form.get("mode", "ratio")

    if mode == "ratio":
        ratio_str = request.form.get("ratio", "1:1")
        rw, rh = [int(x) for x in ratio_str.split(":")]
        target_ratio = rw / rh
        current_ratio = img.width / img.height

        if current_ratio > target_ratio:
            new_w = int(img.height * target_ratio)
            left = (img.width - new_w) // 2
            box = (left, 0, left + new_w, img.height)
        else:
            new_h = int(img.width / target_ratio)
            top = (img.height - new_h) // 2
            box = (0, top, img.width, top + new_h)
    else:
        left = int(request.form.get("left", 0))
        top = int(request.form.get("top", 0))
        right = int(request.form.get("right", img.width))
        bottom = int(request.form.get("bottom", img.height))
        box = (left, top, right, bottom)

    img = img.crop(box)

    ext = files[0].filename.rsplit(".", 1)[1].lower() if "." in files[0].filename else "png"
    fmt_info = FORMAT_MAP.get(ext, FORMAT_MAP["png"])
    buf = image_to_bytes(img, fmt_info[0])

    name = files[0].filename.rsplit(".", 1)[0] + f"_cropped.{fmt_info[2]}"
    return send_file(buf, mimetype=fmt_info[1], as_attachment=True, download_name=name)


@bp.route("/rotate", methods=["POST"])
def rotate():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="No file uploaded."), 400

    action = request.form.get("action", "90")
    img = get_pil_image(files[0])

    if action == "90":
        img = img.rotate(-90, expand=True)
    elif action == "180":
        img = img.rotate(180, expand=True)
    elif action == "270":
        img = img.rotate(90, expand=True)
    elif action == "flip_h":
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    elif action == "flip_v":
        img = img.transpose(Image.FLIP_TOP_BOTTOM)

    ext = files[0].filename.rsplit(".", 1)[1].lower() if "." in files[0].filename else "png"
    fmt_info = FORMAT_MAP.get(ext, FORMAT_MAP["png"])
    buf = image_to_bytes(img, fmt_info[0])

    name = files[0].filename.rsplit(".", 1)[0] + f"_rotated.{fmt_info[2]}"
    return send_file(buf, mimetype=fmt_info[1], as_attachment=True, download_name=name)


@bp.route("/watermark", methods=["POST"])
def watermark():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="No file uploaded."), 400

    text = request.form.get("text", "Watermark")
    if not text:
        return jsonify(error="Please enter watermark text."), 400

    position = request.form.get("position", "center")
    opacity = int(request.form.get("opacity", 40))
    fontsize = int(request.form.get("fontsize", 36))

    img = get_pil_image(files[0]).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    try:
        font = ImageFont.truetype("arial.ttf", fontsize)
    except OSError:
        font = ImageFont.load_default()

    alpha = int(255 * opacity / 100)
    fill = (255, 255, 255, alpha)

    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]

    if position == "tiled":
        step_x = tw + 60
        step_y = th + 60
        for y in range(0, img.height + step_y, step_y):
            for x in range(0, img.width + step_x, step_x):
                draw.text((x, y), text, fill=fill, font=font)
    else:
        margin = 20
        positions = {
            "center": ((img.width - tw) / 2, (img.height - th) / 2),
            "bottom-right": (img.width - tw - margin, img.height - th - margin),
            "bottom-left": (margin, img.height - th - margin),
            "top-right": (img.width - tw - margin, margin),
            "top-left": (margin, margin),
        }
        pos = positions.get(position, positions["center"])
        draw.text(pos, text, fill=fill, font=font)

    result = Image.alpha_composite(img, overlay).convert("RGB")

    ext = files[0].filename.rsplit(".", 1)[1].lower() if "." in files[0].filename else "png"
    fmt_info = FORMAT_MAP.get(ext, FORMAT_MAP["png"])
    buf = image_to_bytes(result, fmt_info[0])

    name = files[0].filename.rsplit(".", 1)[0] + f"_watermarked.{fmt_info[2]}"
    return send_file(buf, mimetype=fmt_info[1], as_attachment=True, download_name=name)


@bp.route("/exif", methods=["POST"])
def exif():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="No file uploaded."), 400

    action = request.form.get("action", "view")
    img = get_pil_image(files[0])

    if action == "view":
        exif_data = {}
        raw_exif = img._getexif()
        if raw_exif:
            for tag_id, value in raw_exif.items():
                tag_name = TAGS.get(tag_id, tag_id)
                # Convert bytes to string for JSON serialization
                if isinstance(value, bytes):
                    try:
                        value = value.decode("utf-8", errors="replace")
                    except Exception:
                        value = str(value)
                elif not isinstance(value, (str, int, float, list, dict, bool, type(None))):
                    value = str(value)
                exif_data[str(tag_name)] = value
        if not exif_data:
            return jsonify(text="No EXIF data found in this image.")
        import json
        return jsonify(text=json.dumps(exif_data, indent=2, ensure_ascii=False))
    else:
        # Strip EXIF by re-saving without exif
        cleaned = Image.new(img.mode, img.size)
        cleaned.putdata(list(img.getdata()))

        ext = files[0].filename.rsplit(".", 1)[1].lower() if "." in files[0].filename else "png"
        fmt_info = FORMAT_MAP.get(ext, FORMAT_MAP["png"])
        buf = image_to_bytes(cleaned, fmt_info[0])

        name = files[0].filename.rsplit(".", 1)[0] + f"_clean.{fmt_info[2]}"
        return send_file(buf, mimetype=fmt_info[1], as_attachment=True, download_name=name)


@bp.route("/favicon", methods=["POST"])
def favicon():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="No file uploaded."), 400

    size_opt = request.form.get("sizes", "all")
    size_map = {
        "all": [16, 32, 48, 64, 128, 256],
        "standard": [16, 32, 48],
        "16": [16],
        "32": [32],
    }
    sizes = size_map.get(size_opt, size_map["all"])

    img = get_pil_image(files[0]).convert("RGBA")
    icons = []
    for s in sizes:
        icons.append(img.resize((s, s), Image.LANCZOS))

    buf = io.BytesIO()
    icons[0].save(buf, format="ICO", sizes=[(s, s) for s in sizes],
                  append_images=icons[1:] if len(icons) > 1 else [])
    buf.seek(0)

    return send_file(buf, mimetype="image/x-icon",
                     as_attachment=True, download_name="favicon.ico")


@bp.route("/ocr", methods=["POST"])
def ocr():
    if not HAS_TESSERACT:
        return jsonify(error="OCR requires 'pytesseract' package and Tesseract binary. Install with: pip install pytesseract, then install Tesseract from https://github.com/tesseract-ocr/tesseract"), 400

    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="No file uploaded."), 400

    img = get_pil_image(files[0])
    text = pytesseract.image_to_string(img)

    if not text.strip():
        return jsonify(text="(No text detected in image)")
    return jsonify(text=text)
