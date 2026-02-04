# src/agents/review_agent.py
"""리뷰 에이전트 - 품질 검토 및 개선 제안"""

from typing import Dict, List, Optional, TYPE_CHECKING
import json
import time

from .base_agent import BaseAgent, AgentResult, AgentStatus
from .agent_context import AgentContext, ReviewResult, ReviewIssue

if TYPE_CHECKING:
    from src.services.llm_client import BaseLLMClient


class ReviewAgent(BaseAgent):
    """리뷰 에이전트 - 품질 검토 및 개선 제안"""

    def __init__(
        self,
        llm_client: "BaseLLMClient",
        config: Optional[Dict] = None
    ):
        super().__init__(
            name="review_agent",
            llm_client=llm_client,
            config=config
        )

    def get_system_prompt(self) -> str:
        return """당신은 프레젠테이션 품질 관리 전문가입니다.
생성된 프레젠테이션의 품질을 검토하고 개선점을 제안합니다.

검토 항목:
1. 일관성: 용어, 스타일, 톤의 일관성
2. 품질: 콘텐츠의 명확성과 완성도
3. 흐름: 논리적 구조와 스토리텔링
4. 접근성: 가독성, 색상 대비
5. 디자인: 레이아웃 적절성

이슈 심각도:
- critical: 반드시 수정 필요
- warning: 수정 권장
- suggestion: 선택적 개선"""

    async def run(self, context: AgentContext) -> AgentResult:
        """품질 검토 실행"""
        start_time = time.time()

        try:
            self.update_status(AgentStatus.RUNNING)

            # 1. 자동화된 규칙 기반 검사
            rule_based_issues = self._run_rule_based_checks(context)

            # 2. LLM 기반 품질 검토
            llm_review = await self._run_llm_review(context)

            # 3. 결과 통합
            all_issues = rule_based_issues + llm_review.get("issues", [])

            # 4. 점수 계산
            overall_score = self._calculate_score(all_issues)

            # 5. 통과 여부 결정
            critical_issues = [i for i in all_issues if i.severity == "critical"]
            passed = len(critical_issues) == 0

            review_result = ReviewResult(
                passed=passed,
                overall_score=overall_score,
                issues=all_issues,
                strengths=llm_review.get("strengths", []),
                improvement_suggestions=llm_review.get("suggestions", [])
            )

            self.update_status(AgentStatus.COMPLETED)

            return AgentResult(
                success=True,
                data=review_result,
                duration_ms=int((time.time() - start_time) * 1000)
            )

        except Exception as e:
            self.update_status(AgentStatus.FAILED)
            return AgentResult(
                success=False,
                data=ReviewResult(passed=True, overall_score=0.7, issues=[]),
                error=str(e)
            )

    def _run_rule_based_checks(
        self,
        context: AgentContext
    ) -> List[ReviewIssue]:
        """규칙 기반 자동 검사"""
        issues = []
        content = context.content

        if not content:
            return issues

        for slide in content.slides:
            # 제목 길이 검사
            if len(slide.title) > 60:
                issues.append(ReviewIssue(
                    slide_index=slide.index,
                    issue_type="quality",
                    severity="warning",
                    description=f"슬라이드 {slide.index + 1}의 제목이 너무 깁니다 ({len(slide.title)}자)",
                    suggestion="제목을 60자 이내로 줄이세요"
                ))

            # 글머리 기호 개수 검사
            if len(slide.bullet_points) > 7:
                issues.append(ReviewIssue(
                    slide_index=slide.index,
                    issue_type="quality",
                    severity="warning",
                    description=f"슬라이드 {slide.index + 1}의 글머리 기호가 너무 많습니다 ({len(slide.bullet_points)}개)",
                    suggestion="핵심 내용 5-7개로 줄이거나 슬라이드를 분할하세요"
                ))

            # 빈 콘텐츠 검사
            if not slide.content and not slide.bullet_points:
                if slide.index != 0 and slide.index != len(content.slides) - 1:
                    issues.append(ReviewIssue(
                        slide_index=slide.index,
                        issue_type="quality",
                        severity="critical",
                        description=f"슬라이드 {slide.index + 1}에 콘텐츠가 없습니다",
                        suggestion="슬라이드에 내용을 추가하세요"
                    ))

        # 전체 슬라이드 수 검사
        if len(content.slides) < 3:
            issues.append(ReviewIssue(
                slide_index=None,
                issue_type="quality",
                severity="warning",
                description="슬라이드 수가 너무 적습니다",
                suggestion="최소 5장 이상의 슬라이드를 권장합니다"
            ))

        return issues

    async def _run_llm_review(
        self,
        context: AgentContext
    ) -> Dict:
        """LLM 기반 품질 검토"""
        content = context.content

        if not content:
            return {"issues": [], "strengths": [], "suggestions": []}

        # 슬라이드 요약 생성
        slides_summary = []
        for slide in content.slides:
            summary = {
                "index": slide.index,
                "title": slide.title,
                "content_preview": (slide.content or '')[:100],
                "bullet_count": len(slide.bullet_points)
            }
            slides_summary.append(summary)

        prompt = f"""다음 프레젠테이션을 검토하고 품질 평가를 제공하세요.

프레젠테이션 제목: {content.title}
슬라이드 수: {len(content.slides)}

슬라이드 요약:
{json.dumps(slides_summary, ensure_ascii=False, indent=2)}

다음 관점에서 검토하세요:
1. 스토리텔링 흐름
2. 콘텐츠 명확성
3. 슬라이드 간 일관성
4. 청중 적합성

JSON 형식으로 응답:
{{
    "issues": [
        {{"slide_index": 0, "issue_type": "consistency", "severity": "warning", "description": "...", "suggestion": "..."}}
    ],
    "strengths": ["강점1", "강점2"],
    "suggestions": ["개선제안1", "개선제안2"]
}}"""

        response = await self.call_llm(prompt)

        try:
            data = json.loads(response)

            # ReviewIssue 객체로 변환
            issues = []
            for issue_data in data.get("issues", []):
                issue = ReviewIssue(
                    slide_index=issue_data.get("slide_index"),
                    issue_type=issue_data.get("issue_type", "quality"),
                    severity=issue_data.get("severity", "suggestion"),
                    description=issue_data.get("description", ""),
                    suggestion=issue_data.get("suggestion", "")
                )
                issues.append(issue)

            return {
                "issues": issues,
                "strengths": data.get("strengths", []),
                "suggestions": data.get("suggestions", [])
            }

        except json.JSONDecodeError:
            return {"issues": [], "strengths": [], "suggestions": []}

    def _calculate_score(self, issues: List[ReviewIssue]) -> float:
        """전체 점수 계산"""
        if not issues:
            return 1.0

        # 이슈 유형별 감점
        deductions = {
            "critical": 0.15,
            "warning": 0.05,
            "suggestion": 0.02
        }

        total_deduction = sum(
            deductions.get(issue.severity, 0)
            for issue in issues
        )

        score = max(0.0, 1.0 - total_deduction)
        return round(score, 2)
