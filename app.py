from flask import Flask, render_template
from config import Config
from models.db import initialize_database
from models.user_model import UserModel
from routes.slot_routes import slot_bp
from routes.reservation_routes import reservation_bp
from routes.admin_routes import admin_bp
from routes.auth_routes import auth_bp
from utils.auth import get_current_user


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    initialize_database()

    UserModel.ensure_default_admin(
        full_name=Config.DEFAULT_ADMIN_NAME,
        email=Config.DEFAULT_ADMIN_EMAIL,
        password=Config.DEFAULT_ADMIN_PASSWORD,
        phone=Config.DEFAULT_ADMIN_PHONE
    )

    app.register_blueprint(slot_bp)
    app.register_blueprint(reservation_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)

    @app.context_processor
    def inject_current_user():
        current_user = get_current_user()
        return {
            "current_user": current_user,
            "is_logged_in": current_user is not None,
            "is_admin": bool(current_user and current_user.get("is_admin"))
        }

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("index.html", error_message="Page not found."), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("index.html", error_message="Internal server error."), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.DEBUG
    )