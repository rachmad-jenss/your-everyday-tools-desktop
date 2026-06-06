from utils.capabilities import QUALITY_HIGH, get_capabilities


def test_capabilities_shape():
    data = get_capabilities()

    assert data["offline"] is True
    assert "engines" in data
    assert "routes" in data
    assert "libreoffice" in data["engines"]
    assert data["routes"]["/spreadsheet/excel-to-pdf"]["label"] == "Excel to PDF"
    assert data["routes"]["/image/svg-to-png"]["quality"] == QUALITY_HIGH
