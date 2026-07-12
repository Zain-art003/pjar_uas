import mimetypes
import os
import re

from flask import Blueprint, Response, abort, current_app, render_template, request
from flask_login import current_user, login_required

from app.models import FileUpload

stream_bp = Blueprint("stream", __name__)

CHUNK_SIZE = 1024 * 1024  # 1 MB per chunk


@stream_bp.route("/watch/<int:file_id>")
@login_required
def watch(file_id):
    record = FileUpload.query.get_or_404(file_id)
    if record.uploader_id != current_user.id:
        abort(403)
    if not record.can_preview:
        abort(404)
    return render_template("watch.html", file=record)


@stream_bp.route("/stream/<int:file_id>")
@login_required
def stream(file_id):
    """
    Streaming video dengan dukungan HTTP Range request, supaya
    tombol seek / maju-mundur di video player berfungsi normal
    dan video tidak perlu didownload penuh dulu sebelum diputar.
    """
    record = FileUpload.query.get_or_404(file_id)
    if record.uploader_id != current_user.id:
        abort(403)
    if not record.can_preview:
        abort(404)

    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], record.stored_name)
    if not os.path.exists(filepath):
        abort(404)

    file_size = os.path.getsize(filepath)
    range_header = request.headers.get("Range", None)

    mimetype, _ = mimetypes.guess_type(filepath)
    if not mimetype:
        mimetype = "application/octet-stream"

    if range_header:
        match = re.search(r"bytes=(\d+)-(\d*)", range_header)
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else min(start + CHUNK_SIZE, file_size - 1)
        end = min(end, file_size - 1)
        length = end - start + 1

        with open(filepath, "rb") as f:
            f.seek(start)
            data = f.read(length)

        response = Response(data, 206, mimetype=mimetype, direct_passthrough=True)
        response.headers.add("Content-Range", f"bytes {start}-{end}/{file_size}")
        response.headers.add("Accept-Ranges", "bytes")
        response.headers.add("Content-Length", str(length))
        return response

    def generate():
        with open(filepath, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk

    response = Response(generate(), mimetype=mimetype)
    response.headers.add("Content-Length", str(file_size))
    response.headers.add("Accept-Ranges", "bytes")
    return response
