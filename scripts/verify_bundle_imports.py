"""Verify PyInstaller output contains essential bundled modules."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist" / "YourEverydayTools" / "_internal"

# File/dir name fragments that must exist after a successful desktop build.
REQUIRED_FRAGMENTS = [
    "pdf2docx",
    "pdfplumber",
    "cv2",
    "pyzbar",
    "matplotlib",
]


def main() -> int:
    if not DIST.is_dir():
        print(f"FAIL: bundle directory not found: {DIST}")
        print("Run: pyinstaller your-everyday-tools.spec --clean --noconfirm")
        return 1

    names = {p.name.lower() for p in DIST.iterdir()}
    all_paths = " ".join(str(p).lower() for p in DIST.rglob("*"))

    missing = []
    for frag in REQUIRED_FRAGMENTS:
        if frag.lower() not in names and frag.lower() not in all_paths:
            missing.append(frag)

    if missing:
        print("FAIL: bundle missing required modules:")
        for m in missing:
            print(f"  - {m}")
        return 1

    print(f"OK: bundle at {DIST} contains all required modules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
