from flask import Blueprint, render_template

bp = Blueprint("security", __name__)


@bp.route("/password-generator")
def password_generator():
    return render_template("tools/password_generator.html")


@bp.route("/hash-generator")
def hash_generator():
    return render_template("tools/hash_generator.html")
