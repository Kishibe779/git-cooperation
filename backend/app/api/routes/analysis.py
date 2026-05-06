from fastapi import APIRouter, Header

from app.core.config import get_settings
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, MetaResponse
from app.services.analyzer import ResumeAnalyzer
from app.services.store import store

router = APIRouter(tags=["analysis"])
analyzer = ResumeAnalyzer()


@router.get("/meta", response_model=MetaResponse)
def get_meta() -> MetaResponse:
    settings = get_settings()
    available = ["auto"]
    if settings.allow_mock_provider:
        available.append("mock")
    if settings.deepseek_enabled:
        available.append("deepseek_strict")
        if settings.llm_enable_fallback:
            available.append("deepseek")
    return MetaResponse(
        app_name=settings.app_name,
        version=settings.app_version,
        default_provider="deepseek_strict" if settings.deepseek_enabled else settings.default_provider,
        available_providers=available,
        llm_enabled=settings.deepseek_enabled,
        model_name=settings.deepseek_model if settings.deepseek_enabled else None,
        cors_origins=settings.cors_origins,
    )


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_resume(payload: AnalyzeRequest, authorization: str | None = Header(default=None)) -> AnalyzeResponse:
    result = analyzer.analyze(payload)
    user_id = payload.user_id
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        user_id = store.get_user_by_token(token).id
    return store.save_analysis(user_id, result)
