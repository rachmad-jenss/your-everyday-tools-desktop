import os
import re

ROOT = os.path.join(os.path.dirname(__file__), "..", "templates", "tools")


def migrate_single(path):
    with open(path, encoding="utf-8") as f:
        content = f.read()
    title_m = re.search(r"\{% block title %\}(.+?) - ", content)
    title = title_m.group(1).strip() if title_m else "Tool"
    desc_m = re.search(r'<div class="tool-header">\s*<h1>[^<]*</h1>\s*<p>([^<]*)</p>', content, re.S)
    desc = desc_m.group(1).strip() if desc_m else ""
    scripts_m = re.search(r"\{% block scripts %\}(.*?)\{% endblock %\}", content, re.S)
    scripts = scripts_m.group(1).strip() if scripts_m else ""
    body_m = re.search(r"\{% block content %\}(.*?)\{% endblock %\}", content, re.S)
    body = body_m.group(1).strip() if body_m else ""
    body = re.sub(r'^<div class="client-tool">\s*', "", body)
    body = re.sub(r'<div class="tool-header">.*?</div>\s*', "", body, count=1, flags=re.S)
    body = re.sub(r"\s*</div>\s*$", "", body)
    title = title.replace('"', '\\"')
    desc = desc.replace('"', '\\"')
    return f'''{{% extends "layouts/tool_workspace.html" %}}
{{% set title = "{title}" %}}
{{% set description = "{desc}" %}}
{{% set workspace_single = true %}}

{{% block workspace_input %}}
{body}
{{% endblock %}}

{{% block scripts %}}
{scripts}
{{% endblock %}}
'''


def migrate_formatter(orig, input_id, output_id, input_ph, btn1, btn2, fn1, fn2):
    title_m = re.search(r"\{% block title %\}(.+?) - ", orig)
    title = title_m.group(1).strip().replace('"', '\\"') if title_m else "Formatter"
    desc_m = re.search(r'<p>([^<]*)</p>', orig)
    desc = desc_m.group(1).strip().replace('"', '\\"') if desc_m else ""
    scripts_m = re.search(r"\{% block scripts %\}(.*?)\{% endblock %\}", orig, re.S)
    scripts = scripts_m.group(1).strip() if scripts_m else ""
    return f'''{{% extends "layouts/tool_workspace.html" %}}
{{% set title = "{title}" %}}
{{% set description = "{desc}" %}}

{{% block workspace_input %}}
<div style="display:flex;gap:.5rem;margin-bottom:.75rem;">
    <button type="button" class="btn btn-secondary btn-small" onclick="{fn1}()">{btn1}</button>
    <button type="button" class="btn btn-secondary btn-small" onclick="{fn2}()">{btn2}</button>
</div>
<textarea id="{input_id}" placeholder="{input_ph}" style="min-height:280px;width:100%;"></textarea>
{{% endblock %}}

{{% block workspace_output_toolbar %}}
<button type="button" class="btn btn-small" onclick="copyOutput()"><i class="bi bi-clipboard"></i> Copy</button>
{{% endblock %}}

{{% block workspace_output %}}
<pre id="{output_id}" style="min-height:280px;margin:0;white-space:pre-wrap;word-break:break-word;font-family:Consolas,Monaco,monospace;font-size:.85rem;"></pre>
{{% endblock %}}

{{% block scripts %}}
{scripts}
{{% endblock %}}
'''


for name in ["jwt_decoder.html", "cron_parser.html"]:
    path = os.path.join(ROOT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(migrate_single(path))
    print("single", name)

formatters = [
    ("css_formatter.html", "css-input", "css-output", ".example { color: red; }", "Beautify", "Minify", "formatCSS", "minifyCSS"),
    ("html_formatter.html", "html-input", "html-output", "<div>Hello</div>", "Beautify", "Minify", "formatHTML", "minifyHTML"),
    ("js_formatter.html", "js-input", "js-output", "function hello(){}", "Beautify", "Minify", "formatJS", "minifyJS"),
    ("xml_formatter.html", "xml-input", "xml-output", "<root></root>", "Beautify", "Minify", "formatXML", "minifyXML"),
]

for args in formatters:
    path = os.path.join(ROOT, args[0])
    with open(path, encoding="utf-8") as f:
        orig = f.read()
    with open(path, "w", encoding="utf-8") as f:
        f.write(migrate_formatter(orig, *args[1:]))
    print("formatter", args[0])
