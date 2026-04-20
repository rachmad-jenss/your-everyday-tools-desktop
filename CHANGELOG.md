# Changelog

All notable changes to **Your Everyday Tools** are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project loosely follows [Semantic Versioning](https://semver.org/).

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
