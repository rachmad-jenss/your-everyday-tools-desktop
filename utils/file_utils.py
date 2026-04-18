import io
import zipfile


def make_zip(files: list[tuple[str, bytes]]) -> io.BytesIO:
    """Create a ZIP file in memory from a list of (filename, data) tuples."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files:
            zf.writestr(name, data)
    buf.seek(0)
    return buf


def allowed_file(filename: str, extensions: set[str]) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in extensions
