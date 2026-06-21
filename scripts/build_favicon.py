"""Build favicon.svg using exact bi-tools glyph from bundled font."""
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

ROOT = Path(__file__).resolve().parents[1]
font_path = ROOT / "static" / "fonts" / "bootstrap-icons.woff"
favicon_path = ROOT / "static" / "favicon.svg"
path_cache = ROOT / "static" / "tools-icon-path.txt"


def glyph_path_d() -> str:
    if path_cache.exists():
        return path_cache.read_text(encoding="utf-8").strip()
    font = TTFont(font_path)
    cmap = font.getBestCmap()
    glyph_name = cmap[0xF5DB]
    glyph_set = font.getGlyphSet()
    pen = SVGPathPen(glyph_set)
    glyph_set[glyph_name].draw(pen)
    # fontTools 4.x: serialize path commands to SVG d
    parts = []
    for cmd in pen.getCommands():
        op = cmd[0]
        pts = cmd[1]
        if op == "moveTo":
            parts.append(f"M{pts[0]} {pts[1]}")
        elif op == "lineTo":
            parts.append(f"L{pts[0]} {pts[1]}")
        elif op == "curveTo":
            parts.append(
                f"C{pts[0]} {pts[1]} {pts[2]} {pts[3]} {pts[4]} {pts[5]}"
            )
        elif op == "qCurveTo":
            parts.append("Q" + " ".join(f"{p[0]} {p[1]}" for p in pts))
        elif op == "closePath":
            parts.append("Z")
    d = "".join(parts)
    path_cache.write_text(d, encoding="utf-8")
    return d


font = TTFont(font_path)
upem = font["head"].unitsPerEm
d = glyph_path_d()

favicon = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="none">
  <rect width="32" height="32" rx="8" fill="#4f46e5"/>
  <svg x="8" y="8" width="16" height="16" viewBox="0 0 {upem} {upem}">
    <g transform="scale(1 -1) translate(0 -{upem})" fill="#ffffff">
      <path d="{d}"/>
    </g>
  </svg>
</svg>
"""

favicon_path.write_text(favicon, encoding="utf-8")
print(f"Wrote {favicon_path}")
