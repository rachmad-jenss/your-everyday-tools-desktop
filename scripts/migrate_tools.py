import glob
import os
import re


def extract_block(content, block_name):
    m = re.search(rf"\{{% block {block_name} %\}}(.*?)\{{% endblock %\}}", content, re.S)
    return m.group(1).strip() if m else ""


def extract_title(content):
    m = re.search(r"\{% block title %\}(.+?) - ", content)
    return m.group(1).strip() if m else "Tool"


def extract_tool_header(content):
    m = re.search(
        r'<div class="tool-header">\s*<h1>([^<]*)</h1>\s*<p>([^<]*)</p>\s*</div>',
        content,
        re.S,
    )
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return extract_title(content), ""


def strip_pane_inner(pane_html):
    pane_html = re.sub(r'^\s*<div class="pane">\s*', "", pane_html)
    pane_html = re.sub(r'\s*</div>\s*$', "", pane_html)
    pane_html = re.sub(r'<div class="pane-header">.*?</div>\s*', "", pane_html, flags=re.S)
    pane_html = re.sub(r'^\s*<div class="pane-body">\s*', "", pane_html)
    pane_html = re.sub(r'\s*</div>\s*$', "", pane_html)
    return pane_html.strip()


def extract_split_panes(content):
    m = re.search(r'<div class="split-pane">(.*?)</div>\s*(?:</div>\s*)?(?:<div id=|\{% endblock|\{% block scripts)', content, re.S)
    if not m:
        return None
    inner = m.group(1)
    parts = inner.split('<div class="pane">')
    parts = [p for p in parts if p.strip()]
    if len(parts) < 2:
        return None
    return strip_pane_inner(parts[0]), strip_pane_inner(parts[1])


def extract_body_content(content):
    block = extract_block(content, "content")
    block = re.sub(r'^\s*<div class="client-tool"[^>]*>\s*', "", block)
    block = re.sub(r'<div class="tool-header">.*?</div>\s*', "", block, count=1, flags=re.S)
    block = re.sub(r'\s*</div>\s*$', "", block)
    return block.strip()


def migrate(path):
    with open(path, encoding="utf-8") as f:
        content = f.read()

    title, desc = extract_tool_header(content)
    title = title.replace('"', '\\"')
    desc = desc.replace('"', '\\"')
    scripts = extract_block(content, "scripts")
    scripts_block = f"{{% block scripts %}}\n{scripts}\n{{% endblock %}}" if scripts else ""

    panes = extract_split_panes(content)
    if panes:
        left, right = panes
        extra = ""
        em = re.search(r'</div>\s*(<div id="[^"]+"[^>]*>.*?</div>)\s*(?:\{% endblock|\{% block scripts)', content, re.S)
        if em:
            extra = "\n" + em.group(1)
        return f'''{{% extends "layouts/tool_workspace.html" %}}
{{% set title = "{title}" %}}
{{% set description = "{desc}" %}}

{{% block workspace_input %}}
{left}
{{% endblock %}}

{{% block workspace_output %}}
{right}{extra}
{{% endblock %}}

{scripts_block}
'''

    body = extract_body_content(content)
    return f'''{{% extends "layouts/tool_workspace.html" %}}
{{% set title = "{title}" %}}
{{% set description = "{desc}" %}}
{{% set workspace_single = true %}}

{{% block workspace_input %}}
{body}
{{% endblock %}}

{scripts_block}
'''


def main():
    base = os.path.join(os.path.dirname(__file__), "..", "templates", "tools")
    for path in sorted(glob.glob(os.path.join(base, "*.html"))):
        out = migrate(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(out)
        print("migrated", os.path.basename(path))


if __name__ == "__main__":
    main()
