# src/agents/content_agent.py
"""콘텐츠 에이전트 - 슬라이드 내용 작성"""

from typing import Dict, List, Optional, TYPE_CHECKING
import json
import time

from .base_agent import BaseAgent, AgentResult, AgentStatus
from .agent_context import AgentContext, ContentContext, SlideContent

if TYPE_CHECKING:
    from src.services.llm_client import BaseLLMClient


class ContentAgent(BaseAgent):
    """콘텐츠 에이전트 - 슬라이드 내용 작성"""

    def __init__(
        self,
        llm_client: "BaseLLMClient",
        config: Optional[Dict] = None
    ):
        super().__init__(
            name="content_agent",
            llm_client=llm_client,
            config=config
        )

    def get_system_prompt(self) -> str:
        return """당신은 프레젠테이션 콘텐츠 전문 작가입니다.
주어진 정보를 바탕으로 설득력 있고 구조화된 프레젠테이션 콘텐츠를 작성합니다.

핵심 원칙:
1. 명확한 스토리라인 구축
2. 슬라이드당 하나의 핵심 메시지
3. 간결하고 임팩트 있는 문장
4. 청중 중심의 콘텐츠
5. 논리적 흐름과 전환

각 슬라이드는 다음을 포함합니다:
- 제목 (명확하고 간결)
- 본문 내용 또는 글머리 기호
- 발표자 노트 (상세 설명)
- 핵심 메시지 (슬라이드의 takeaway)"""

    async def run(self, context: AgentContext) -> AgentResult:
        """콘텐츠 생성 실행"""
        start_time = time.time()

        try:
            self.update_status(AgentStatus.RUNNING)

            # 1. 전체 개요 생성
            outline = await self._generate_outline(context)

            # 2. 각 슬라이드 콘텐츠 상세 작성
            slides = await self._generate_slide_contents(
                context,
                outline
            )

            # 3. 발표자 노트 생성
            slides_with_notes = await self._generate_speaker_notes(
                context,
                slides
            )

            # 4. 전환 문구 추가
            final_slides = self._add_transitions(slides_with_notes)

            content_context = ContentContext(
                title=outline["title"],
                subtitle=outline.get("subtitle", ""),
                slides=final_slides,
                overall_narrative=outline.get("narrative", ""),
                key_takeaways=outline.get("takeaways", [])
            )

            self.update_status(AgentStatus.COMPLETED)

            return AgentResult(
                success=True,
                data=content_context,
                duration_ms=int((time.time() - start_time) * 1000)
            )

        except Exception as e:
            self.update_status(AgentStatus.FAILED)
            return AgentResult(
                success=False,
                data=None,
                error=str(e)
            )

    async def _generate_outline(
        self,
        context: AgentContext
    ) -> Dict:
        """프레젠테이션 개요 생성"""
        user_input = context.user_input
        research = context.research

        # 리서치 컨텍스트 구성
        research_context = ""
        if research:
            research_context = f"""
리서치 결과:
- 핵심 포인트: {', '.join(research.key_points[:5])}
- 주요 트렌드: {', '.join(research.trends[:3])}
- 요약: {research.summary}
"""

        prompt = f"""다음 정보를 바탕으로 프레젠테이션 개요를 작성하세요.

주제: {user_input.topic}
슬라이드 수: {user_input.slide_count}
언어: {user_input.language}
대상 청중: {user_input.audience or '일반'}
발표 목적: {user_input.purpose or '정보 전달'}
{research_context}

개요에 포함할 내용:
1. 프레젠테이션 제목
2. 부제목 (선택)
3. 각 슬라이드의 제목과 간략한 내용 설명
4. 전체 스토리라인
5. 핵심 takeaway (3-5개)

JSON 형식으로 응답하세요."""

        response = await self.call_llm(
            prompt=prompt,
            json_schema=self._get_outline_schema()
        )

        return json.loads(response)

    async def _generate_slide_contents(
        self,
        context: AgentContext,
        outline: Dict
    ) -> List[SlideContent]:
        """각 슬라이드 상세 콘텐츠 생성"""
        slides = []

        for i, slide_outline in enumerate(outline.get("slides", [])):
            slide_content = await self._generate_single_slide(
                context,
                slide_outline,
                i,
                len(outline["slides"])
            )
            slides.append(slide_content)

        return slides

    async def _generate_single_slide(
        self,
        context: AgentContext,
        slide_outline: Dict,
        index: int,
        total: int
    ) -> SlideContent:
        """단일 슬라이드 콘텐츠 생성"""
        user_input = context.user_input

        position = "첫 번째 (도입)" if index == 0 else \
                   "마지막 (결론)" if index == total - 1 else \
                   f"{index + 1}번째"

        prompt = f"""다음 슬라이드의 상세 콘텐츠를 작성하세요.

슬라이드 위치: {position} / 전체 {total}장
슬라이드 제목: {slide_outline.get('title', '')}
슬라이드 개요: {slide_outline.get('description', '')}

대상 청중: {user_input.audience or '일반'}
언어: {user_input.language}

작성 지침:
- 제목: 명확하고 간결하게 (10단어 이내)
- 본문: 핵심 내용만 (3-4문장 또는 글머리 기호 3-5개)
- 핵심 메시지: 청중이 기억해야 할 한 문장

JSON 형식으로 응답하세요."""

        response = await self.call_llm(
            prompt=prompt,
            json_schema=self._get_slide_content_schema()
        )

        data = json.loads(response)

        return SlideContent(
            index=index,
            title=data.get("title", slide_outline.get("title", "")),
            content=data.get("content", ""),
            bullet_points=data.get("bullet_points", []),
            key_message=data.get("key_message", "")
        )

    async def _generate_speaker_notes(
        self,
        context: AgentContext,
        slides: List[SlideContent]
    ) -> List[SlideContent]:
        """발표자 노트 생성"""
        user_input = context.user_input

        prompt = f"""다음 슬라이드들의 발표자 노트를 작성하세요.

발표 시간: {user_input.duration_minutes or 10}분
청중: {user_input.audience or '일반'}

슬라이드 목록:
{self._format_slides_for_notes(slides)}

각 슬라이드에 대해 발표자가 참고할 상세 노트를 작성하세요.
- 설명할 핵심 포인트
- 예시나 사례
- 청중 참여 유도 멘트 (적절한 경우)

JSON 형식으로 응답하세요: {{"notes": ["슬라이드1 노트", "슬라이드2 노트", ...]}}"""

        response = await self.call_llm(prompt)

        try:
            data = json.loads(response)
            notes_list = data.get("notes", [])

            for i, slide in enumerate(slides):
                if i < len(notes_list):
                    slide.notes = notes_list[i]

        except json.JSONDecodeError:
            pass

        return slides

    def _add_transitions(
        self,
        slides: List[SlideContent]
    ) -> List[SlideContent]:
        """슬라이드 간 전환 문구 추가"""
        for i in range(1, len(slides)):
            prev_title = slides[i - 1].title
            # 간단한 전환 문구 생성
            slides[i].transition_text = f"'{prev_title}'에 이어서..."

        return slides

    def _format_slides_for_notes(self, slides: List[SlideContent]) -> str:
        """노트 생성용 슬라이드 포맷"""
        formatted = []
        for slide in slides:
            content = slide.content or ', '.join(slide.bullet_points[:3])
            formatted.append(f"[{slide.index + 1}] {slide.title}: {content[:100]}")
        return '\n'.join(formatted)

    def _get_outline_schema(self) -> Dict:
        """개요 스키마"""
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "subtitle": {"type": "string"},
                "slides": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    }
                },
                "narrative": {"type": "string"},
                "takeaways": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["title", "slides"]
        }

    def _get_slide_content_schema(self) -> Dict:
        """슬라이드 콘텐츠 스키마"""
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "bullet_points": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "key_message": {"type": "string"}
            },
            "required": ["title"]
        }
