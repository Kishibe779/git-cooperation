from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field


def _load_env_files() -> None:
    backend_root = Path(__file__).resolve().parents[2]
    candidates = [
        backend_root / ".env",
        backend_root / ".env.local",
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        Path.cwd() / ".env.local",
        Path.cwd().parent / ".env.local",
    ]
    for env_file in candidates:
        if not env_file.exists():
            continue
        for raw_line in env_file.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("'").strip('"'))


def _to_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class AppSettings(BaseModel):
    app_name: str = "Resume Optimizer API"
    app_version: str = "2.0.0"
    app_env: str = "development"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:5500",
            "http://localhost:5500",
            "http://127.0.0.1:8000",
            "http://localhost:8000",
        ]
    )
    default_provider: str = "mock"
    allow_mock_provider: bool = False
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    llm_timeout_seconds: float = 45.0
    llm_enable_fallback: bool = True

    @property
    def deepseek_enabled(self) -> bool:
        return bool(self.deepseek_api_key)


class ProviderSettings(BaseModel):
    provider: str = "mock"
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None
    timeout_seconds: float = 45.0
    fallback_enabled: bool = True


@lru_cache
def get_settings() -> AppSettings:
    _load_env_files()
    cors_raw = os.getenv("APP_CORS_ORIGINS")
    origins = (
        [item.strip() for item in cors_raw.split(",") if item.strip()]
        if cors_raw
        else AppSettings().cors_origins
    )
    return AppSettings(
        app_name=os.getenv("APP_NAME", "Resume Optimizer API"),
        app_version=os.getenv("APP_VERSION", "2.0.0"),
        app_env=os.getenv("APP_ENV", "development"),
        cors_origins=origins,
        default_provider=os.getenv("APP_DEFAULT_PROVIDER", "mock").strip().lower(),
        allow_mock_provider=_to_bool(os.getenv("APP_ALLOW_MOCK"), False),
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash"),
        llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "45")),
        llm_enable_fallback=_to_bool(os.getenv("LLM_ENABLE_FALLBACK"), True),
    )


def get_provider_settings(provider: str | None) -> ProviderSettings:
    settings = get_settings()
    chosen = (provider or "auto").strip().lower()
    if chosen == "auto":
        chosen = "deepseek_strict" if settings.deepseek_enabled else settings.default_provider
    if chosen in {"deepseek", "deepseek_strict"}:
        return ProviderSettings(
            provider="deepseek",
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model,
            timeout_seconds=settings.llm_timeout_seconds,
            fallback_enabled=False if chosen == "deepseek_strict" else settings.llm_enable_fallback,
        )
    return ProviderSettings(
        provider="mock",
        timeout_seconds=settings.llm_timeout_seconds,
        fallback_enabled=settings.llm_enable_fallback,
    )
