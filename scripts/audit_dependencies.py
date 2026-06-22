"""Audit Python/native dependencies for desktop bundling policy.

Essential Python packages must be in requirements-core.txt and collected by
PyInstaller. Large optional packages stay in requirements-optional.txt.
Native binaries (FFmpeg, Tesseract) are downloaded via the Electron installer.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ESSENTIAL_IMPORTS = {
    "fitz": "PyMuPDF",
    "pdf2docx": "pdf2docx",
    "cv2": "opencv-python-headless (pdf2docx)",
    "pdfplumber": "pdfplumber",
    "pyzbar": "pyzbar",
    "pillow_heif": "pillow-heif",
    "pytesseract": "pytesseract",
    "ezdxf": "ezdxf",
    "matplotlib": "matplotlib",
    "pptx": "python-pptx",
    "cryptography": "cryptography",
}

OPTIONAL_IMPORTS = {
    "rembg": "rembg[cpu]",
    "onnxruntime": "rembg[cpu]",
    "whisper": "openai-whisper",
    "marker": "marker-pdf",
}

NATIVE_COMPONENTS = {
    "ffmpeg": "Electron downloader (~193 MB)",
    "tesseract": "Electron downloader (~182 MB)",
    "libreoffice": "User install / future optional download",
}


def _read_requirements(name: str) -> set[str]:
    path = ROOT / name
    if not path.is_file():
        return set()
    names: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-r"):
            continue
        pkg = line.split(";")[0].strip().split("[")[0].strip().lower()
        names.add(pkg)
    return names


def main() -> int:
    core = _read_requirements("requirements-core.txt")
    optional = _read_requirements("requirements-optional.txt")

    print("=== Essential Python imports ===")
    missing_runtime: list[str] = []
    for mod, label in ESSENTIAL_IMPORTS.items():
        ok = importlib.util.find_spec(mod) is not None
        status = "OK" if ok else "MISSING"
        print(f"  [{status}] {mod} ({label})")
        if not ok:
            missing_runtime.append(mod)

    print("\n=== Optional Python imports (not bundled in desktop) ===")
    for mod, label in OPTIONAL_IMPORTS.items():
        ok = importlib.util.find_spec(mod) is not None
        print(f"  [{'OK' if ok else '—'}] {mod} ({label})")

    print("\n=== requirements-core.txt spot check ===")
    expected_in_core = {
        "pdf2docx", "pdfplumber", "pyzbar", "pillow-heif", "pytesseract",
        "ezdxf", "matplotlib", "opencv-python-headless", "pymupdf",
    }
    for pkg in sorted(expected_in_core):
        found = pkg in core or pkg.replace("-", "_") in core
        print(f"  [{'OK' if found else 'MISSING'}] {pkg}")

    print("\n=== Native components (Electron downloader) ===")
    for name, note in NATIVE_COMPONENTS.items():
        print(f"  • {name}: {note}")

    if missing_runtime:
        print(f"\nFAIL: {len(missing_runtime)} essential import(s) missing in this environment.")
        return 1

    print("\nAll essential imports available in this environment.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
