import io
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite:///test_media_view.db")

from app import create_app
from app.models import FileUpload, User, db


class MediaViewUploadTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmpdir, "test_media_view.db")
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path}"

        self.app = create_app()
        self.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        self.client = self.app.test_client()

        with self.app.app_context():
            db.drop_all()
            db.create_all()

            user = User(username="tester", email="tester@example.com")
            user.set_password("secret123")
            db.session.add(user)
            db.session.commit()

            self.user_id = user.id

    def test_audio_file_can_be_uploaded_and_viewed(self):
        with self.app.app_context():
            login = self.client.post(
                "/login",
                data={"username": "tester", "password": "secret123"},
                follow_redirects=True,
            )
            self.assertEqual(login.status_code, 200)

            upload = self.client.post(
                "/upload",
                data={"file": (io.BytesIO(b"fake-audio-bytes"), "sample.mp3")},
                content_type="multipart/form-data",
                follow_redirects=True,
            )
            self.assertEqual(upload.status_code, 200)
            self.assertIn("File berhasil diupload.", upload.get_data(as_text=True))

            record = FileUpload.query.filter_by(uploader_id=self.user_id).first()
            self.assertIsNotNone(record)

            watch = self.client.get(f"/watch/{record.id}")
            self.assertEqual(watch.status_code, 200)

            stream = self.client.get(f"/stream/{record.id}")
            self.assertEqual(stream.status_code, 200)
            self.assertIn("audio/mpeg", stream.headers.get("Content-Type", ""))

    def test_text_file_can_be_previewed_in_browser(self):
        with self.app.app_context():
            login = self.client.post(
                "/login",
                data={"username": "tester", "password": "secret123"},
                follow_redirects=True,
            )
            self.assertEqual(login.status_code, 200)

            upload = self.client.post(
                "/upload",
                data={"file": (io.BytesIO(b"hello from text file"), "sample.txt")},
                content_type="multipart/form-data",
                follow_redirects=True,
            )
            self.assertEqual(upload.status_code, 200)
            self.assertIn("File berhasil diupload.", upload.get_data(as_text=True))

            record = FileUpload.query.filter_by(original_name="sample.txt", uploader_id=self.user_id).first()
            self.assertIsNotNone(record)

            watch = self.client.get(f"/watch/{record.id}")
            self.assertEqual(watch.status_code, 200)
            self.assertIn("iframe", watch.get_data(as_text=True))
            self.assertIn("/view/", watch.get_data(as_text=True))

    @patch("app.auth.send_email", return_value=(True, "Email berhasil dikirim."))
    def test_register_sends_notification_email(self, mock_send_email):
        response = self.client.post(
            "/register",
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "secret123",
                "confirm_password": "secret123",
            },
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_send_email.call_count, 1)

    @patch("app.auth.send_email", return_value=(True, "Email berhasil dikirim."))
    def test_login_sends_notification_email(self, mock_send_email):
        response = self.client.post(
            "/login",
            data={"username": "tester", "password": "secret123"},
            follow_redirects=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(mock_send_email.call_count, 1)


if __name__ == "__main__":
    unittest.main()
