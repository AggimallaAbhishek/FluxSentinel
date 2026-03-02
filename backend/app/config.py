import os


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///fluxsentinel.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Pool tuning is important for cloud DB latency and burst traffic from simulator nodes.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": _env_int("DB_POOL_RECYCLE", 300),
        "pool_size": _env_int("DB_POOL_SIZE", 10),
        "max_overflow": _env_int("DB_MAX_OVERFLOW", 20),
        "pool_timeout": _env_int("DB_POOL_TIMEOUT", 30),
    }

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    MODEL_PATH = os.getenv("MODEL_PATH", "app/ml/model.pkl")
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*")
