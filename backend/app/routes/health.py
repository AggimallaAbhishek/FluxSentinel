from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from app.extensions import db

import redis


health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    return jsonify({"status": "ok", "service": "FluxSentinel"}), 200


@health_bp.get("/health/deep")
def deep_health_check():
    checks = {}
    overall_status = "ok"

    try:
        db.session.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok"}
    except Exception as exc:
        db.session.rollback()
        overall_status = "degraded"
        checks["database"] = {
            "status": "error",
            "error": exc.__class__.__name__,
        }

    try:
        redis.Redis.from_url(
            current_app.config["REDIS_URL"], decode_responses=True
        ).ping()
        checks["redis"] = {"status": "ok"}
    except Exception as exc:
        overall_status = "degraded"
        checks["redis"] = {
            "status": "error",
            "error": exc.__class__.__name__,
        }

    status_code = 200 if overall_status == "ok" else 503
    return (
        jsonify(
            {
                "status": overall_status,
                "service": "FluxSentinel",
                "checks": checks,
            }
        ),
        status_code,
    )
