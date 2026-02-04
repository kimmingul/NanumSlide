"""AI 기반 프레젠테이션 생성 서비스"""

import json
import re
import uuid
from datetime import datetime
from typing import Optional, Callable, Any

from src.core.presentation import Presentation, Slide, SlideLayoutType
from src.services.llm_client import create_llm_client, BaseLLMClient
from src.services.image_service import search_image


# 프레젠테이션 생성 프롬프트
OUTLINE_SYSTEM_PROMPT = """당신은 프레젠테이션 구조를 설계하는 전문가입니다.
사용자의 요청에 따라 효과적인 프레젠테이션 개요를 작성합니다.
각 슬라이드의 제목, 핵심 내용, 레이아웃을 명확하게 제시합니다."""

OUTLINE_PROMPT_TEMPLATE = """다음 주제로 {slide_count}장의 프레젠테이션 개요를 작성해주세요.

주제: {topic}
언어: {language}

다음 JSON 형식으로 응답해주세요:
{{
  "title": "프레젠테이션 제목",
  "slides": [
    {{
      "title": "슬라이드 제목",
      "layout": "title|title_content|bullet_points|title_image",
      "content": "슬라이드 내용 (한 문단)",
      "bullet_points": ["항목1", "항목2", "항목3"],
      "notes": "발표자 노트",
      "image_prompt": "이미지 검색 키워드 (영문)"
    }}
  ]
}}

첫 번째 슬라이드는 반드시 "title" 레이아웃으로 제목 슬라이드여야 합니다.
마지막 슬라이드는 결론 또는 Q&A 슬라이드로 구성해주세요."""

SLIDE_CONTENT_SYSTEM_PROMPT = """당신은 프레젠테이션 콘텐츠 작성 전문가입니다.
주어진 슬라이드 개요를 바탕으로 상세하고 설득력 있는 내용을 작성합니다.
간결하면서도 핵심을 전달하는 문장을 사용합니다."""

SLIDE_CONTENT_PROMPT_TEMPLATE = """다음 슬라이드의 상세 내용을 작성해주세요.

제목: {title}
레이아웃: {layout}
개요: {outline}

다음 JSON 형식으로 응답해주세요:
{{
  "content": "상세 내용 (2-3문장)",
  "bullet_points": ["핵심 포인트 1", "핵심 포인트 2", "핵심 포인트 3"],
  "notes": "발표자 노트 (발표 시 참고할 내용)"
}}"""


# 응답 스키마 (OpenAI Responses API 요구사항: additionalProperties 필수)
OUTLINE_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "slides": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "layout": {"type": "string"},
                    "content": {"type": "string"},
                    "bullet_points": {"type": "array", "items": {"type": "string"}},
                    "notes": {"type": "string"},
                    "image_prompt": {"type": "string"},
                },
                "required": ["title", "layout", "content", "bullet_points", "notes", "image_prompt"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "slides"],
    "additionalProperties": False,
}


class PresentationGenerator:
    """프레젠테이션 생성기"""

    def __init__(self, llm_client: Optional[BaseLLMClient] = None):
        self.llm_client = llm_client or create_llm_client()
        self._progress_callback: Optional[Callable[[str, int], None]] = None

    def set_progress_callback(self, callback: Callable[[str, int], None]):
        """진행률 콜백 설정"""
        self._progress_callback = callback

    def _report_progress(self, message: str, percent: int):
        """진행률 보고"""
        if self._progress_callback:
            self._progress_callback(message, percent)

    async def generate(
        self,
        topic: str,
        slide_count: int = 8,
        language: str = "한국어",
        template: str = "기본",
        reference_content: str = "",
    ) -> Presentation:
        """프레젠테이션 생성"""
        self._report_progress("개요 생성 중...", 10)

        # 1. 개요 생성
        outline = await self._generate_outline(topic, slide_count, language, reference_content)

        self._report_progress("슬라이드 구성 중...", 50)

        # 2. 프레젠테이션 객체 생성
        presentation = Presentation(
            id=str(uuid.uuid4()),
            title=outline.get("title", topic),
            language=language,
            prompt=topic,
            created_at=datetime.now().isoformat(),
        )

        # 3. 슬라이드 생성 및 이미지 검색
        slides_data = outline.get("slides", [])
        total_slides = len(slides_data)

        for i, slide_data in enumerate(slides_data):
            # 진행률 계산 (50~90%)
            progress = 50 + int((i + 1) / total_slides * 40)
            self._report_progress(f"슬라이드 {i + 1}/{total_slides} 생성 중...", progress)

            # 이미지 검색 (image_prompt가 있는 경우)
            image_prompt = slide_data.get("image_prompt")
            if image_prompt:
                self._report_progress(f"이미지 검색 중... ({i + 1}/{total_slides})", progress)
                try:
                    image_url = await search_image(image_prompt)
                    if image_url:
                        slide_data["image_url"] = image_url
                except Exception as e:
                    print(f"이미지 검색 실패 (슬라이드 {i + 1}): {e}")

            slide = self._create_slide(slide_data, i + 1)
            presentation.add_slide(slide)

        self._report_progress("완료", 100)
        return presentation

    async def _generate_outline(
        self,
        topic: str,
        slide_count: int,
        language: str,
        reference_content: str = "",
    ) -> dict:
        """프레젠테이션 개요 생성"""
        prompt = OUTLINE_PROMPT_TEMPLATE.format(
            topic=topic,
            slide_count=slide_count,
            language=language,
        )

        # 참고 자료가 있으면 프롬프트에 추가
        if reference_content:
            prompt += f"\n\n=== 참고 자료 ===\n아래 내용을 참고하여 프레젠테이션을 작성해주세요:\n\n{reference_content[:10000]}"

        # 1차 시도: 구조화된 응답
        try:
            result = await self.llm_client.generate_structured(
                prompt=prompt,
                response_schema=OUTLINE_RESPONSE_SCHEMA,
                system_prompt=OUTLINE_SYSTEM_PROMPT,
            )
            if result and result.get("slides"):
                return result
        except Exception as e:
            print(f"구조화 응답 실패, 일반 생성으로 대체: {e}")

        # 2차 시도: 일반 텍스트 생성 후 JSON 파싱
        try:
            text_response = await self.llm_client.generate(
                prompt=prompt + "\n\n반드시 위의 JSON 형식으로만 응답해주세요. 다른 텍스트 없이 JSON만 출력하세요.",
                system_prompt=OUTLINE_SYSTEM_PROMPT,
            )
            result = self._parse_json_from_text(text_response)
            if result and result.get("slides"):
                return result
        except Exception as e:
            print(f"일반 생성도 실패: {e}")
            raise Exception(f"프레젠테이션 개요 생성 실패: {e}")

    def _parse_json_from_text(self, text: str) -> dict:
        """텍스트에서 JSON 추출 및 파싱"""
        # JSON 블록 찾기 (```json ... ``` 또는 { ... })
        json_patterns = [
            r'```json\s*([\s\S]*?)\s*```',  # ```json 블록
            r'```\s*([\s\S]*?)\s*```',       # ``` 블록
            r'(\{[\s\S]*\})',                # 중괄호 블록
        ]

        for pattern in json_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue

        # 전체 텍스트를 JSON으로 시도
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            raise ValueError(f"JSON 파싱 실패. 응답: {text[:500]}")

    def _create_slide(self, slide_data: dict, index: int) -> Slide:
        """슬라이드 객체 생성"""
        layout_str = slide_data.get("layout", "title_content")
        layout = self._parse_layout(layout_str)

        return Slide(
            id=f"slide_{index}",
            layout=layout,
            title=slide_data.get("title", f"슬라이드 {index}"),
            subtitle=slide_data.get("subtitle", ""),
            content=slide_data.get("content", ""),
            bullet_points=slide_data.get("bullet_points", []),
            notes=slide_data.get("notes", ""),
            image_prompt=slide_data.get("image_prompt"),
            image_url=slide_data.get("image_url"),
        )

    def _parse_layout(self, layout_str: str) -> SlideLayoutType:
        """레이아웃 문자열을 열거형으로 변환"""
        layout_map = {
            "title": SlideLayoutType.TITLE,
            "title_content": SlideLayoutType.TITLE_CONTENT,
            "two_column": SlideLayoutType.TWO_COLUMN,
            "title_image": SlideLayoutType.TITLE_IMAGE,
            "image_full": SlideLayoutType.IMAGE_FULL,
            "bullet_points": SlideLayoutType.BULLET_POINTS,
            "chart": SlideLayoutType.CHART,
            "quote": SlideLayoutType.QUOTE,
            "blank": SlideLayoutType.BLANK,
        }
        return layout_map.get(layout_str.lower(), SlideLayoutType.TITLE_CONTENT)


async def generate_presentation(
    topic: str,
    slide_count: int = 8,
    language: str = "한국어",
    template: str = "기본",
    progress_callback: Optional[Callable[[str, int], None]] = None,
) -> Presentation:
    """프레젠테이션 생성 (편의 함수)"""
    generator = PresentationGenerator()
    if progress_callback:
        generator.set_progress_callback(progress_callback)
    return await generator.generate(topic, slide_count, language, template)
