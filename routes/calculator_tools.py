from flask import Blueprint, render_template

bp = Blueprint("calc", __name__)


@bp.route("/calculator")
def calculator():
    return render_template("tools/calculator.html")


@bp.route("/unit-converter")
def unit_converter():
    return render_template("tools/unit_converter.html")


@bp.route("/color-converter")
def color_converter():
    return render_template("tools/color_converter.html")


@bp.route("/percentage")
def percentage():
    return render_template("tools/percentage_calc.html")


@bp.route("/date")
def date_calc():
    return render_template("tools/date_calc.html")
