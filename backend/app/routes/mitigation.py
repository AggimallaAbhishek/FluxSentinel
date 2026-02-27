from flask import Blueprint, jsonify

from app.models.blocked_ip import BlockedIP
from app.models.mitigation_event import MitigationEvent


mitigation_bp = Blueprint("mitigation", __name__)


@mitigation_bp.get("/blocked-ips")
def list_blocked_ips():
    records = BlockedIP.query.order_by(BlockedIP.blocked_at.desc()).all()
    return (
        jsonify(
            [
                {
                    "ip": row.ip,
                    "blocked_at": row.blocked_at.isoformat(),
                    "reason": row.reason,
                }
                for row in records
            ]
        ),
        200,
    )


@mitigation_bp.get("/mitigation-events")
def list_mitigation_events():
    records = MitigationEvent.query.order_by(MitigationEvent.timestamp.desc()).all()
    return (
        jsonify(
            [
                {
                    "id": row.id,
                    "ip": row.ip,
                    "severity": row.severity,
                    "action": row.action,
                    "timestamp": row.timestamp.isoformat(),
                }
                for row in records
            ]
        ),
        200,
    )
