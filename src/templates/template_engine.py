"""템플릿 엔진 모듈

템플릿을 로드하고 프레젠테이션 사양을 생성합니다.
"""

import json
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from pathlib import Path
from dataclasses import dataclass, field

from .template_loader import TemplateLoader
from .layout_matcher import LayoutMatcher, ContentAnalysis
from .layout_types import Layout, LayoutType, LayoutCategory, LayoutRegion, DEFAULT_LAYOUTS
from .color_schemes import ColorPalette, get_color_scheme

if TYPE_CHECKING:
    pass


@dataclass
class SlideSpec:
    """슬라이드 사양

    단일 슬라이드의 레이아웃, 콘텐츠, 디자인 사양을 정의합니다.
    """
    index: int
    layout: LayoutType
    content: Dict[str, Any]
    design: Dict[str, Any]
    animations: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "index": self.index,
            "layout": self.layout.value,
            "content": self.content,
            "design": self.design,
            "animations": self.animations
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SlideSpec":
        """딕셔너리에서 생성"""
        return cls(
            index=data["index"],
            layout=LayoutType(data["layout"]),
            content=data["content"],
            design=data["design"],
            animations=data.get("animations")
        )


@dataclass
class PresentationSpec:
    """프레젠테이션 사양

    전체 프레젠테이션의 템플릿, 색상, 슬라이드 사양을 정의합니다.
    """
    template_id: str
    color_scheme: str
    slides: List[SlideSpec]
    metadata: Dict[str, Any]
    typography: Optional[Dict[str, Any]] = None
    aspect_ratio: str = "16:9"

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "template_id": self.template_id,
            "color_scheme": self.color_scheme,
            "slides": [s.to_dict() for s in self.slides],
            "metadata": self.metadata,
            "typography": self.typography,
            "aspect_ratio": self.aspect_ratio
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PresentationSpec":
        """딕셔너리에서 생성"""
        return cls(
            template_id=data["template_id"],
            color_scheme=data["color_scheme"],
            slides=[SlideSpec.from_dict(s) for s in data["slides"]],
            metadata=data["metadata"],
            typography=data.get("typography"),
            aspect_ratio=data.get("aspect_ratio", "16:9")
        )

    @property
    def slide_count(self) -> int:
        """슬라이드 수"""
        return len(self.slides)

    def get_slide(self, index: int) -> Optional[SlideSpec]:
        """인덱스로 슬라이드 사양 조회"""
        if 0 <= index < len(self.slides):
            return self.slides[index]
        return None


class TemplateEngine:
    """템플릿 엔진

    템플릿을 로드하고 콘텐츠와 디자인 컨텍스트를 기반으로
    프레젠테이션 사양을 생성합니다.
    """

    def __init__(self, templates_dir: str = "templates"):
        """초기화

        Args:
            templates_dir: 템플릿 디렉토리 경로
        """
        self.loader = TemplateLoader(templates_dir)
        self.layout_matcher = LayoutMatcher({})
        self._layouts_cache: Dict[str, Layout] = {}

    def recommend_template(
        self,
        topic: str,
        purpose: Optional[str] = None,
        audience: Optional[str] = None,
        style: Optional[str] = None
    ) -> str:
        """주제에 맞는 템플릿 추천

        Args:
            topic: 프레젠테이션 주제
            purpose: 발표 목적
            audience: 대상 청중
            style: 선호 스타일

        Returns:
            추천 템플릿 ID
        """
        # 키워드 기반 카테고리 추론
        category = self._infer_category(topic, purpose)

        # 해당 카테고리의 인기 템플릿 조회
        templates = self.loader.list_templates(category=category)

        if templates:
            return templates[0].id

        # 기본 템플릿
        return "pitch_deck"

    def _infer_category(
        self,
        topic: str,
        purpose: Optional[str]
    ) -> str:
        """카테고리 추론

        Args:
            topic: 주제
            purpose: 목적

        Returns:
            추론된 카테고리 ID
        """
        topic_lower = topic.lower()
        purpose_lower = (purpose or "").lower()

        # 비즈니스 키워드
        business_keywords = [
            '투자', '사업', '비즈니스', 'business', '제안', '보고',
            '매출', '실적', '전략', '계획', '스타트업', 'startup',
            '회사', '기업', '프로젝트', '분기', '연간'
        ]

        # 교육 키워드
        education_keywords = [
            '강의', '교육', '학습', '연구', '논문', 'research',
            '워크샵', '세미나', '튜토리얼', 'tutorial', '학교',
            '대학', '수업', '강좌', '트레이닝'
        ]

        # 마케팅 키워드
        marketing_keywords = [
            '마케팅', 'marketing', '캠페인', '브랜드', '제품',
            '런칭', 'launch', '홍보', 'PR', '광고', '소셜',
            '프로모션', '이벤트'
        ]

        # 크리에이티브 키워드
        creative_keywords = [
            '포트폴리오', 'portfolio', '디자인', '창작', '아트',
            '스토리', '케이스', '쇼케이스'
        ]

        combined = topic_lower + ' ' + purpose_lower

        if any(kw in combined for kw in business_keywords):
            return "business"
        if any(kw in combined for kw in education_keywords):
            return "education"
        if any(kw in combined for kw in marketing_keywords):
            return "marketing"
        if any(kw in combined for kw in creative_keywords):
            return "creative"

        return "business"  # 기본값

    def create_presentation_spec(
        self,
        template_id: str,
        content_context: Any,
        design_context: Any
    ) -> PresentationSpec:
        """프레젠테이션 사양 생성

        Args:
            template_id: 템플릿 ID
            content_context: 콘텐츠 컨텍스트 객체
            design_context: 디자인 컨텍스트 객체

        Returns:
            PresentationSpec 객체
        """
        template = self.loader.get_template(template_id)
        if not template:
            template = self._get_default_template()

        slides = []
        content_slides = getattr(content_context, 'slides', [])
        design_slides = getattr(design_context, 'slides', [])
        total = len(content_slides)

        for i, slide_content in enumerate(content_slides):
            # 디자인 컨텍스트에서 레이아웃 가져오기
            slide_design = design_slides[i] if i < len(design_slides) else None

            # 레이아웃 결정
            if slide_design and hasattr(slide_design, 'layout_type'):
                try:
                    layout_type = LayoutType(slide_design.layout_type)
                except ValueError:
                    layout_type = self.layout_matcher.match(
                        slide_content,
                        i,
                        total,
                        slides[-1].layout if slides else None
                    )
            else:
                layout_type = self.layout_matcher.match(
                    slide_content,
                    i,
                    total,
                    slides[-1].layout if slides else None
                )

            # 슬라이드 사양 생성
            slide_spec = SlideSpec(
                index=i,
                layout=layout_type,
                content={
                    "title": getattr(slide_content, 'title', ''),
                    "subtitle": getattr(slide_content, 'subtitle', ''),
                    "content": getattr(slide_content, 'content', ''),
                    "bullet_points": getattr(slide_content, 'bullet_points', []),
                    "notes": getattr(slide_content, 'notes', '')
                },
                design={
                    "color_scheme": getattr(design_context, 'color_scheme', 'professional'),
                    "emphasis": getattr(slide_design, 'color_emphasis', None) if slide_design else None
                }
            )
            slides.append(slide_spec)

        # 타이포그래피 설정
        typography = template.get("design", {}).get("typography", {
            "heading_font": "Pretendard",
            "body_font": "Pretendard"
        })

        return PresentationSpec(
            template_id=template_id,
            color_scheme=getattr(design_context, 'color_scheme', 'professional'),
            slides=slides,
            metadata={
                "title": getattr(content_context, 'title', ''),
                "subtitle": getattr(content_context, 'subtitle', ''),
                "template_name": template.get("metadata", {}).get("name", "")
            },
            typography=typography,
            aspect_ratio=template.get("design", {}).get("aspect_ratio", "16:9")
        )

    def create_presentation_spec_simple(
        self,
        template_id: str,
        slides_data: List[Dict[str, Any]],
        color_scheme: str = "professional",
        title: str = "",
        subtitle: str = ""
    ) -> PresentationSpec:
        """간단한 프레젠테이션 사양 생성

        딕셔너리 형태의 슬라이드 데이터로부터 사양을 생성합니다.

        Args:
            template_id: 템플릿 ID
            slides_data: 슬라이드 데이터 목록
            color_scheme: 색상 스키마 이름
            title: 프레젠테이션 제목
            subtitle: 부제목

        Returns:
            PresentationSpec 객체
        """
        template = self.loader.get_template(template_id) or self._get_default_template()

        slides = []
        total = len(slides_data)

        for i, slide_data in enumerate(slides_data):
            # 레이아웃 결정
            layout_str = slide_data.get("layout")
            if layout_str:
                try:
                    layout_type = LayoutType(layout_str)
                except ValueError:
                    layout_type = self._infer_layout(slide_data, i, total, slides)
            else:
                layout_type = self._infer_layout(slide_data, i, total, slides)

            slide_spec = SlideSpec(
                index=i,
                layout=layout_type,
                content={
                    "title": slide_data.get("title", ""),
                    "subtitle": slide_data.get("subtitle", ""),
                    "content": slide_data.get("content", ""),
                    "bullet_points": slide_data.get("bullet_points", []),
                    "notes": slide_data.get("notes", "")
                },
                design={
                    "color_scheme": color_scheme,
                    "emphasis": slide_data.get("emphasis")
                }
            )
            slides.append(slide_spec)

        return PresentationSpec(
            template_id=template_id,
            color_scheme=color_scheme,
            slides=slides,
            metadata={
                "title": title,
                "subtitle": subtitle,
                "template_name": template.get("metadata", {}).get("name", "")
            },
            typography=template.get("design", {}).get("typography"),
            aspect_ratio=template.get("design", {}).get("aspect_ratio", "16:9")
        )

    def _infer_layout(
        self,
        slide_data: Dict[str, Any],
        index: int,
        total: int,
        previous_slides: List[SlideSpec]
    ) -> LayoutType:
        """슬라이드 데이터에서 레이아웃 추론"""
        # 간단한 객체 생성하여 매처에 전달
        class SimpleSlide:
            def __init__(self, data):
                self.title = data.get("title", "")
                self.subtitle = data.get("subtitle", "")
                self.content = data.get("content", "")
                self.bullet_points = data.get("bullet_points", [])
                self.image_url = data.get("image_url")
                self.chart_data = data.get("chart_data")

        simple_slide = SimpleSlide(slide_data)
        previous_layout = previous_slides[-1].layout if previous_slides else None

        return self.layout_matcher.match(simple_slide, index, total, previous_layout)

    def _get_default_template(self) -> Dict:
        """기본 템플릿 반환"""
        return {
            "id": "default",
            "metadata": {"name": "Default"},
            "design": {
                "aspect_ratio": "16:9",
                "base_width": 1920,
                "base_height": 1080,
                "color_schemes": {
                    "default": {
                        "primary": "#007acc",
                        "secondary": "#005a9e",
                        "accent": "#0ea5e9",
                        "background": "#ffffff",
                        "text": "#1a202c"
                    }
                },
                "typography": {
                    "heading_font": "Pretendard",
                    "body_font": "Pretendard",
                    "sizes": {
                        "title": 54,
                        "heading1": 44,
                        "heading2": 36,
                        "body": 24,
                        "caption": 18
                    }
                }
            }
        }

    def get_layout(self, layout_type: LayoutType) -> Layout:
        """레이아웃 정의 조회

        Args:
            layout_type: 레이아웃 타입

        Returns:
            Layout 객체
        """
        layout_id = layout_type.value

        if layout_id in self._layouts_cache:
            return self._layouts_cache[layout_id]

        # 레이아웃 파일 로드
        layout = self._load_layout(layout_id)
        self._layouts_cache[layout_id] = layout

        return layout

    def _load_layout(self, layout_id: str) -> Layout:
        """레이아웃 파일 로드

        Args:
            layout_id: 레이아웃 ID

        Returns:
            Layout 객체
        """
        # 레이아웃 카테고리 결정
        category = self._get_layout_category(layout_id)

        layout_path = self.loader.templates_dir / "layouts" / category / f"{layout_id}.json"

        if layout_path.exists():
            with open(layout_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return self._parse_layout(data)

        # 기본 레이아웃 반환
        return self._get_default_layout(layout_id)

    def _get_layout_category(self, layout_id: str) -> str:
        """레이아웃 카테고리 결정

        Args:
            layout_id: 레이아웃 ID

        Returns:
            카테고리 이름
        """
        if 'title' in layout_id:
            return 'title'
        if 'image' in layout_id:
            return 'image'
        if 'chart' in layout_id or 'statistics' in layout_id or 'comparison' in layout_id:
            return 'data'
        if layout_id in ['quote', 'timeline', 'team_grid', 'contact', 'agenda']:
            return 'special'
        return 'content'

    def _parse_layout(self, data: Dict) -> Layout:
        """레이아웃 데이터 파싱

        Args:
            data: 레이아웃 데이터 딕셔너리

        Returns:
            Layout 객체
        """
        regions = []
        for r in data.get("regions", []):
            pos = r.get("position", {})
            region = LayoutRegion(
                id=r["id"],
                type=r["type"],
                purpose=r["purpose"],
                x=pos.get("x", 0),
                y=pos.get("y", 0),
                width=pos.get("width", 100),
                height=pos.get("height", 100),
                accepts=r.get("accepts", []),
                style=r.get("style")
            )
            regions.append(region)

        # layout_type 결정
        layout_id = data["id"]
        try:
            layout_type = LayoutType(layout_id)
        except ValueError:
            layout_type = LayoutType.SINGLE_COLUMN

        # category 결정
        category_str = data.get("category", self._get_layout_category(layout_id))
        try:
            category = LayoutCategory(category_str)
        except ValueError:
            category = LayoutCategory.CONTENT

        return Layout(
            id=layout_id,
            name=data.get("name", layout_id),
            category=category,
            layout_type=layout_type,
            regions=regions,
            constraints=data.get("constraints", {}),
            animations=data.get("animations"),
            description=data.get("description", "")
        )

    def _get_default_layout(self, layout_id: str) -> Layout:
        """기본 레이아웃 생성

        Args:
            layout_id: 레이아웃 ID

        Returns:
            Layout 객체
        """
        # DEFAULT_LAYOUTS에서 찾기
        try:
            layout_type = LayoutType(layout_id)
            if layout_type in DEFAULT_LAYOUTS:
                return DEFAULT_LAYOUTS[layout_type]
        except ValueError:
            pass

        # 기본 단일 열 레이아웃 생성
        return Layout(
            id=layout_id,
            name=layout_id.replace('_', ' ').title(),
            category=LayoutCategory.CONTENT,
            layout_type=LayoutType.SINGLE_COLUMN,
            regions=[
                LayoutRegion(
                    id="title",
                    type="text",
                    purpose="heading",
                    x=60, y=60, width=1800, height=80,
                    accepts=["text"]
                ),
                LayoutRegion(
                    id="content",
                    type="content",
                    purpose="primary",
                    x=60, y=180, width=1800, height=800,
                    accepts=["text", "bullet_points"]
                )
            ],
            constraints={}
        )

    def get_color_palette(self, template_id: str, scheme_name: str) -> ColorPalette:
        """템플릿의 색상 팔레트 조회

        Args:
            template_id: 템플릿 ID
            scheme_name: 색상 스키마 이름

        Returns:
            ColorPalette 객체
        """
        template = self.loader.get_template(template_id)
        if template:
            design = template.get("design", {})
            schemes = design.get("color_schemes", {})
            if scheme_name in schemes:
                return ColorPalette.from_dict(schemes[scheme_name])

        # 기본 색상 스키마 반환
        return get_color_scheme(scheme_name)

    def get_typography(self, template_id: str) -> Dict[str, Any]:
        """템플릿의 타이포그래피 설정 조회

        Args:
            template_id: 템플릿 ID

        Returns:
            타이포그래피 설정 딕셔너리
        """
        template = self.loader.get_template(template_id)
        if template:
            return template.get("design", {}).get("typography", {})

        return {
            "heading_font": "Pretendard",
            "body_font": "Pretendard",
            "sizes": {
                "title": 54,
                "heading1": 44,
                "heading2": 36,
                "body": 24,
                "caption": 18
            },
            "weights": {
                "title": 700,
                "heading": 600,
                "body": 400
            }
        }

    def validate_presentation_spec(self, spec: PresentationSpec) -> List[str]:
        """프레젠테이션 사양 검증

        Args:
            spec: 검증할 PresentationSpec

        Returns:
            검증 오류 메시지 목록 (비어있으면 유효함)
        """
        errors = []

        if not spec.slides:
            errors.append("슬라이드가 없습니다.")

        for i, slide in enumerate(spec.slides):
            if not slide.content.get("title"):
                errors.append(f"슬라이드 {i + 1}: 제목이 없습니다.")

        return errors
