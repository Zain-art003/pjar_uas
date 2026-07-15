from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.mailer import send_email
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

        success, email_status = send_email(
            email,
            "Registrasi berhasil",
            f"Halo {username},\n\nAkun Anda berhasil dibuat di webapp. Silakan login menggunakan username dan password Anda.",
        )
        if success:
            flash("Registrasi berhasil, silakan login. Notifikasi email telah dikirim.", "success")
        else:
            flash("Registrasi berhasil, silakan login. Namun email notifikasi gagal dikirim: " + email_status, "warning")

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
        success, email_status = send_email(
            user.email,
            "Login berhasil",
            f"Halo {user.username},\n\nKami mencatat login berhasil ke akun Anda pada {user.created_at.strftime('%d %B %Y %H:%M:%S') if user.created_at else 'waktu sekarang'}.",
        )
        if success:
            flash(f"Selamat datang, {user.username}! Notifikasi email telah dikirim.", "success")
        else:
            flash(f"Selamat datang, {user.username}! Login berhasil, namun notifikasi email gagal dikirim: {email_status}", "warning")
        next_page = request.args.get("next")
        return redirect(next_page or url_for("files.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Anda telah logout.", "success")
    return redirect(url_for("auth.login"))
