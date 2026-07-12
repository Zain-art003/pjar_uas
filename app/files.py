import os
import uuid

from flask import (
    Blueprint, abort, current_app, flash, redirect,
    render_template, request, send_from_directory, url_for,
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.mailer import send_email
from app.models import FileUpload, db

files_bp = Blueprint("files", __name__)


def _allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def _is_video(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["VIDEO_EXTENSIONS"]


def _is_audio(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["AUDIO_EXTENSIONS"]


@files_bp.route("/")
@login_required
def dashboard():
    my_files = (
        FileUpload.query.filter_by(uploader_id=current_user.id)
        .order_by(FileUpload.uploaded_at.desc())
        .all()
    )
    return render_template("dashboard.html", files=my_files)


@files_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            flash("Tidak ada file yang dipilih.", "error")
            return redirect(url_for("files.upload"))

        file = request.files["file"]
        if file.filename == "":
            flash("Tidak ada file yang dipilih.", "error")
            return redirect(url_for("files.upload"))

        if not _allowed_file(file.filename):
            flash("Tipe file tidak diizinkan.", "error")
            return redirect(url_for("files.upload"))

        original_name = secure_filename(file.filename)
        ext = original_name.rsplit(".", 1)[-1].lower()
        stored_name = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)

        file.save(filepath)
        filesize = os.path.getsize(filepath)

        record = FileUpload(
            original_name=original_name,
            stored_name=stored_name,
            filesize=filesize,
            is_video=_is_video(original_name),
            uploader_id=current_user.id,
        )
        db.session.add(record)
        db.session.commit()

        flash("File berhasil diupload.", "success")
        return redirect(url_for("files.dashboard"))

    return render_template("upload.html")


@files_bp.route("/view/<int:file_id>")
@login_required
def view(file_id):
    record = FileUpload.query.get_or_404(file_id)
    if record.uploader_id != current_user.id:
        abort(403)

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        record.stored_name,
        as_attachment=False,
        download_name=record.original_name,
    )


@files_bp.route("/download/<int:file_id>")
@login_required
def download(file_id):
    record = FileUpload.query.get_or_404(file_id)
    if record.uploader_id != current_user.id:
        abort(403)
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"],
        record.stored_name,
        as_attachment=True,
        download_name=record.original_name,
    )


@files_bp.route("/delete/<int:file_id>", methods=["POST"])
@login_required
def delete(file_id):
    record = FileUpload.query.get_or_404(file_id)
    if record.uploader_id != current_user.id:
        abort(403)

    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], record.stored_name)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(record)
    db.session.commit()
    flash("File berhasil dihapus.", "success")
    return redirect(url_for("files.dashboard"))


@files_bp.route("/send/<int:file_id>", methods=["GET", "POST"])
@login_required
def send(file_id):
    record = FileUpload.query.get_or_404(file_id)
    if record.uploader_id != current_user.id:
        abort(403)

    if request.method == "POST":
        to_email = request.form.get("to_email", "").strip()
        message = request.form.get("message", "").strip()

        if not to_email:
            flash("Alamat email tujuan wajib diisi.", "error")
            return render_template("send_file.html", file=record)

        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], record.stored_name)
        ok, msg = send_email(
            to_email=to_email,
            subject=f"File dikirim: {record.original_name}",
            body=message or f"{current_user.username} mengirimkan file: {record.original_name}",
            attachment_path=filepath,
        )
        flash(msg, "success" if ok else "error")
        return redirect(url_for("files.dashboard"))

    return render_template("send_file.html", file=record)
