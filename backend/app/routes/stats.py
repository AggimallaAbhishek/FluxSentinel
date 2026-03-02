from collections import defaultdict
from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from app.extensions import db
from app.models.blocked_ip import BlockedIP
from app.models.mitigation_event import MitigationEvent
from app.models.traffic_log import TrafficLog


stats_bp = Blueprint("stats", __name__)


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_positive_int(
    name: str,
    default: int,
    min_value: int,
    max_value: int,
) -> tuple[int | None, tuple[dict, int] | None]:
    raw_value = request.args.get(name)
    if raw_value is None:
        return default, None

    try:
        value = int(raw_value)
    except ValueError:
        return None, ({"error": f"{name} must be an integer"}, 400)

    if value < min_value or value > max_value:
        return (
            None,
            ({"error": f"{name} must be between {min_value} and {max_value}"}, 400),
        )

    return value, None


def _bucket_start(dt: datetime, bucket_minutes: int) -> datetime:
    dt_utc = _as_utc(dt) or datetime.now(timezone.utc)
    bucket_seconds = bucket_minutes * 60
    epoch_seconds = int(dt_utc.timestamp())
    floored = epoch_seconds - (epoch_seconds % bucket_seconds)
    return datetime.fromtimestamp(floored, tz=timezone.utc)


@stats_bp.get("/stats/overview")
def stats_overview():
    minutes, error = _parse_positive_int("minutes", default=60, min_value=1, max_value=10080)
    if error:
        return jsonify(error[0]), error[1]

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=minutes)

    logs_in_window = TrafficLog.query.filter(TrafficLog.timestamp >= window_start)
    total_logs = logs_in_window.count()

    avg_request_rate = (
        db.session.query(func.avg(TrafficLog.request_rate))
        .filter(TrafficLog.timestamp >= window_start)
        .scalar()
    )
    peak_request_rate = (
        db.session.query(func.max(TrafficLog.request_rate))
        .filter(TrafficLog.timestamp >= window_start)
        .scalar()
    )

    total_attacks = (
        MitigationEvent.query.filter(MitigationEvent.timestamp >= window_start).count()
    )
    blocked_ips_count = BlockedIP.query.count()

    last_log_at = db.session.query(func.max(TrafficLog.timestamp)).scalar()
    last_attack_at = db.session.query(func.max(MitigationEvent.timestamp)).scalar()

    candidates = [_as_utc(last_log_at), _as_utc(last_attack_at)]
    last_event_at = max((dt for dt in candidates if dt is not None), default=None)

    return (
        jsonify(
            {
                "window_minutes": minutes,
                "total_logs": int(total_logs),
                "total_attacks": int(total_attacks),
                "blocked_ips_count": int(blocked_ips_count),
                "avg_request_rate": round(float(avg_request_rate or 0), 2),
                "peak_request_rate": int(peak_request_rate or 0),
                "last_event_at": last_event_at.isoformat() if last_event_at else None,
            }
        ),
        200,
    )


@stats_bp.get("/stats/timeline")
def stats_timeline():
    minutes, minutes_error = _parse_positive_int(
        "minutes", default=60, min_value=1, max_value=10080
    )
    if minutes_error:
        return jsonify(minutes_error[0]), minutes_error[1]

    bucket_minutes, bucket_error = _parse_positive_int(
        "bucket_minutes", default=5, min_value=1, max_value=60
    )
    if bucket_error:
        return jsonify(bucket_error[0]), bucket_error[1]

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=minutes)

    logs = (
        TrafficLog.query.filter(TrafficLog.timestamp >= window_start)
        .order_by(TrafficLog.timestamp.asc())
        .all()
    )
    attacks = (
        MitigationEvent.query.filter(MitigationEvent.timestamp >= window_start)
        .order_by(MitigationEvent.timestamp.asc())
        .all()
    )

    buckets: dict[datetime, dict] = defaultdict(
        lambda: {
            "total_requests": 0,
            "sum_request_rate": 0.0,
            "attack_events": 0,
            "sum_severity": 0.0,
        }
    )

    for row in logs:
        key = _bucket_start(row.timestamp, bucket_minutes)
        buckets[key]["total_requests"] += 1
        buckets[key]["sum_request_rate"] += float(row.request_rate)

    for row in attacks:
        key = _bucket_start(row.timestamp, bucket_minutes)
        buckets[key]["attack_events"] += 1
        buckets[key]["sum_severity"] += float(row.severity)

    start_bucket = _bucket_start(window_start, bucket_minutes)
    end_bucket = _bucket_start(now, bucket_minutes)
    step = timedelta(minutes=bucket_minutes)

    timeline = []
    cursor = start_bucket
    while cursor <= end_bucket:
        bucket = buckets[cursor]
        total_requests = bucket["total_requests"]
        attack_events = bucket["attack_events"]

        avg_request_rate = (
            bucket["sum_request_rate"] / total_requests if total_requests > 0 else 0.0
        )
        avg_severity = (
            bucket["sum_severity"] / attack_events if attack_events > 0 else 0.0
        )

        timeline.append(
            {
                "timestamp": cursor.isoformat(),
                "total_requests": int(total_requests),
                "avg_request_rate": round(avg_request_rate, 2),
                "attack_events": int(attack_events),
                "avg_severity": round(avg_severity, 2),
            }
        )
        cursor += step

    return (
        jsonify(
            {
                "window_minutes": minutes,
                "bucket_minutes": bucket_minutes,
                "timeline": timeline,
            }
        ),
        200,
    )


@stats_bp.get("/stats/top-ips")
def stats_top_ips():
    minutes, minutes_error = _parse_positive_int(
        "minutes", default=60, min_value=1, max_value=10080
    )
    if minutes_error:
        return jsonify(minutes_error[0]), minutes_error[1]

    limit, limit_error = _parse_positive_int("limit", default=10, min_value=1, max_value=100)
    if limit_error:
        return jsonify(limit_error[0]), limit_error[1]

    window_start = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    rows = (
        db.session.query(
            TrafficLog.ip.label("ip"),
            func.count(TrafficLog.id).label("request_count"),
            func.avg(TrafficLog.request_rate).label("avg_request_rate"),
            func.max(TrafficLog.request_rate).label("peak_request_rate"),
            func.max(TrafficLog.timestamp).label("last_seen"),
        )
        .filter(TrafficLog.timestamp >= window_start)
        .group_by(TrafficLog.ip)
        .order_by(func.count(TrafficLog.id).desc(), func.max(TrafficLog.request_rate).desc())
        .limit(limit)
        .all()
    )

    blocked_ips = {row.ip for row in BlockedIP.query.all()}

    payload = []
    for row in rows:
        last_seen = _as_utc(row.last_seen)
        payload.append(
            {
                "ip": row.ip,
                "request_count": int(row.request_count or 0),
                "avg_request_rate": round(float(row.avg_request_rate or 0), 2),
                "peak_request_rate": int(row.peak_request_rate or 0),
                "blocked": row.ip in blocked_ips,
                "last_seen": last_seen.isoformat() if last_seen else None,
            }
        )

    return jsonify({"window_minutes": minutes, "limit": limit, "ips": payload}), 200
