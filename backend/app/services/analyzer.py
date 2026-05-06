from __future__ import annotations

import re
from collections import Counter

from app.core.config import get_provider_settings
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, MatchOverview, ProviderMeta, SuggestionSection
from app.providers.base import ProviderResult
from app.providers.factory import build_provider


class ResumeAnalyzer:
    keyword_groups = {
        "Python 开发": ["python", "fastapi", "django", "flask"],
        "数据分析": ["sql", "数据分析", "pandas", "numpy", "bi", "报表"],
        "前端协作": ["javascript", "typescript", "vue", "react", "前端", "页面"],
        "项目管理": ["项目管理", "需求分析", "排期", "甘特图", "里程碑", "风险"],
        "沟通协作": ["沟通", "协作", "跨部门", "团队合作", "汇报"],
        "结果导向": ["增长", "优化", "提升", "转化", "效率", "成本", "交付"],
        "AI 应用": ["llm", "大模型", "提示词", "rag", "embedding", "openai", "deepseek", "智能体"],
        "文档表达": ["文档", "报告", "总结", "方案", "ppt", "汇总"],
    }

    stop_words = {
        "负责",
        "熟悉",
        "参与",
        "使用",
        "进行",
        "能够",
        "相关",
        "工作",
        "项目",
        "经验",
        "系统",
        "开发",
        "能力",
        "优化",
        "设计",
        "实现",
        "以及",
        "岗位",
        "需求",
        "用户",
        "完成",
    }

    def analyze(self, payload: AnalyzeRequest) -> AnalyzeResponse:
        resume_text = self._normalize(payload.resume_text)
        job_text = self._normalize(payload.job_description)

        matched_keywords, missing_keywords = self._compare_keywords(resume_text, job_text)
        keyword_density = self._keyword_density(resume_text)
        resume_focus = self._extract_focus_terms(resume_text)
        score = self._calculate_score(matched_keywords, missing_keywords, keyword_density)

        fallback = self._build_fallback_content(
            candidate_name=payload.candidate_name,
            target_role=payload.target_role,
            score=score,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            keyword_density=keyword_density,
            resume_focus=resume_focus,
            resume_text=resume_text,
        )

        context = {
            "candidate_name": payload.candidate_name,
            "target_role": payload.target_role,
            "score": score,
            "matched_keywords": matched_keywords,
            "missing_keywords": missing_keywords,
            "resume_focus": resume_focus,
            "keyword_density": keyword_density,
            "resume_text": payload.resume_text.strip(),
            "job_description": payload.job_description.strip(),
        }
        provider = build_provider(get_provider_settings(payload.provider))
        generated = provider.generate(context=context, fallback=fallback)

        return AnalyzeResponse(
            candidate_name=payload.candidate_name,
            target_role=payload.target_role,
            provider_meta=ProviderMeta(
                provider_used=generated.provider_used,
                model_used=generated.model_used,
                fallback_used=generated.fallback_used,
                llm_enabled=generated.llm_enabled,
            ),
            summary=generated.summary,
            match_overview=MatchOverview(
                score=score,
                matched_keywords=matched_keywords,
                missing_keywords=missing_keywords,
                resume_focus=resume_focus,
            ),
            strengths=generated.strengths,
            risks=generated.risks,
            suggestion_sections=[
                SuggestionSection(title=str(section["title"]), items=list(section["items"]))
                for section in generated.suggestion_sections
            ],
            optimized_summary=generated.optimized_summary,
            tailored_bullets=generated.tailored_bullets,
            keyword_density=keyword_density,
            report_markdown=self._build_markdown_report(
                candidate_name=payload.candidate_name,
                target_role=payload.target_role,
                generated=generated,
                score=score,
                matched_keywords=matched_keywords,
                missing_keywords=missing_keywords,
                keyword_density=keyword_density,
            ),
        )

    def _build_fallback_content(
        self,
        *,
        candidate_name: str,
        target_role: str,
        score: int,
        matched_keywords: list[str],
        missing_keywords: list[str],
        keyword_density: dict[str, int],
        resume_focus: list[str],
        resume_text: str,
    ) -> ProviderResult:
        strengths = self._build_strengths(matched_keywords, keyword_density, resume_text)
        risks = self._build_risks(missing_keywords, resume_text)
        suggestion_sections = self._build_sections(matched_keywords, missing_keywords, keyword_density)
        focus = "、".join(resume_focus[:3]) or "项目执行、结果交付、跨团队协作"
        matched = "、".join(matched_keywords[:4]) or "基础能力"
        missing = "、".join(missing_keywords[:3]) or "量化成果、岗位关键词和业务闭环"

        return ProviderResult(
            summary=(
                f"{candidate_name} 当前与 {target_role} 的匹配度为 {score} 分，优势主要体现在 {matched}。"
                f"建议优先补充 {missing} 的直接证据，并用结果导向句式改写经历。"
            ),
            optimized_summary=(
                f"具备 {focus} 相关经验，能够围绕 {target_role} 的关键目标梳理需求、推进执行，"
                "并通过可量化结果证明个人价值。"
            ),
            strengths=strengths,
            risks=risks,
            suggestion_sections=suggestion_sections,
            tailored_bullets=self._build_tailored_bullets(target_role, matched_keywords, missing_keywords),
            provider_used="mock",
            model_used=None,
            fallback_used=False,
            llm_enabled=False,
        )

    def _normalize(self, text: str) -> str:
        lowered = text.lower().replace("\r\n", "\n")
        return re.sub(r"\s+", " ", lowered).strip()

    def _compare_keywords(self, resume_text: str, job_text: str) -> tuple[list[str], list[str]]:
        matched: list[str] = []
        missing: list[str] = []
        for label, terms in self.keyword_groups.items():
            job_hit = any(term in job_text for term in terms)
            resume_hit = any(term in resume_text for term in terms)
            if job_hit and resume_hit:
                matched.append(label)
            elif job_hit and not resume_hit:
                missing.append(label)
        return matched[:6], missing[:6]

    def _keyword_density(self, resume_text: str) -> dict[str, int]:
        density: dict[str, int] = {}
        for label, terms in self.keyword_groups.items():
            density[label] = sum(resume_text.count(term) for term in terms)
        return density

    def _extract_focus_terms(self, resume_text: str) -> list[str]:
        tokens = re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z]{3,}", resume_text)
        cleaned = [token for token in tokens if token not in self.stop_words and len(token) > 1]
        counts = Counter(cleaned)
        return [term for term, _ in counts.most_common(5)]

    def _calculate_score(
        self,
        matched_keywords: list[str],
        missing_keywords: list[str],
        keyword_density: dict[str, int],
    ) -> int:
        match_part = len(matched_keywords) * 12
        missing_penalty = len(missing_keywords) * 6
        density_bonus = min(sum(1 for count in keyword_density.values() if count > 0) * 2, 16)
        score = 45 + match_part + density_bonus - missing_penalty
        return max(35, min(96, score))

    def _build_strengths(
        self,
        matched_keywords: list[str],
        keyword_density: dict[str, int],
        resume_text: str,
    ) -> list[str]:
        strengths: list[str] = []
        if matched_keywords:
            strengths.append(f"已覆盖岗位关键能力：{'、'.join(matched_keywords[:4])}。")
        dense_terms = [label for label, count in keyword_density.items() if count >= 2]
        if dense_terms:
            strengths.append(f"简历对 {'、'.join(dense_terms[:3])} 的表达较充分，便于招聘方快速识别能力。")
        if any(token in resume_text for token in ["提升", "%", "降低", "增长", "缩短"]):
            strengths.append("包含量化结果或业务改进描述，能增强说服力。")
        if not strengths:
            strengths.append("简历整体信息完整，具备继续优化为岗位定制版的基础。")
        return strengths[:4]

    def _build_risks(self, missing_keywords: list[str], resume_text: str) -> list[str]:
        risks: list[str] = []
        if missing_keywords:
            risks.append(f"岗位强调 {'、'.join(missing_keywords[:4])}，但简历中缺少直接证据。")
        if "负责" in resume_text and not any(token in resume_text for token in ["提升", "增长", "优化", "降低"]):
            risks.append("职责描述偏多，量化成果偏少，可能影响简历筛选效率。")
        if len(resume_text) < 180:
            risks.append("当前简历信息较短，建议补充项目背景、行动过程和结果指标。")
        if not risks:
            risks.append("当前没有明显结构性风险，建议进一步贴合目标岗位措辞。")
        return risks[:4]

    def _build_sections(
        self,
        matched_keywords: list[str],
        missing_keywords: list[str],
        keyword_density: dict[str, int],
    ) -> list[dict[str, list[str] | str]]:
        emphasis = [label for label, count in keyword_density.items() if count > 0][:4]
        if not emphasis:
            emphasis = ["项目成果", "业务价值", "沟通协作"]
        missing = missing_keywords or ["岗位关键词", "量化结果", "项目闭环"]

        return [
            {
                "title": "优先保留",
                "items": [f"继续强化 {item} 相关项目经历，用结果句式表达。" for item in emphasis[:3]],
            },
            {
                "title": "重点补强",
                "items": [f"补充 {item} 的具体案例、指标或工具使用细节。" for item in missing[:3]],
            },
            {
                "title": "改写建议",
                "items": [
                    "将“负责某项工作”改写为“在什么场景下，通过什么方法，带来了什么结果”。",
                    "每段项目经历尽量包含背景、动作、结果三部分，方便面试官快速判断价值。",
                    "将最贴合岗位的项目放在前面，弱相关经历压缩为 1 到 2 行。",
                ],
            },
        ]

    def _build_tailored_bullets(
        self,
        target_role: str,
        matched_keywords: list[str],
        missing_keywords: list[str],
    ) -> list[str]:
        primary_match = matched_keywords[0] if matched_keywords else "核心能力"
        primary_gap = missing_keywords[0] if missing_keywords else "量化成果"
        return [
            f"围绕 {target_role} 重新排列项目顺序，将最能证明 {primary_match} 的经历放在前两段。",
            f"将职责描述改写为结果描述，尤其补充与 {primary_gap} 相关的指标、方法和业务影响。",
            "每段项目经历使用“背景-行动-结果”结构，控制在 2 到 3 句内，提升 HR 首轮阅读效率。",
        ]

    def _build_markdown_report(
        self,
        *,
        candidate_name: str,
        target_role: str,
        generated: ProviderResult,
        score: int,
        matched_keywords: list[str],
        missing_keywords: list[str],
        keyword_density: dict[str, int],
    ) -> str:
        section_lines: list[str] = []
        for section in generated.suggestion_sections:
            section_lines.append(f"### {section['title']}")
            for item in section["items"]:
                section_lines.append(f"- {item}")
            section_lines.append("")

        return "\n".join(
            [
                f"# {candidate_name} 的简历优化报告",
                "",
                f"- 目标岗位：{target_role}",
                f"- 匹配得分：{score}",
                f"- 生成方式：{generated.provider_used}"
                + (f" / {generated.model_used}" if generated.model_used else ""),
                "",
                "## 综合结论",
                generated.summary,
                "",
                "## 优化摘要",
                generated.optimized_summary,
                "",
                "## 匹配关键词",
                ", ".join(matched_keywords) if matched_keywords else "暂无明显匹配项",
                "",
                "## 缺失关键词",
                ", ".join(missing_keywords) if missing_keywords else "暂无明显缺口",
                "",
                "## 简历优势",
                *[f"- {item}" for item in generated.strengths],
                "",
                "## 风险提示",
                *[f"- {item}" for item in generated.risks],
                "",
                "## 定制化改写建议",
                *[f"- {item}" for item in generated.tailored_bullets],
                "",
                "## 关键词分布",
                *[f"- {label}: {count}" for label, count in keyword_density.items()],
                "",
                *section_lines,
            ]
        ).strip()
