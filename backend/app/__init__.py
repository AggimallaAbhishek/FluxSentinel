from flask import Flask

from .config import Config
from .extensions import db, migrate, socketio
from .routes.health import health_bp
from .routes.logs import logs_bp
from .routes.mitigation import mitigation_bp


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins=app.config["CORS_ALLOWED_ORIGINS"])

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(logs_bp, url_prefix="/api")
    app.register_blueprint(mitigation_bp, url_prefix="/api")

    return app
