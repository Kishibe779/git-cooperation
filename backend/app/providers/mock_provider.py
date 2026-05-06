from app.providers.base import ProviderResult, SuggestionProvider


class MockSuggestionProvider(SuggestionProvider):
    def generate(self, context: dict, fallback: ProviderResult) -> ProviderResult:
        score = context["score"]
        matched = "、".join(context["matched_keywords"][:4]) or "核心经历"
        missing = "、".join(context["missing_keywords"][:3]) or "量化成果、岗位关键词和业务闭环"
        focus = "、".join(context["resume_focus"][:3]) or "项目执行、结果交付、跨团队协作"

        return ProviderResult(
            summary=(
                f"该简历与目标岗位的匹配度为 {score} 分，当前优势主要集中在 {matched}。"
                f"若要提升通过率，建议优先补充 {missing} 相关证据，并强化结果导向描述。"
            ),
            optimized_summary=(
                f"具备扎实的 {focus} 经验，能够围绕 {context['target_role']} 的核心目标快速梳理需求、"
                "推动执行并通过量化结果证明价值，适合承担从方案落地到持续优化的完整工作闭环。"
            ),
            strengths=fallback.strengths,
            risks=fallback.risks,
            suggestion_sections=fallback.suggestion_sections,
            tailored_bullets=fallback.tailored_bullets,
            provider_used="mock",
            model_used=None,
            fallback_used=False,
            llm_enabled=False,
        )
