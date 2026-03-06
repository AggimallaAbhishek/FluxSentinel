from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from app.extensions import db

import redis


health_bp = Blueprint("health", __name__)


def _format_exc(exc: Exception) -> dict:
    payload = {"status": "error", "error": "check_failed"}
    if current_app.config.get("EXPOSE_INTERNAL_ERRORS", False):
        # Keep error details short for debugging in non-sensitive environments.
        message = str(exc)
        if len(message) > 240:
            message = f"{message[:240]}..."
        payload["error"] = exc.__class__.__name__
        payload["message"] = message
    return payload


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
        checks["database"] = _format_exc(exc)

    try:
        redis.Redis.from_url(
            current_app.config["REDIS_URL"], decode_responses=True
        ).ping()
        checks["redis"] = {"status": "ok"}
    except Exception as exc:
        overall_status = "degraded"
        checks["redis"] = _format_exc(exc)

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
