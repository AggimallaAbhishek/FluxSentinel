from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models.traffic_log import TrafficLog
from app.services.feature_engineering import extract_features
from app.services.mitigation_engine import handle_threat
from app.services.redis_service import increment_request_counter
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

    log_entry = TrafficLog(
        ip=payload["ip"],
        timestamp=parsed_timestamp,
        endpoint=payload["endpoint"],
        request_rate=int(payload["request_rate"]),
        status_code=int(payload["status_code"]),
        payload_size=int(payload["payload_size"]),
    )

    db.session.add(log_entry)
    increment_request_counter(payload["ip"])

    features = extract_features(payload)
    prediction, probability, severity = predict_threat(features)

    response_payload = {
        "prediction": int(prediction),
        "probability": round(probability, 4),
        "severity": int(severity),
    }

    if prediction == 1:
        mitigation = handle_threat(
            ip=payload["ip"], severity=severity, reason="ml_detected_attack"
        )
        emit_alert(
            {
                "type": "threat_alert",
                "ip": payload["ip"],
                "severity": severity,
                "probability": probability,
                "action": mitigation["action"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        response_payload["mitigation"] = mitigation

    db.session.commit()
    return jsonify(response_payload), 201
