import os

from flask import Flask
from flask_login import LoginManager

from config import Config
from app.models import User, db

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Silakan login terlebih dahulu."
login_manager.login_message_category = "error"


def create_app():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "templates"),
        static_folder=os.path.join(base_dir, "static"),
    )
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(base_dir, "instance"), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from app.auth import auth_bp
    from app.files import files_bp
    from app.stream import stream_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(stream_bp)

    with app.app_context():
        db.create_all()

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app
