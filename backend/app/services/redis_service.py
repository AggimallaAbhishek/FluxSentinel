import time

import redis
from flask import current_app


_client = None
_fallback_counters = {}
_fallback_blacklist = {}


def _get_client() -> redis.Redis:
    global _client

    if _client is None:
        _client = redis.Redis.from_url(
            current_app.config["REDIS_URL"], decode_responses=True
        )
    return _client


def _now() -> float:
    return time.time()


def _fallback_increment(key: str, ttl_seconds: int) -> int:
    now = _now()
    count, expires_at = _fallback_counters.get(key, (0, now + ttl_seconds))

    if expires_at <= now:
        count = 0
        expires_at = now + ttl_seconds

    count += 1
    _fallback_counters[key] = (count, expires_at)
    return count


def increment_request_counter(ip: str, ttl_seconds: int = 60) -> int:
    key = f"ip_counter:{ip}"

    try:
        client = _get_client()
        count = client.incr(key)
        if count == 1:
            client.expire(key, ttl_seconds)
        return int(count)
    except redis.RedisError:
        return _fallback_increment(key, ttl_seconds)


def add_ip_to_blacklist(ip: str, ttl_seconds: int = 600) -> None:
    key = f"blacklist:{ip}"

    try:
        _get_client().set(key, "1", ex=ttl_seconds)
    except redis.RedisError:
        _fallback_blacklist[key] = _now() + ttl_seconds


def is_ip_blacklisted(ip: str) -> bool:
    key = f"blacklist:{ip}"

    try:
        return _get_client().exists(key) == 1
    except redis.RedisError:
        expires_at = _fallback_blacklist.get(key)
        if expires_at is None:
            return False
        if expires_at <= _now():
            _fallback_blacklist.pop(key, None)
            return False
        return True
