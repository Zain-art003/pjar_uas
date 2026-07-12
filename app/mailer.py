"""
Modul pengiriman email lewat SMTP.

Kredensial SMTP TIDAK ditulis di sini — semuanya dibaca dari
environment variable (lihat config.py / file .env), supaya tidak
pernah ter-commit ke Git atau ter-expose di kode.
"""
import smtplib
import mimetypes
from email.message import EmailMessage

from flask import current_app


def send_email(to_email: str, subject: str, body: str, attachment_path: str | None = None) -> tuple[bool, str]:
    """
    Kirim email biasa, opsional dengan lampiran file.
    Return (sukses: bool, pesan: str)
    """
    smtp_server = current_app.config["SMTP_SERVER"]
    smtp_port = current_app.config["SMTP_PORT"]
    smtp_username = current_app.config["SMTP_USERNAME"]
    smtp_password = current_app.config["SMTP_PASSWORD"]
    sender_name = current_app.config["SMTP_SENDER_NAME"]

    if not smtp_username or not smtp_password:
        return False, "SMTP belum dikonfigurasi. Isi SMTP_USERNAME dan SMTP_PASSWORD di file .env"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{smtp_username}>"
    msg["To"] = to_email
    msg.set_content(body)

    if attachment_path:
        ctype, encoding = mimetypes.guess_type(attachment_path)
        if ctype is None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with open(attachment_path, "rb") as f:
            data = f.read()
        filename = attachment_path.split("/")[-1]
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=filename)

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=20) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        return True, "Email berhasil dikirim."
    except smtplib.SMTPAuthenticationError:
        return False, "Autentikasi SMTP gagal. Periksa SMTP_USERNAME / SMTP_PASSWORD (App Password) di .env"
    except Exception as e:  # noqa: BLE001
        return False, f"Gagal mengirim email: {e}"
