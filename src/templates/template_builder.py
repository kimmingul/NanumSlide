"""템플릿 빌더 모듈

새 템플릿을 프로그래밍 방식으로 생성하는 빌더 클래스를 제공합니다.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class TemplateBuilder:
    """템플릿 빌더

    프로그래밍 방식으로 템플릿을 생성합니다.
    메서드 체이닝을 지원하여 유창한(fluent) API를 제공합니다.
    """

    id: str
    name: str
    name_ko: str
    category: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    color_schemes: Dict[str, Dict] = field(default_factory=dict)
    layouts: Dict[str, str] = field(default_factory=dict)
    structure: List[Dict] = field(default_factory=list)
    typography: Optional[Dict[str, Any]] = None
    spacing: Optional[Dict[str, int]] = None
    assets: Optional[Dict[str, Any]] = None
    best_for: List[str] = field(default_factory=list)
    _aspect_ratio: str = "16:9"
    _base_width: int = 1920
    _base_height: int = 1080

    def add_tag(self, tag: str) -> "TemplateBuilder":
        """태그 추가

        Args:
            tag: 추가할 태그

        Returns:
            self (메서드 체이닝)
        """
        if tag not in self.tags:
            self.tags.append(tag)
        return self

    def add_tags(self, tags: List[str]) -> "TemplateBuilder":
        """여러 태그 추가

        Args:
            tags: 추가할 태그 목록

        Returns:
            self (메서드 체이닝)
        """
        for tag in tags:
            self.add_tag(tag)
        return self

    def add_best_for(self, purpose: str) -> "TemplateBuilder":
        """사용 목적 추가

        Args:
            purpose: 템플릿 사용 목적

        Returns:
            self (메서드 체이닝)
        """
        if purpose not in self.best_for:
            self.best_for.append(purpose)
        return self

    def add_color_scheme(
        self,
        name: str,
        primary: str,
        secondary: str,
        accent: str,
        background: str = "#ffffff",
        text: str = "#1a202c",
        text_light: str = "#718096"
    ) -> "TemplateBuilder":
        """색상 스키마 추가

        Args:
            name: 스키마 이름
            primary: 주요 색상
            secondary: 보조 색상
            accent: 강조 색상
            background: 배경 색상
            text: 텍스트 색상
            text_light: 밝은 텍스트 색상

        Returns:
            self (메서드 체이닝)
        """
        self.color_schemes[name] = {
            "primary": primary,
            "secondary": secondary,
            "accent": accent,
            "background": background,
            "text": text,
            "text_light": text_light
        }
        return self

    def add_slide_type(
        self,
        type_name: str,
        layout: str,
        required: bool = False,
        name_ko: str = ""
    ) -> "TemplateBuilder":
        """슬라이드 타입 추가

        Args:
            type_name: 타입 이름 (예: "title", "problem", "solution")
            layout: 기본 레이아웃 이름
            required: 필수 여부
            name_ko: 한글 이름

        Returns:
            self (메서드 체이닝)
        """
        self.structure.append({
            "type": type_name,
            "layout": layout,
            "required": required,
            "name": name_ko or type_name
        })
        return self

    def set_default_layout(
        self,
        slide_type: str,
        layout: str
    ) -> "TemplateBuilder":
        """기본 레이아웃 설정

        Args:
            slide_type: 슬라이드 타입
            layout: 레이아웃 이름

        Returns:
            self (메서드 체이닝)
        """
        self.layouts[slide_type] = layout
        return self

    def set_typography(
        self,
        heading_font: str = "Pretendard",
        body_font: str = "Pretendard",
        sizes: Optional[Dict[str, int]] = None,
        weights: Optional[Dict[str, int]] = None
    ) -> "TemplateBuilder":
        """타이포그래피 설정

        Args:
            heading_font: 제목 폰트
            body_font: 본문 폰트
            sizes: 폰트 크기 딕셔너리
            weights: 폰트 굵기 딕셔너리

        Returns:
            self (메서드 체이닝)
        """
        self.typography = {
            "heading_font": heading_font,
            "body_font": body_font,
            "sizes": sizes or {
                "title": 54,
                "heading1": 44,
                "heading2": 36,
                "body": 24,
                "caption": 18
            },
            "weights": weights or {
                "title": 700,
                "heading": 600,
                "body": 400
            }
        }
        return self

    def set_spacing(
        self,
        margin: int = 60,
        padding: int = 40,
        gap: int = 24
    ) -> "TemplateBuilder":
        """간격 설정

        Args:
            margin: 외부 여백
            padding: 내부 여백
            gap: 요소 간 간격

        Returns:
            self (메서드 체이닝)
        """
        self.spacing = {
            "margin": margin,
            "padding": padding,
            "gap": gap
        }
        return self

    def set_aspect_ratio(
        self,
        ratio: str = "16:9",
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> "TemplateBuilder":
        """화면 비율 설정

        Args:
            ratio: 화면 비율 (예: "16:9", "4:3")
            width: 기본 너비 (픽셀)
            height: 기본 높이 (픽셀)

        Returns:
            self (메서드 체이닝)
        """
        self._aspect_ratio = ratio

        if width and height:
            self._base_width = width
            self._base_height = height
        elif ratio == "16:9":
            self._base_width = 1920
            self._base_height = 1080
        elif ratio == "4:3":
            self._base_width = 1440
            self._base_height = 1080
        elif ratio == "16:10":
            self._base_width = 1920
            self._base_height = 1200

        return self

    def set_assets(
        self,
        master_pptx: str = "master.pptx",
        thumbnail: str = "thumbnail.png",
        icons: Optional[List[str]] = None,
        placeholder_images: Optional[List[str]] = None
    ) -> "TemplateBuilder":
        """에셋 설정

        Args:
            master_pptx: 마스터 PPTX 파일명
            thumbnail: 썸네일 이미지 파일명
            icons: 사용 가능한 아이콘 목록
            placeholder_images: 플레이스홀더 이미지 목록

        Returns:
            self (메서드 체이닝)
        """
        self.assets = {
            "master_pptx": master_pptx,
            "thumbnail": thumbnail,
            "icons": icons or [],
            "placeholder_images": placeholder_images or []
        }
        return self

    def build(self) -> Dict:
        """템플릿 정의 생성

        Returns:
            템플릿 정의 딕셔너리
        """
        # 필수 슬라이드 수 계산
        required_count = len([s for s in self.structure if s.get("required")])

        # 기본 타이포그래피 설정
        typography = self.typography or {
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

        # 기본 간격 설정
        spacing = self.spacing or {
            "margin": 60,
            "padding": 40,
            "gap": 24
        }

        return {
            "id": self.id,
            "version": "1.0.0",
            "metadata": {
                "name": self.name,
                "name_ko": self.name_ko,
                "category": self.category,
                "description": self.description,
                "author": "NanumSlide",
                "license": "MIT"
            },
            "design": {
                "aspect_ratio": self._aspect_ratio,
                "base_width": self._base_width,
                "base_height": self._base_height,
                "color_schemes": self.color_schemes,
                "typography": typography,
                "spacing": spacing
            },
            "structure": {
                "recommended_slides": self.structure,
                "min_slides": max(3, required_count),
                "max_slides": 20,
                "optimal_slides": len(self.structure)
            },
            "layouts": self.layouts,
            "tags": self.tags,
            "best_for": self.best_for,
            "assets": self.assets or {
                "master_pptx": "master.pptx",
                "thumbnail": "thumbnail.png"
            }
        }

    def save(self, templates_dir: str = "templates") -> Path:
        """템플릿 파일 저장

        Args:
            templates_dir: 템플릿 디렉토리 경로

        Returns:
            저장된 template.json 파일 경로
        """
        template_data = self.build()

        # 디렉토리 생성
        template_path = Path(templates_dir) / self.category / self.id
        template_path.mkdir(parents=True, exist_ok=True)

        # template.json 저장
        json_path = template_path / "template.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, ensure_ascii=False, indent=2)

        return json_path

    def to_index_entry(self, popularity: int = 50) -> Dict:
        """인덱스 엔트리 생성

        Args:
            popularity: 인기도 점수 (0-100)

        Returns:
            인덱스에 추가할 템플릿 엔트리
        """
        from datetime import date

        today = date.today().isoformat()

        return {
            "id": self.id,
            "name": self.name,
            "name_ko": self.name_ko,
            "category": self.category,
            "description": self.description,
            "tags": self.tags,
            "thumbnail": f"{self.category}/{self.id}/thumbnail.png",
            "slides_count": len(self.structure),
            "color_schemes": list(self.color_schemes.keys()),
            "best_for": self.best_for,
            "popularity": popularity,
            "created_at": today,
            "updated_at": today
        }


# 템플릿 생성 헬퍼 함수들

def create_pitch_deck_template() -> TemplateBuilder:
    """피치덱 템플릿 생성

    Returns:
        구성된 TemplateBuilder
    """
    builder = TemplateBuilder(
        id="pitch_deck",
        name="Pitch Deck",
        name_ko="투자 유치용 피치덱",
        category="business",
        description="스타트업 투자 유치를 위한 전문적인 피치덱 템플릿"
    )

    # 태그 추가
    builder.add_tags(["startup", "funding", "investor", "venture"])

    # 사용 목적 추가
    builder.add_best_for("스타트업 소개")
    builder.add_best_for("투자 유치")
    builder.add_best_for("사업 계획")

    # 색상 스키마 추가
    builder.add_color_scheme(
        "professional",
        primary="#1a365d",
        secondary="#2c5282",
        accent="#3182ce"
    )

    builder.add_color_scheme(
        "bold",
        primary="#e53e3e",
        secondary="#c53030",
        accent="#fc8181",
        background="#1a202c",
        text="#ffffff",
        text_light="#a0aec0"
    )

    builder.add_color_scheme(
        "tech",
        primary="#805ad5",
        secondary="#6b46c1",
        accent="#9f7aea",
        background="#1a202c",
        text="#ffffff",
        text_light="#a0aec0"
    )

    # 슬라이드 구조 정의
    builder.add_slide_type("title", "title_centered", required=True, name_ko="표지")
    builder.add_slide_type("problem", "two_column", required=True, name_ko="문제 정의")
    builder.add_slide_type("solution", "image_left", required=True, name_ko="해결책")
    builder.add_slide_type("product", "image_right", required=False, name_ko="제품/서비스")
    builder.add_slide_type("market", "chart_centered", required=True, name_ko="시장 규모")
    builder.add_slide_type("business_model", "two_column", required=True, name_ko="비즈니스 모델")
    builder.add_slide_type("traction", "statistics", required=False, name_ko="성과/지표")
    builder.add_slide_type("competition", "comparison", required=False, name_ko="경쟁 분석")
    builder.add_slide_type("team", "team_grid", required=True, name_ko="팀 소개")
    builder.add_slide_type("financials", "chart_centered", required=False, name_ko="재무 계획")
    builder.add_slide_type("ask", "single_column", required=True, name_ko="투자 요청")
    builder.add_slide_type("contact", "contact", required=True, name_ko="연락처")

    # 에셋 설정
    builder.set_assets(
        icons=["rocket", "chart", "team", "money", "target"],
        placeholder_images=["product_mockup.png", "team_photo.png", "chart_placeholder.png"]
    )

    return builder


def create_quarterly_report_template() -> TemplateBuilder:
    """분기 보고서 템플릿 생성

    Returns:
        구성된 TemplateBuilder
    """
    builder = TemplateBuilder(
        id="quarterly_report",
        name="Quarterly Report",
        name_ko="분기 보고서",
        category="business",
        description="깔끔하고 전문적인 분기 실적 보고서 템플릿"
    )

    builder.add_tags(["report", "quarterly", "financial", "corporate"])
    builder.add_best_for("실적 보고")
    builder.add_best_for("분기 리뷰")
    builder.add_best_for("경영 보고")

    builder.add_color_scheme(
        "corporate",
        primary="#1e40af",
        secondary="#1d4ed8",
        accent="#3b82f6",
        background="#f8fafc",
        text="#0f172a",
        text_light="#64748b"
    )

    builder.add_color_scheme(
        "minimal",
        primary="#374151",
        secondary="#6b7280",
        accent="#9ca3af",
        background="#ffffff",
        text="#111827",
        text_light="#9ca3af"
    )

    builder.add_slide_type("title", "title_centered", required=True, name_ko="표지")
    builder.add_slide_type("agenda", "bullet_points", required=True, name_ko="목차")
    builder.add_slide_type("executive_summary", "two_column", required=True, name_ko="요약")
    builder.add_slide_type("financial_highlights", "statistics", required=True, name_ko="재무 하이라이트")
    builder.add_slide_type("revenue", "chart_centered", required=True, name_ko="매출 분석")
    builder.add_slide_type("expenses", "chart_centered", required=False, name_ko="비용 분석")
    builder.add_slide_type("kpis", "statistics", required=True, name_ko="핵심 지표")
    builder.add_slide_type("achievements", "bullet_points", required=False, name_ko="주요 성과")
    builder.add_slide_type("challenges", "two_column", required=False, name_ko="도전과제")
    builder.add_slide_type("outlook", "single_column", required=True, name_ko="전망")
    builder.add_slide_type("conclusion", "single_column", required=True, name_ko="결론")

    return builder


def create_lecture_template() -> TemplateBuilder:
    """강의용 템플릿 생성

    Returns:
        구성된 TemplateBuilder
    """
    builder = TemplateBuilder(
        id="lecture",
        name="Lecture",
        name_ko="강의",
        category="education",
        description="교육 및 강의를 위한 깔끔한 템플릿"
    )

    builder.add_tags(["education", "lecture", "teaching", "academic"])
    builder.add_best_for("대학 강의")
    builder.add_best_for("교육 세미나")
    builder.add_best_for("수업 자료")

    builder.add_color_scheme(
        "academic",
        primary="#1e3a5f",
        secondary="#2d5a87",
        accent="#4a90c2",
        background="#f8fafc",
        text="#1a202c",
        text_light="#718096"
    )

    builder.add_color_scheme(
        "warm",
        primary="#92400e",
        secondary="#b45309",
        accent="#d97706",
        background="#fffbeb",
        text="#1c1917",
        text_light="#78716c"
    )

    builder.add_slide_type("title", "title_with_subtitle", required=True, name_ko="표지")
    builder.add_slide_type("learning_objectives", "bullet_points", required=True, name_ko="학습 목표")
    builder.add_slide_type("introduction", "single_column", required=True, name_ko="도입")
    builder.add_slide_type("content", "two_column", required=True, name_ko="본문")
    builder.add_slide_type("example", "image_right", required=False, name_ko="예시")
    builder.add_slide_type("key_concepts", "bullet_points", required=True, name_ko="핵심 개념")
    builder.add_slide_type("summary", "single_column", required=True, name_ko="요약")
    builder.add_slide_type("questions", "contact", required=True, name_ko="질문")

    return builder


def create_product_launch_template() -> TemplateBuilder:
    """제품 출시 템플릿 생성

    Returns:
        구성된 TemplateBuilder
    """
    builder = TemplateBuilder(
        id="product_launch",
        name="Product Launch",
        name_ko="제품 출시",
        category="marketing",
        description="신제품 출시 발표를 위한 임팩트 있는 템플릿"
    )

    builder.add_tags(["marketing", "product", "launch", "announcement"])
    builder.add_best_for("신제품 발표")
    builder.add_best_for("제품 소개")
    builder.add_best_for("런칭 이벤트")

    builder.add_color_scheme(
        "vibrant",
        primary="#7c3aed",
        secondary="#8b5cf6",
        accent="#a78bfa",
        background="#0f0f0f",
        text="#ffffff",
        text_light="#d4d4d8"
    )

    builder.add_color_scheme(
        "clean",
        primary="#0ea5e9",
        secondary="#38bdf8",
        accent="#7dd3fc",
        background="#ffffff",
        text="#0f172a",
        text_light="#64748b"
    )

    builder.add_slide_type("title", "title_image_background", required=True, name_ko="표지")
    builder.add_slide_type("teaser", "image_full", required=False, name_ko="티저")
    builder.add_slide_type("reveal", "image_full", required=True, name_ko="제품 공개")
    builder.add_slide_type("features", "two_column", required=True, name_ko="주요 기능")
    builder.add_slide_type("benefits", "bullet_points", required=True, name_ko="핵심 혜택")
    builder.add_slide_type("demo", "image_left", required=False, name_ko="데모")
    builder.add_slide_type("pricing", "comparison", required=True, name_ko="가격")
    builder.add_slide_type("availability", "single_column", required=True, name_ko="출시 일정")
    builder.add_slide_type("cta", "contact", required=True, name_ko="행동 촉구")

    return builder
