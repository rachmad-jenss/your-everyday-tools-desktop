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


@bp.route("/case-converter")
def case_converter():
    return render_template("tools/case_converter.html")


@bp.route("/text-diff")
def text_diff():
    return render_template("tools/text_diff.html")


@bp.route("/regex-tester")
def regex_tester():
    return render_template("tools/regex_tester.html")


@bp.route("/slug-generator")
def slug_generator():
    return render_template("tools/slug_generator.html")


@bp.route("/json-yaml")
def json_yaml():
    return render_template("tools/json_yaml.html")


@bp.route("/lorem-ipsum")
def lorem_ipsum():
    return render_template("tools/lorem_ipsum.html")
