import io
from flask import Blueprint, render_template, request, send_file, jsonify
from PIL import Image, ImageDraw, ImageFont
from PIL.ExifTags import TAGS

from routes._helpers import safe_int, safe_float, log_error, NO_FILE_SINGLE

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
    """Open an uploaded image. Caller is responsible for closing.

    Used by routes that need a single in-memory PIL.Image. Routes that should
    properly close the image on error paths use _safe_open_image() instead.
    """
    return Image.open(io.BytesIO(file.read()))


def _safe_open_image(file):
    """Open a Werkzeug FileStorage as a PIL.Image, raising ValueError on failure.

    Returns the opened image (caller should close or use as a context manager).
    """
    try:
        return Image.open(io.BytesIO(file.read()))
    except Exception as e:
        log_error(e, "Image.open")
        raise ValueError("Could not read image (file may be corrupted or not an image).")


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


@bp.route("/animated")
def animated_page():
    return render_template("upload_tool.html",
        title="Animated WebP / GIF",
        description="Convert animated GIF to WebP, or animated WebP to GIF (preserves timing)",
        endpoint="/image/animated",
        accept=".gif,.webp",
        multiple=False,
        options=[
            {"type": "select", "name": "target", "label": "Output Format",
             "choices": [
                 {"value": "webp", "label": "Animated WebP"},
                 {"value": "gif", "label": "GIF"},
             ]},
            {"type": "range", "name": "quality", "label": "WebP Quality",
             "default": 80, "min": 10, "max": 100, "step": 5, "suffix": "%",
             "depends_on": {"target": "webp"}},
            {"type": "number", "name": "fps", "label": "Override FPS (0 = keep original)",
             "default": 0, "min": 0, "max": 60},
            {"type": "checkbox", "name": "lossless", "label": "Lossless",
             "check_label": "Lossless WebP (larger file)", "default": False,
             "depends_on": {"target": "webp"}},
        ])


@bp.route("/ocr")
def ocr_page():
    return render_template("upload_tool.html",
        title="Image to Text (OCR)",
        description="Extract text from images using optical character recognition",
        endpoint="/image/ocr",
        accept=IMAGE_ACCEPT,
        multiple=False,
        options=[])


@bp.route("/palette")
def palette_page():
    return render_template("upload_tool.html",
        title="Color Palette",
        description="Extract the dominant colors from an image",
        endpoint="/image/palette",
        accept=IMAGE_ACCEPT,
        multiple=False,
        options=[
            {"type": "number", "name": "count", "label": "Number of colors", "default": 8, "min": 2, "max": 32},
            {"type": "select", "name": "method", "label": "Method", "default": "quantize",
             "choices": [
                 {"value": "quantize", "label": "Pillow quantize (fast, median-cut)"},
                 {"value": "grid", "label": "Grid sampling (broader spread)"},
             ]},
        ])


@bp.route("/svg-to-png")
def svg_to_png_page():
    return render_template("upload_tool.html",
        title="SVG to PNG",
        description="Rasterise an SVG file to a PNG image",
        endpoint="/image/svg-to-png",
        accept=".svg",
        multiple=False,
        options=[
            {"type": "number", "name": "width", "label": "Output width (pixels, 0 = native size)",
             "default": 0, "min": 0, "max": 8192},
            {"type": "checkbox", "name": "transparent", "label": "Background",
             "default": True, "check_label": "Transparent (otherwise white)"},
        ])


@bp.route("/svg-optimize")
def svg_optimize_page():
    return render_template("upload_tool.html",
        title="SVG Optimizer",
        description="Strip comments, metadata, and whitespace from SVG files",
        endpoint="/image/svg-optimize",
        accept=".svg",
        multiple=False,
        options=[
            {"type": "checkbox", "name": "strip_comments", "label": "Comments",
             "default": True, "check_label": "Remove <!-- comments -->"},
            {"type": "checkbox", "name": "strip_metadata", "label": "Metadata",
             "default": True, "check_label": "Remove <metadata>, <title>, <desc>, editor namespaces"},
            {"type": "checkbox", "name": "collapse_whitespace", "label": "Whitespace",
             "default": True, "check_label": "Collapse whitespace between tags"},
            {"type": "number", "name": "decimals", "label": "Max decimal places for numbers",
             "default": 3, "min": 0, "max": 6},
        ])


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
        return jsonify(error=NO_FILE_SINGLE), 400

    try:
        img = _safe_open_image(files[0])
    except ValueError as e:
        return jsonify(error=str(e)), 400

    mode = request.form.get("mode", "percentage")

    if mode == "percentage":
        pct = safe_float(request.form.get("percentage"), 50.0,
                         min_val=1.0, max_val=1000.0) / 100.0
        new_size = (max(1, int(img.width * pct)),
                    max(1, int(img.height * pct)))
    else:
        w_raw = request.form.get("width", "").strip()
        h_raw = request.form.get("height", "").strip()
        keep_ratio = request.form.get("keep_ratio") == "on"

        if not w_raw and not h_raw:
            return jsonify(error="Enter at least a width or a height."), 400

        w = safe_int(w_raw, 0, min_val=1, max_val=20000) if w_raw else None
        h = safe_int(h_raw, 0, min_val=1, max_val=20000) if h_raw else None

        if keep_ratio:
            if w and h:
                ratio = min(w / img.width, h / img.height)
                new_size = (max(1, int(img.width * ratio)),
                            max(1, int(img.height * ratio)))
            elif w:
                ratio = w / img.width
                new_size = (w, max(1, int(img.height * ratio)))
            else:
                ratio = h / img.height
                new_size = (max(1, int(img.width * ratio)), h)
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
        return jsonify(error=NO_FILE_SINGLE), 400

    quality = safe_int(request.form.get("quality"), 70, min_val=1, max_val=100)
    try:
        img = _safe_open_image(files[0])
    except ValueError as e:
        return jsonify(error=str(e)), 400

    # Always output as JPEG for best compression
    buf = image_to_bytes(img, "JPEG", quality=quality)

    name = files[0].filename.rsplit(".", 1)[0] + "_compressed.jpg"
    return send_file(buf, mimetype="image/jpeg", as_attachment=True, download_name=name)


@bp.route("/convert", methods=["POST"])
def convert():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    target = request.form.get("format", "png")
    fmt_info = FORMAT_MAP.get(target, FORMAT_MAP["png"])

    try:
        img = _safe_open_image(files[0])
    except ValueError as e:
        return jsonify(error=str(e)), 400

    buf = image_to_bytes(img, fmt_info[0])

    name = files[0].filename.rsplit(".", 1)[0] + f".{fmt_info[2]}"
    return send_file(buf, mimetype=fmt_info[1], as_attachment=True, download_name=name)


@bp.route("/remove-bg", methods=["POST"])
def remove_bg():
    if not HAS_REMBG:
        return jsonify(error="Background removal requires the 'rembg' package. Install with: pip install rembg"), 400

    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    input_data = files[0].read()
    try:
        output_data = rembg_remove(input_data)
    except Exception as e:
        log_error(e, "remove_bg")
        return jsonify(error="Background removal failed (the file may not be a valid image)."), 400

    name = files[0].filename.rsplit(".", 1)[0] + "_nobg.png"
    return send_file(io.BytesIO(output_data), mimetype="image/png",
                     as_attachment=True, download_name=name)


@bp.route("/crop", methods=["POST"])
def crop():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    try:
        img = _safe_open_image(files[0])
    except ValueError as e:
        return jsonify(error=str(e)), 400

    mode = request.form.get("mode", "ratio")

    if mode == "ratio":
        ratio_str = request.form.get("ratio", "1:1")
        try:
            rw, rh = [int(x) for x in ratio_str.split(":")]
            if rw <= 0 or rh <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return jsonify(error="Invalid ratio. Use a value like 1:1, 4:3, or 16:9."), 400
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
        left = safe_int(request.form.get("left"), 0,
                        min_val=0, max_val=img.width - 1)
        top = safe_int(request.form.get("top"), 0,
                       min_val=0, max_val=img.height - 1)
        right = safe_int(request.form.get("right"), img.width,
                         min_val=left + 1, max_val=img.width)
        bottom = safe_int(request.form.get("bottom"), img.height,
                          min_val=top + 1, max_val=img.height)
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
        return jsonify(error=NO_FILE_SINGLE), 400

    action = request.form.get("action", "90")
    try:
        img = _safe_open_image(files[0])
    except ValueError as e:
        return jsonify(error=str(e)), 400

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
        return jsonify(error=NO_FILE_SINGLE), 400

    text = request.form.get("text", "Watermark")
    if not text:
        return jsonify(error="Please enter watermark text."), 400

    position = request.form.get("position", "center")
    opacity = safe_int(request.form.get("opacity"), 40, min_val=1, max_val=100)
    fontsize = safe_int(request.form.get("fontsize"), 36, min_val=8, max_val=400)

    try:
        img = _safe_open_image(files[0]).convert("RGBA")
    except ValueError as e:
        return jsonify(error=str(e)), 400
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
        return jsonify(error=NO_FILE_SINGLE), 400

    action = request.form.get("action", "view")
    try:
        img = _safe_open_image(files[0])
    except ValueError as e:
        return jsonify(error=str(e)), 400

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
        return jsonify(error=NO_FILE_SINGLE), 400

    size_opt = request.form.get("sizes", "all")
    size_map = {
        "all": [16, 32, 48, 64, 128, 256],
        "standard": [16, 32, 48],
        "16": [16],
        "32": [32],
    }
    sizes = size_map.get(size_opt, size_map["all"])

    try:
        img = _safe_open_image(files[0]).convert("RGBA")
    except ValueError as e:
        return jsonify(error=str(e)), 400
    icons = []
    for s in sizes:
        icons.append(img.resize((s, s), Image.LANCZOS))

    buf = io.BytesIO()
    icons[0].save(buf, format="ICO", sizes=[(s, s) for s in sizes],
                  append_images=icons[1:] if len(icons) > 1 else [])
    buf.seek(0)

    return send_file(buf, mimetype="image/x-icon",
                     as_attachment=True, download_name="favicon.ico")


@bp.route("/animated", methods=["POST"])
def animated():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    target = request.form.get("target", "webp").lower()
    quality = safe_int(request.form.get("quality"), 80, min_val=1, max_val=100)
    fps_override = safe_int(request.form.get("fps"), 0, min_val=0, max_val=60)
    lossless = request.form.get("lossless") == "on"

    try:
        src = _safe_open_image(files[0])
    except ValueError as e:
        return jsonify(error=str(e)), 400

    frames = []
    durations = []
    try:
        while True:
            frame = src.copy()
            if frame.mode == "P":
                frame = frame.convert("RGBA")
            frames.append(frame)
            durations.append(src.info.get("duration", 100))
            src.seek(src.tell() + 1)
    except EOFError:
        pass

    if not frames:
        return jsonify(error="No frames found in image."), 400

    if fps_override > 0:
        per_frame_ms = int(1000 / fps_override)
        durations = [per_frame_ms] * len(frames)

    loop = src.info.get("loop", 0)
    buf = io.BytesIO()
    base = files[0].filename.rsplit(".", 1)[0]

    if target == "webp":
        save_kwargs = {
            "format": "WEBP",
            "save_all": True,
            "append_images": frames[1:],
            "duration": durations,
            "loop": loop,
            "lossless": lossless,
        }
        if not lossless:
            save_kwargs["quality"] = quality
        frames[0].save(buf, **save_kwargs)
        buf.seek(0)
        return send_file(buf, mimetype="image/webp",
                         as_attachment=True, download_name=base + ".webp")

    # GIF output — GIF palette is 256 colors
    gif_frames = [f.convert("RGBA") for f in frames]
    disposal_frames = []
    for f in gif_frames:
        if f.mode == "RGBA":
            bg = Image.new("RGBA", f.size, (255, 255, 255, 255))
            bg.paste(f, mask=f.split()[3])
            disposal_frames.append(bg.convert("P", palette=Image.ADAPTIVE, colors=256))
        else:
            disposal_frames.append(f.convert("P", palette=Image.ADAPTIVE, colors=256))

    disposal_frames[0].save(
        buf, format="GIF", save_all=True,
        append_images=disposal_frames[1:],
        duration=durations, loop=loop, optimize=True, disposal=2,
    )
    buf.seek(0)
    return send_file(buf, mimetype="image/gif",
                     as_attachment=True, download_name=base + ".gif")


@bp.route("/ocr", methods=["POST"])
def ocr():
    if not HAS_TESSERACT:
        return jsonify(error="OCR requires 'pytesseract' package and Tesseract binary. Install with: pip install pytesseract, then install Tesseract from https://github.com/tesseract-ocr/tesseract"), 400

    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    try:
        img = _safe_open_image(files[0])
    except ValueError as e:
        return jsonify(error=str(e)), 400

    try:
        text = pytesseract.image_to_string(img)
    except Exception as e:
        log_error(e, "ocr")
        return jsonify(error="OCR failed (Tesseract may not be installed correctly)."), 400

    if not text.strip():
        return jsonify(text="(No text detected in image)")
    return jsonify(text=text)


@bp.route("/palette", methods=["POST"])
def palette():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    count = safe_int(request.form.get("count"), 8, min_val=2, max_val=32)
    method = request.form.get("method", "quantize")

    try:
        img = _safe_open_image(files[0]).convert("RGBA")
    except ValueError as e:
        return jsonify(error=str(e)), 400
    # Composite onto white to ignore transparency for colour analysis
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
    img = bg

    # Downsample large images for speed — quantization cost is O(pixels)
    MAX_DIM = 600
    if max(img.size) > MAX_DIM:
        ratio = MAX_DIM / max(img.size)
        img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)

    if method == "grid":
        # Sample pixels on a grid, collapse close colours by 16-bucket quantization
        samples: dict[tuple, int] = {}
        step = max(1, int((img.width * img.height / 4000) ** 0.5))
        for y in range(0, img.height, step):
            for x in range(0, img.width, step):
                r, g, b = img.getpixel((x, y))[:3]
                key = (r // 16 * 16, g // 16 * 16, b // 16 * 16)
                samples[key] = samples.get(key, 0) + 1
        sorted_colours = sorted(samples.items(), key=lambda kv: -kv[1])[:count]
        total = sum(c for _, c in sorted_colours) or 1
        palette_list = [
            {"hex": "#{:02x}{:02x}{:02x}".format(*rgb),
             "rgb": list(rgb),
             "percent": round(c * 100 / total, 1)}
            for rgb, c in sorted_colours
        ]
    else:
        quant = img.quantize(colors=count, method=Image.Quantize.MEDIANCUT)
        pal_bytes = quant.getpalette() or []
        colour_counts = quant.getcolors() or []
        counts_by_index = {idx: cnt for cnt, idx in colour_counts}
        total = sum(counts_by_index.values()) or 1
        actual_count = min(count, len(pal_bytes) // 3)
        palette_list = []
        for i in range(actual_count):
            r, g, b = pal_bytes[i * 3], pal_bytes[i * 3 + 1], pal_bytes[i * 3 + 2]
            palette_list.append({
                "hex": f"#{r:02x}{g:02x}{b:02x}",
                "rgb": [r, g, b],
                "percent": round(counts_by_index.get(i, 0) * 100 / total, 1),
            })
        # Drop entries with 0% (uninhabited palette slots)
        palette_list = [p for p in palette_list if p["percent"] > 0] or palette_list[:1]
        palette_list.sort(key=lambda p: -p["percent"])

    # Build a preview swatch PNG (one column per colour, weighted widths)
    swatch_w, swatch_h = 600, 120
    swatch = Image.new("RGB", (swatch_w, swatch_h), (255, 255, 255))
    draw = ImageDraw.Draw(swatch)
    # Normalise widths so they sum to swatch_w
    weights = [max(p["percent"], 3) for p in palette_list]  # floor so tiny colours are visible
    total_w = sum(weights)
    x = 0
    for p, w in zip(palette_list, weights):
        seg = int(swatch_w * w / total_w)
        draw.rectangle([x, 0, x + seg, swatch_h], fill=tuple(p["rgb"]))
        x += seg
    if x < swatch_w:
        draw.rectangle([x, 0, swatch_w, swatch_h], fill=tuple(palette_list[-1]["rgb"]))

    swatch_buf = io.BytesIO()
    swatch.save(swatch_buf, format="PNG")
    import base64
    swatch_b64 = base64.b64encode(swatch_buf.getvalue()).decode()

    lines = ["Color palette:"]
    for p in palette_list:
        lines.append(f"  {p['hex']}  rgb({p['rgb'][0]}, {p['rgb'][1]}, {p['rgb'][2]})   {p['percent']}%")
    lines.append("")
    lines.append(f"<img src='data:image/png;base64,{swatch_b64}' style='max-width:100%;border-radius:6px;margin-top:.6rem'>")

    return jsonify(text="\n".join(lines))


@bp.route("/svg-to-png", methods=["POST"])
def svg_to_png():
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPM

    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="Please upload an SVG file."), 400

    svg_bytes = files[0].read()
    svg_stream = io.BytesIO(svg_bytes)
    try:
        drawing = svg2rlg(svg_stream)
    except Exception as e:
        log_error(e, "svg-to-png parse")
        return jsonify(error="Could not parse SVG (file may be malformed)."), 400
    if drawing is None:
        return jsonify(error="SVG parser returned no drawing — is the file valid?"), 400

    target_w = safe_int(request.form.get("width"), 0, min_val=0, max_val=10000)
    transparent = request.form.get("transparent") == "on"

    if target_w > 0 and drawing.width > 0:
        scale = target_w / drawing.width
        drawing.width *= scale
        drawing.height *= scale
        drawing.scale(scale, scale)

    bg_hex = None if transparent else "white"
    png_bytes = renderPM.drawToString(drawing, fmt="PNG", bg=0xffffff if bg_hex == "white" else 0xffffff)
    # Pillow post-process to add transparency if requested (renderPM always outputs white bg)
    if transparent:
        img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        datas = img.getdata()
        new_data = [
            (r, g, b, 0) if (r, g, b) == (255, 255, 255) else (r, g, b, a)
            for (r, g, b, a) in datas
        ]
        img.putdata(new_data)
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        buf.seek(0)
        out_bytes = buf.getvalue()
    else:
        out_bytes = png_bytes

    name = files[0].filename.rsplit(".", 1)[0] + ".png"
    return send_file(io.BytesIO(out_bytes), mimetype="image/png",
                     as_attachment=True, download_name=name)


@bp.route("/svg-optimize", methods=["POST"])
def svg_optimize():
    import re

    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="Please upload an SVG file."), 400

    raw = files[0].read()
    try:
        svg = raw.decode("utf-8")
    except UnicodeDecodeError:
        svg = raw.decode("utf-8", errors="ignore")

    original_size = len(raw)

    strip_comments = request.form.get("strip_comments") == "on"
    strip_metadata = request.form.get("strip_metadata") == "on"
    collapse_ws = request.form.get("collapse_whitespace") == "on"
    decimals = safe_int(request.form.get("decimals"), 3, min_val=0, max_val=6)

    if strip_comments:
        svg = re.sub(r"<!--[\s\S]*?-->", "", svg)

    if strip_metadata:
        for tag in ("metadata", "title", "desc"):
            svg = re.sub(rf"<{tag}\b[^>]*>[\s\S]*?</{tag}>", "", svg, flags=re.IGNORECASE)
            svg = re.sub(rf"<{tag}\b[^/]*/>", "", svg, flags=re.IGNORECASE)
        # Strip common editor-specific namespaces (inkscape, sodipodi, adobe, sketch)
        svg = re.sub(r"\s+(sodipodi|inkscape|adobe|sketch):[a-zA-Z_-]+\s*=\s*\"[^\"]*\"", "", svg)
        svg = re.sub(r"\s+xmlns:(sodipodi|inkscape|adobe|sketch)\s*=\s*\"[^\"]*\"", "", svg)

    # Round numbers to `decimals` places
    def _round(m):
        num = float(m.group(0))
        if num == int(num):
            return str(int(num))
        s = f"{num:.{decimals}f}".rstrip("0").rstrip(".")
        return s or "0"
    svg = re.sub(r"-?\d+\.\d+", _round, svg)

    if collapse_ws:
        svg = re.sub(r">\s+<", "><", svg)
        svg = re.sub(r"\s{2,}", " ", svg)
        svg = svg.strip()

    optimized_bytes = svg.encode("utf-8")
    saved_pct = round((original_size - len(optimized_bytes)) * 100 / original_size, 1) if original_size else 0

    name = files[0].filename.rsplit(".", 1)[0] + "_optimized.svg"
    resp = send_file(io.BytesIO(optimized_bytes), mimetype="image/svg+xml",
                     as_attachment=True, download_name=name)
    resp.headers["X-Original-Size"] = str(original_size)
    resp.headers["X-Optimized-Size"] = str(len(optimized_bytes))
    resp.headers["X-Saved-Percent"] = str(saved_pct)
    return resp
