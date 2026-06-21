"""Extract bi-tools SVG path from bundled bootstrap-icons font."""
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

ROOT = Path(__file__).resolve().parents[1]
font_path = ROOT / "static" / "fonts" / "bootstrap-icons.woff"
out_path = ROOT / "static" / "tools-icon-path.txt"

font = TTFont(font_path)
cmap = font.getBestCmap()
code = 0xF5DB
glyph_name = cmap.get(code)
if not glyph_name:
    raise SystemExit(f"Glyph for U+{code:04X} not found")

glyph_set = font.getGlyphSet()
pen = SVGPathPen(glyph_set)
glyph_set[glyph_name].draw(pen)
path = pen.getCommands()
# SVGPathPen getCommands returns path d string via getValue in newer API
if hasattr(pen, "getValue"):
    path = pen.getValue()

out_path.write_text(path, encoding="utf-8")
print(glyph_name)
print(path[:120] + ("..." if len(path) > 120 else ""))
