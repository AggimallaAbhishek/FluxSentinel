from flask import Flask
from flask_cors import CORS

from .config import Config
from .extensions import db, migrate, socketio
from .routes.health import health_bp
from .routes.logs import logs_bp
from .routes.mitigation import mitigation_bp


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    cors_origins = app.config["CORS_ALLOWED_ORIGINS"]
    if isinstance(cors_origins, str) and "," in cors_origins:
        cors_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})
    socketio.init_app(app, cors_allowed_origins=cors_origins)

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(logs_bp, url_prefix="/api")
    app.register_blueprint(mitigation_bp, url_prefix="/api")

    return app
