import json

import httpx

from app.core.config import ProviderSettings
from app.providers.base import ProviderResult
from app.providers.deepseek_provider import DeepSeekSuggestionProvider


def test_deepseek_provider_parses_json_response(monkeypatch) -> None:
    response_payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "summary": "匹配度较好，建议补充量化成果。",
                            "optimized_summary": "具备岗位所需能力，建议突出项目价值。",
                            "strengths": ["掌握 Python", "有协作经验"],
                            "risks": ["量化成果不足"],
                            "suggestion_sections": [
                                {"title": "优先保留", "items": ["保留 Python 项目"]},
                                {"title": "重点补强", "items": ["补充业务指标"]},
                                {"title": "改写建议", "items": ["使用结果导向句式"]},
                            ],
                            "tailored_bullets": ["重写首段项目经历"],
                        },
                        ensure_ascii=False,
                    )
                }
            }
        ]
    }

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return response_payload

    class FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)

    provider = DeepSeekSuggestionProvider(
        ProviderSettings(
            provider="deepseek",
            api_key="test",
            base_url="https://api.deepseek.com/v1",
            model="deepseek-chat",
        )
    )
    fallback = ProviderResult(
        summary="fallback",
        optimized_summary="fallback",
        strengths=["s1"],
        risks=["r1"],
        suggestion_sections=[{"title": "t", "items": ["i"]}],
        tailored_bullets=["b1"],
        provider_used="mock",
    )

    result = provider.generate(
        context={
            "candidate_name": "张三",
            "target_role": "后端工程师",
            "score": 82,
            "matched_keywords": ["Python 开发"],
            "missing_keywords": ["结果导向"],
            "resume_focus": ["python", "fastapi"],
            "keyword_density": {"Python 开发": 2},
        },
        fallback=fallback,
    )

    assert result.provider_used == "deepseek"
    assert result.model_used == "deepseek-chat"
    assert result.summary
