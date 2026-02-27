import redis
from flask import current_app


_client = None


def _get_client() -> redis.Redis:
    global _client

    if _client is None:
        _client = redis.Redis.from_url(
            current_app.config["REDIS_URL"], decode_responses=True
        )
    return _client


def increment_request_counter(ip: str, ttl_seconds: int = 60) -> int:
    key = f"ip_counter:{ip}"
    client = _get_client()
    count = client.incr(key)
    if count == 1:
        client.expire(key, ttl_seconds)
    return int(count)


def add_ip_to_blacklist(ip: str, ttl_seconds: int = 600) -> None:
    key = f"blacklist:{ip}"
    _get_client().set(key, "1", ex=ttl_seconds)


def is_ip_blacklisted(ip: str) -> bool:
    key = f"blacklist:{ip}"
    return _get_client().exists(key) == 1
