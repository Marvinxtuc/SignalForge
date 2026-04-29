from dataclasses import dataclass, field
import os


DEFAULT_CORS_ALLOW_ORIGINS = ("http://localhost:3000", "http://127.0.0.1:3000")


def parse_cors_allow_origins(value: str | None) -> tuple[str, ...]:
    if value is None:
        return DEFAULT_CORS_ALLOW_ORIGINS

    origins: list[str] = []
    for origin in value.split(","):
        normalized = origin.strip().rstrip("/")
        if normalized:
            origins.append(normalized)
    return tuple(origins) or DEFAULT_CORS_ALLOW_ORIGINS


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "")
    redis_url: str = os.getenv("REDIS_URL", "")
    cors_allow_origins: tuple[str, ...] = field(
        default_factory=lambda: parse_cors_allow_origins(os.getenv("CORS_ALLOW_ORIGINS"))
    )


settings = Settings()
