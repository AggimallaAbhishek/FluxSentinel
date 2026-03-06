from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request

from app.extensions import db
from app.models.traffic_log import TrafficLog
from app.services.feature_engineering import extract_features
from app.services.mitigation_engine import handle_threat
from app.services.redis_service import (
    get_blacklist_ttl,
    increment_request_counter,
    is_ip_blacklisted,
)
from app.services.threat_detection import predict_threat
from app.services.websocket_service import emit_alert


logs_bp = Blueprint("logs", __name__)


@logs_bp.post("/collect-log")
def collect_log():
    payload = request.get_json(silent=True) or {}
    required_fields = ["ip", "endpoint", "request_rate", "status_code", "payload_size"]
    missing_fields = [field for field in required_fields if field not in payload]

    if missing_fields:
        return jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}), 400

    timestamp = payload.get("timestamp")
    if timestamp:
        try:
            parsed_timestamp = datetime.fromisoformat(timestamp)
        except ValueError:
            return jsonify({"error": "timestamp must be ISO-8601 formatted"}), 400
    else:
        parsed_timestamp = datetime.now(timezone.utc)

    ip = str(payload["ip"]).strip()
    if not ip:
        return jsonify({"error": "ip must be a non-empty string"}), 400

    if is_ip_blacklisted(ip):
        retry_after_seconds = get_blacklist_ttl(ip)
        response_payload = {"error": "ip_temporarily_blocked", "ip": ip}
        if retry_after_seconds is not None:
            response_payload["retry_after_seconds"] = retry_after_seconds
        return jsonify(response_payload), 429

    try:
        request_rate = int(payload["request_rate"])
        status_code = int(payload["status_code"])
        payload_size = int(payload["payload_size"])
    except (TypeError, ValueError):
        return (
            jsonify(
                {
                    "error": (
                        "request_rate, status_code, and payload_size must be integer values"
                    )
                }
            ),
            400,
        )

    try:
        log_entry = TrafficLog(
            ip=ip,
            timestamp=parsed_timestamp,
            endpoint=payload["endpoint"],
            request_rate=request_rate,
            status_code=status_code,
            payload_size=payload_size,
        )

        db.session.add(log_entry)
        increment_request_counter(ip)

        features = extract_features(payload)
        prediction, probability, severity = predict_threat(features)

        response_payload = {
            "prediction": int(prediction),
            "probability": round(probability, 4),
            "severity": int(severity),
        }

        if prediction == 1:
            mitigation = handle_threat(
                ip=ip, severity=severity, reason="ml_detected_attack"
            )
            emit_alert(
                {
                    "type": "threat_alert",
                    "ip": ip,
                    "severity": severity,
                    "probability": probability,
                    "action": mitigation["action"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            response_payload["mitigation"] = mitigation

        db.session.commit()
        return jsonify(response_payload), 201
    except Exception as exc:
        db.session.rollback()
        current_app.logger.exception("Failed to process /collect-log request")
        error_payload = {"error": "failed_to_process_log"}
        if current_app.config.get("EXPOSE_INTERNAL_ERRORS", False):
            error_payload.update(
                {"detail": exc.__class__.__name__, "message": str(exc)}
            )
        return (
            jsonify(error_payload),
            500,
        )
