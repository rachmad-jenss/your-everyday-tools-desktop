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
