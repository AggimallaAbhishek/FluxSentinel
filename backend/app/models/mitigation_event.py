from datetime import datetime, timezone

from app.extensions import db


class MitigationEvent(db.Model):
    __tablename__ = "mitigation_events"

    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(64), nullable=False, index=True)
    severity = db.Column(db.Integer, nullable=False)
    action = db.Column(db.Text, nullable=False)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
