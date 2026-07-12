import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-jangan-dipakai-di-produksi")

    # Contoh format DATABASE_URL untuk MySQL:
    # mysql+pymysql://USER:PASSWORD@HOST:3306/NAMA_DATABASE
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://webapp_user:webapp_pass123@localhost:3306/webapp_db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # batas ukuran upload: 500 MB

    ALLOWED_EXTENSIONS = {
        "png", "jpg", "jpeg", "gif", "pdf", "doc", "docx",
        "xlsx", "zip", "rar", "txt", "mp4", "webm", "mov", "mkv",
    }
    VIDEO_EXTENSIONS = {"mp4", "webm", "mov", "mkv"}

    # SMTP
    SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_SENDER_NAME = os.environ.get("SMTP_SENDER_NAME", "MyApp")
