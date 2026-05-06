from app.models.schemas import AnalyzeRequest
from app.services.analyzer import ResumeAnalyzer


def test_analyzer_returns_stable_structure() -> None:
    analyzer = ResumeAnalyzer()
    payload = AnalyzeRequest(
        candidate_name="张三",
        target_role="AI产品实习生",
        resume_text=(
            "负责使用 Python 和 FastAPI 开发简历分析工具，整理文档并与前端协作。"
            "通过优化流程将测试效率提升 30%，参与需求分析和项目排期。"
        ),
        job_description=(
            "岗位需要熟悉 Python、项目管理、沟通协作、文档表达，"
            "有 AI 应用或大模型相关经历更佳。"
        ),
        provider="mock",
    )

    result = analyzer.analyze(payload)

    assert result.match_overview.score >= 60
    assert "Python 开发" in result.match_overview.matched_keywords
    assert len(result.suggestion_sections) == 3
    assert result.optimized_summary
    assert result.provider_meta.provider_used == "mock"
    assert len(result.tailored_bullets) >= 1
