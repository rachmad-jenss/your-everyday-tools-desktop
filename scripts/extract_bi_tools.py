import re
from pathlib import Path

css = Path("static/css/icons.css").read_text(encoding="utf-8")
m = re.search(r"\.bi-tools::before\{content:\"\\([^\"]+)\"", css)
print(m.group(1) if m else "not found")
