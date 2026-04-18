import io
import fitz  # PyMuPDF
from flask import Blueprint, render_template, request, send_file, jsonify
from PIL import Image
import img2pdf

try:
    from pdf2docx import Converter as Pdf2DocxConverter
    HAS_PDF2DOCX = True
except ImportError:
    HAS_PDF2DOCX = False

bp = Blueprint("convert", __name__)


# ── Page Routes ──────────────────────────────────

@bp.route("/to-pdf")
def to_pdf_page():
    return render_template("upload_tool.html",
        title="Files to PDF",
        description="Convert images and text files to PDF",
        endpoint="/convert/to-pdf",
        accept=".jpg,.jpeg,.png,.bmp,.tiff,.webp,.txt",
        multiple=True,
        options=[])


@bp.route("/pdf-to-word")
def pdf_to_word_page():
    return render_template("upload_tool.html",
        title="PDF to Word",
        description="Convert PDF documents to Word (.docx) format",
        endpoint="/convert/pdf-to-word",
        accept=".pdf",
        multiple=False,
        options=[])


@bp.route("/pdf-to-images")
def pdf_to_images_page():
    return render_template("upload_tool.html",
        title="PDF to Images",
        description="Convert each PDF page to an image",
        endpoint="/convert/pdf-to-images",
        accept=".pdf",
        multiple=False,
        options=[
            {"type": "select", "name": "format", "label": "Image Format",
             "choices": [
                 {"value": "png", "label": "PNG"},
                 {"value": "jpg", "label": "JPG"},
             ]},
            {"type": "number", "name": "dpi", "label": "Resolution (DPI)", "default": 200, "min": 72, "max": 600},
        ])


@bp.route("/pdf-to-text")
def pdf_to_text_page():
    return render_template("upload_tool.html",
        title="PDF to Text",
        description="Extract all text content from a PDF document",
        endpoint="/convert/pdf-to-text",
        accept=".pdf",
        multiple=False,
        options=[])


# ── Processing Routes ────────────────────────────

@bp.route("/to-pdf", methods=["POST"])
def to_pdf():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="No files uploaded."), 400

    pdf_doc = fitz.open()

    for f in files:
        name = f.filename.lower()
        data = f.read()

        if name.endswith(".txt"):
            # Text file → PDF page
            text = data.decode("utf-8", errors="replace")
            page = pdf_doc.new_page(width=595, height=842)  # A4
            tw = fitz.TextWriter(page.rect)
            font = fitz.Font("helv")
            # Insert text with wrapping
            where = fitz.Point(50, 50)
            rect = fitz.Rect(50, 50, 545, 792)
            page.insert_textbox(rect, text, fontsize=11, fontname="helv")
        else:
            # Image → PDF page
            try:
                img_data = data
                # Convert to format fitz can handle
                pil_img = Image.open(io.BytesIO(data))
                if pil_img.mode in ("RGBA", "P"):
                    pil_img = pil_img.convert("RGB")
                buf = io.BytesIO()
                pil_img.save(buf, format="JPEG", quality=95)
                img_data = buf.getvalue()

                img_doc = fitz.open(stream=img_data, filetype="jpeg")
                rect = img_doc[0].rect
                pdf_page = pdf_doc.new_page(width=rect.width, height=rect.height)
                pdf_page.insert_image(rect, stream=img_data)
                img_doc.close()
            except Exception as e:
                return jsonify(error=f"Error processing {f.filename}: {str(e)}"), 400

    output = io.BytesIO()
    pdf_doc.save(output)
    pdf_doc.close()
    output.seek(0)

    return send_file(output, mimetype="application/pdf",
                     as_attachment=True, download_name="converted.pdf")


@bp.route("/pdf-to-word", methods=["POST"])
def pdf_to_word():
    if not HAS_PDF2DOCX:
        return jsonify(error="pdf2docx package not installed. Run: pip install pdf2docx"), 400

    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="No file uploaded."), 400

    import tempfile, os
    pdf_data = files[0].read()

    with tempfile.TemporaryDirectory() as tmpdir:
        pdf_path = os.path.join(tmpdir, "input.pdf")
        docx_path = os.path.join(tmpdir, "output.docx")

        with open(pdf_path, "wb") as f:
            f.write(pdf_data)

        try:
            cv = Pdf2DocxConverter(pdf_path)
            cv.convert(docx_path)
            cv.close()
        except Exception as e:
            return jsonify(error=f"Conversion failed: {str(e)}"), 400

        with open(docx_path, "rb") as f:
            result = io.BytesIO(f.read())

    result.seek(0)
    name = files[0].filename.rsplit(".", 1)[0] + ".docx"
    return send_file(result, mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                     as_attachment=True, download_name=name)


@bp.route("/pdf-to-images", methods=["POST"])
def pdf_to_images():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="No file uploaded."), 400

    fmt = request.form.get("format", "png")
    dpi = int(request.form.get("dpi", 200))

    pdf_data = files[0].read()
    doc = fitz.open(stream=pdf_data, filetype="pdf")

    from utils.file_utils import make_zip
    images = []
    mat = fitz.Matrix(dpi / 72, dpi / 72)

    for i, page in enumerate(doc):
        pix = page.get_pixmap(matrix=mat)
        if fmt == "jpg":
            img_bytes = pix.tobytes("jpeg")
            ext = "jpg"
        else:
            img_bytes = pix.tobytes("png")
            ext = "png"
        images.append((f"page_{i + 1}.{ext}", img_bytes))

    doc.close()

    if len(images) == 1:
        mime = "image/png" if fmt == "png" else "image/jpeg"
        return send_file(io.BytesIO(images[0][1]), mimetype=mime,
                         as_attachment=True, download_name=images[0][0])

    zip_buf = make_zip(images)
    name = files[0].filename.rsplit(".", 1)[0] + "_images.zip"
    return send_file(zip_buf, mimetype="application/zip",
                     as_attachment=True, download_name=name)


@bp.route("/pdf-to-text", methods=["POST"])
def pdf_to_text():
    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="No file uploaded."), 400

    pdf_data = files[0].read()
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    text_parts = []

    for i, page in enumerate(doc):
        text_parts.append(f"--- Page {i + 1} ---")
        text_parts.append(page.get_text())

    doc.close()
    return jsonify(text="\n".join(text_parts))
