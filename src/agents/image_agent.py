# src/agents/image_agent.py
"""이미지 에이전트 - 이미지 생성/검색 및 시각 자료 준비"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
import json
import asyncio
import time

from .base_agent import BaseAgent, AgentResult, AgentStatus
from .agent_context import AgentContext, MediaContext, SlideMedia, SlideDesign

if TYPE_CHECKING:
    from src.services.llm_client import BaseLLMClient


class ImageAgent(BaseAgent):
    """이미지 에이전트 - 이미지 생성/검색 및 시각 자료 준비"""

    def __init__(
        self,
        llm_client: "BaseLLMClient",
        image_service: Any,
        config: Optional[Dict] = None
    ):
        super().__init__(
            name="image_agent",
            llm_client=llm_client,
            config=config
        )
        self.image_service = image_service

    def get_system_prompt(self) -> str:
        return """당신은 프레젠테이션 비주얼 전문가입니다.
슬라이드 콘텐츠에 적합한 이미지, 아이콘, 차트를 결정합니다.

이미지 선택 원칙:
1. 콘텐츠와 직접적으로 관련된 이미지
2. 프로페셔널하고 고품질의 비주얼
3. 일관된 스타일 유지
4. 텍스트를 보완하는 이미지 (중복 아님)
5. 적절한 이미지 검색 키워드 생성"""

    async def run(self, context: AgentContext) -> AgentResult:
        """이미지 처리 실행"""
        start_time = time.time()

        try:
            self.update_status(AgentStatus.RUNNING)

            content = context.content
            design = context.design
            user_input = context.user_input

            # 이미지 비활성화된 경우
            if not user_input.include_images:
                return AgentResult(
                    success=True,
                    data=MediaContext(slides=[]),
                    duration_ms=0
                )

            # 1. 각 슬라이드의 이미지 요구사항 분석
            image_requirements = await self._analyze_image_requirements(
                context
            )

            # 2. 이미지 검색/생성 (병렬 처리)
            slide_media_list = await self._process_images(
                image_requirements,
                user_input.language
            )

            # 3. 차트 데이터 처리 (차트가 필요한 슬라이드)
            if user_input.include_charts:
                slide_media_list = await self._process_charts(
                    context,
                    slide_media_list
                )

            media_context = MediaContext(
                slides=slide_media_list,
                image_style=self._determine_image_style(user_input.style)
            )

            self.update_status(AgentStatus.COMPLETED)

            return AgentResult(
                success=True,
                data=media_context,
                duration_ms=int((time.time() - start_time) * 1000)
            )

        except Exception as e:
            self.update_status(AgentStatus.FAILED)
            return AgentResult(
                success=False,
                data=None,
                error=str(e)
            )

    async def _analyze_image_requirements(
        self,
        context: AgentContext
    ) -> List[Dict[str, Any]]:
        """각 슬라이드의 이미지 요구사항 분석"""
        content = context.content
        design = context.design

        if not content or not content.slides:
            return []

        # 슬라이드 정보 구성
        slides_info = []
        for i, slide in enumerate(content.slides):
            slide_design = design.slides[i] if design and i < len(design.slides) else None

            info = {
                "index": i,
                "title": slide.title,
                "content": slide.content[:200] if slide.content else "",
                "layout": slide_design.layout_type if slide_design else "title_content",
                "needs_image": self._layout_needs_image(
                    slide_design.layout_type if slide_design else "title_content"
                )
            }
            slides_info.append(info)

        prompt = f"""각 슬라이드에 적합한 이미지 검색 키워드를 생성하세요.

슬라이드 정보:
{json.dumps(slides_info, ensure_ascii=False, indent=2)}

규칙:
1. 영어 키워드 사용 (검색 정확도)
2. 2-4개 단어로 구성
3. 구체적이고 명확한 키워드
4. needs_image가 false면 키워드 생략

JSON 배열로 응답:
[{{"index": 0, "keywords": "business meeting", "style": "photo"}}, ...]"""

        response = await self.call_llm(prompt)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return [{"index": i, "keywords": "", "style": "photo"}
                    for i in range(len(content.slides))]

    async def _process_images(
        self,
        requirements: List[Dict[str, Any]],
        language: str
    ) -> List[SlideMedia]:
        """이미지 검색/생성 처리"""
        slide_media_list = []

        # 병렬 처리를 위한 태스크 생성
        async def process_single_image(req: Dict) -> SlideMedia:
            slide_media = SlideMedia(index=req["index"])

            keywords = req.get("keywords", "")
            if not keywords:
                return slide_media

            try:
                # 이미지 검색/생성 - image_service가 search_image 함수인 경우
                if callable(self.image_service):
                    image_url = await self.image_service(keywords)
                    if image_url:
                        slide_media.images.append({
                            "url": image_url,
                            "source": "image_service",
                            "alt_text": keywords
                        })
                # image_service가 search_image 메서드를 가진 객체인 경우
                elif hasattr(self.image_service, 'search_image'):
                    image_result = await self.image_service.search_image(keywords)
                    if image_result:
                        slide_media.images.append({
                            "url": image_result.get("url") if isinstance(image_result, dict) else image_result,
                            "source": image_result.get("source", "image_service") if isinstance(image_result, dict) else "image_service",
                            "alt_text": keywords
                        })

            except Exception as e:
                # 이미지 실패 시 빈 결과 반환
                pass

            return slide_media

        # 동시에 최대 5개 이미지 처리
        semaphore = asyncio.Semaphore(5)

        async def bounded_process(req):
            async with semaphore:
                return await process_single_image(req)

        tasks = [bounded_process(req) for req in requirements]
        results = await asyncio.gather(*tasks)

        return list(results)

    async def _process_charts(
        self,
        context: AgentContext,
        slide_media_list: List[SlideMedia]
    ) -> List[SlideMedia]:
        """차트 처리"""
        design = context.design
        research = context.research

        if not design or not design.slides:
            return slide_media_list

        # 차트가 필요한 슬라이드 식별
        for i, slide_design in enumerate(design.slides):
            if slide_design.visualization_type == "chart":
                # 리서치에서 관련 통계 찾기
                if research and research.statistics:
                    chart_data = self._prepare_chart_data(
                        research.statistics,
                        slide_design
                    )
                    if chart_data and i < len(slide_media_list):
                        slide_media_list[i].charts.append(chart_data)

        return slide_media_list

    def _layout_needs_image(self, layout_type: str) -> bool:
        """레이아웃에 이미지가 필요한지 확인"""
        image_layouts = [
            "title_image", "image_left", "image_right",
            "image_full", "two_column"
        ]
        return layout_type in image_layouts

    def _determine_image_style(self, style: Optional[str]) -> str:
        """이미지 스타일 결정"""
        style_map = {
            "formal": "photo",
            "casual": "photo",
            "creative": "illustration",
        }
        return style_map.get(style or "formal", "photo")

    def _prepare_chart_data(
        self,
        statistics: List[Dict],
        slide_design: SlideDesign
    ) -> Optional[Dict[str, Any]]:
        """차트 데이터 준비"""
        if not statistics:
            return None

        # 첫 번째 통계 데이터 사용 (간단한 구현)
        stat = statistics[0]

        return {
            "type": "bar",  # 기본 차트 타입
            "title": stat.get("description", ""),
            "data": stat.get("value", ""),
            "source": stat.get("source", "")
        }
