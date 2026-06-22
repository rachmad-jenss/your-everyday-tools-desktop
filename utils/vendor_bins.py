"""Shared helpers for locating vendor-downloaded native binaries."""

from __future__ import annotations

import os
import sys


def _app_base() -> str:
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def vendor_subdir(name: str) -> str:
    return os.path.join(_app_base(), "vendor", name)


def _exe_name(base: str) -> str:
    return f"{base}.exe" if sys.platform == "win32" else base


def find_ffmpeg() -> tuple[str | None, str | None]:
    vendor_dir = vendor_subdir("ffmpeg")
    ffmpeg_path = os.path.join(vendor_dir, _exe_name("ffmpeg"))
    ffprobe_path = os.path.join(vendor_dir, _exe_name("ffprobe"))
    if os.path.isfile(ffmpeg_path):
        ffprobe = ffprobe_path if os.path.isfile(ffprobe_path) else None
        return ffmpeg_path, ffprobe
    return None, None


def find_tesseract() -> str | None:
    vendor_dir = vendor_subdir("tesseract")
    tess_path = os.path.join(vendor_dir, _exe_name("tesseract"))
    return tess_path if os.path.isfile(tess_path) else None


def configure_pytesseract() -> bool:
    """Point pytesseract at the vendor Tesseract binary when present."""
    try:
        import pytesseract
    except ImportError:
        return False

    tess = find_tesseract()
    if not tess:
        return False

    pytesseract.pytesseract.tesseract_cmd = tess
    tessdata = os.path.join(os.path.dirname(tess), "tessdata")
    if os.path.isdir(tessdata):
        os.environ.setdefault("TESSDATA_PREFIX", tessdata)
    return True
