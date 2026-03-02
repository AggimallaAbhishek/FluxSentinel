from datetime import datetime, timedelta, timezone

from app import create_app
from app.extensions import db
from app.models.blocked_ip import BlockedIP
from app.models.mitigation_event import MitigationEvent
from app.models.traffic_log import TrafficLog


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = "redis://localhost:6379/0"
    MODEL_PATH = "app/ml/model.pkl"
    CORS_ALLOWED_ORIGINS = "*"


def _seed_data() -> None:
    now = datetime.now(timezone.utc)

    logs = [
        TrafficLog(
            ip="1.1.1.1",
            timestamp=now - timedelta(minutes=2),
            endpoint="/login",
            request_rate=120,
            status_code=200,
            payload_size=700,
        ),
        TrafficLog(
            ip="1.1.1.1",
            timestamp=now - timedelta(minutes=1),
            endpoint="/api/status",
            request_rate=140,
            status_code=200,
            payload_size=680,
        ),
        TrafficLog(
            ip="2.2.2.2",
            timestamp=now - timedelta(minutes=1),
            endpoint="/search",
            request_rate=80,
            status_code=200,
            payload_size=400,
        ),
    ]

    blocked = BlockedIP(
        ip="1.1.1.1",
        blocked_at=now - timedelta(minutes=1),
        reason="ml_detected_attack",
    )
    event = MitigationEvent(
        ip="1.1.1.1",
        severity=88,
        action="temporary_block",
        timestamp=now - timedelta(minutes=1),
    )

    db.session.add_all(logs + [blocked, event])
    db.session.commit()


def test_stats_overview_endpoint():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        _seed_data()

    client = app.test_client()
    response = client.get("/api/stats/overview?minutes=10")

    assert response.status_code == 200
    data = response.get_json()

    assert data["window_minutes"] == 10
    assert data["total_logs"] == 3
    assert data["total_attacks"] == 1
    assert data["blocked_ips_count"] == 1
    assert data["peak_request_rate"] == 140
    assert data["last_event_at"] is not None


def test_stats_timeline_endpoint():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        _seed_data()

    client = app.test_client()
    response = client.get("/api/stats/timeline?minutes=10&bucket_minutes=5")

    assert response.status_code == 200
    data = response.get_json()

    assert data["window_minutes"] == 10
    assert data["bucket_minutes"] == 5
    assert isinstance(data["timeline"], list)

    total_requests = sum(point["total_requests"] for point in data["timeline"])
    total_attacks = sum(point["attack_events"] for point in data["timeline"])

    assert total_requests == 3
    assert total_attacks == 1


def test_stats_top_ips_endpoint():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        _seed_data()

    client = app.test_client()
    response = client.get("/api/stats/top-ips?minutes=10&limit=5")

    assert response.status_code == 200
    data = response.get_json()

    assert data["window_minutes"] == 10
    assert data["limit"] == 5
    assert len(data["ips"]) >= 2

    top_ip = data["ips"][0]
    assert top_ip["ip"] == "1.1.1.1"
    assert top_ip["request_count"] == 2
    assert top_ip["blocked"] is True


def test_stats_overview_validation_error():
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/api/stats/overview?minutes=0")
    assert response.status_code == 400
    assert "error" in response.get_json()
