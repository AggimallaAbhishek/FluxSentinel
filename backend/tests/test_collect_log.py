import redis

from app import create_app
from app.extensions import db
from app.models.traffic_log import TrafficLog
from app.routes import logs as logs_route
from app.services import redis_service


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = "redis://localhost:6379/0"
    MODEL_PATH = "ml/model.pkl"
    CORS_ALLOWED_ORIGINS = "*"


class BrokenRedis:
    def incr(self, *_args, **_kwargs):
        raise redis.ConnectionError("redis unavailable")

    def expire(self, *_args, **_kwargs):
        raise redis.ConnectionError("redis unavailable")

    def set(self, *_args, **_kwargs):
        raise redis.ConnectionError("redis unavailable")

    def exists(self, *_args, **_kwargs):
        raise redis.ConnectionError("redis unavailable")


def test_collect_log_works_without_redis(monkeypatch):
    app = create_app(TestConfig)

    monkeypatch.setattr(redis_service, "_get_client", lambda: BrokenRedis())
    monkeypatch.setattr(redis_service, "_fallback_counters", {})
    monkeypatch.setattr(redis_service, "_fallback_blacklist", {})

    with app.app_context():
        db.create_all()

    client = app.test_client()
    response = client.post(
        "/api/collect-log",
        json={
            "ip": "1.2.3.4",
            "endpoint": "/login",
            "request_rate": 250,
            "status_code": 401,
            "payload_size": 1200,
        },
    )

    assert response.status_code == 201
    payload = response.get_json()
    assert payload["prediction"] == 1
    assert payload["mitigation"]["action"] == "temporary_block"

    with app.app_context():
        assert TrafficLog.query.count() == 1


def test_collect_log_rejects_blacklisted_ip(monkeypatch):
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()

    monkeypatch.setattr(logs_route, "is_ip_blacklisted", lambda ip: True)
    monkeypatch.setattr(logs_route, "get_blacklist_ttl", lambda ip: 600)

    client = app.test_client()
    response = client.post(
        "/api/collect-log",
        json={
            "ip": "5.6.7.8",
            "endpoint": "/login",
            "request_rate": 280,
            "status_code": 401,
            "payload_size": 1300,
        },
    )

    assert response.status_code == 429
    body = response.get_json()
    assert body["error"] == "ip_temporarily_blocked"
    assert body["retry_after_seconds"] == 600

    with app.app_context():
        assert TrafficLog.query.count() == 0


def test_collect_log_hides_internal_error_details_by_default(monkeypatch):
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()

    monkeypatch.setattr(
        logs_route,
        "predict_threat",
        lambda _features: (_ for _ in ()).throw(RuntimeError("db credentials leaked")),
    )

    client = app.test_client()
    response = client.post(
        "/api/collect-log",
        json={
            "ip": "9.9.9.9",
            "endpoint": "/login",
            "request_rate": 300,
            "status_code": 401,
            "payload_size": 1500,
        },
    )

    assert response.status_code == 500
    body = response.get_json()
    assert body == {"error": "failed_to_process_log"}
