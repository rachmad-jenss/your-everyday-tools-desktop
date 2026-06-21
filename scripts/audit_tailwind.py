#!/usr/bin/env python3
"""Audit Tailwind utility migration status."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TW = re.compile(
    r"\b(flex|grid|rounded-|bg-|text-|px-|py-|gap-|border-|shadow-|max-w-|inline-flex|min-h-11)\b"
)

def audit_html(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "tw": len(TW.findall(text)),
        "btn": len(re.findall(r'class="[^"]*\bbtn\b', text)),
        "form_group": text.count("form-group"),
        "inline_style": len(re.findall(r'style="', text)),
        "palette": "search-palette" in text or "palette-dialog" in text,
    }


def main():
    html_files = sorted(ROOT.glob("templates/**/*.html"))
    # dedupe windows paths
    seen = set()
    unique = []
    for f in html_files:
        key = str(f).lower()
        if key not in seen:
            seen.add(key)
            unique.append(f)

    shell = []
    pages = []
    components = []
    tools = []

    for f in unique:
        rel = str(f.relative_to(ROOT / "templates")).replace("\\", "/")
        data = audit_html(f)
        if rel.startswith("tools/"):
            tools.append(data)
        elif rel.startswith("components/"):
            components.append(data)
        elif rel in ("base.html", "upload_tool.html") or rel.startswith("layouts/"):
            shell.append(data)
        else:
            pages.append(data)

    def bucket(items):
        full = [x for x in items if x["tw"] >= 12 and x["btn"] == 0 and not x["palette"]]
        hybrid = [x for x in items if x not in full and x["tw"] >= 5]
        legacy = [x for x in items if x not in full and x not in hybrid]
        return full, hybrid, legacy

    print("TAILWIND MIGRATION AUDIT")
    print("=" * 60)

    for label, items in [
        ("Shell & layout", shell),
        ("Pages (dashboard/browse)", pages),
        ("Shared components", components),
        ("Tool templates", tools),
    ]:
        full, hybrid, legacy = bucket(items)
        print(f"\n{label}: {len(items)} files")
        print(f"  Done (utility-first): {len(full)}")
        print(f"  Hybrid: {len(hybrid)}")
        print(f"  Legacy: {len(legacy)}")
        for x in full:
            print(f"    [OK] {x['path']}")
        for x in hybrid:
            print(
                f"    [~~] {x['path']} (tw={x['tw']}, btn={x['btn']}, form={x['form_group']}, inline={x['inline_style']})"
            )
        for x in legacy:
            print(
                f"    [--] {x['path']} (tw={x['tw']}, btn={x['btn']}, form={x['form_group']}, inline={x['inline_style']})"
            )

    total = len(unique)
    all_full, all_hybrid, all_legacy = bucket([audit_html(f) for f in unique])
    # recount properly
    audited = [audit_html(f) for f in unique]
    done = sum(1 for x in audited if x["tw"] >= 12 and x["btn"] == 0 and not x["palette"])
    hybrid_n = sum(
        1
        for x in audited
        if not (x["tw"] >= 12 and x["btn"] == 0 and not x["palette"]) and x["tw"] >= 5
    )
    legacy_n = total - done - hybrid_n

    btn_total = sum(x["btn"] for x in audited)
    form_total = sum(x["form_group"] for x in audited)
    inline_total = sum(x["inline_style"] for x in audited)

    print("\n" + "=" * 60)
    print(f"TOTAL templates: {total}")
    print(f"  Utility-first: {done} ({100*done/total:.0f}%)")
    print(f"  Hybrid:        {hybrid_n} ({100*hybrid_n/total:.0f}%)")
    print(f"  Legacy:        {legacy_n} ({100*legacy_n/total:.0f}%)")
    print(f"\nRemaining legacy signals in templates:")
    print(f"  .btn usages:        {btn_total}")
    print(f"  .form-group usages: {form_total}")
    print(f"  inline style=:      {inline_total}")

    js_files = sorted(ROOT.glob("static/js/*.js"))
    print("\nJS dynamic UI:")
    for f in js_files:
        t = f.read_text(encoding="utf-8")
        tw_n = len(TW.findall(t))
        legacy = {
            "toast": "toast toast-" in t,
            "palette": "palette-result" in t,
            "inline-status": "inline-status" in t,
            "capability": "capability-status" in t,
            "breadcrumbs": 'class="sep"' in t,
            "result-meta": "result-meta" in t,
        }
        migrated = {
            "TW object": "const TW" in t,
            "file-list tw": "file-list-card mt-3" in t,
            "sidebar tw": "sidebar-mini-link flex" in t,
        }
        print(f"  {f.name}: tw~{tw_n}, legacy={sum(legacy.values())}, migrated={sum(migrated.values())}")


if __name__ == "__main__":
    main()
