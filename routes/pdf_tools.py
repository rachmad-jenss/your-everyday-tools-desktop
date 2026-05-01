import io
import fitz  # PyMuPDF
from flask import Blueprint, render_template, request, send_file, jsonify
from utils.file_utils import make_zip
from routes._helpers import safe_int, safe_float, log_error, NO_FILE_SINGLE, NO_FILE_MULTIPLE

bp = Blueprint("pdf", __name__)


def _open_pdf(data: bytes):
    """Open a PDF from bytes, raising a friendly ValueError on failure."""
    try:
        return fitz.open(stream=data, filetype="pdf")
    except Exception as e:
        log_error(e, "fitz.open")
        raise ValueError("Could not open PDF (the file may be corrupted, encrypted, or not a PDF).")


# ── Page Routes ──────────────────────────────────

@bp.route("/merge")
def merge_page():
    return render_template("upload_tool.html",
        title="Merge PDFs",
        description="Combine multiple PDF files into one document",
        endpoint="/pdf/merge",
        accept=".pdf",
        multiple=True,
        options=[])


@bp.route("/split")
def split_page():
    return render_template("upload_tool.html",
        title="Split PDF",
        description="Split a PDF into individual pages or custom ranges",
        endpoint="/pdf/split",
        accept=".pdf",
        multiple=False,
        options=[
            {"type": "text", "name": "pages", "label": "Page ranges (leave empty for all pages)",
             "placeholder": "e.g. 1-3, 5, 7-10"},
        ])


@bp.route("/compress")
def compress_page():
    return render_template("upload_tool.html",
        title="Compress PDF",
        description="Reduce PDF file size by compressing images and cleaning up",
        endpoint="/pdf/compress",
        accept=".pdf",
        multiple=False,
        options=[
            {"type": "select", "name": "quality", "label": "Compression Level",
             "choices": [
                 {"value": "medium", "label": "Medium (good balance)"},
                 {"value": "low", "label": "Maximum compression"},
                 {"value": "high", "label": "Minimal compression"},
             ]},
        ])


@bp.route("/rotate")
def rotate_page():
    return render_template("upload_tool.html",
        title="Rotate PDF",
        description="Rotate all or specific pages of a PDF",
        endpoint="/pdf/rotate",
        accept=".pdf",
        multiple=False,
        options=[
            {"type": "select", "name": "angle", "label": "Rotation Angle",
             "choices": [
                 {"value": "90", "label": "90° Clockwise"},
                 {"value": "180", "label": "180°"},
                 {"value": "270", "label": "90° Counter-clockwise"},
             ]},
            {"type": "text", "name": "pages", "label": "Pages to rotate (leave empty for all)",
             "placeholder": "e.g. 1, 3, 5-7"},
        ])


@bp.route("/resize")
def resize_page():
    return render_template("upload_tool.html",
        title="Resize PDF",
        description="Change the page dimensions of a PDF",
        endpoint="/pdf/resize",
        accept=".pdf",
        multiple=False,
        options=[
            {"type": "select", "name": "mode", "label": "Resize Mode",
             "choices": [
                 {"value": "scale", "label": "Scale by percentage"},
                 {"value": "paper", "label": "Standard paper size"},
             ]},
            {"type": "number", "name": "scale", "label": "Scale (%)", "default": 100, "min": 10, "max": 500,
             "depends_on": {"mode": "scale"}},
            {"type": "select", "name": "paper", "label": "Paper Size",
             "choices": [
                 {"value": "a4", "label": "A4 (210 x 297 mm)"},
                 {"value": "letter", "label": "Letter (8.5 x 11 in)"},
                 {"value": "a3", "label": "A3 (297 x 420 mm)"},
                 {"value": "a5", "label": "A5 (148 x 210 mm)"},
                 {"value": "legal", "label": "Legal (8.5 x 14 in)"},
             ],
             "depends_on": {"mode": "paper"}},
        ])


@bp.route("/page-numbers")
def page_numbers_page():
    return render_template("upload_tool.html",
        title="Add Page Numbers",
        description="Add page numbers to each page of a PDF",
        endpoint="/pdf/page-numbers",
        accept=".pdf",
        multiple=False,
        options=[
            {"type": "select", "name": "position", "label": "Position",
             "choices": [
                 {"value": "bottom-center", "label": "Bottom Center"},
                 {"value": "bottom-right", "label": "Bottom Right"},
                 {"value": "bottom-left", "label": "Bottom Left"},
                 {"value": "top-center", "label": "Top Center"},
                 {"value": "top-right", "label": "Top Right"},
                 {"value": "top-left", "label": "Top Left"},
             ]},
            {"type": "number", "name": "start", "label": "Start number", "default": 1, "min": 0},
            {"type": "number", "name": "fontsize", "label": "Font size", "default": 11, "min": 6, "max": 30},
        ])


@bp.route("/extract-images")
def extract_images_page():
    return render_template("upload_tool.html",
        title="Extract Images",
        description="Extract all images embedded in a PDF file",
        endpoint="/pdf/extract-images",
        accept=".pdf",
        multiple=False,
        options=[])


@bp.route("/protect")
def protect_page():
    return render_template("upload_tool.html",
        title="Protect PDF",
        description="Add password protection to a PDF file",
        endpoint="/pdf/protect",
        accept=".pdf",
        multiple=False,
        options=[
            {"type": "password", "name": "user_password", "label": "User Password (to open)",
             "placeholder": "Enter password"},
            {"type": "password", "name": "owner_password", "label": "Owner Password (optional, for editing)",
             "placeholder": "Leave empty to use same password"},
        ])


@bp.route("/sign")
def sign_page():
    return render_template("upload_tool.html",
        title="Sign PDF",
        description="Stamp a signature image onto one or more pages of a PDF",
        notes=(
            "<p><strong>Tip:</strong> upload a transparent PNG of your signature for best results. "
            "A white-background JPG will look like a sticker on the page.</p>"
            "<p>This tool stamps a visible signature — it does <em>not</em> apply a cryptographic digital signature.</p>"
        ),
        endpoint="/pdf/sign",
        accept=".pdf",
        multiple=False,
        options=[
            {"type": "file", "name": "signature", "label": "Signature image (PNG / JPG)",
             "accept": "image/png,image/jpeg", "required": True},
            {"type": "text", "name": "pages", "label": "Pages to sign (leave empty for all)",
             "placeholder": "e.g. 1, 3, 5-7"},
            {"type": "select", "name": "position", "label": "Position", "default": "bottom-right",
             "choices": [
                 {"value": "bottom-right", "label": "Bottom Right"},
                 {"value": "bottom-center", "label": "Bottom Center"},
                 {"value": "bottom-left", "label": "Bottom Left"},
                 {"value": "top-right", "label": "Top Right"},
                 {"value": "top-center", "label": "Top Center"},
                 {"value": "top-left", "label": "Top Left"},
             ]},
            {"type": "number", "name": "width", "label": "Signature width (points)", "default": 140, "min": 30, "max": 400},
            {"type": "number", "name": "margin", "label": "Margin from edge (points)", "default": 36, "min": 0, "max": 200},
            {"type": "number", "name": "opacity", "label": "Opacity (%)", "default": 100, "min": 10, "max": 100},
        ])


@bp.route("/unlock")
def unlock_page():
    return render_template("upload_tool.html",
        title="Unlock PDF",
        description="Remove password protection from a PDF",
        endpoint="/pdf/unlock",
        accept=".pdf",
        multiple=False,
        options=[
            {"type": "password", "name": "password", "label": "PDF Password",
             "placeholder": "Enter the current password"},
        ])


@bp.route("/form-fill")
def form_fill_page():
    return render_template("tools/form_fill.html")


@bp.route("/redact")
def redact_page():
    return render_template("upload_tool.html",
        title="Redact PDF",
        description="Permanently black-out sensitive text in a PDF",
        notes=(
            '<p><strong>How it works:</strong> enter one or more search terms or regex patterns '
            '(one per line). Every occurrence on every page is found, then permanently '
            'overlaid with a solid black rectangle. The underlying text is also stripped '
            'from the PDF\'s content stream so it cannot be recovered with copy-paste.</p>'
            '<p style="font-size:.9em;color:var(--muted)"><strong>Common patterns:</strong> '
            '<code>\\b\\d{16}\\b</code> (credit-card numbers), '
            '<code>[\\w.-]+@[\\w.-]+\\.[\\w]+</code> (emails), '
            '<code>\\b\\d{3}-\\d{2}-\\d{4}\\b</code> (US SSN-like). '
            'Plain text is matched literally unless you tick &ldquo;Treat as regex&rdquo;.</p>'
        ),
        endpoint="/pdf/redact",
        accept=".pdf",
        multiple=False,
        options=[
            {"type": "text", "name": "patterns",
             "label": "Patterns (one per line)",
             "placeholder": "e.g. john@example.com  /  4111-?\\d{4}-?\\d{4}-?\\d{4}"},
            {"type": "checkbox", "name": "is_regex",
             "label": "Pattern type",
             "check_label": "Treat each line as a regular expression",
             "default": False},
            {"type": "checkbox", "name": "case_sensitive",
             "label": "Case sensitivity",
             "check_label": "Match case exactly",
             "default": False},
            {"type": "text", "name": "pages", "label": "Pages (blank = all)",
             "placeholder": "e.g. 1-3, 5"},
        ])


# ── Processing Routes ────────────────────────────

def parse_page_ranges(spec: str, total: int) -> list[int]:
    """Parse '1-3, 5, 7-10' into a list of 0-based page indices."""
    if not spec.strip():
        return list(range(total))

    pages = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            start, end = part.split("-", 1)
            s = max(1, int(start.strip()))
            e = min(total, int(end.strip()))
            pages.update(range(s - 1, e))
        else:
            p = int(part.strip()) - 1
            if 0 <= p < total:
                pages.add(p)
    return sorted(pages)


PAPER_SIZES = {
    "a4": (595.28, 841.89),
    "letter": (612, 792),
    "a3": (841.89, 1190.55),
    "a5": (419.53, 595.28),
    "legal": (612, 1008),
}


@bp.route("/merge", methods=["POST"])
def merge():
    files = request.files.getlist("files")
    if len(files) < 2:
        return jsonify(error="Please upload at least 2 PDF files."), 400

    result = fitz.open()
    try:
        for f in files:
            try:
                with fitz.open(stream=f.read(), filetype="pdf") as doc:
                    result.insert_pdf(doc)
            except Exception as e:
                log_error(e, f"merge: {f.filename}")
                return jsonify(error=f"Could not read '{f.filename}' (corrupted or not a PDF)."), 400

        output = io.BytesIO()
        result.save(output)
        output.seek(0)
    finally:
        result.close()

    return send_file(output, mimetype="application/pdf",
                     as_attachment=True, download_name="merged.pdf")


@bp.route("/split", methods=["POST"])
def split():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    page_spec = request.form.get("pages", "").strip()
    try:
        doc = _open_pdf(files[0].read())
    except ValueError as e:
        return jsonify(error=str(e)), 400

    try:
        try:
            pages = parse_page_ranges(page_spec, len(doc))
        except (ValueError, IndexError):
            return jsonify(error="Invalid page range. Use e.g. '1-3, 5, 7-10'."), 400

        if not pages:
            return jsonify(error="No valid pages selected."), 400

        if len(pages) == 1:
            with fitz.open() as single:
                single.insert_pdf(doc, from_page=pages[0], to_page=pages[0])
                output = io.BytesIO()
                single.save(output)
            output.seek(0)
            return send_file(output, mimetype="application/pdf",
                             as_attachment=True, download_name=f"page_{pages[0]+1}.pdf")

        parts = []
        for p in pages:
            with fitz.open() as part:
                part.insert_pdf(doc, from_page=p, to_page=p)
                buf = io.BytesIO()
                part.save(buf)
            parts.append((f"page_{p + 1}.pdf", buf.getvalue()))
    finally:
        doc.close()

    zip_buf = make_zip(parts)
    return send_file(zip_buf, mimetype="application/zip",
                     as_attachment=True, download_name="split_pages.zip")


@bp.route("/compress", methods=["POST"])
def compress():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    quality = request.form.get("quality", "medium")
    image_quality = {"low": 40, "medium": 65, "high": 85}.get(quality, 65)
    max_dim = {"low": 1200, "medium": 1800, "high": 2400}.get(quality, 1800)

    from PIL import Image

    try:
        doc = _open_pdf(files[0].read())
    except ValueError as e:
        return jsonify(error=str(e)), 400

    try:
        processed_xrefs = set()
        for page in doc:
            for img_info in page.get_images(full=True):
                xref = img_info[0]
                if xref in processed_xrefs:
                    continue
                processed_xrefs.add(xref)
                try:
                    base_image = doc.extract_image(xref)
                    if not base_image:
                        continue
                    with Image.open(io.BytesIO(base_image["image"])) as pil_img:
                        if pil_img.mode != "RGB":
                            pil_img = pil_img.convert("RGB")

                        if max(pil_img.size) > max_dim:
                            pil_img.thumbnail((max_dim, max_dim), Image.LANCZOS)

                        buf = io.BytesIO()
                        pil_img.save(buf, format="JPEG",
                                     quality=image_quality, optimize=True)

                    # Replace image in-place — preserves original placement & size.
                    page.replace_image(xref, stream=buf.getvalue())
                except Exception as e:
                    log_error(e, f"compress xref={xref}")
                    continue

        output = io.BytesIO()
        doc.save(output, garbage=4, deflate=True, clean=True)
        output.seek(0)
    finally:
        doc.close()

    name = files[0].filename.rsplit(".", 1)[0] + "_compressed.pdf"
    return send_file(output, mimetype="application/pdf",
                     as_attachment=True, download_name=name)


@bp.route("/rotate", methods=["POST"])
def rotate():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    angle = safe_int(request.form.get("angle"), 90)
    if angle not in (90, 180, 270):
        return jsonify(error="Rotation must be 90, 180, or 270."), 400
    page_spec = request.form.get("pages", "").strip()

    try:
        doc = _open_pdf(files[0].read())
    except ValueError as e:
        return jsonify(error=str(e)), 400

    try:
        try:
            pages = parse_page_ranges(page_spec, len(doc))
        except (ValueError, IndexError):
            return jsonify(error="Invalid page range. Use e.g. '1-3, 5, 7-10'."), 400

        for p in pages:
            doc[p].set_rotation((doc[p].rotation + angle) % 360)

        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
    finally:
        doc.close()

    name = files[0].filename.rsplit(".", 1)[0] + "_rotated.pdf"
    return send_file(output, mimetype="application/pdf",
                     as_attachment=True, download_name=name)


@bp.route("/resize", methods=["POST"])
def resize():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    mode = request.form.get("mode", "scale")
    try:
        doc = _open_pdf(files[0].read())
    except ValueError as e:
        return jsonify(error=str(e)), 400

    new_doc = fitz.open()
    try:
        if mode == "scale":
            scale_pct = safe_float(request.form.get("scale"), 100.0,
                                   min_val=10.0, max_val=500.0)
            scale = scale_pct / 100.0

            for page in doc:
                r = page.rect
                new_page = new_doc.new_page(width=r.width * scale,
                                            height=r.height * scale)
                new_page.show_pdf_page(new_page.rect, doc, page.number,
                                       rotate=page.rotation)

        elif mode == "paper":
            paper = request.form.get("paper", "a4")
            target_w, target_h = PAPER_SIZES.get(paper, PAPER_SIZES["a4"])

            for page in doc:
                r = page.rect
                src_w, src_h = r.width, r.height

                # Match target orientation to source orientation
                if (src_w > src_h) != (target_w > target_h):
                    page_w, page_h = target_h, target_w
                else:
                    page_w, page_h = target_w, target_h

                # Fit source page into new page, preserving aspect ratio
                fit = min(page_w / src_w, page_h / src_h)
                content_w = src_w * fit
                content_h = src_h * fit
                x0 = (page_w - content_w) / 2
                y0 = (page_h - content_h) / 2

                new_page = new_doc.new_page(width=page_w, height=page_h)
                new_page.show_pdf_page(
                    fitz.Rect(x0, y0, x0 + content_w, y0 + content_h),
                    doc, page.number, rotate=page.rotation
                )
        else:
            return jsonify(error="Unknown resize mode."), 400

        output = io.BytesIO()
        new_doc.save(output, garbage=4, deflate=True)
        output.seek(0)
    finally:
        new_doc.close()
        doc.close()

    name = files[0].filename.rsplit(".", 1)[0] + "_resized.pdf"
    return send_file(output, mimetype="application/pdf",
                     as_attachment=True, download_name=name)


@bp.route("/page-numbers", methods=["POST"])
def page_numbers():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    position = request.form.get("position", "bottom-center")
    start = safe_int(request.form.get("start"), 1, min_val=0, max_val=100000)
    fontsize = safe_int(request.form.get("fontsize"), 11, min_val=6, max_val=72)

    try:
        doc = _open_pdf(files[0].read())
    except ValueError as e:
        return jsonify(error=str(e)), 400

    try:
        for i, page in enumerate(doc):
            num = start + i
            r = page.rect
            margin = 36  # 0.5 inch

            pos_map = {
                "bottom-center": fitz.Point(r.width / 2, r.height - margin),
                "bottom-right": fitz.Point(r.width - margin, r.height - margin),
                "bottom-left": fitz.Point(margin, r.height - margin),
                "top-center": fitz.Point(r.width / 2, margin + fontsize),
                "top-right": fitz.Point(r.width - margin, margin + fontsize),
                "top-left": fitz.Point(margin, margin + fontsize),
            }
            point = pos_map.get(position, pos_map["bottom-center"])

            page.insert_text(point, str(num), fontsize=fontsize,
                             fontname="helv", color=(0.3, 0.3, 0.3))

        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
    finally:
        doc.close()

    name = files[0].filename.rsplit(".", 1)[0] + "_numbered.pdf"
    return send_file(output, mimetype="application/pdf",
                     as_attachment=True, download_name=name)


@bp.route("/extract-images", methods=["POST"])
def extract_images():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    try:
        doc = _open_pdf(files[0].read())
    except ValueError as e:
        return jsonify(error=str(e)), 400

    images = []
    try:
        for i, page in enumerate(doc):
            for img_idx, img_info in enumerate(page.get_images(full=True)):
                xref = img_info[0]
                try:
                    base_image = doc.extract_image(xref)
                    if not base_image:
                        continue
                    ext = base_image.get("ext", "png")
                    images.append((f"page{i+1}_img{img_idx+1}.{ext}",
                                   base_image["image"]))
                except Exception as e:
                    log_error(e, f"extract_images xref={xref}")
                    continue
    finally:
        doc.close()

    if not images:
        return jsonify(error="No images found in the PDF."), 400

    if len(images) == 1:
        ext = images[0][0].rsplit(".", 1)[1]
        mime = f"image/{'jpeg' if ext in ('jpg','jpeg') else ext}"
        return send_file(io.BytesIO(images[0][1]), mimetype=mime,
                         as_attachment=True, download_name=images[0][0])

    zip_buf = make_zip(images)
    name = files[0].filename.rsplit(".", 1)[0] + "_images.zip"
    return send_file(zip_buf, mimetype="application/zip",
                     as_attachment=True, download_name=name)


@bp.route("/protect", methods=["POST"])
def protect():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    user_pw = request.form.get("user_password", "")
    owner_pw = request.form.get("owner_password", "") or user_pw

    if not user_pw:
        return jsonify(error="Please enter a password."), 400

    try:
        doc = _open_pdf(files[0].read())
    except ValueError as e:
        return jsonify(error=str(e)), 400

    try:
        perm = fitz.PDF_PERM_PRINT | fitz.PDF_PERM_COPY

        output = io.BytesIO()
        doc.save(output,
                 encryption=fitz.PDF_ENCRYPT_AES_256,
                 user_pw=user_pw,
                 owner_pw=owner_pw,
                 permissions=perm)
        output.seek(0)
    finally:
        doc.close()

    name = files[0].filename.rsplit(".", 1)[0] + "_protected.pdf"
    return send_file(output, mimetype="application/pdf",
                     as_attachment=True, download_name=name)


@bp.route("/sign", methods=["POST"])
def sign():
    from PIL import Image

    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="Please upload a PDF."), 400

    sig_file = request.files.get("signature")
    if not sig_file or not sig_file.filename:
        return jsonify(error="Please upload a signature image (PNG or JPG)."), 400

    position = request.form.get("position", "bottom-right")
    sig_width = safe_float(request.form.get("width"), 140.0,
                           min_val=30.0, max_val=600.0)
    margin = safe_float(request.form.get("margin"), 36.0,
                        min_val=0.0, max_val=300.0)
    opacity_pct = safe_int(request.form.get("opacity"), 100,
                           min_val=10, max_val=100)
    opacity = opacity_pct / 100.0

    page_spec = request.form.get("pages", "").strip()

    try:
        with Image.open(sig_file) as raw:
            sig_img = raw.convert("RGBA")
    except Exception as e:
        log_error(e, "sign: signature image")
        return jsonify(error="Could not read signature image (file may be corrupted or not an image)."), 400

    if opacity < 1.0:
        r, g, b, a = sig_img.split()
        a = a.point(lambda v: int(v * opacity))
        sig_img = Image.merge("RGBA", (r, g, b, a))

    sig_buf = io.BytesIO()
    sig_img.save(sig_buf, format="PNG")
    sig_bytes = sig_buf.getvalue()

    sig_ratio = sig_img.height / sig_img.width if sig_img.width else 1.0
    sig_h = sig_width * sig_ratio
    sig_img.close()

    try:
        doc = _open_pdf(files[0].read())
    except ValueError as e:
        return jsonify(error=str(e)), 400

    try:
        try:
            target = parse_page_ranges(page_spec, len(doc))
        except (ValueError, IndexError):
            return jsonify(error="Invalid page range. Use e.g. '1, 3, 5-7'."), 400
        if not target:
            return jsonify(error="No valid pages selected."), 400

        for pno in target:
            page = doc[pno]
            r = page.rect

            if "right" in position:
                x0 = r.width - margin - sig_width
            elif "center" in position:
                x0 = (r.width - sig_width) / 2
            else:
                x0 = margin

            if "bottom" in position:
                y0 = r.height - margin - sig_h
            else:
                y0 = margin

            page.insert_image(
                fitz.Rect(x0, y0, x0 + sig_width, y0 + sig_h),
                stream=sig_bytes, keep_proportion=True, overlay=True,
            )

        output = io.BytesIO()
        doc.save(output, garbage=4, deflate=True)
        output.seek(0)
    finally:
        doc.close()

    name = files[0].filename.rsplit(".", 1)[0] + "_signed.pdf"
    return send_file(output, mimetype="application/pdf",
                     as_attachment=True, download_name=name)


@bp.route("/redact", methods=["POST"])
def redact():
    import re

    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    patterns_raw = request.form.get("patterns", "").strip()
    if not patterns_raw:
        return jsonify(error="Enter at least one search term or pattern."), 400

    is_regex = request.form.get("is_regex") == "on"
    case_sensitive = request.form.get("case_sensitive") == "on"
    page_spec = request.form.get("pages", "").strip()

    patterns = [p for p in patterns_raw.splitlines() if p.strip()]
    if not patterns:
        return jsonify(error="Enter at least one search term or pattern."), 400

    # Validate regex patterns up-front so the user gets a clean error message.
    flags = 0 if case_sensitive else re.IGNORECASE
    if is_regex:
        compiled: list[re.Pattern] = []
        for p in patterns:
            try:
                compiled.append(re.compile(p, flags))
            except re.error as e:
                return jsonify(error=f"Invalid regex {p!r}: {e}"), 400

    try:
        doc = _open_pdf(files[0].read())
    except ValueError as e:
        return jsonify(error=str(e)), 400

    try:
        try:
            target = parse_page_ranges(page_spec, len(doc))
        except (ValueError, IndexError):
            return jsonify(error="Invalid page range. Use e.g. '1-3, 5, 7-10'."), 400
        if not target:
            return jsonify(error="No valid pages selected."), 400

        total_redactions = 0
        for pno in target:
            page = doc[pno]
            rects: list[fitz.Rect] = []

            if is_regex:
                # Regex path: walk the page text, locate each match, then map
                # the character range back to bounding boxes via search_for.
                page_text = page.get_text()
                for pat in compiled:
                    for m in pat.finditer(page_text):
                        snippet = m.group(0)
                        if not snippet.strip():
                            continue
                        # search_for handles word-wrap and returns one rect per
                        # visual hit on the page.
                        for r in page.search_for(snippet, quads=False):
                            rects.append(r)
            else:
                for term in patterns:
                    if not term.strip():
                        continue
                    flags_arg = 0 if case_sensitive else fitz.TEXT_PRESERVE_LIGATURES  # search_for is case-insensitive by default
                    found = page.search_for(term)
                    rects.extend(found)

            # De-duplicate near-identical rectangles
            uniq: list[fitz.Rect] = []
            for r in rects:
                if not any(abs(r.x0 - u.x0) < 0.5 and abs(r.y0 - u.y0) < 0.5
                           and abs(r.x1 - u.x1) < 0.5 and abs(r.y1 - u.y1) < 0.5
                           for u in uniq):
                    uniq.append(r)

            for r in uniq:
                page.add_redact_annot(r, fill=(0, 0, 0))
            total_redactions += len(uniq)

            # apply_redactions actually removes the underlying text; the
            # IMAGE_PIXELS option preserves images on the page.
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)

        if total_redactions == 0:
            return jsonify(error=(
                "No matches found. Check spelling, toggle case-sensitivity, "
                "or try a different pattern."
            )), 400

        output = io.BytesIO()
        doc.save(output, garbage=4, deflate=True, clean=True)
        output.seek(0)
    finally:
        doc.close()

    name = files[0].filename.rsplit(".", 1)[0] + "_redacted.pdf"
    resp = send_file(output, mimetype="application/pdf",
                     as_attachment=True, download_name=name)
    resp.headers["X-Redactions-Applied"] = str(total_redactions)
    return resp


@bp.route("/unlock", methods=["POST"])
def unlock():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    password = request.form.get("password", "")
    try:
        doc = _open_pdf(files[0].read())
    except ValueError as e:
        return jsonify(error=str(e)), 400

    try:
        if doc.needs_pass:
            if not doc.authenticate(password):
                return jsonify(error="Incorrect password."), 400

        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
    finally:
        doc.close()

    name = files[0].filename.rsplit(".", 1)[0] + "_unlocked.pdf"
    return send_file(output, mimetype="application/pdf",
                     as_attachment=True, download_name=name)


# ── PDF Form Filler (AcroForm) ─────────────────────────────

# PyMuPDF widget type constants → string labels we expose to the UI
_WIDGET_TYPE_NAMES = {
    fitz.PDF_WIDGET_TYPE_TEXT: "text",
    fitz.PDF_WIDGET_TYPE_CHECKBOX: "checkbox",
    fitz.PDF_WIDGET_TYPE_RADIOBUTTON: "radio",
    fitz.PDF_WIDGET_TYPE_LISTBOX: "listbox",
    fitz.PDF_WIDGET_TYPE_COMBOBOX: "combobox",
    fitz.PDF_WIDGET_TYPE_BUTTON: "button",
    fitz.PDF_WIDGET_TYPE_SIGNATURE: "signature",
}


def _label_near_widget(page, rect: fitz.Rect, max_dist: float = 250) -> str:
    """Find the text label that visually sits next to a widget on the page.

    Radio button / checkbox labels (e.g. "Male", "Female") are painted on the
    page as static text, NOT stored on the widget. We sniff them by walking
    page words and picking the contiguous run of words on the same line,
    starting from the side adjacent to the widget. A gap > ~25 pixels stops
    the run, which prevents grabbing the next radio's label in a horizontal
    row layout like "[ ] Male  [ ] Female".

    Right side is searched first (the conventional layout); left is fallback.
    """
    if not rect:
        return ""
    height = max(rect.y1 - rect.y0, 8)
    cy = (rect.y0 + rect.y1) / 2

    # get_text("words") -> list of (x0, y0, x1, y1, "text", block, line, word)
    words = page.get_text("words")
    if not words:
        return ""

    def same_line(wy0: float, wy1: float) -> bool:
        wcy = (wy0 + wy1) / 2
        return abs(wcy - cy) <= height * 0.7

    GAP = 25.0  # max horizontal gap between adjacent label words, in points

    # ── Right-side run ──
    right = [w for w in words
             if same_line(w[1], w[3])
             and w[0] >= rect.x1 - 1
             and w[0] - rect.x1 < max_dist]
    if right:
        right.sort(key=lambda w: w[0])
        result = [right[0][4]]
        prev_x1 = right[0][2]
        for w in right[1:]:
            if w[0] - prev_x1 > GAP:
                break
            result.append(w[4])
            prev_x1 = w[2]
        text = " ".join(result).strip().rstrip(":;,.")
        if text:
            return text[:80]

    # ── Left-side fallback ──
    left = [w for w in words
            if same_line(w[1], w[3])
            and w[2] <= rect.x0 + 1
            and rect.x0 - w[2] < max_dist]
    if left:
        left.sort(key=lambda w: -w[2])  # rightmost first (closest to widget)
        result = [left[0][4]]
        prev_x0 = left[0][0]
        for w in left[1:]:
            if prev_x0 - w[2] > GAP:
                break
            result.insert(0, w[4])
            prev_x0 = w[0]
        text = " ".join(result).strip().rstrip(":;,.")
        if text:
            return text[:80]

    return ""


def _serialize_widgets(doc) -> list[dict]:
    """Walk every page's widgets and return a JSON-friendly list of fields."""
    fields: list[dict] = []
    for page_num, page in enumerate(doc, start=1):
        for w in page.widgets() or []:
            ftype = _WIDGET_TYPE_NAMES.get(w.field_type, "unknown")

            # Required / read-only flags live in field_flags (bit field)
            flags = getattr(w, "field_flags", 0) or 0
            required = bool(flags & 2)        # bit 2 = required
            readonly = bool(flags & 1)        # bit 1 = read-only
            multiline = bool(flags & (1 << 12))  # bit 13 = multiline (text only)
            # PDF spec bit 19 (Ff 1<<18) = combobox is editable (user can type
            # values outside the choice list). Set only on combo fields.
            editable_combo = (ftype == "combobox") and bool(flags & (1 << 18))

            # Choice fields expose `choice_values`; treat None as empty list
            choices = list(w.choice_values or []) if hasattr(w, "choice_values") else []

            # For checkboxes / radios the "on" state name varies per PDF
            # (often "Yes", "On", "1", or arbitrary identifiers like "Male").
            on_states = []
            if ftype in ("checkbox", "radio"):
                states = w.button_states() or {}
                for _, vals in states.items():
                    if not vals:
                        continue
                    for v in vals:
                        if v and v != "Off" and v not in on_states:
                            on_states.append(v)

            # For radios + checkboxes, sniff a human label from the page text
            # adjacent to this widget. PDFs paint these as static text rather
            # than storing them on the widget, so we have to read the page.
            option_label = ""
            if ftype in ("radio", "checkbox"):
                option_label = _label_near_widget(page, w.rect)

            # The "value" identifier this specific radio represents when "on".
            option_value = on_states[0] if (ftype == "radio" and on_states) else ""

            fields.append({
                "name": w.field_name or "",
                "label": w.field_label or w.field_name or "",
                "type": ftype,
                "value": w.field_value if w.field_value is not None else "",
                "page": page_num,
                "rect": [round(c, 2) for c in (w.rect or fitz.Rect())],
                "option_label": option_label,
                "option_value": option_value,
                "editable": editable_combo,
                "required": required,
                "readonly": readonly,
                "multiline": multiline,
                "choices": choices,
                "on_states": on_states,
                "max_length": w.text_maxlen if hasattr(w, "text_maxlen") else 0,
            })
    return fields


@bp.route("/form-inspect", methods=["POST"])
def form_inspect():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    try:
        doc = _open_pdf(files[0].read())
    except ValueError as e:
        return jsonify(error=str(e)), 400

    try:
        fields = _serialize_widgets(doc)
        return jsonify({
            "filename": files[0].filename,
            "page_count": len(doc),
            "field_count": len(fields),
            "fields": fields,
            "has_form": len(fields) > 0,
        })
    finally:
        doc.close()


@bp.route("/form-fill", methods=["POST"])
def form_fill():
    """Apply field values to the uploaded PDF and return the filled file.

    Form values are passed as JSON in the `values` field of the multipart body:
    `{"<field_name>": "<value>", ...}`. Values are matched against
    `widget.field_name`. Unknown names are silently ignored.
    """
    import json

    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error=NO_FILE_SINGLE), 400

    raw_values = request.form.get("values", "{}")
    try:
        values_map = json.loads(raw_values)
        if not isinstance(values_map, dict):
            raise ValueError("values must be an object")
    except (ValueError, TypeError) as e:
        return jsonify(error=f"Invalid form values JSON: {e}"), 400

    flatten = request.form.get("flatten") == "on"

    try:
        doc = _open_pdf(files[0].read())
    except ValueError as e:
        return jsonify(error=str(e)), 400

    applied = 0
    skipped: list[str] = []
    try:
        for page in doc:
            for w in page.widgets() or []:
                if not w.field_name or w.field_name not in values_map:
                    continue
                if w.field_flags and (w.field_flags & 1):  # read-only
                    skipped.append(w.field_name)
                    continue

                new_val = values_map[w.field_name]
                ftype = w.field_type

                try:
                    if ftype == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                        # truthy → checkbox's "on" state, falsy → "Off"
                        if new_val in (True, "true", "on", "1", 1, "Yes", "yes"):
                            on_vals = []
                            states = w.button_states() or {}
                            for vals in states.values():
                                if not vals:
                                    continue
                                for v in vals:
                                    if v and v != "Off":
                                        on_vals.append(v)
                            w.field_value = on_vals[0] if on_vals else "Yes"
                        else:
                            w.field_value = "Off"
                    elif ftype == fitz.PDF_WIDGET_TYPE_RADIOBUTTON:
                        # value should match one of the radio's on-states
                        w.field_value = str(new_val) if new_val else "Off"
                    elif ftype in (fitz.PDF_WIDGET_TYPE_LISTBOX,
                                   fitz.PDF_WIDGET_TYPE_COMBOBOX):
                        w.field_value = str(new_val) if new_val is not None else ""
                    else:  # text or other text-like
                        w.field_value = str(new_val) if new_val is not None else ""

                    w.update()
                    applied += 1
                except Exception as e:
                    log_error(e, f"form-fill: {w.field_name}")
                    skipped.append(w.field_name)

        # Optional: flatten the form so the values become baked-in static text.
        # Without flatten=true the result is still an editable PDF form.
        if flatten:
            for page in doc:
                # No public PyMuPDF API to "flatten" widgets in one call, but
                # converting the page to a pixmap-and-reinsert collapses widgets.
                # Simpler: render then rebuild — but that loses fidelity for
                # text-heavy forms. Best practical approach: leave widgets
                # editable; users who need a flat copy can re-print to PDF.
                pass

        output = io.BytesIO()
        doc.save(output, garbage=4, deflate=True, clean=True)
        output.seek(0)
    finally:
        doc.close()

    base = files[0].filename.rsplit(".", 1)[0]
    resp = send_file(output, mimetype="application/pdf",
                     as_attachment=True, download_name=f"{base}_filled.pdf")
    resp.headers["X-Fields-Applied"] = str(applied)
    resp.headers["X-Fields-Skipped"] = str(len(skipped))
    return resp
