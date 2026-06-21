"""Verify all tool routes return 200 and use new layout."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, TOOL_CATEGORIES

errors = []
ok = 0

with app.test_client() as c:
    for cat in TOOL_CATEGORIES:
        for tool in cat["tools"]:
            path = f"/{cat['id']}/{tool['id']}"
            r = c.get(path)
            html = r.data.decode("utf-8", errors="replace")
            if r.status_code != 200:
                errors.append((path, f"HTTP {r.status_code}"))
            elif "tool-workspace" not in html and "layouts/tool_workspace" not in html:
                errors.append((path, "missing tool-workspace"))
            else:
                ok += 1

print(f"Tool pages: {ok} OK, {len(errors)} issues")
for e in errors:
    print(" ", e)
