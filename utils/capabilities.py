"""Local engine detection and conversion metadata helpers.

The app is offline-first, so high-fidelity conversion depends on tools that
are installed on the user's machine. This module centralizes that discovery so
routes and the UI agree on what is high fidelity, basic fallback, or missing.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable


QUALITY_HIGH = "high"
QUALITY_BASIC = "basic"
QUALITY_UNAVAILABLE = "unavailable"


def find_soffice() -> str | None:
    """Detect LibreOffice. PATH first, then common per-OS install locations."""
    found = shutil.which("soffice") or shutil.which("libreoffice")
    if found:
        return found

    import sys

    candidates: list[str] = []
    if sys.platform == "win32":
        program_files = [
            os.environ.get("ProgramFiles", r"C:\Program Files"),
            os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
            os.environ.get("ProgramW6432", r"C:\Program Files"),
        ]
        for pf in program_files:
            if pf:
                candidates.append(os.path.join(pf, "LibreOffice", "program", "soffice.exe"))
                candidates.append(os.path.join(pf, "LibreOffice", "program", "soffice.com"))
    elif sys.platform == "darwin":
        candidates.append("/Applications/LibreOffice.app/Contents/MacOS/soffice")
    else:
        candidates.extend([
            "/usr/bin/soffice",
            "/usr/bin/libreoffice",
            "/usr/local/bin/soffice",
            "/usr/local/bin/libreoffice",
            "/opt/libreoffice/program/soffice",
            "/snap/bin/libreoffice",
        ])

    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


def _package_available(import_name: str) -> bool:
    return importlib.util.find_spec(import_name) is not None


def _binary_version(path: str | None, args: Iterable[str]) -> str | None:
    if not path:
        return None
    try:
        proc = subprocess.run(
            [path, *args],
            capture_output=True,
            text=True,
            timeout=3,
        )
    except Exception:
        return None
    text = (proc.stdout or proc.stderr or "").strip()
    return text.splitlines()[0][:160] if text else None


def _binary_engine(engine_id: str, label: str, path: str | None,
                   version_args: Iterable[str], install_hint: str,
                   quality: str = QUALITY_HIGH) -> dict:
    version_args = list(version_args)
    return {
        "id": engine_id,
        "label": label,
        "available": bool(path),
        "path": path,
        "version": _binary_version(path, version_args) if path and version_args else None,
        "quality": quality if path else QUALITY_UNAVAILABLE,
        "install_hint": install_hint,
        "kind": "binary",
    }


def _package_engine(engine_id: str, label: str, import_name: str,
                    install_hint: str, quality: str = QUALITY_HIGH) -> dict:
    available = _package_available(import_name)
    return {
        "id": engine_id,
        "label": label,
        "available": available,
        "path": None,
        "version": None,
        "quality": quality if available else QUALITY_UNAVAILABLE,
        "install_hint": install_hint,
        "kind": "python-package",
    }


def _combined_package_engine(engine_id: str, label: str, import_names: Iterable[str],
                             install_hint: str, quality: str = QUALITY_HIGH) -> dict:
    missing = [name for name in import_names if not _package_available(name)]
    return {
        "id": engine_id,
        "label": label,
        "available": not missing,
        "path": None,
        "version": None,
        "quality": quality if not missing else QUALITY_UNAVAILABLE,
        "install_hint": install_hint,
        "kind": "python-package",
        "missing_packages": missing,
    }


def _oda_path() -> str | None:
    return shutil.which("ODAFileConverter") or shutil.which("oda_file_converter")


def get_capabilities() -> dict:
    soffice = find_soffice()
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    tesseract = shutil.which("tesseract")
    oda = _oda_path()

    engines = {
        "libreoffice": _binary_engine(
            "libreoffice",
            "LibreOffice",
            soffice,
            ["--version"],
            "Install LibreOffice locally, then restart this app.",
        ),
        "ffmpeg": _binary_engine(
            "ffmpeg", "FFmpeg", ffmpeg, ["-version"],
            "Install FFmpeg locally and make sure it is on PATH.",
        ),
        "ffprobe": _binary_engine(
            "ffprobe", "FFprobe", ffprobe, ["-version"],
            "Install FFmpeg locally; ffprobe ships with it.",
        ),
        "tesseract": _binary_engine(
            "tesseract", "Tesseract OCR", tesseract, ["--version"],
            "Install the Tesseract binary and required language packs.",
        ),
        "oda": _binary_engine(
            "oda", "ODA File Converter", oda, [],
            "Install ODA File Converter for DWG support.",
        ),
        "pymupdf": _package_engine(
            "pymupdf", "PyMuPDF", "fitz",
            "Install PyMuPDF with pip install PyMuPDF.",
        ),
        "pdf2docx": _package_engine(
            "pdf2docx", "pdf2docx", "pdf2docx",
            "Install pdf2docx with pip install pdf2docx.",
            quality="medium",
        ),
        "pdfplumber": _package_engine(
            "pdfplumber", "pdfplumber", "pdfplumber",
            "Install pdfplumber with pip install pdfplumber.",
            quality="medium",
        ),
        "marker": _package_engine(
            "marker", "Marker PDF", "marker",
            "Install marker-pdf locally; first use downloads local model weights.",
        ),
        "pytesseract": _package_engine(
            "pytesseract", "pytesseract", "pytesseract",
            "Install pytesseract with pip install pytesseract.",
        ),
        "pyzbar": _package_engine(
            "pyzbar", "pyzbar", "pyzbar",
            "Install pyzbar and the local ZBar shared library.",
        ),
        "rembg": _combined_package_engine(
            "rembg", "rembg", ["rembg", "onnxruntime"],
            'Install rembg with CPU support: pip install "rembg[cpu]".',
        ),
        "pillow-heif": _package_engine(
            "pillow-heif", "pillow-heif", "pillow_heif",
            "Install pillow-heif with pip install pillow-heif.",
        ),
        "whisper": _package_engine(
            "whisper", "Whisper", "whisper",
            "Install Whisper with pip install openai-whisper.",
        ),
        "python-pptx": _package_engine(
            "python-pptx", "python-pptx", "pptx",
            "Install python-pptx with pip install python-pptx.",
            quality="medium",
        ),
    }

    return {
        "offline": True,
        "engines": engines,
        "routes": _route_statuses(engines),
    }


ROUTE_REQUIREMENTS = {
    "/convert/to-pdf": {
        "label": "Files to PDF",
        "primary": ["libreoffice"],
        "fallback": "Basic Python renderer for images, text, and simple DOCX.",
    },
    "/convert/html-to-pdf": {
        "label": "HTML to PDF",
        "primary": ["libreoffice"],
        "fallback": "Basic PyMuPDF HTML renderer.",
    },
    "/spreadsheet/excel-to-pdf": {
        "label": "Excel to PDF",
        "primary": ["libreoffice"],
        "fallback": "Basic ReportLab table renderer.",
    },
    "/convert/pdf-to-word": {
        "label": "PDF to Word",
        "primary_any": ["pdf2docx", "marker", "pymupdf"],
        "fallback": "Visual-copy and flowing-text modes remain local fallbacks.",
    },
    "/convert/pdf-to-excel": {
        "label": "PDF to Excel",
        "primary_any": ["pdfplumber", "pymupdf"],
        "fallback": "PyMuPDF table detection.",
    },
    "/convert/pdf-to-pptx": {
        "label": "PDF to PowerPoint",
        "primary": ["libreoffice"],
        "fallback": "Image-per-slide PowerPoint output.",
    },
    "/convert/pptx-to-pdf": {
        "label": "PowerPoint to PDF",
        "primary": ["libreoffice"],
        "fallback": None,
    },
    "/convert/ocr-pdf": {
        "label": "OCR PDF",
        "primary": ["tesseract", "pytesseract"],
        "fallback": None,
    },
    "/image/svg-to-png": {
        "label": "SVG to PNG",
        "primary": [],
        "fallback": "Browser canvas renderer; server svglib renderer remains available as fallback.",
    },
    "/image/ocr": {
        "label": "Image OCR",
        "primary": ["tesseract", "pytesseract"],
        "fallback": None,
    },
    "/media/convert-audio": {"label": "Convert Audio", "primary": ["ffmpeg"], "fallback": None},
    "/media/convert-video": {"label": "Convert Video", "primary": ["ffmpeg"], "fallback": None},
    "/media/extract-audio": {"label": "Extract Audio", "primary": ["ffmpeg"], "fallback": None},
    "/media/trim": {"label": "Trim Media", "primary": ["ffmpeg"], "fallback": None},
    "/media/compress-video": {"label": "Compress Video", "primary": ["ffmpeg"], "fallback": None},
    "/media/video-to-gif": {"label": "Video to GIF", "primary": ["ffmpeg"], "fallback": None},
    "/media/burn-subtitles": {"label": "Burn Subtitles", "primary": ["ffmpeg"], "fallback": None},
    "/media/normalize-audio": {"label": "Normalize Audio", "primary": ["ffmpeg"], "fallback": None},
    "/media/transcribe": {"label": "Speech to Text", "primary": ["ffmpeg", "whisper"], "fallback": None},
}


def _route_statuses(engines: dict) -> dict:
    statuses = {}
    for endpoint, req in ROUTE_REQUIREMENTS.items():
        primary = req.get("primary", [])
        primary_any = req.get("primary_any", [])
        if primary:
            available = all(engines[e]["available"] for e in primary if e in engines)
        elif primary_any:
            available = any(engines[e]["available"] for e in primary_any if e in engines)
        else:
            available = True

        if available:
            quality = QUALITY_HIGH
            status = "High fidelity"
        elif req.get("fallback"):
            quality = QUALITY_BASIC
            status = "Basic fallback"
        else:
            quality = QUALITY_UNAVAILABLE
            status = "Unavailable"

        missing = [
            e for e in [*primary, *primary_any]
            if e in engines and not engines[e]["available"]
        ]
        statuses[endpoint] = {
            "label": req["label"],
            "quality": quality,
            "status": status,
            "required_engines": primary or primary_any,
            "missing_engines": missing,
            "fallback": req.get("fallback"),
        }
    return statuses


def set_conversion_metadata(response, engine: str, quality: str,
                            warnings: str | Iterable[str] | None = None):
    response.headers["X-Conversion-Engine"] = engine
    response.headers["X-Conversion-Quality"] = quality
    if warnings:
        if isinstance(warnings, str):
            warning_text = warnings
        else:
            warning_text = "; ".join(str(w) for w in warnings if w)
        if warning_text:
            response.headers["X-Fidelity-Warnings"] = warning_text[:1000]
    return response


def metadata_payload(data: dict | None = None, *, engine: str, quality: str,
                     warnings: Iterable[str] | str | None = None) -> dict:
    payload = dict(data or {})
    payload["engine"] = engine
    payload["quality"] = quality
    if warnings:
        payload["warnings"] = [warnings] if isinstance(warnings, str) else list(warnings)
    return payload


def soffice_convert(file_data: bytes, source_ext: str, target_ext: str = "pdf",
                    timeout: int = 180) -> bytes | None:
    """Run LibreOffice headless conversion with an isolated user profile."""
    soffice = find_soffice()
    if not soffice:
        return None

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        profile_dir = tmp_path / "lo-profile"
        profile_dir.mkdir(parents=True, exist_ok=True)
        in_path = tmp_path / f"input.{source_ext.lstrip('.').lower()}"
        in_path.write_bytes(file_data)

        profile_uri = profile_dir.resolve().as_uri()
        cmd = [
            soffice,
            f"-env:UserInstallation={profile_uri}",
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--norestore",
            "--convert-to",
            target_ext,
            "--outdir",
            str(tmp_path),
            str(in_path),
        ]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                timeout=timeout,
            )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None
        if proc.returncode != 0:
            return None

        candidates = [
            p for p in tmp_path.iterdir()
            if p.is_file() and p.suffix.lower() == f".{target_ext.lower()}"
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0].read_bytes()
