from flask import Blueprint, redirect, render_template, url_for

admin_bp = Blueprint("admin_ui", __name__)

@admin_bp.get("/")
def index_redirect():
    return redirect(url_for("admin_ui.admin_dashboard"))


@admin_bp.get("/admin")
def admin_dashboard():
    return render_template("admin.html")
