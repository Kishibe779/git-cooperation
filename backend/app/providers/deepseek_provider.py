from __future__ import annotations

import json

import httpx

from app.core.config import ProviderSettings
from app.core.errors import ProviderConfigurationError, ProviderRequestError
from app.providers.base import ProviderResult, SuggestionProvider


class DeepSeekSuggestionProvider(SuggestionProvider):
    def __init__(self, settings: ProviderSettings) -> None:
        self.settings = settings

    def generate(self, context: dict, fallback: ProviderResult) -> ProviderResult:
        if not self.settings.api_key or not self.settings.base_url or not self.settings.model:
            raise ProviderConfigurationError("DeepSeek 尚未配置，请在服务端设置 DEEPSEEK_API_KEY。")

        payload = {
            "model": self.settings.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是专业的中文简历优化顾问。"
                        "必须返回合法 JSON，对候选人的简历进行岗位匹配与优化建议输出。"
                    ),
                },
                {"role": "user", "content": self._build_prompt(context, fallback)},
            ],
            "temperature": 0.4,
            "max_tokens": 1200,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self.settings.api_key}",
            "Content-Type": "application/json",
        }
        url = self.settings.base_url.rstrip("/") + "/chat/completions"

        try:
            with httpx.Client(timeout=self.settings.timeout_seconds) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            if self.settings.fallback_enabled:
                fallback.provider_used = "deepseek"
                fallback.model_used = self.settings.model
                fallback.fallback_used = True
                fallback.llm_enabled = True
                return fallback
            if status_code in {401, 403}:
                raise ProviderRequestError(
                    "DeepSeek authentication failed. Check DEEPSEEK_API_KEY, base URL, and model."
                ) from exc
            raise ProviderRequestError(f"DeepSeek request failed with HTTP {status_code}: {exc}") from exc
        except httpx.HTTPError as exc:
            if self.settings.fallback_enabled:
                fallback.provider_used = "deepseek"
                fallback.model_used = self.settings.model
                fallback.fallback_used = True
                fallback.llm_enabled = True
                return fallback
            raise ProviderRequestError(f"DeepSeek request failed: {exc}") from exc

        try:
            content = response.json()["choices"][0]["message"]["content"]
            parsed = self._parse_json_content(content)
            return ProviderResult(
                summary=str(parsed["summary"]).strip(),
                optimized_summary=str(parsed["optimized_summary"]).strip(),
                strengths=[str(item).strip() for item in parsed["strengths"]][:4],
                risks=[str(item).strip() for item in parsed["risks"]][:4],
                suggestion_sections=[
                    {
                        "title": str(section["title"]).strip(),
                        "items": [str(item).strip() for item in section["items"]][:4],
                    }
                    for section in parsed["suggestion_sections"][:3]
                ],
                tailored_bullets=[str(item).strip() for item in parsed["tailored_bullets"]][:4],
                provider_used="deepseek",
                model_used=self.settings.model,
                fallback_used=False,
                llm_enabled=True,
            )
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            if self.settings.fallback_enabled:
                fallback.provider_used = "deepseek"
                fallback.model_used = self.settings.model
                fallback.fallback_used = True
                fallback.llm_enabled = True
                return fallback
            raise ProviderRequestError(f"DeepSeek response parse failed: {exc}") from exc

    def _build_prompt(self, context: dict, fallback: ProviderResult) -> str:
        return (
            "请根据以下上下文生成简历优化结果，并返回 JSON。"
            "禁止输出 markdown，禁止解释。"
            "JSON 必须包含以下字段："
            "summary(string), optimized_summary(string), strengths(string[]), risks(string[]), "
            "suggestion_sections([{title:string, items:string[]}]), tailored_bullets(string[])."
            "请优先参考候选人的真实能力与岗位差距，不要夸大。"
            "\n上下文数据："
            + json.dumps(
                {
                    "candidate_name": context["candidate_name"],
                    "target_role": context["target_role"],
                    "score": context["score"],
                    "matched_keywords": context["matched_keywords"],
                    "missing_keywords": context["missing_keywords"],
                    "resume_focus": context["resume_focus"],
                    "keyword_density": context["keyword_density"],
                    "resume_text": context.get("resume_text", ""),
                    "job_description": context.get("job_description", ""),
                    "fallback": {
                        "summary": fallback.summary,
                        "optimized_summary": fallback.optimized_summary,
                        "strengths": fallback.strengths,
                        "risks": fallback.risks,
                        "suggestion_sections": fallback.suggestion_sections,
                        "tailored_bullets": fallback.tailored_bullets,
                    },
                },
                ensure_ascii=False,
            )
        )

    def _parse_json_content(self, content: str) -> dict:
        cleaned = content.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start >= 0 and end > start:
                return json.loads(cleaned[start : end + 1])
            raise
