import io
import fitz  # PyMuPDF
from flask import Blueprint, render_template, request, send_file, jsonify
from PIL import Image
import img2pdf
from docx import Document as DocxDocument
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

try:
    from pdf2docx import Converter as Pdf2DocxConverter
    HAS_PDF2DOCX = True
except ImportError:
    HAS_PDF2DOCX = False

try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

try:
    import ezdxf
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False

import shutil
ODA_CONVERTER = shutil.which("ODAFileConverter") or shutil.which("oda_file_converter")

bp = Blueprint("convert", __name__)


# ── Page Routes ──────────────────────────────────

@bp.route("/to-pdf")
def to_pdf_page():
    return render_template("upload_tool.html",
        title="Files to PDF",
        description="Convert images, Word documents, and text files to PDF",
        endpoint="/convert/to-pdf",
        accept=".jpg,.jpeg,.png,.bmp,.tiff,.webp,.txt,.docx",
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


OCR_LANGS = [
    {"value": "eng", "label": "English"},
    {"value": "ind", "label": "Indonesian"},
    {"value": "fra", "label": "French"},
    {"value": "deu", "label": "German"},
    {"value": "spa", "label": "Spanish"},
    {"value": "ita", "label": "Italian"},
    {"value": "por", "label": "Portuguese"},
    {"value": "rus", "label": "Russian"},
    {"value": "chi_sim", "label": "Chinese (Simplified)"},
    {"value": "chi_tra", "label": "Chinese (Traditional)"},
    {"value": "jpn", "label": "Japanese"},
    {"value": "kor", "label": "Korean"},
    {"value": "ara", "label": "Arabic"},
    {"value": "hin", "label": "Hindi"},
]


@bp.route("/ocr-pdf")
def ocr_pdf_page():
    return render_template("upload_tool.html",
        title="OCR PDF",
        description="Extract text from scanned PDFs or create a searchable PDF with a hidden text layer",
        endpoint="/convert/ocr-pdf",
        accept=".pdf",
        multiple=False,
        options=[
            {"type": "select", "name": "mode", "label": "Output",
             "choices": [
                 {"value": "searchable", "label": "Searchable PDF (image + text layer)"},
                 {"value": "text", "label": "Extracted text only"},
             ]},
            {"type": "select", "name": "lang", "label": "Language",
             "choices": OCR_LANGS},
            {"type": "number", "name": "dpi", "label": "OCR Resolution (DPI)",
             "default": 200, "min": 100, "max": 400},
        ])


@bp.route("/cad-to-pdf")
def cad_to_pdf_page():
    if ODA_CONVERTER:
        notes = (
            '<p><i class="bi bi-check-circle-fill" style="color:#2ec4b6"></i> '
            '<strong>DWG support is enabled.</strong> ODA File Converter was detected at '
            f'<code>{ODA_CONVERTER}</code>.</p>'
            '<p>DXF files are rendered directly. DWG files are auto-converted to DXF first.</p>'
        )
    else:
        notes = (
            '<p><strong>DXF works out of the box.</strong> DWG files need the free '
            '<a href="https://www.opendesign.com/guestfiles/oda_file_converter" target="_blank" rel="noopener">'
            'ODA File Converter</a> installed and available on your system <code>PATH</code>.</p>'
            '<details>'
            '<summary>How to install ODA File Converter</summary>'
            '<ol>'
            '<li>Download the installer for your OS from '
            '<a href="https://www.opendesign.com/guestfiles/oda_file_converter" target="_blank" rel="noopener">opendesign.com</a> '
            '(free, guest download — no account required).</li>'
            '<li>Run the installer. Defaults are fine.</li>'
            '<li><strong>Add it to your PATH so this app can find it:</strong>'
            '<ul>'
            '<li><strong>Windows:</strong> add <code>C:\\Program Files\\ODA\\ODAFileConverter_title_version</code> '
            '(the folder containing <code>ODAFileConverter.exe</code>) to your <em>System Environment Variables</em> &rarr; <code>Path</code>.</li>'
            '<li><strong>macOS:</strong> <code>ln -s /Applications/ODAFileConverter.app/Contents/MacOS/ODAFileConverter /usr/local/bin/ODAFileConverter</code></li>'
            '<li><strong>Linux:</strong> the <code>.deb</code>/<code>.rpm</code> package installs <code>ODAFileConverter</code> on PATH automatically. Otherwise symlink the binary into <code>/usr/local/bin</code>.</li>'
            '</ul></li>'
            '<li>Open a new terminal and verify: <code>ODAFileConverter</code> (should launch the tool GUI, or exit silently).</li>'
            '<li><strong>Restart this Flask server</strong> so it picks up the updated PATH.</li>'
            '</ol>'
            '<p style="margin-top:.4rem">Alternative: open your DWG in free tools like <a href="https://www.autodesk.com/viewers" target="_blank" rel="noopener">Autodesk Viewer</a>, LibreCAD, or QCAD and export it as DXF, then upload the DXF here.</p>'
            '</details>'
        )

    return render_template("upload_tool.html",
        title="CAD to PDF/Image",
        description="Convert DXF drawings to PDF or PNG. DWG is supported when ODA File Converter is installed.",
        notes=notes,
        endpoint="/convert/cad-to-pdf",
        accept=".dxf,.dwg",
        multiple=False,
        options=[
            {"type": "select", "name": "format", "label": "Output Format",
             "choices": [
                 {"value": "pdf", "label": "PDF"},
                 {"value": "png", "label": "PNG"},
             ]},
            {"type": "number", "name": "dpi", "label": "PNG Resolution (DPI)",
             "default": 150, "min": 72, "max": 600,
             "depends_on": {"format": "png"}},
        ])


@bp.route("/html-to-pdf")
def html_to_pdf_page():
    return render_template("upload_tool.html",
        title="HTML to PDF",
        description="Convert HTML content to a PDF document",
        endpoint="/convert/html-to-pdf",
        text_input=True,
        text_label="HTML Content",
        text_placeholder="<h1>Hello World</h1>\n<p>Paste your HTML here...</p>",
        accept="",
        multiple=False,
        options=[],
        button_text="Convert to PDF")


# ── Helpers ──────────────────────────────────────

def _docx_to_pdf(data: bytes) -> bytes:
    """Convert a .docx file (as bytes) to PDF bytes using python-docx + reportlab."""
    doc = DocxDocument(io.BytesIO(data))
    buf = io.BytesIO()

    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    normal.fontName = "Helvetica"
    normal.fontSize = 11
    normal.leading = 14

    heading_styles = {}
    for level in range(1, 4):
        size = {1: 18, 2: 15, 3: 13}[level]
        heading_styles[level] = ParagraphStyle(
            f"Heading{level}", parent=normal,
            fontName="Helvetica-Bold", fontSize=size, leading=size + 4,
            spaceBefore=12, spaceAfter=6,
        )

    pdf = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=inch, rightMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    story = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            story.append(Spacer(1, 6))
            continue

        style_name = para.style.name.lower() if para.style else ""

        if "heading 1" in style_name:
            story.append(Paragraph(text, heading_styles[1]))
        elif "heading 2" in style_name:
            story.append(Paragraph(text, heading_styles[2]))
        elif "heading 3" in style_name:
            story.append(Paragraph(text, heading_styles[3]))
        else:
            # Preserve basic inline formatting
            rich = _build_rich_text(para)
            story.append(Paragraph(rich, normal))

    # Handle tables
    for table in doc.tables:
        tdata = []
        for row in table.rows:
            tdata.append([cell.text for cell in row.cells])
        if tdata:
            t = Table(tdata, repeatRows=1)
            t.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.9, 0.9, 0.95)),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(Spacer(1, 8))
            story.append(t)
            story.append(Spacer(1, 8))

    if not story:
        story.append(Paragraph("(empty document)", normal))

    pdf.build(story)
    return buf.getvalue()


def _build_rich_text(para) -> str:
    """Convert a python-docx paragraph's runs into reportlab-compatible rich text."""
    parts = []
    for run in para.runs:
        text = run.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if not text:
            continue
        if run.bold and run.italic:
            parts.append(f"<b><i>{text}</i></b>")
        elif run.bold:
            parts.append(f"<b>{text}</b>")
        elif run.italic:
            parts.append(f"<i>{text}</i>")
        elif run.underline:
            parts.append(f"<u>{text}</u>")
        else:
            parts.append(text)
    return "".join(parts) or para.text


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

        if name.endswith(".docx"):
            # Word document → PDF pages
            try:
                docx_pdf_bytes = _docx_to_pdf(data)
                docx_pdf = fitz.open(stream=docx_pdf_bytes, filetype="pdf")
                pdf_doc.insert_pdf(docx_pdf)
                docx_pdf.close()
            except Exception as e:
                return jsonify(error=f"Error converting {f.filename}: {str(e)}"), 400
        elif name.endswith(".txt"):
            # Text file → PDF page
            text = data.decode("utf-8", errors="replace")
            page = pdf_doc.new_page(width=595, height=842)  # A4
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


@bp.route("/html-to-pdf", methods=["POST"])
def html_to_pdf():
    html = request.form.get("text", "").strip()
    if not html:
        return jsonify(error="Please enter some HTML content."), 400

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4

    # Wrap in basic structure if no <html> tag present
    if "<html" not in html.lower():
        html = f"<html><body>{html}</body></html>"

    try:
        page.insert_htmlbox(fitz.Rect(50, 50, 545, 792), html)
    except Exception as e:
        return jsonify(error=f"HTML rendering failed: {str(e)}"), 400

    output = io.BytesIO()
    doc.save(output)
    doc.close()
    output.seek(0)

    return send_file(output, mimetype="application/pdf",
                     as_attachment=True, download_name="converted.pdf")


@bp.route("/ocr-pdf", methods=["POST"])
def ocr_pdf():
    if not HAS_TESSERACT:
        return jsonify(error="OCR requires 'pytesseract' and the Tesseract binary. Install: pip install pytesseract, plus Tesseract from https://github.com/tesseract-ocr/tesseract"), 400

    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="No file uploaded."), 400

    mode = request.form.get("mode", "searchable")
    lang = request.form.get("lang", "eng")
    dpi = int(request.form.get("dpi", 200))

    pdf_data = files[0].read()
    src = fitz.open(stream=pdf_data, filetype="pdf")
    zoom = dpi / 72

    try:
        if mode == "text":
            text_parts = []
            for i, page in enumerate(src):
                pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(img, lang=lang)
                text_parts.append(f"--- Page {i + 1} ---\n{text.strip()}")
            src.close()
            combined = "\n\n".join(text_parts).strip()
            return jsonify(text=combined or "(No text detected)")

        output = fitz.open()
        for page in src:
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            page_pdf_bytes = pytesseract.image_to_pdf_or_hocr(img, extension="pdf", lang=lang)
            sub = fitz.open(stream=page_pdf_bytes, filetype="pdf")
            output.insert_pdf(sub)
            sub.close()
        src.close()

        buf = io.BytesIO()
        output.save(buf)
        output.close()
        buf.seek(0)

        name = files[0].filename.rsplit(".", 1)[0] + "_ocr.pdf"
        return send_file(buf, mimetype="application/pdf",
                         as_attachment=True, download_name=name)
    except pytesseract.TesseractNotFoundError:
        return jsonify(error="Tesseract binary not found. Install from https://github.com/tesseract-ocr/tesseract and ensure it is on PATH."), 400
    except Exception as e:
        msg = str(e)
        if "language" in msg.lower() or "traineddata" in msg.lower():
            return jsonify(error=f"Language pack '{lang}' not installed. Download its .traineddata file into your Tesseract tessdata directory."), 400
        return jsonify(error=f"OCR failed: {msg}"), 400


@bp.route("/cad-to-pdf", methods=["POST"])
def cad_to_pdf():
    if not HAS_EZDXF:
        return jsonify(error="CAD conversion requires 'ezdxf' and 'matplotlib'. Install: pip install ezdxf matplotlib"), 400

    files = request.files.getlist("files")
    if not files or not files[0].filename:
        return jsonify(error="No file uploaded."), 400

    target = request.form.get("format", "pdf")
    dpi = int(request.form.get("dpi", 150))

    filename = files[0].filename
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    file_data = files[0].read()

    import tempfile, os, subprocess
    with tempfile.TemporaryDirectory() as tmpdir:
        if ext == "dwg":
            if not ODA_CONVERTER:
                return jsonify(error="DWG support requires ODA File Converter. Download it free from https://www.opendesign.com/guestfiles/oda_file_converter and ensure it is on your PATH. Or convert your DWG to DXF first."), 400

            in_dir = os.path.join(tmpdir, "in")
            out_dir = os.path.join(tmpdir, "out")
            os.makedirs(in_dir)
            os.makedirs(out_dir)
            dwg_path = os.path.join(in_dir, "input.dwg")
            with open(dwg_path, "wb") as f:
                f.write(file_data)

            try:
                subprocess.run(
                    [ODA_CONVERTER, in_dir, out_dir, "ACAD2018", "DXF", "0", "1", "*.DWG"],
                    check=True, capture_output=True, timeout=60,
                )
            except subprocess.CalledProcessError as e:
                return jsonify(error=f"DWG to DXF conversion failed: {e.stderr.decode(errors='replace')[:200]}"), 400
            except subprocess.TimeoutExpired:
                return jsonify(error="DWG conversion timed out."), 400

            dxf_path = os.path.join(out_dir, "input.dxf")
            if not os.path.exists(dxf_path):
                return jsonify(error="DWG to DXF conversion produced no output."), 400
            doc = ezdxf.readfile(dxf_path)
        elif ext == "dxf":
            dxf_path = os.path.join(tmpdir, "input.dxf")
            with open(dxf_path, "wb") as f:
                f.write(file_data)
            try:
                doc = ezdxf.readfile(dxf_path)
            except Exception as e:
                return jsonify(error=f"Invalid DXF file: {str(e)[:200]}"), 400
        else:
            return jsonify(error="Upload a .dxf or .dwg file."), 400

        msp = doc.modelspace()
        fig = plt.figure()
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_aspect("equal")
        ax.set_axis_off()

        try:
            ctx = RenderContext(doc)
            backend = MatplotlibBackend(ax)
            Frontend(ctx, backend).draw_layout(msp, finalize=True)
        except Exception as e:
            plt.close(fig)
            return jsonify(error=f"Rendering failed: {str(e)[:200]}"), 400

        buf = io.BytesIO()
        base_name = filename.rsplit(".", 1)[0]
        if target == "pdf":
            fig.savefig(buf, format="pdf", bbox_inches="tight", pad_inches=0.2)
            plt.close(fig)
            buf.seek(0)
            return send_file(buf, mimetype="application/pdf",
                             as_attachment=True, download_name=base_name + ".pdf")
        else:
            fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", pad_inches=0.2)
            plt.close(fig)
            buf.seek(0)
            return send_file(buf, mimetype="image/png",
                             as_attachment=True, download_name=base_name + ".png")
