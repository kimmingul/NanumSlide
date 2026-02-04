# src/agents/orchestrator.py
"""에이전트 오케스트레이터 - 전체 생성 프로세스 관리"""

from typing import Callable, Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass

from .base_agent import BaseAgent, AgentResult, AgentStatus
from .agent_context import (
    AgentContext,
    ContextStatus,
    UserInput,
    ResearchContext,
    DesignContext,
    SlideDesign
)
from .research_agent import ResearchAgent
from .content_agent import ContentAgent
from .design_agent import DesignAgent
from .image_agent import ImageAgent
from .review_agent import ReviewAgent

if TYPE_CHECKING:
    from src.services.llm_client import BaseLLMClient


@dataclass
class ExecutionPhase:
    """실행 단계 정의"""
    name: str
    agent: BaseAgent
    depends_on: List[str]  # 의존하는 이전 단계
    progress_start: float
    progress_end: float


class AgentOrchestrator:
    """에이전트 오케스트레이터"""

    def __init__(
        self,
        llm_client: "BaseLLMClient",
        image_service: Any,
        web_search_service: Optional[Any] = None,
        config: Optional[Dict] = None
    ):
        self.llm_client = llm_client
        self.image_service = image_service
        self.web_search_service = web_search_service
        self.config = config or {}

        # 에이전트 초기화
        self._init_agents()

        # 콜백
        self._progress_callback: Optional[Callable[[float, str], None]] = None
        self._phase_callback: Optional[Callable[[str], None]] = None

    def _init_agents(self) -> None:
        """에이전트 초기화"""
        self.research_agent = ResearchAgent(
            llm_client=self.llm_client,
            web_search_service=self.web_search_service
        )
        self.content_agent = ContentAgent(
            llm_client=self.llm_client
        )
        self.design_agent = DesignAgent(
            llm_client=self.llm_client
        )
        self.image_agent = ImageAgent(
            llm_client=self.llm_client,
            image_service=self.image_service
        )
        self.review_agent = ReviewAgent(
            llm_client=self.llm_client
        )

    def set_progress_callback(
        self,
        callback: Callable[[float, str], None]
    ) -> None:
        """진행 상태 콜백 설정"""
        self._progress_callback = callback

    def set_phase_callback(
        self,
        callback: Callable[[str], None]
    ) -> None:
        """단계 변경 콜백 설정"""
        self._phase_callback = callback

    def _report_progress(self, progress: float, message: str) -> None:
        """진행 상태 보고"""
        if self._progress_callback:
            self._progress_callback(progress, message)

    def _report_phase(self, phase: str) -> None:
        """단계 변경 보고"""
        if self._phase_callback:
            self._phase_callback(phase)

    async def generate(
        self,
        user_input: UserInput
    ) -> AgentContext:
        """프레젠테이션 생성 실행"""

        # 컨텍스트 초기화
        context = AgentContext(user_input=user_input)
        context.status = ContextStatus.IN_PROGRESS

        try:
            # Phase 1: 리서치 (0% ~ 20%)
            self._report_progress(0, "주제 리서치 중...")
            self._report_phase("research")
            context.set_phase("research", 0)

            research_result = await self.research_agent.run(context)
            if research_result.success:
                context.research = research_result.data
            else:
                # 리서치 실패 시에도 계속 진행 (선택적)
                context.research = ResearchContext(summary="리서치 스킵됨")

            self._report_progress(20, "리서치 완료")

            # Phase 2: 콘텐츠 생성 (20% ~ 50%)
            self._report_progress(20, "콘텐츠 작성 중...")
            self._report_phase("content")
            context.set_phase("content", 20)

            content_result = await self.content_agent.run(context)
            if not content_result.success:
                raise Exception(f"콘텐츠 생성 실패: {content_result.error}")
            context.content = content_result.data

            self._report_progress(50, "콘텐츠 작성 완료")

            # Phase 3: 디자인 결정 (50% ~ 60%)
            self._report_progress(50, "디자인 계획 중...")
            self._report_phase("design")
            context.set_phase("design", 50)

            design_result = await self.design_agent.run(context)
            if design_result.success:
                context.design = design_result.data
            else:
                # 기본 디자인 적용
                context.design = self._get_default_design(context)

            self._report_progress(60, "디자인 계획 완료")

            # Phase 4: 이미지/미디어 생성 (60% ~ 90%)
            self._report_progress(60, "이미지 생성 중...")
            self._report_phase("media")
            context.set_phase("media", 60)

            media_result = await self.image_agent.run(context)
            if media_result.success:
                context.media = media_result.data

            self._report_progress(90, "이미지 생성 완료")

            # Phase 5: 품질 검토 (90% ~ 100%)
            self._report_progress(90, "품질 검토 중...")
            self._report_phase("review")
            context.set_phase("review", 90)

            review_result = await self.review_agent.run(context)
            context.review = review_result.data

            # 심각한 이슈가 있으면 자동 수정 시도
            if context.review and not context.review.passed:
                await self._apply_review_fixes(context)

            self._report_progress(100, "생성 완료")
            self._report_phase("completed")
            context.status = ContextStatus.COMPLETED

        except Exception as e:
            context.status = ContextStatus.FAILED
            self._report_phase("failed")
            raise

        return context

    async def _apply_review_fixes(self, context: AgentContext) -> None:
        """리뷰 피드백 기반 자동 수정"""
        if not context.review or not context.review.issues:
            return

        critical_issues = [
            issue for issue in context.review.issues
            if issue.severity == "critical"
        ]

        for issue in critical_issues:
            # 이슈 유형별 자동 수정 로직
            if issue.issue_type == "consistency":
                # 일관성 문제 수정
                pass
            elif issue.issue_type == "quality":
                # 품질 문제 수정
                pass

    def _get_default_design(self, context: AgentContext) -> DesignContext:
        """기본 디자인 컨텍스트 생성"""
        slides = []

        if context.content and context.content.slides:
            for i, slide in enumerate(context.content.slides):
                layout = "title" if i == 0 else "title_content"
                slides.append(SlideDesign(index=i, layout_type=layout))

        return DesignContext(
            template_id="default",
            color_scheme=context.user_input.theme,
            slides=slides
        )

    def get_agents(self) -> Dict[str, BaseAgent]:
        """모든 에이전트 반환"""
        return {
            "research": self.research_agent,
            "content": self.content_agent,
            "design": self.design_agent,
            "image": self.image_agent,
            "review": self.review_agent
        }

    def get_agent_status(self) -> Dict[str, AgentStatus]:
        """모든 에이전트 상태 반환"""
        return {
            "research": self.research_agent.status,
            "content": self.content_agent.status,
            "design": self.design_agent.status,
            "image": self.image_agent.status,
            "review": self.review_agent.status
        }
