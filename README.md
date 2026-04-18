# Your Everyday Tools

A lightweight, self-hosted web app that bundles 33 everyday utilities into a single interface. Built with Python + Flask, zero JavaScript frameworks, and minimal CSS — no bloat, just tools.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Features

### Document Conversion
| Tool | Description |
|------|-------------|
| **Files to PDF** | Convert images (JPG, PNG, BMP, TIFF, WebP) and text files to PDF |
| **PDF to Word** | Convert PDF documents to `.docx` format |
| **PDF to Images** | Export each PDF page as PNG or JPG (configurable DPI) |
| **PDF to Text** | Extract all text content from a PDF |

### PDF Tools
| Tool | Description |
|------|-------------|
| **Merge PDFs** | Combine multiple PDF files into one document |
| **Split PDF** | Split a PDF into individual pages or custom page ranges |
| **Compress PDF** | Reduce PDF file size (low / medium / high compression) |
| **Rotate PDF** | Rotate all or specific pages (90, 180, 270 degrees) |
| **Resize PDF** | Scale pages by percentage or fit to standard paper sizes (A3–A5, Letter, Legal) |
| **Page Numbers** | Add page numbers with configurable position, font size, and start number |
| **Extract Images** | Extract all embedded images from a PDF |
| **Protect PDF** | Encrypt a PDF with user and owner passwords (AES-256) |
| **Unlock PDF** | Remove password protection from a PDF |

### Image Tools
| Tool | Description |
|------|-------------|
| **Resize Image** | Resize by percentage or exact pixel dimensions (with aspect ratio lock) |
| **Compress Image** | Reduce file size with adjustable quality slider (10–100%) |
| **Convert Format** | Convert between PNG, JPG, WebP, BMP, and TIFF |
| **Remove Background** | Automatically remove image backgrounds using AI |
| **Crop Image** | Crop by aspect ratio (1:1, 4:3, 16:9, etc.) or custom coordinates |
| **Rotate / Flip** | Rotate 90/180/270 degrees, flip horizontal or vertical |
| **Add Watermark** | Add text watermark with configurable position, opacity, size, and tiled mode |

### Text & Data (client-side, no upload needed)
| Tool | Description |
|------|-------------|
| **JSON Formatter** | Format, validate, and minify JSON |
| **CSV / JSON** | Convert between CSV and JSON in both directions |
| **Base64** | Encode and decode Base64 strings |
| **URL Encode** | Encode and decode URL components |
| **Word Counter** | Count words, characters, sentences, paragraphs, and estimate reading time |
| **Markdown Preview** | Live Markdown-to-HTML preview |

### Calculators (client-side)
| Tool | Description |
|------|-------------|
| **Calculator** | Basic + scientific calculator with keyboard support |
| **Unit Converter** | Length, weight, temperature, area, volume, speed, data, and time |
| **Color Converter** | Convert between HEX, RGB, and HSL with live preview and color picker |
| **Percentage Calc** | Four common percentage calculations in one page |
| **Date Calculator** | Date difference, add/subtract days, day-of-week lookup |

### QR Code
| Tool | Description |
|------|-------------|
| **Generate QR** | Create QR codes from text/URLs with custom size, border, and color |
| **Read QR** | Decode QR codes from uploaded images |

---

## Quick Start

### Prerequisites

- **Python 3.10+**

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/your-everyday-tools.git
cd your-everyday-tools

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

### Run

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## Optional Dependencies

The core app works out of the box with the main dependencies. Some features require additional packages that may need system-level libraries:

| Package | Feature | Notes |
|---------|---------|-------|
| `rembg` | Remove Background | Installs ONNX Runtime (~500 MB). The app works without it and shows a helpful message if missing. |
| `pyzbar` | Read QR Code | Requires the [ZBar](https://github.com/NaturalHistoryMuseum/pyzbar#installation) shared library on your system. |
| `pdf2docx` | PDF to Word | Pure Python, but conversion quality depends on PDF complexity. |

If you only need the core tools, install the minimal set:

```bash
pip install Flask Pillow PyMuPDF "qrcode[pil]" markdown reportlab img2pdf
```

---

## Project Structure

```
your-everyday-tools/
├── app.py                          # Flask app, tool registry, blueprint registration
├── requirements.txt
├── utils/
│   └── file_utils.py               # Shared helpers (ZIP creation, file validation)
├── routes/
│   ├── convert_tools.py            # Document conversion endpoints
│   ├── pdf_tools.py                # PDF manipulation endpoints
│   ├── image_tools.py              # Image processing endpoints
│   ├── text_tools.py               # Text & data tool page routes
│   ├── calculator_tools.py         # Calculator page routes
│   └── qr_tools.py                # QR code endpoints
├── templates/
│   ├── base.html                   # Main layout (sidebar + content area)
│   ├── index.html                  # Home page with tool cards
│   ├── upload_tool.html            # Universal template for all file-based tools
│   └── tools/                      # Individual client-side tool templates
│       ├── calculator.html
│       ├── unit_converter.html
│       ├── color_converter.html
│       ├── percentage_calc.html
│       ├── date_calc.html
│       ├── json_formatter.html
│       ├── csv_json.html
│       ├── base64.html
│       ├── url_encode.html
│       ├── word_counter.html
│       └── markdown_preview.html
└── static/
    ├── css/style.css               # All styles (~400 lines, no framework)
    └── js/main.js                  # File upload, AJAX, sidebar, shared logic
```

### Architecture Notes

- **One universal template** — `upload_tool.html` powers all 20+ server-side tools. Each route passes title, description, accepted file types, and form options as template variables. No per-tool template duplication.
- **Client-side tools** (text utilities, calculators) run entirely in the browser with vanilla JavaScript — zero server round-trips.
- **In-memory processing** — all file operations use `BytesIO`. No temporary files are written to disk.
- **No CSS framework** — custom CSS with CSS Grid, Flexbox, and CSS custom properties. The only external resource is Bootstrap Icons via CDN (~100 KB) for the icon set.
- **Graceful degradation** — heavy optional packages (`rembg`, `pyzbar`, `pdf2docx`) are checked at import time. If missing, the affected tool shows a clear install instruction instead of crashing.

---

## Configuration

The app has sensible defaults. You can adjust these in `app.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_CONTENT_LENGTH` | `100 MB` | Maximum upload file size |
| `debug` | `True` | Flask debug mode (disable in production) |
| `port` | `5000` | Server port |

---

## Deployment

For production use, run with a WSGI server instead of the built-in Flask server:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

On Windows, use `waitress` instead:

```bash
pip install waitress
waitress-serve --port=8000 app:app
```

---

## License

MIT
