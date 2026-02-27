from datetime import datetime, timezone

from app.extensions import db
from app.models.blocked_ip import BlockedIP
from app.models.mitigation_event import MitigationEvent
from app.services.redis_service import add_ip_to_blacklist


TEMP_BLOCK_TTL_SECONDS = 600


def handle_threat(ip: str, severity: int, reason: str) -> dict:
    add_ip_to_blacklist(ip, TEMP_BLOCK_TTL_SECONDS)

    blocked_row = BlockedIP.query.filter_by(ip=ip).first()
    if blocked_row is None:
        blocked_row = BlockedIP(ip=ip, reason=reason)

    blocked_row.blocked_at = datetime.now(timezone.utc)
    blocked_row.reason = reason

    event_row = MitigationEvent(
        ip=ip,
        severity=severity,
        action="temporary_block",
        timestamp=datetime.now(timezone.utc),
    )

    db.session.add(blocked_row)
    db.session.add(event_row)

    return {
        "ip": ip,
        "severity": severity,
        "action": "temporary_block",
        "ttl_seconds": TEMP_BLOCK_TTL_SECONDS,
    }
