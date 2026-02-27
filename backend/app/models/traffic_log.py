from datetime import datetime, timezone

from app.extensions import db


class TrafficLog(db.Model):
    __tablename__ = "traffic_logs"

    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(64), nullable=False, index=True)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    endpoint = db.Column(db.String(255), nullable=False)
    request_rate = db.Column(db.Integer, nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    payload_size = db.Column(db.Integer, nullable=False)
