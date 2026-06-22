"""Runtime helpers for frozen (desktop) vs dev (web) installs."""

from __future__ import annotations

import sys


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def pip_or_bundle_hint(*, pip: str, bundled: bool = True) -> str:
    """User-facing hint when a Python package is missing."""
    if is_frozen():
        if bundled:
            return (
                "Komponen ini seharusnya sudah termasuk di aplikasi desktop. "
                "Perbarui ke versi terbaru atau laporkan bug."
            )
        return "Fitur ini tidak tersedia di build desktop (paket terlalu besar). Gunakan mode fallback."
    return f"Run: pip install {pip}"


def component_install_hint(component: str) -> str:
    """User-facing hint when a downloadable native component is missing."""
    if is_frozen():
        return f"Buka Help → Kelola Komponen untuk mengunduh {component}."
    return f"Install {component} locally and make sure it is on PATH."
