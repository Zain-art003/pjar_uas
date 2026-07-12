from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.models import User, db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("files.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("Semua field wajib diisi.", "error")
            return render_template("register.html")

        if password != confirm:
            flash("Konfirmasi password tidak cocok.", "error")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password minimal 8 karakter.", "error")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("Username sudah dipakai.", "error")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("Email sudah terdaftar.", "error")
            return render_template("register.html")

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registrasi berhasil, silakan login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("files.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash("Username atau password salah.", "error")
            return render_template("login.html")

        login_user(user)
        flash(f"Selamat datang, {user.username}!", "success")
        next_page = request.args.get("next")
        return redirect(next_page or url_for("files.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Anda telah logout.", "success")
    return redirect(url_for("auth.login"))
