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
            {"id": "html-to-pdf", "name": "HTML to PDF", "desc": "Convert HTML content to PDF", "icon": "bi-filetype-html"},
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
        "name": "QR Code",
        "icon": "bi-qr-code",
        "tools": [
            {"id": "generate", "name": "Generate QR", "desc": "Create QR codes from text or URLs", "icon": "bi-qr-code"},
            {"id": "read", "name": "Read QR", "desc": "Decode QR codes from images", "icon": "bi-qr-code-scan"},
        ],
    },
    {
        "id": "security",
        "name": "Security",
        "icon": "bi-shield-lock-fill",
        "tools": [
            {"id": "password-generator", "name": "Password Generator", "desc": "Generate strong random passwords", "icon": "bi-key-fill"},
            {"id": "hash-generator", "name": "Hash Generator", "desc": "Generate MD5, SHA hashes", "icon": "bi-fingerprint"},
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

app.register_blueprint(convert_bp, url_prefix="/convert")
app.register_blueprint(pdf_bp, url_prefix="/pdf")
app.register_blueprint(image_bp, url_prefix="/image")
app.register_blueprint(text_bp, url_prefix="/text")
app.register_blueprint(calc_bp, url_prefix="/calc")
app.register_blueprint(qr_bp, url_prefix="/qr")
app.register_blueprint(security_bp, url_prefix="/security")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
