from datetime import datetime, timezone

from app.extensions import db


class BlockedIP(db.Model):
    __tablename__ = "blocked_ips"

    ip = db.Column(db.String(64), primary_key=True)
    blocked_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    reason = db.Column(db.Text, nullable=False)
