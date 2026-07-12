from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    files = db.relationship("FileUpload", backref="uploader", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class FileUpload(db.Model):
    __tablename__ = "file_upload"

    id = db.Column(db.Integer, primary_key=True)
    original_name = db.Column(db.String(255), nullable=False)
    stored_name = db.Column(db.String(255), unique=True, nullable=False)
    filesize = db.Column(db.Integer, default=0)
    is_video = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    uploader_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    @property
    def is_audio(self) -> bool:
        ext = self.stored_name.rsplit(".", 1)[-1].lower() if "." in self.stored_name else ""
        return ext in {"mp3", "wav", "ogg", "m4a", "flac", "aac"}

    @property
    def can_preview(self) -> bool:
        return self.is_video or self.is_audio

    def human_size(self) -> str:
        size = self.filesize or 0
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def __repr__(self):
        return f"<FileUpload {self.original_name}>"
