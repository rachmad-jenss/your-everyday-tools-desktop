"""Upload workspace + conversion smoke tests (no browser required)."""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Valid 1x1 PNG (base64)
TINY_PNG = __import__("base64").b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

MAIN_JS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static",
    "js",
    "main.js",
)

UPLOAD_MARKERS = [
    "upload-add-more",
    "preview-download-btn",
    "workspace-preview-grid",
    "const blob = await resp.blob()",
    "revokeInputPreviewUrls",
    "outputResultUrl",
]

errors = []


def check_main_js():
    with open(MAIN_JS, encoding="utf-8") as f:
        src = f.read()
    for marker in UPLOAD_MARKERS:
        if marker not in src:
            errors.append((MAIN_JS, f"missing marker: {marker}"))
    # blob must be defined before createObjectURL in the submit handler
    block = re.search(
        r"} else \{\s*const blob = await resp\.blob\(\);[\s\S]*?URL\.createObjectURL\(blob\)",
        src,
    )
    if not block:
        errors.append((MAIN_JS, "blob/createObjectURL order regression"))


def check_upload_pages():
    ok = 0
    pages = ["/convert/to-pdf", "/pdf/merge"]
    with app.test_client() as c:
        for path in pages:
            r = c.get(path)
            html = r.data.decode("utf-8", errors="replace")
            if r.status_code != 200:
                errors.append((path, f"HTTP {r.status_code}"))
                continue
            missing = [m for m in UPLOAD_MARKERS[:3] if m not in html]
            if missing:
                errors.append((path, f"missing html: {missing}"))
            else:
                ok += 1
    return ok


def check_to_pdf_post():
    with app.test_client() as c:
        data = {
            "files": (io.BytesIO(TINY_PNG), "test.png"),
        }
        r = c.post(
            "/convert/to-pdf",
            data=data,
            content_type="multipart/form-data",
        )
        ct = r.headers.get("Content-Type", "")
        if r.status_code != 200:
            errors.append(("/convert/to-pdf POST", f"HTTP {r.status_code}: {r.data[:200]}"))
            return False
        if "application/pdf" not in ct:
            errors.append(("/convert/to-pdf POST", f"wrong content-type: {ct}"))
            return False
        if len(r.data) < 100:
            errors.append(("/convert/to-pdf POST", "pdf too small"))
            return False
        if not r.data.startswith(b"%PDF"):
            errors.append(("/convert/to-pdf POST", "not a pdf"))
            return False
        return True


def main():
    check_main_js()
    pages_ok = check_upload_pages()
    pdf_ok = check_to_pdf_post()

    print(f"Upload pages: {pages_ok} OK")
    print(f"to-pdf POST: {'OK' if pdf_ok else 'FAIL'}")
    print(f"main.js checks: {'OK' if not any(e[0] == MAIN_JS for e in errors) else 'FAIL'}")

    if errors:
        print(f"\n{len(errors)} issue(s):")
        for e in errors:
            print(" ", e)
        sys.exit(1)

    print("\nAll upload workspace tests passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
