import redis

from app import create_app
from app.extensions import db
from app.models.traffic_log import TrafficLog
from app.services import redis_service


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = "redis://localhost:6379/0"
    MODEL_PATH = "app/ml/model.pkl"
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
