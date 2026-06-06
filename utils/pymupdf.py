"""PyMuPDF import guard.

PyMuPDF's import name is `fitz`, but there is also an unrelated PyPI package
named `fitz` that imports `frontend`/Starlette and crashes at startup. Keep the
diagnostic in one place so users get actionable setup instructions.
"""


def import_pymupdf():
    try:
        import fitz  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "PyMuPDF is required, but Python could not import the correct 'fitz' module. "
            "Use the project virtual environment (run run.bat on Windows), or fix this "
            "Python environment with: python -m pip uninstall -y fitz frontend && "
            "python -m pip install --upgrade PyMuPDF"
        ) from exc

    if not hasattr(fitz, "open") or not hasattr(fitz, "Document"):
        path = getattr(fitz, "__file__", "unknown location")
        raise RuntimeError(
            "Python imported a package named 'fitz', but it is not PyMuPDF "
            f"({path}). Uninstall the wrong package and install PyMuPDF: "
            "python -m pip uninstall -y fitz frontend && "
            "python -m pip install --upgrade PyMuPDF"
        )
    return fitz
