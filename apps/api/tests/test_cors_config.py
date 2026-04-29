from app.config import DEFAULT_CORS_ALLOW_ORIGINS, parse_cors_allow_origins, settings
from app.main import app


def test_cors_allow_origins_parser_default() -> None:
    assert parse_cors_allow_origins(None) == DEFAULT_CORS_ALLOW_ORIGINS


def test_cors_allow_origins_parser_empty_value_uses_default() -> None:
    assert parse_cors_allow_origins(" , , /// ") == DEFAULT_CORS_ALLOW_ORIGINS


def test_cors_allow_origins_parser_trims_spaces_filters_empty_and_removes_trailing_slash() -> None:
    assert parse_cors_allow_origins(" http://localhost:3000/ , , http://127.0.0.1:3000/// ") == (
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    )


def test_main_cors_allow_origins_does_not_include_wildcard() -> None:
    cors_middleware = next(
        middleware
        for middleware in app.user_middleware
        if middleware.cls.__name__ == "CORSMiddleware"
    )

    assert cors_middleware.kwargs["allow_origins"] == settings.cors_allow_origins
    assert "*" not in cors_middleware.kwargs["allow_origins"]
