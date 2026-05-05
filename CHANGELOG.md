# Changelog

All notable changes to **Your Everyday Tools** are documented here. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project loosely follows [Semantic Versioning](https://semver.org/).

## [Desktop 1.2.2-mac] — 2026-05-05

### Added

- **macOS support (Apple Silicon)** — The desktop app is now available as a `.dmg` for macOS arm64 (M1/M2/M3/M4). Intel Mac users can run via Rosetta 2. Note: the macOS build is not code-signed; users need to right-click → Open on first launch.
- **GitHub Actions CI/CD** — Unified workflow (`.github/workflows/build-desktop.yml`) automatically builds both Windows and macOS installers when a `v*` tag is pushed. Releases are created as draft, both platforms upload their artifacts, then the release is published.

### Notes

- macOS build does not include the NSIS component downloader (FFmpeg/Tesseract). Mac users should install these via Homebrew: `brew install ffmpeg tesseract`.
- Auto-update via `electron-updater` is supported on macOS (`latest-mac.yml` is published alongside the DMG).

## [Desktop 1.2.2] — 2026-05-03

Desktop-only release. No changes to the Flask/Python backend.

### Fixed

- **`ModuleNotFoundError: No module named 'jaraco'`** — Flask failed to start because `pkg_resources` (imported by the PyInstaller runtime hook `pyi_rth_pkgres`) pulls in `jaraco.text` at module level. Added `jaraco.text` as an explicit `hiddenimport` in the `.spec` file so PyInstaller bundles it correctly.
- **curl.exe crash (0xc0000142) during component download** — NSIS `makensis.exe` is a 32-bit process; `$SYSDIR` therefore resolves to `SysWOW64`, where the Windows-bundled `curl.exe` fails to initialize under `CREATE_NO_WINDOW`. Replaced all curl calls with `PowerShell WebClient.DownloadFile`, which works correctly in the NSIS `nsExec::ExecToLog` environment.
- **Console windows appearing during install** — switched component download/extract commands from `ExecWait` (creates a visible console window) to `nsExec::ExecToLog` (runs hidden, logs output to the NSIS detail box).
- **Cek Update showed no dialog when already up to date** — `update-not-available` event only logged to console; `checkForUpdatesManual()` also had a broken promise-chain check. Fixed with a `isManualUpdateCheck` flag: manual checks now always show a dialog ("Tidak ada update" or "Tidak bisa cek update").

### Improved

- **Component selection moved into the NSIS installer wizard** — FFmpeg and Tesseract checkboxes now appear as a dedicated wizard page (after directory selection, before the Installing progress screen). Downloads and extraction happen during installation rather than on first app launch.
- **Kelola Komponen shows installed status** — when opening *Help → Kelola Komponen*, components that are already installed now show a green **✓ Terinstall** badge and are unchecked by default (no accidental re-download). If all components are installed, the subtitle changes to "Semua komponen sudah terinstall. Centang jika ingin menginstall ulang." and the skip button becomes "Tutup".

## [0.6.2] — 2026-04-29

### Improved — Requirements & expectations on every tool page

Audited all 100 tool pages and added clear "Requirements & expectations" notes wherever they were missing. Users no longer have to start a conversion to discover that a tool needs LibreOffice / FFmpeg / Tesseract / pyzbar / rembg / etc.

- **Tools with hard external dependencies** now show their install status up-front (green check if detected, yellow warning + per-OS install instructions if missing): OCR PDF, Image OCR, Remove Background, Read QR Code, Generate Barcode (in addition to the ones that already had this: HEIC Converter, Files to PDF, HTML to PDF, PDF to PowerPoint, PowerPoint to PDF, Speech to Text, Encrypt File, all FFmpeg-backed media tools).
- **Tools with format quirks or input expectations** got concise expectation notes: PDF to Images (DPI guide + format choice), PDF to Text ("only works on text PDFs, scans need OCR first"), Excel to CSV/JSON (formula caching note, multi-sheet behaviour), Excel to PDF (honest about not being pixel-perfect), Compress PDF (which PDFs benefit, JPEG re-encoding details), Compress Image (JPG-only output, quality guide), Convert Subtitles (supported formats + drift limitations), Extract Images (raster-only, vectors not exported), Protect / Unlock PDF (encryption details, no-cracker disclaimer), Generate Barcode (per-format input requirements), SVG to PNG (renderer limitations).
- **Markdown to PDF / Word** custom templates picked up notes about supported syntax and known limitations (no remote image fetch).

Tools with notes coverage: **43 of 100**, up from 24. The remaining 57 are pure client-side utilities (calculators, formatters, JSON tools, dev utilities) that have no external dependencies and self-explanatory behaviour.

### Fixed — Word→PDF (Files to PDF) layout quality

Users reported "messy layout" and "missing images" when converting `.docx` to PDF. Root cause: the tool was silently falling back to a hand-rolled python-docx + reportlab rebuilder when LibreOffice wasn't on `PATH` — and that fallback didn't handle images at all and emitted tables out of document order. Three fixes:

- **Smarter LibreOffice detection.** Most Windows users install LibreOffice via the regular installer but never add it to PATH, so the app couldn't find it. Detection now checks PATH first, then common per-OS install paths (`C:\Program Files\LibreOffice\program\soffice.exe` and the x86 variant on Windows, `/Applications/LibreOffice.app/...` on macOS, `/usr/bin/`, `/usr/local/bin/`, `/opt/libreoffice/`, `/snap/bin/` on Linux). Users no longer have to mess with PATH.
- **Fallback now handles images and document order.** When LibreOffice genuinely isn't available, the fallback walks the docx body in original order (so paragraphs and tables appear interleaved correctly, not all paragraphs first then all tables), and embeds inline images by extracting them from the docx's relationships and re-rendering through reportlab's `Image` flowable. Custom fonts, headers/footers, columns, page breaks, text boxes, and SmartArt are still fallback-unsupported — for those, install LibreOffice. The page notes now spell out exactly what the fallback does and doesn't preserve.
- **`X-Conversion-Engine` response header.** The Files-to-PDF response now carries a header (`libreoffice` or `fallback`) so users and admins can quickly tell which engine actually ran without trawling logs.

### Improved
- **PDF to PowerPoint: Editable mode.** Users complained that the previous behaviour put the entire PDF page as an image on each slide, so nothing was clickable or editable in PowerPoint. The tool now offers two modes:
  - **Editable** *(new default when LibreOffice is detected)* — uses LibreOffice's PDF importer to convert each page into native PowerPoint elements (text frames, lines, shapes, embedded images). You can click on text to edit it, change fonts, rearrange shapes. Layout fidelity is good but not pixel-perfect.
  - **Image** *(previous behaviour, still available)* — renders each PDF page as a single picture on a slide. Visually identical to the source, but nothing is editable.
  Page range works in both modes (Editable mode pre-filters the PDF before passing it to LibreOffice). The Image-mode slide-size and DPI options have been clearly labelled as such on the page.

### Fixed
- **PDF to Excel: now finds borderless tables.** Users were reporting that the same PDF returned "no tables found" in PDF→Excel but PDF→Word (Layout mode) successfully extracted tables. Root cause: PyMuPDF's `find_tables()` defaults to `strategy="lines"` which only detects tables with visible borders, while `pdf2docx` (used by PDF→Word) detects both ruled and borderless tables. PDF→Excel now exposes a **table detection strategy** option:
  - **Auto** *(default)* — tries lines first, falls back to text-alignment if no ruled tables are found. Best of both worlds with no false-positive risk on multi-column body text.
  - **Lines only** — original behavior, conservative.
  - **Text alignment only** — for borderless tables (financial reports, invoices, schedules).
- The "no tables found" error message now suggests the alternate strategy or directs users to PDF→Word in Layout mode if even text-strategy detection fails.

## [0.6.1] — 2026-04-29

### Added
- **Fill PDF Form** *(PDF Tools)* — upload a PDF that has AcroForm fields (the kind in tax forms, gov applications, and most fillable PDFs), inspect the fields in your browser, fill them, and download the filled PDF. Supports text, multi-line text, checkbox, radio, listbox, and combobox field types. Two-step UI: `/pdf/form-inspect` returns the field schema as JSON, then `/pdf/form-fill` applies values. PDFs without form fields surface a clear "this PDF doesn't have an AcroForm" message rather than silently doing nothing. XFA-only forms (some Adobe-only forms) are not supported — limitation of PyMuPDF, not the project.

### Improved
- **Fill PDF Form: human radio/checkbox labels.** PDF radio buttons store opaque on-state values (often `0`/`1`/`Yes`/arbitrary identifiers) but the human label like "Male" / "Female" is painted on the page as static text *next to* the widget — not part of the field. Form Filler now sniffs that nearby text and shows the human label in the UI, while keeping the PDF on-state value as the actual submitted value (and as a tooltip for power users). Same for checkbox labels. The sniffer correctly handles vertical lists, horizontal rows ("○ Male  ○ Female"), and multi-word labels ("I agree to the terms and conditions"), stopping at gaps > 25pt to avoid grabbing the next widget's label.
- **Fill PDF Form: editable comboboxes.** PDF combobox fields can be either strict (only the listed choices are accepted) or editable (user can type a custom value not in the list — bit 19 of the field flags). Form Filler now detects this flag and renders editable comboboxes as a free-text input with the listed choices offered as suggestions via `<datalist>`, while strict comboboxes remain `<select>` dropdowns. Both render with a small hint explaining the constraint. Custom values typed into editable fields are written into the PDF correctly.

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
