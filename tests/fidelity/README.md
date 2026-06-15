# Fidelity Test Fixtures

This suite is for local/offline conversion fidelity checks. Tests should skip
cleanly when an optional local engine is unavailable.

Planned fixture groups:

- `documents`: DOCX, PPTX, XLSX, HTML, and representative PDFs.
- `images`: JPEG with EXIF orientation, transparent PNG, WebP, HEIC when available.
- `svg`: filters, masks, viewBox-only sizing, embedded raster images.
- `media`: short audio/video clips with known codecs for stream-copy checks.
- `cad`: small DXF/DWG samples with common entities and unsupported-entity warnings.

PDF-like output checks should rasterize pages with PyMuPDF and compare page
count, dimensions, and pixel similarity within fixed thresholds. Office outputs
can assert structure directly and optionally round-trip through LibreOffice to
PDF when LibreOffice is installed.
