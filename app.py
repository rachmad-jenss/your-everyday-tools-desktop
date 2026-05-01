import os
from flask import Flask, render_template

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB max upload

TOOL_CATEGORIES = [
    {
        "id": "convert",
        "name": "Document Conversion",
        "icon": "bi-file-earmark-arrow-right-fill",
        "tools": [
            {"id": "to-pdf", "name": "Files to PDF", "desc": "Convert images and text files to PDF", "icon": "bi-file-pdf-fill"},
            {"id": "pdf-to-word", "name": "PDF to Word", "desc": "Convert PDF to Word document", "icon": "bi-file-word-fill"},
            {"id": "pdf-to-images", "name": "PDF to Images", "desc": "Convert PDF pages to images", "icon": "bi-file-image-fill"},
            {"id": "pdf-to-text", "name": "PDF to Text", "desc": "Extract text content from PDF", "icon": "bi-file-text-fill"},
            {"id": "pdf-to-excel", "name": "PDF to Excel", "desc": "Extract tables from PDF into an .xlsx", "icon": "bi-file-earmark-spreadsheet-fill"},
            {"id": "html-to-pdf", "name": "HTML to PDF", "desc": "Convert HTML content to PDF", "icon": "bi-filetype-html"},
            {"id": "md-to-pdf", "name": "Markdown to PDF", "desc": "Convert Markdown text or files to PDF", "icon": "bi-markdown-fill"},
            {"id": "md-to-docx", "name": "Markdown to Word", "desc": "Convert Markdown to a Word .docx document", "icon": "bi-file-word-fill"},
            {"id": "pdf-to-pptx", "name": "PDF to PowerPoint", "desc": "Each PDF page becomes a slide image", "icon": "bi-file-earmark-slides-fill"},
            {"id": "pptx-to-pdf", "name": "PowerPoint to PDF", "desc": "Convert .pptx / .ppt / .odp to PDF (needs LibreOffice)", "icon": "bi-file-earmark-pdf-fill"},
            {"id": "ocr-pdf", "name": "OCR PDF", "desc": "Make scanned PDFs searchable or extract text", "icon": "bi-file-earmark-text-fill"},
            {"id": "cad-to-pdf", "name": "CAD to PDF/Image", "desc": "Convert DXF/DWG drawings to PDF or PNG", "icon": "bi-rulers"},
        ],
    },
    {
        "id": "pdf",
        "name": "PDF Tools",
        "icon": "bi-file-pdf-fill",
        "tools": [
            {"id": "merge", "name": "Merge PDFs", "desc": "Combine multiple PDFs into one", "icon": "bi-union"},
            {"id": "split", "name": "Split PDF", "desc": "Split PDF into individual pages", "icon": "bi-scissors"},
            {"id": "compress", "name": "Compress PDF", "desc": "Reduce PDF file size", "icon": "bi-file-zip-fill"},
            {"id": "rotate", "name": "Rotate PDF", "desc": "Rotate PDF pages", "icon": "bi-arrow-clockwise"},
            {"id": "resize", "name": "Resize PDF", "desc": "Change PDF page dimensions", "icon": "bi-aspect-ratio-fill"},
            {"id": "page-numbers", "name": "Page Numbers", "desc": "Add page numbers to PDF", "icon": "bi-123"},
            {"id": "extract-images", "name": "Extract Images", "desc": "Extract images from PDF", "icon": "bi-images"},
            {"id": "protect", "name": "Protect PDF", "desc": "Add password protection to PDF", "icon": "bi-lock-fill"},
            {"id": "unlock", "name": "Unlock PDF", "desc": "Remove PDF password", "icon": "bi-unlock-fill"},
            {"id": "sign", "name": "Sign PDF", "desc": "Stamp a signature image onto PDF pages", "icon": "bi-pen-fill"},
            {"id": "redact", "name": "Redact PDF", "desc": "Permanently black-out sensitive text", "icon": "bi-eraser-fill"},
            {"id": "form-fill", "name": "Fill PDF Form", "desc": "Fill AcroForm fields and download a filled PDF", "icon": "bi-input-cursor-text"},
        ],
    },
    {
        "id": "spreadsheet",
        "name": "Spreadsheet",
        "icon": "bi-file-earmark-spreadsheet-fill",
        "tools": [
            {"id": "excel-to-csv", "name": "Excel to CSV/JSON", "desc": "Export sheets as CSV or JSON", "icon": "bi-table"},
            {"id": "csv-to-excel", "name": "CSV/JSON to Excel", "desc": "Build .xlsx from CSV or JSON files", "icon": "bi-file-earmark-spreadsheet"},
            {"id": "excel-to-pdf", "name": "Excel to PDF", "desc": "Convert workbook to PDF (one section per sheet)", "icon": "bi-file-pdf"},
            {"id": "merge", "name": "Merge Workbooks", "desc": "Combine multiple Excel files into one", "icon": "bi-union"},
            {"id": "split", "name": "Split Sheets", "desc": "Export each sheet as its own .xlsx", "icon": "bi-scissors"},
            {"id": "info", "name": "Excel Info & Preview", "desc": "List sheets, counts, and preview rows", "icon": "bi-info-circle-fill"},
            {"id": "csv-tools", "name": "CSV Toolkit", "desc": "Filter, sort, and deduplicate CSV rows", "icon": "bi-funnel-fill"},
        ],
    },
    {
        "id": "image",
        "name": "Image Tools",
        "icon": "bi-image-fill",
        "tools": [
            {"id": "resize", "name": "Resize Image", "desc": "Resize by percentage or dimensions", "icon": "bi-arrows-angle-expand"},
            {"id": "compress", "name": "Compress Image", "desc": "Reduce image file size", "icon": "bi-file-zip-fill"},
            {"id": "convert", "name": "Convert Format", "desc": "Convert between image formats", "icon": "bi-arrow-left-right"},
            {"id": "remove-bg", "name": "Remove Background", "desc": "Remove image background", "icon": "bi-eraser-fill"},
            {"id": "crop", "name": "Crop Image", "desc": "Crop images to specific dimensions", "icon": "bi-crop"},
            {"id": "rotate", "name": "Rotate / Flip", "desc": "Rotate or flip images", "icon": "bi-arrow-repeat"},
            {"id": "watermark", "name": "Add Watermark", "desc": "Add text watermark to images", "icon": "bi-water"},
            {"id": "exif", "name": "EXIF Viewer", "desc": "View and strip image metadata", "icon": "bi-info-circle-fill"},
            {"id": "favicon", "name": "Favicon Generator", "desc": "Create .ico favicons from images", "icon": "bi-app-indicator"},
            {"id": "ocr", "name": "Image to Text", "desc": "Extract text from images (OCR)", "icon": "bi-card-text"},
            {"id": "animated", "name": "Animated WebP/GIF", "desc": "Convert between animated WebP and GIF", "icon": "bi-film"},
            {"id": "palette", "name": "Color Palette", "desc": "Extract a color palette from an image", "icon": "bi-palette2"},
            {"id": "svg-to-png", "name": "SVG to PNG", "desc": "Rasterize SVG vector files to PNG", "icon": "bi-filetype-svg"},
            {"id": "svg-optimize", "name": "SVG Optimizer", "desc": "Strip metadata and shrink SVG files", "icon": "bi-file-minus-fill"},
            {"id": "heic-convert", "name": "HEIC Converter", "desc": "Convert iPhone .heic photos to JPG / PNG / WebP", "icon": "bi-phone-fill"},
        ],
    },
    {
        "id": "text",
        "name": "Text & Data",
        "icon": "bi-braces",
        "tools": [
            {"id": "json-formatter", "name": "JSON Formatter", "desc": "Format and validate JSON", "icon": "bi-braces"},
            {"id": "csv-json", "name": "CSV / JSON", "desc": "Convert between CSV and JSON", "icon": "bi-table"},
            {"id": "base64", "name": "Base64", "desc": "Encode and decode Base64", "icon": "bi-hash"},
            {"id": "url-encode", "name": "URL Encode", "desc": "Encode and decode URLs", "icon": "bi-link-45deg"},
            {"id": "word-counter", "name": "Word Counter", "desc": "Count words, characters, sentences", "icon": "bi-type"},
            {"id": "markdown", "name": "Markdown Preview", "desc": "Preview Markdown as HTML", "icon": "bi-markdown-fill"},
            {"id": "case-converter", "name": "Case Converter", "desc": "Convert text between cases", "icon": "bi-type-bold"},
            {"id": "text-diff", "name": "Text Diff", "desc": "Compare two texts side by side", "icon": "bi-file-diff-fill"},
            {"id": "regex-tester", "name": "Regex Tester", "desc": "Test regular expressions live", "icon": "bi-search"},
            {"id": "slug-generator", "name": "Slug Generator", "desc": "Create URL-friendly slugs", "icon": "bi-link"},
            {"id": "json-yaml", "name": "JSON / YAML", "desc": "Convert between JSON and YAML", "icon": "bi-filetype-yml"},
            {"id": "lorem-ipsum", "name": "Lorem Ipsum", "desc": "Generate placeholder text", "icon": "bi-text-paragraph"},
            {"id": "line-tools", "name": "Line Tools", "desc": "Sort, dedupe, shuffle, count, and more", "icon": "bi-list-ol"},
            {"id": "extract-patterns", "name": "Extract Patterns", "desc": "Pull emails, URLs, phones, IPs from any text", "icon": "bi-funnel"},
        ],
    },
    {
        "id": "calc",
        "name": "Calculators",
        "icon": "bi-calculator-fill",
        "tools": [
            {"id": "calculator", "name": "Calculator", "desc": "Basic and scientific calculator", "icon": "bi-calculator"},
            {"id": "unit-converter", "name": "Unit Converter", "desc": "Convert between units of measurement", "icon": "bi-arrow-left-right"},
            {"id": "color-converter", "name": "Color Converter", "desc": "Convert HEX, RGB, HSL colors", "icon": "bi-palette-fill"},
            {"id": "percentage", "name": "Percentage Calc", "desc": "Calculate percentages easily", "icon": "bi-percent"},
            {"id": "date", "name": "Date Calculator", "desc": "Calculate date differences", "icon": "bi-calendar-date-fill"},
            {"id": "timestamp", "name": "Timestamp", "desc": "Convert Unix timestamps", "icon": "bi-clock-fill"},
            {"id": "number-base", "name": "Number Base", "desc": "Convert between number bases", "icon": "bi-123"},
            {"id": "pomodoro", "name": "Pomodoro Timer", "desc": "Focus timer with breaks", "icon": "bi-stopwatch-fill"},
        ],
    },
    {
        "id": "qr",
        "name": "QR & Barcodes",
        "icon": "bi-qr-code",
        "tools": [
            {"id": "generate", "name": "Generate QR", "desc": "Create QR codes from text or URLs", "icon": "bi-qr-code"},
            {"id": "read", "name": "Read QR", "desc": "Decode QR codes from images", "icon": "bi-qr-code-scan"},
            {"id": "barcode", "name": "Generate Barcode", "desc": "Code128, EAN, UPC, ISBN and more", "icon": "bi-upc-scan"},
            {"id": "wifi", "name": "WiFi QR Code", "desc": "Generate a scan-to-join WiFi QR code", "icon": "bi-wifi"},
        ],
    },
    {
        "id": "security",
        "name": "Security",
        "icon": "bi-shield-lock-fill",
        "tools": [
            {"id": "password-generator", "name": "Password Generator", "desc": "Generate strong random passwords", "icon": "bi-key-fill"},
            {"id": "hash-generator", "name": "Hash Generator", "desc": "Generate MD5, SHA hashes", "icon": "bi-fingerprint"},
            {"id": "file-hash", "name": "File Hash", "desc": "Compute hashes of uploaded files", "icon": "bi-file-earmark-lock-fill"},
            {"id": "encrypt", "name": "Encrypt File", "desc": "AES-256 encrypt any file with a passphrase", "icon": "bi-lock-fill"},
            {"id": "decrypt", "name": "Decrypt File", "desc": "Decrypt a file produced by Encrypt File", "icon": "bi-unlock-fill"},
        ],
    },
    {
        "id": "dev",
        "name": "Developer Utilities",
        "icon": "bi-code-slash",
        "tools": [
            {"id": "uuid", "name": "UUID Generator", "desc": "Generate v4 UUIDs (bulk supported)", "icon": "bi-hash"},
            {"id": "jwt", "name": "JWT Decoder", "desc": "Decode JWT tokens (client-side)", "icon": "bi-key"},
            {"id": "user-agent", "name": "User-Agent Parser", "desc": "Parse browser, OS, and device info", "icon": "bi-window"},
            {"id": "sql-format", "name": "SQL Formatter", "desc": "Pretty-print SQL with keyword casing", "icon": "bi-filetype-sql"},
            {"id": "xml-format", "name": "XML Formatter", "desc": "Format, validate, and minify XML", "icon": "bi-filetype-xml"},
            {"id": "html-format", "name": "HTML Formatter", "desc": "Beautify or minify HTML", "icon": "bi-filetype-html"},
            {"id": "css-format", "name": "CSS Formatter", "desc": "Beautify or minify CSS", "icon": "bi-filetype-css"},
            {"id": "js-format", "name": "JS Formatter", "desc": "Beautify or minify JavaScript", "icon": "bi-filetype-js"},
            {"id": "cron", "name": "Cron Parser", "desc": "Validate cron and preview runs", "icon": "bi-calendar-week-fill"},
            {"id": "jsonpath", "name": "JSONPath Tester", "desc": "Query JSON with JSONPath expressions", "icon": "bi-search"},
        ],
    },
    {
        "id": "archive",
        "name": "Archive Tools",
        "icon": "bi-file-zip-fill",
        "tools": [
            {"id": "zip", "name": "Create ZIP", "desc": "Bundle multiple files into a .zip", "icon": "bi-file-zip"},
            {"id": "unzip", "name": "Extract ZIP", "desc": "Extract contents of a .zip archive", "icon": "bi-box-arrow-up"},
            {"id": "zip-info", "name": "ZIP Info", "desc": "Inspect archive contents and sizes", "icon": "bi-info-circle-fill"},
        ],
    },
    {
        "id": "media",
        "name": "Audio & Video",
        "icon": "bi-camera-reels-fill",
        "tools": [
            {"id": "convert-audio", "name": "Convert Audio", "desc": "Change between audio formats", "icon": "bi-music-note-beamed"},
            {"id": "convert-video", "name": "Convert Video", "desc": "Change between video formats", "icon": "bi-camera-video-fill"},
            {"id": "extract-audio", "name": "Extract Audio", "desc": "Pull audio track from a video", "icon": "bi-mic-fill"},
            {"id": "trim", "name": "Trim Media", "desc": "Cut audio or video by time range", "icon": "bi-scissors"},
            {"id": "compress-video", "name": "Compress Video", "desc": "Re-encode to a smaller file", "icon": "bi-file-zip-fill"},
            {"id": "video-to-gif", "name": "Video to GIF", "desc": "Convert clips to animated GIFs", "icon": "bi-file-earmark-play-fill"},
            {"id": "subtitle-convert", "name": "Convert Subtitles", "desc": "SRT ↔ VTT with optional time shift", "icon": "bi-badge-cc-fill"},
            {"id": "burn-subtitles", "name": "Burn Subtitles", "desc": "Permanently render subtitles onto a video", "icon": "bi-fire"},
            {"id": "normalize-audio", "name": "Normalize Audio", "desc": "Loudness normalize to a target LUFS (EBU R128)", "icon": "bi-volume-up-fill"},
            {"id": "transcribe", "name": "Speech to Text", "desc": "Transcribe audio/video to text or subtitles (Whisper)", "icon": "bi-mic-fill"},
        ],
    },
]


@app.context_processor
def inject_tools():
    return {"tool_categories": TOOL_CATEGORIES}


@app.route("/")
def index():
    return render_template("index.html")


@app.errorhandler(413)
def too_large(e):
    return {"error": "File too large. Maximum size is 100 MB."}, 413


@app.errorhandler(500)
def server_error(e):
    return {"error": "An internal error occurred."}, 500


# Register blueprints
from routes.convert_tools import bp as convert_bp
from routes.pdf_tools import bp as pdf_bp
from routes.image_tools import bp as image_bp
from routes.text_tools import bp as text_bp
from routes.calculator_tools import bp as calc_bp
from routes.qr_tools import bp as qr_bp
from routes.security_tools import bp as security_bp
from routes.spreadsheet_tools import bp as spreadsheet_bp
from routes.dev_tools import bp as dev_bp
from routes.archive_tools import bp as archive_bp
from routes.media_tools import bp as media_bp

app.register_blueprint(convert_bp, url_prefix="/convert")
app.register_blueprint(pdf_bp, url_prefix="/pdf")
app.register_blueprint(image_bp, url_prefix="/image")
app.register_blueprint(text_bp, url_prefix="/text")
app.register_blueprint(calc_bp, url_prefix="/calc")
app.register_blueprint(qr_bp, url_prefix="/qr")
app.register_blueprint(security_bp, url_prefix="/security")
app.register_blueprint(spreadsheet_bp, url_prefix="/spreadsheet")
app.register_blueprint(dev_bp, url_prefix="/dev")
app.register_blueprint(archive_bp, url_prefix="/archive")
app.register_blueprint(media_bp, url_prefix="/media")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
