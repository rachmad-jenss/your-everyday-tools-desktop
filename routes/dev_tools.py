from datetime import datetime, timezone
from flask import Blueprint, render_template, request, jsonify

try:
    import sqlparse
    HAS_SQLPARSE = True
except ImportError:
    HAS_SQLPARSE = False

try:
    from croniter import croniter
    HAS_CRONITER = True
except ImportError:
    HAS_CRONITER = False

try:
    from jsonpath_ng.ext import parse as jsonpath_parse
    HAS_JSONPATH = True
except ImportError:
    try:
        from jsonpath_ng import parse as jsonpath_parse
        HAS_JSONPATH = True
    except ImportError:
        HAS_JSONPATH = False

import json as _json

bp = Blueprint("dev", __name__)


# ── Client-only pages ──────────────────────────────────

@bp.route("/uuid")
def uuid_generator():
    return render_template("tools/uuid_generator.html")


@bp.route("/jwt")
def jwt_decoder():
    return render_template("tools/jwt_decoder.html")


@bp.route("/user-agent")
def user_agent_parser():
    return render_template("tools/user_agent_parser.html")


@bp.route("/xml-format")
def xml_formatter():
    return render_template("tools/xml_formatter.html")


@bp.route("/html-format")
def html_formatter():
    return render_template("tools/html_formatter.html")


@bp.route("/css-format")
def css_formatter():
    return render_template("tools/css_formatter.html")


@bp.route("/js-format")
def js_formatter():
    return render_template("tools/js_formatter.html")


# ── Server-side helpers ────────────────────────────────

@bp.route("/sql-format", methods=["GET", "POST"])
def sql_format():
    if request.method == "GET":
        return render_template("tools/sql_formatter.html")

    if not HAS_SQLPARSE:
        return jsonify({"error": "sqlparse is not installed on the server."}), 500

    sql = request.form.get("sql", "").strip()
    if not sql:
        return jsonify({"error": "No SQL provided."}), 400

    keyword_case = request.form.get("keyword_case", "upper")
    indent = request.form.get("indent", "2")

    if keyword_case not in ("upper", "lower", "capitalize"):
        keyword_case = "upper"

    if indent == "tab":
        indent_width = 1
        use_tab = True
    else:
        try:
            indent_width = int(indent)
            if indent_width not in (2, 4):
                indent_width = 2
        except ValueError:
            indent_width = 2
        use_tab = False

    try:
        formatted = sqlparse.format(
            sql,
            keyword_case=keyword_case,
            identifier_case=None,
            reindent=True,
            indent_width=indent_width,
            strip_comments=False,
        )
        if use_tab:
            formatted = formatted.replace("  ", "\t")
        return jsonify({"text": formatted})
    except Exception as e:
        return jsonify({"error": f"Formatting failed: {e}"}), 400


@bp.route("/cron", methods=["GET", "POST"])
def cron_parser():
    if request.method == "GET":
        return render_template("tools/cron_parser.html")

    if not HAS_CRONITER:
        return jsonify({"error": "croniter is not installed on the server."}), 500

    expr = request.form.get("expr", "").strip()
    count_raw = request.form.get("count", "10")

    if not expr:
        return jsonify({"error": "No expression provided."}), 400

    try:
        count = max(1, min(50, int(count_raw)))
    except ValueError:
        count = 10

    if not croniter.is_valid(expr):
        return jsonify({"error": "Invalid cron expression."}), 400

    try:
        now = datetime.now(timezone.utc)
        it = croniter(expr, now)
        next_times = []
        for _ in range(count):
            ts = it.get_next(datetime)
            next_times.append(ts.strftime("%Y-%m-%d %H:%M:%S UTC"))

        description = _describe_cron(expr)
        return jsonify({"description": description, "next": next_times})
    except Exception as e:
        return jsonify({"error": f"Parse failed: {e}"}), 400


def _describe_cron(expr: str) -> str:
    parts = expr.split()
    if len(parts) not in (5, 6):
        return expr

    labels = ["Minute", "Hour", "Day of month", "Month", "Day of week"]
    if len(parts) == 6:
        labels = ["Second"] + labels

    lines = [f"Expression: {expr}"]
    for label, val in zip(labels, parts):
        meaning = _field_meaning(val)
        lines.append(f"{label:<14} {val:<10} → {meaning}")
    return "\n".join(lines)


def _field_meaning(val: str) -> str:
    if val == "*":
        return "every value"
    if val.startswith("*/"):
        return f"every {val[2:]}"
    if "-" in val and "/" not in val:
        return f"range {val}"
    if "," in val:
        return f"list: {val}"
    if "/" in val:
        return f"stepped: {val}"
    return f"exactly {val}"


@bp.route("/jsonpath", methods=["GET", "POST"])
def jsonpath_tester():
    if request.method == "GET":
        return render_template("tools/jsonpath_tester.html")

    if not HAS_JSONPATH:
        return jsonify({"error": "jsonpath-ng is not installed on the server."}), 500

    raw = request.form.get("data", "").strip()
    path = request.form.get("path", "").strip()

    if not raw:
        return jsonify({"error": "No JSON data provided."}), 400
    if not path:
        return jsonify({"error": "No JSONPath expression provided."}), 400

    try:
        data = _json.loads(raw)
    except _json.JSONDecodeError as e:
        return jsonify({"error": f"Invalid JSON: {e}"}), 400

    try:
        expr = jsonpath_parse(path)
    except Exception as e:
        return jsonify({"error": f"Invalid JSONPath: {e}"}), 400

    try:
        matches = [m.value for m in expr.find(data)]
        return jsonify({"count": len(matches), "matches": matches})
    except Exception as e:
        return jsonify({"error": f"Evaluation failed: {e}"}), 400
