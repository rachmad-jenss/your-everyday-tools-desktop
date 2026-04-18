from flask import Blueprint, render_template

bp = Blueprint("text", __name__)


@bp.route("/json-formatter")
def json_formatter():
    return render_template("tools/json_formatter.html")


@bp.route("/csv-json")
def csv_json():
    return render_template("tools/csv_json.html")


@bp.route("/base64")
def base64_page():
    return render_template("tools/base64.html")


@bp.route("/url-encode")
def url_encode():
    return render_template("tools/url_encode.html")


@bp.route("/word-counter")
def word_counter():
    return render_template("tools/word_counter.html")


@bp.route("/markdown")
def markdown_preview():
    return render_template("tools/markdown_preview.html")
