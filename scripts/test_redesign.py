"""Smoke tests for Clean Workspace UI redesign."""
import json
import re
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:5000"

PAGES = [
    ("/", ["dashboard-greeting", "category-cards-grid", "search-palette", "__TOOL_INDEX__"]),
    ("/tools", ["all-tools-search", "tools-grid"]),
    ("/favorites", ["favorites-grid"]),
    ("/recent", ["recent-tools-grid"]),
    ("/settings", ["settings-page", "clear-local-data"]),
    ("/text/json-formatter", ["tool-workspace", "json-input"]),
    ("/pdf/merge", ["tool-workspace", "upload-zone", "workspace-output-panel"]),
    ("/convert/pdf-to-word", ["tool-workspace", "sidebar-fav-btn", "data-favorite"]),
    ("/calc/calculator", ["single-column", "calc-result", "grid-cols-4"]),
]

STATIC_ASSETS = [
    "/static/css/app.css",
    "/static/js/main.js",
    "/static/js/favorites.js",
    "/static/js/recent-activity.js",
    "/static/js/search-palette.js",
]


def fetch(path):
    req = urllib.request.Request(BASE + path, headers={"User-Agent": "redesign-test"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, resp.read().decode("utf-8", errors="replace")


def main():
    passed = 0
    failed = []

    for path, needles in PAGES:
        try:
            status, html = fetch(path)
            if status != 200:
                failed.append((path, f"HTTP {status}"))
                continue
            missing = [n for n in needles if n not in html]
            if missing:
                failed.append((path, f"missing: {missing}"))
            else:
                passed += 1
                print(f"PASS  {path}")
        except Exception as e:
            failed.append((path, str(e)))
            print(f"FAIL  {path}: {e}")

    for path in STATIC_ASSETS:
        try:
            status, body = fetch(path)
            if status == 200 and len(body) > 100:
                passed += 1
                print(f"PASS  {path}")
            else:
                failed.append((path, f"HTTP {status} or empty"))
        except Exception as e:
            failed.append((path, str(e)))

    # tool_index JSON sanity
    try:
        _, html = fetch("/")
        m = re.search(r"window\.__TOOL_INDEX__\s*=\s*(\[.*?\]);", html, re.S)
        if not m:
            failed.append(("tool_index", "not found in home page"))
        else:
            tools = json.loads(m.group(1))
            if len(tools) < 90:
                failed.append(("tool_index", f"only {len(tools)} tools"))
            else:
                passed += 1
                print(f"PASS  tool_index ({len(tools)} tools)")
    except Exception as e:
        failed.append(("tool_index", str(e)))

    # capabilities endpoint
    try:
        status, body = fetch("/capabilities")
        data = json.loads(body)
        if "engines" in data and "ffmpeg" in data["engines"]:
            passed += 1
            print("PASS  /capabilities")
        else:
            failed.append(("/capabilities", "invalid shape"))
    except Exception as e:
        failed.append(("/capabilities", str(e)))

    print(f"\n{passed} passed, {len(failed)} failed")
    for path, err in failed:
        print(f"  FAIL {path}: {err}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
