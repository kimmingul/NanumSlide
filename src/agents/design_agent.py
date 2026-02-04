# src/agents/design_agent.py
"""디자인 에이전트 - 레이아웃 및 시각적 요소 결정"""

from typing import Dict, List, Optional, TYPE_CHECKING
import json
import time

from .base_agent import BaseAgent, AgentResult, AgentStatus
from .agent_context import AgentContext, DesignContext, SlideDesign

if TYPE_CHECKING:
    from src.services.llm_client import BaseLLMClient


class DesignAgent(BaseAgent):
    """디자인 에이전트 - 레이아웃 및 시각적 요소 결정"""

    # 사용 가능한 레이아웃 타입
    LAYOUT_TYPES = [
        "title",            # 제목 슬라이드
        "title_content",    # 제목 + 본문
        "two_column",       # 2단 레이아웃
        "title_image",      # 제목 + 이미지
        "image_left",       # 왼쪽 이미지 + 오른쪽 텍스트
        "image_right",      # 오른쪽 이미지 + 왼쪽 텍스트
        "image_full",       # 전체 이미지
        "bullet_points",    # 글머리 기호
        "comparison",       # 비교 레이아웃
        "timeline",         # 타임라인
        "chart",            # 차트 중심
        "quote",            # 인용문
        "team",             # 팀 소개
        "contact",          # 연락처/CTA
    ]

    def __init__(
        self,
        llm_client: "BaseLLMClient",
        config: Optional[Dict] = None
    ):
        super().__init__(
            name="design_agent",
            llm_client=llm_client,
            config=config
        )

    def get_system_prompt(self) -> str:
        return f"""당신은 프레젠테이션 디자인 전문가입니다.
콘텐츠에 최적화된 레이아웃과 시각적 요소를 결정합니다.

사용 가능한 레이아웃:
{', '.join(self.LAYOUT_TYPES)}

디자인 원칙:
1. 콘텐츠 유형에 맞는 레이아웃 선택
2. 시각적 다양성 유지 (연속 동일 레이아웃 지양)
3. 핵심 메시지 강조를 위한 시각화
4. 일관된 색상 및 폰트 사용
5. 청중의 주목을 끄는 디자인

제목 슬라이드 = title
마지막 슬라이드 = title 또는 contact
데이터/통계 = chart
비교 내용 = comparison 또는 two_column
스토리/시간순 = timeline
일반 내용 = title_content, bullet_points, image_left, image_right"""

    async def run(self, context: AgentContext) -> AgentResult:
        """디자인 결정 실행"""
        start_time = time.time()

        try:
            self.update_status(AgentStatus.RUNNING)

            user_input = context.user_input

            # 1. 적합한 템플릿 선택
            template_id = await self._select_template(context)

            # 2. 각 슬라이드 레이아웃 결정
            slide_designs = await self._assign_layouts(context)

            # 3. 색상 스키마 결정
            color_scheme = self._determine_color_scheme(user_input.theme)

            # 4. 폰트 페어링 결정
            font_pairing = self._determine_font_pairing(user_input.style)

            design_context = DesignContext(
                template_id=template_id,
                color_scheme=color_scheme,
                font_pairing=font_pairing,
                slides=slide_designs
            )

            self.update_status(AgentStatus.COMPLETED)

            return AgentResult(
                success=True,
                data=design_context,
                duration_ms=int((time.time() - start_time) * 1000)
            )

        except Exception as e:
            self.update_status(AgentStatus.FAILED)
            return AgentResult(
                success=False,
                data=None,
                error=str(e)
            )

    async def _select_template(self, context: AgentContext) -> str:
        """템플릿 선택"""
        user_input = context.user_input

        # 사용자가 지정한 템플릿이 있으면 사용
        if user_input.template_id:
            return user_input.template_id

        # LLM을 통해 적합한 템플릿 추천
        prompt = f"""프레젠테이션에 적합한 템플릿을 선택하세요.

주제: {user_input.topic}
목적: {user_input.purpose or '정보 전달'}
청중: {user_input.audience or '일반'}
스타일: {user_input.style or 'professional'}

사용 가능한 템플릿 카테고리:
- business: 비즈니스, 투자, 보고서
- education: 교육, 강의, 연구
- marketing: 마케팅, 제품 소개
- creative: 창의적, 예술적
- minimal: 미니멀, 깔끔

가장 적합한 템플릿 카테고리를 JSON으로 응답하세요:
{{"template_id": "카테고리명"}}"""

        response = await self.call_llm(prompt)

        try:
            data = json.loads(response)
            return data.get("template_id", "business")
        except json.JSONDecodeError:
            return "business"

    async def _assign_layouts(
        self,
        context: AgentContext
    ) -> List[SlideDesign]:
        """각 슬라이드 레이아웃 할당"""
        content = context.content

        if not content or not content.slides:
            return []

        slides = content.slides

        # 슬라이드 정보 요약
        slides_info = []
        for slide in slides:
            info = {
                "index": slide.index,
                "title": slide.title,
                "has_bullets": len(slide.bullet_points) > 0,
                "bullet_count": len(slide.bullet_points),
                "content_length": len(slide.content),
                "is_first": slide.index == 0,
                "is_last": slide.index == len(slides) - 1
            }
            slides_info.append(info)

        prompt = f"""각 슬라이드에 적합한 레이아웃을 결정하세요.

사용 가능한 레이아웃:
{', '.join(self.LAYOUT_TYPES)}

슬라이드 정보:
{json.dumps(slides_info, ensure_ascii=False, indent=2)}

규칙:
1. 첫 슬라이드 = "title"
2. 마지막 슬라이드 = "title" 또는 "contact"
3. 연속으로 같은 레이아웃 3번 이상 사용 금지
4. 글머리 기호 3개 이상 = "bullet_points"
5. 비교/대조 내용 = "comparison" 또는 "two_column"

JSON 배열로 응답하세요:
[{{"index": 0, "layout": "title", "visualization": null}}, ...]"""

        response = await self.call_llm(prompt)

        try:
            layouts_data = json.loads(response)

            slide_designs = []
            for data in layouts_data:
                design = SlideDesign(
                    index=data.get("index", 0),
                    layout_type=data.get("layout", "title_content"),
                    visualization_type=data.get("visualization"),
                    image_position=data.get("image_position")
                )
                slide_designs.append(design)

            return slide_designs

        except json.JSONDecodeError:
            # 폴백: 기본 레이아웃 할당
            return self._get_default_layouts(len(slides))

    def _get_default_layouts(self, count: int) -> List[SlideDesign]:
        """기본 레이아웃 할당"""
        designs = []
        for i in range(count):
            if i == 0:
                layout = "title"
            elif i == count - 1:
                layout = "title"
            else:
                layout = "title_content"

            designs.append(SlideDesign(index=i, layout_type=layout))

        return designs

    def _determine_color_scheme(self, theme: str) -> str:
        """색상 스키마 결정"""
        # 테마에 따른 색상 스키마 매핑
        scheme_map = {
            "default": "blue",
            "business": "navy",
            "education": "green",
            "minimal": "monochrome",
            "creative": "vibrant",
            "dark": "dark_blue",
            "warm": "orange",
            "cool": "teal"
        }
        return scheme_map.get(theme, "blue")

    def _determine_font_pairing(self, style: Optional[str]) -> Dict[str, str]:
        """폰트 페어링 결정"""
        pairings = {
            "formal": {
                "heading": "Pretendard",
                "body": "Noto Sans KR"
            },
            "casual": {
                "heading": "Nanum Gothic",
                "body": "Nanum Gothic"
            },
            "creative": {
                "heading": "Black Han Sans",
                "body": "Noto Sans KR"
            },
            "default": {
                "heading": "Pretendard",
                "body": "Pretendard"
            }
        }
        return pairings.get(style or "default", pairings["default"])
