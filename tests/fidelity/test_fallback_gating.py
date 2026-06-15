import io

import pytest


def _load_app_or_skip():
    try:
        from app import app
    except ImportError as exc:
        pytest.skip(f"App dependencies are not installed: {exc}")
    return app


def test_docx_to_pdf_requires_explicit_basic_fallback(monkeypatch):
    app = _load_app_or_skip()
    from routes import convert_tools

    monkeypatch.setattr(convert_tools, "_soffice_convert", lambda *args, **kwargs: None)

    with app.test_client() as client:
        resp = client.post(
            "/convert/to-pdf",
            data={"files": (io.BytesIO(b"not-a-real-docx"), "sample.docx")},
            content_type="multipart/form-data",
        )

    assert resp.status_code == 400
    assert b"Allow basic Python fallback" in resp.data


def test_excel_to_pdf_requires_explicit_basic_fallback(monkeypatch):
    app = _load_app_or_skip()
    from routes import spreadsheet_tools

    monkeypatch.setattr(spreadsheet_tools, "soffice_convert", lambda *args, **kwargs: None)

    with app.test_client() as client:
        resp = client.post(
            "/spreadsheet/excel-to-pdf",
            data={"files": (io.BytesIO(b"not-a-real-xlsx"), "sample.xlsx")},
            content_type="multipart/form-data",
        )

    assert resp.status_code == 400
    assert b"Allow basic table fallback" in resp.data


def test_excel_to_pdf_high_fidelity_metadata(monkeypatch):
    app = _load_app_or_skip()
    from routes import spreadsheet_tools

    monkeypatch.setattr(spreadsheet_tools, "soffice_convert", lambda *args, **kwargs: b"%PDF-1.4\n%%EOF\n")

    with app.test_client() as client:
        resp = client.post(
            "/spreadsheet/excel-to-pdf",
            data={"files": (io.BytesIO(b"fake-xlsx"), "sample.xlsx")},
            content_type="multipart/form-data",
        )

    assert resp.status_code == 200
    assert resp.headers["X-Conversion-Engine"] == "libreoffice"
    assert resp.headers["X-Conversion-Quality"] == "high"


def test_capabilities_endpoint_returns_routes():
    app = _load_app_or_skip()

    with app.test_client() as client:
        resp = client.get("/capabilities")

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["offline"] is True
    assert "/convert/to-pdf" in data["routes"]
