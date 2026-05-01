# Changelog

All notable changes to **Your Everyday Tools** are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project loosely follows [Semantic Versioning](https://semver.org/).

## [0.6.0] — 2026-04-29

### Added — 8 new tools across 6 categories (total now 99)

- **HEIC Converter** *(Image Tools)* — convert iPhone `.heic` / `.heif` photos to JPG, PNG, or WebP, single or bulk → ZIP. Once `pillow-heif` is installed, **every other image tool** in the app (resize, crop, palette, watermark, OCR, etc.) also auto-accepts HEIC inputs.
- **Line Tools** *(Text & Data)* — client-side bundle: sort A→Z / Z→A / numerically, dedupe (keep order or alphabetic), shuffle, reverse, trim, drop empty, number lines, count words/chars. All in-browser.
- **Extract Patterns** *(Text & Data)* — client-side regex extractor for emails, URLs, phone numbers, IPv4/IPv6, hashtags, @mentions, and numbers. Toggle dedupe + sort, output as separate sections or merged list.
- **Redact PDF** *(PDF Tools)* — permanently black-out sensitive text by literal match or regex. Underlying text is removed from the PDF content stream so it cannot be recovered with copy-paste; image-rendering pixels are also covered. Supports page-range scoping and case sensitivity toggles. Returns 400 with a friendly error if no patterns match (rather than silently returning the original).
- **WiFi QR Code** *(QR & Barcodes)* — generate a scan-to-join WiFi QR (WPA / WEP / open / hidden), with proper escaping of `\\`, `;`, `,`, `:`, and `"` in SSID and password per the WIFI: URI scheme. Uses high error-correction so printed/photographed QRs still scan.
- **Encrypt File / Decrypt File** *(Security)* — AES-256-CBC file encryption with PBKDF2-HMAC-SHA256 key derivation (600,000 iterations + 8-byte random salt). Output is byte-identical to `openssl enc -aes-256-cbc -pbkdf2 -iter 600000`, so users can decrypt with the OpenSSL CLI too. Wrong passphrase returns a clean error rather than corrupted output.
- **Normalize Audio** *(Audio & Video)* — FFmpeg `loudnorm` (EBU R128) with one-button presets for streaming (-14 LUFS), Apple Podcasts (-16), broadcast (-23, -24). Output format can match input or transcode to MP3 / WAV / FLAC.
- **Speech to Text** *(Audio & Video)* — local Whisper transcription to plain text, SRT, or WebVTT. Five model sizes (tiny → large), optional language hint. Optional install (`pip install openai-whisper`); model is cached in-memory after first load to avoid re-downloading. Honest UI guidance about CPU vs GPU speed.

### Changed
- Image tool inputs now include `.heic` / `.heif` automatically when `pillow-heif` is installed.
- Tool count: 91 → 99.

### Dependencies
- Added `cryptography` to core (used by Encrypt/Decrypt File).
- Added `pillow-heif` and `openai-whisper` to optional dependencies.

## [0.5.1] — 2026-04-28

### Added
- **PDF to PowerPoint** *(Document Conversion)* — render each PDF page as an image and drop it onto its own slide in a `.pptx`. Choose between 16:9, 4:3, or A4 slide sizes, set DPI, and optionally restrict to a page range. Aspect-fit math centers each page on the slide.
- **PowerPoint to PDF** *(Document Conversion)* — convert `.pptx`, `.ppt`, or `.odp` presentations to PDF via LibreOffice (`soffice`). Detection note on the page tells the user whether LibreOffice is on PATH and how to install it if not — same UX as the FFmpeg-backed media tools.

### Fixed — layout fidelity in document conversions

User reports of "messy layout after conversion" traced to three weak engines. All three now optionally route through LibreOffice for a major fidelity jump, falling back to the previous engine when LibreOffice isn't installed.

- **Files to PDF (Word documents)** — `.docx`/`.doc`/`.odt` files now convert via `soffice --headless --convert-to pdf` when LibreOffice is available, preserving fonts, tables, columns, headers/footers, and image placement. Falls back to the previous python-docx + reportlab rebuilder for `.docx` only when soffice is missing. Now also accepts `.doc` and `.odt` (LibreOffice path).
- **HTML to PDF** — switched primary renderer to LibreOffice for proper CSS, table, and styled-content support. Falls back to PyMuPDF's `insert_htmlbox` when soffice is missing. The previous renderer was producing unstyled output for anything beyond plain text + simple tables.
- **PDF to Word** — added three new modes alongside the existing **Layout** (pdf2docx) mode, since PDF→Word is fundamentally lossy and different documents need different strategies:
  - **Smart structure** — analyses font sizes and bold ratios to detect headings (H1/H2/H3), bullet lists, and numbered lists, emitting a `.docx` with proper Word styles (visible in the navigation pane). Best for articles, blog posts, books, and documentation.
  - **Flowing text** — extracts text in reading order, emitting one paragraph per PDF block. No structure detection, but always clean.
  - **Marker (optional)** — uses the [marker-pdf](https://github.com/VikParuchuri/marker) ML library for best-in-class structure understanding. Install with `pip install marker-pdf`; first use downloads ~2 GB of models and conversion is slow on CPU.

  All four modes now also support a **page range** option (e.g. `1-3, 5, 8-10`) and Layout mode also exposes a **detect borderless tables** advanced toggle (pdf2docx `parse_stream_table`). Layout mode now closes its `Pdf2DocxConverter` in a try/finally.

### Changed — comprehensive quality pass across all file-handling routes
- **Bounds-checked numeric input** — all `int(request.form.get(...))` and `float(request.form.get(...))` calls now go through new `safe_int()` / `safe_float()` helpers in `routes/_helpers.py` that clamp to sensible ranges and fall back to defaults on bad input. Replaces 25+ unguarded conversions across `pdf_tools`, `image_tools`, `convert_tools`, `spreadsheet_tools`, `media_tools`, and `qr_tools`. POSTing `dpi=99999` or `quality=abc` now returns a sensible result instead of crashing.
- **Resource cleanup** — every `fitz.open()`, `Image.open()`, `load_workbook()`, and `zipfile.ZipFile()` is now wrapped in either a `with` block or try/finally so document handles are closed even when processing throws. Prevents file-handle and memory leaks under error conditions.
- **Sanitized error responses** — exception text from PyMuPDF / Pillow / openpyxl / Tesseract / svglib is no longer surfaced raw to users (was leaking stack-trace fragments and internal file paths). Friendly messages now go to the client; full exceptions are logged via `app.logger`. Affected routes: every PDF/image/conversion/OCR endpoint.
- **Standardized "no file uploaded" messages** — single new helper string `NO_FILE_SINGLE` ("Please upload a file.") replaces eight different ad-hoc variants across the routes.
- **Encrypted-ZIP detection** — `archive_tools.unzip` now inspects ZIP entry flag bits up-front to detect password-protected archives, replacing fragile string-matching on RuntimeError messages.
- **Crop bounds clamping** — `image_tools.crop` now clamps custom crop coordinates to the image bounds (was accepting negative values and out-of-bounds rectangles).
- **Palette extractor stability** — fixed an `IndexError` crash on single-color or low-color images where PIL's quantizer returns fewer palette entries than requested.

### Dependencies
- Added `python-pptx` to `requirements.txt` for the PDF→PPT slide builder.

## [0.5.0] — 2026-04-20

### Added — 10 new tools across 6 categories
- **Sign PDF** *(PDF Tools)* — stamp a signature image (PNG/JPG) onto selected pages with position, width, margin, and opacity control.
- **Markdown to PDF** *(Document Conversion)* — paste or upload Markdown, choose page size and font size, download a rendered PDF. Uses PyMuPDF's `Story` + `DocumentWriter` for proper multi-page pagination.
- **Markdown to Word** *(Document Conversion)* — convert Markdown to a `.docx` document with proper heading, list, quote, and code styles.
- **CSV Toolkit** *(Spreadsheet)* — filter, sort, and de-duplicate CSV rows. Auto-detects delimiter, supports `=`, `!=`, `contains`, `startswith`, `endswith`, `>`, `>=`, `<`, `<=`, `empty`, `notempty` filter operators; smart/text/number sort; full-row or by-column dedupe.
- **Color Palette** *(Image Tools)* — extract a dominant color palette from an image (2–16 colors) with quantization or grid-sampling methods; returns a swatch preview with hex codes.
- **SVG to PNG** *(Image Tools)* — rasterize SVG vectors to PNG at a chosen width, with optional transparent background.
- **SVG Optimizer** *(Image Tools)* — strip comments, editor metadata (Inkscape/Sketch/Adobe namespaces), and round decimals to shrink SVG files. Reports savings.
- **Generate Barcode** *(QR & Barcodes)* — create Code128, Code39, EAN-13/8, UPC-A, ISBN-10/13, ISSN, JAN, or PZN barcodes as PNG or SVG.
- **Convert Subtitles** *(Audio & Video)* — convert between SRT and WebVTT with optional time shift (positive or negative seconds).
- **Burn Subtitles** *(Audio & Video)* — permanently render a `.srt`/`.vtt` file into a video (hardsub) via FFmpeg, with font-size and quality control.

### Changed
- **QR Code** category renamed to **QR & Barcodes** to accommodate the new barcode generator.
- Tool count now stands at **89** across 11 categories.

### Dependencies
- Added `python-barcode` (barcode generation) and `svglib` (SVG rasterization) to `requirements.txt`.

## [0.4.3] — 2026-04-20

### Added
- **PDF to Excel** — extract tables from a PDF into an `.xlsx` workbook. Three modes: tables-only, tables-with-text-fallback, or text-only. Three sheet organizations: one sheet per table, one per page, or all combined. Powered by PyMuPDF's native `find_tables()` — no new dependencies. For scanned PDFs, run **OCR PDF** first.

## [0.4.2] — 2026-04-20

### Added
- **Double-click launchers** — `run.bat` for Windows, `run.command` for macOS, and `run.sh` for Linux. Non-technical users only need to install Python once, then double-click the launcher. It auto-creates a virtual environment, installs dependencies, starts the server, and opens the browser. Close the window to stop.
- `.gitattributes` pinning LF line endings on shell/command files so the launchers work after a Windows checkout.

## [0.4.1] — 2026-04-20

### Fixed
- **PDF Compress** no longer breaks page layout. Compressed images are now replaced in-place via `page.replace_image(xref, ...)` instead of being re-inserted at full page dimensions, so the original placement, size, and positioning matrix are preserved. Images shared across multiple pages are also deduplicated so they're only recompressed once.
- **PDF Resize** now actually scales page content instead of only changing the media box (which previously just cropped the visible area, leaving images and text clipped or misaligned). Scale mode renders each page onto a new page at the new size; paper-size mode fits content into the target with aspect ratio preserved and orientation matched.
- **Upload UI** — the invisible file input no longer covers the uploaded file list. The remove buttons on each listed file are now clickable. Structural fix: `.file-list` is now a sibling of `.upload-zone` rather than a child.

### Added
- Per-quality image-dimension cap on PDF Compress (1200/1800/2400 px max edge for low/medium/high) so photo-heavy PDFs actually shrink.

## [0.4.0] — 2026-04-20

### Added — Developer Utilities (new category, 10 tools)
- **UUID Generator** (client-side) — v4 UUIDs, bulk generation, formatting options.
- **JWT Decoder** (client-side) — decodes JWT header/payload/signature; does not verify signatures.
- **User-Agent Parser** (client-side) — extracts browser, OS, device, and engine.
- **SQL Formatter** — pretty-prints SQL via `sqlparse` with configurable keyword case and indent.
- **XML Formatter** (client-side) — format, validate, and minify XML via DOMParser.
- **HTML Formatter** (client-side) — beautify/minify with correct handling of void tags, inline tags, and raw-content blocks.
- **CSS Formatter** (client-side) — indent-aware beautify/minify.
- **JS Formatter** (client-side) — basic beautify/minify with string and comment protection.
- **Cron Parser** — validates expressions and previews upcoming runs via `croniter`.
- **JSONPath Tester** — evaluates JSONPath expressions via `jsonpath-ng`.

### Added — Archive Tools (new category, 3 tools)
- **Create ZIP** — bundle multiple files with Deflate or Store compression.
- **Extract ZIP** — extract archive contents (500 MB cap; encrypted ZIPs rejected).
- **ZIP Info** — list entries with sizes, dates, and overall compression ratio.

### Added — Audio & Video (new category, 6 tools — requires FFmpeg on PATH)
- **Convert Audio** — MP3/WAV/OGG/FLAC/AAC/M4A/Opus with adjustable bitrate.
- **Convert Video** — MP4/WebM/MKV/MOV/AVI with sensible codec defaults.
- **Extract Audio** — pull audio track from a video file.
- **Trim Media** — cut by start/end time; stream-copy first, re-encodes on failure.
- **Compress Video** — H.264 re-encode at configurable CRF and preset.
- **Video to GIF** — with FPS, width, start, and duration options.

### Added — Security
- **File Hash** — streaming MD5/SHA-1/SHA-256/SHA-512 of uploaded files.

### Added — Dependencies
- `sqlparse`, `croniter`, `jsonpath-ng` added to `requirements.txt`.
- FFmpeg documented as an optional external binary; each media tool page shows install instructions and a detected/not-detected banner.

## [0.3.0] — 2026-04-19

### Added — Spreadsheet (new category, 6 tools)
- **Excel to CSV / JSON** — export sheets from `.xlsx` / `.xls` to CSV or JSON (array-of-objects or array-of-arrays), single sheet or all sheets as ZIP.
- **CSV / JSON to Excel** — build `.xlsx` from CSV/JSON files, one sheet per file, optional bold/shaded header row.
- **Excel to PDF** — one section per sheet, configurable page size, orientation, and font size. 5000-row cap per sheet.
- **Merge Workbooks** — combine multiple Excel files, optionally prefixing sheet names with source filename.
- **Split Sheets** — export each sheet as its own `.xlsx`.
- **Excel Info & Preview** — list sheet names, row/column counts, and preview rows.

### Added — Dependencies
- `openpyxl` (required) and `xlrd` (for legacy `.xls` read) added to `requirements.txt`.

## [0.2.0] — 2026-04-19

### Added
- **OCR PDF** — make scanned PDFs searchable (image + hidden text layer) or extract text. 14 languages supported via optional `pytesseract`.
- **CAD to PDF / Image** — render DXF directly via `ezdxf` + `matplotlib`. DWG supported via optional **ODA File Converter** (auto-detected on PATH). Full install guide added to README and to the CAD tool page.
- **Animated WebP / GIF** — convert between the two formats, preserving per-frame durations.

### Removed
- MIT license badge from README (project has no license).

## [0.1.0] — 2026-04-18

### Added
- Initial release — 48 tools across 7 categories: Document Conversion, PDF Tools, Image Tools, Text & Data, Calculators, QR Code, Security.
- One universal upload template (`upload_tool.html`) powering all server-side tools.
- Client-side-only tools for text utilities, calculators, password and hash generators.
- Graceful degradation for heavy optional dependencies (`rembg`, `pyzbar`, `pdf2docx`).
- Screenshots, README, `.gitignore`.
