"""레이아웃 타입 정의 모듈

레이아웃 카테고리, 타입 열거형 및 레이아웃 영역/정의 데이터클래스를 제공합니다.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


class LayoutCategory(Enum):
    """레이아웃 카테고리"""
    TITLE = "title"
    CONTENT = "content"
    IMAGE = "image"
    DATA = "data"
    SPECIAL = "special"


class LayoutType(Enum):
    """레이아웃 타입"""
    # Title layouts
    TITLE_CENTERED = "title_centered"
    TITLE_LEFT = "title_left"
    TITLE_WITH_SUBTITLE = "title_with_subtitle"
    TITLE_IMAGE_BG = "title_image_background"

    # Content layouts
    SINGLE_COLUMN = "single_column"
    TWO_COLUMN = "two_column"
    THREE_COLUMN = "three_column"
    BULLET_POINTS = "bullet_points"

    # Image layouts
    IMAGE_FULL = "image_full"
    IMAGE_LEFT = "image_left"
    IMAGE_RIGHT = "image_right"
    IMAGE_BACKGROUND = "image_background"
    IMAGE_GRID = "image_grid"

    # Data layouts
    CHART_CENTERED = "chart_centered"
    STATISTICS = "statistics"
    COMPARISON = "comparison"
    TABLE = "table"

    # Special layouts
    QUOTE = "quote"
    TIMELINE = "timeline"
    TEAM_GRID = "team_grid"
    CONTACT = "contact"
    AGENDA = "agenda"


@dataclass
class LayoutRegion:
    """레이아웃 영역 정의

    슬라이드 내의 특정 영역을 정의합니다.
    각 영역은 위치, 크기, 허용되는 콘텐츠 타입 등의 정보를 포함합니다.
    """
    id: str
    type: str           # "text", "image", "chart", "content"
    purpose: str        # "heading", "primary", "secondary", "accent"
    x: int
    y: int
    width: int
    height: int
    accepts: List[str]  # 허용되는 콘텐츠 타입
    style: Optional[Dict[str, Any]] = None

    def contains_point(self, px: int, py: int) -> bool:
        """주어진 좌표가 이 영역 내에 있는지 확인"""
        return (self.x <= px <= self.x + self.width and
                self.y <= py <= self.y + self.height)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "type": self.type,
            "purpose": self.purpose,
            "position": {
                "x": self.x,
                "y": self.y,
                "width": self.width,
                "height": self.height
            },
            "accepts": self.accepts,
            "style": self.style
        }


@dataclass
class Layout:
    """레이아웃 정의

    슬라이드의 전체 레이아웃을 정의합니다.
    여러 영역(region)으로 구성되며, 각 영역에 콘텐츠를 배치할 수 있습니다.
    """
    id: str
    name: str
    category: LayoutCategory
    layout_type: LayoutType
    regions: List[LayoutRegion]
    constraints: Dict[str, Any]
    animations: Optional[Dict[str, Any]] = None
    description: str = ""

    def get_region(self, region_id: str) -> Optional[LayoutRegion]:
        """ID로 영역 조회"""
        for region in self.regions:
            if region.id == region_id:
                return region
        return None

    def get_primary_region(self) -> Optional[LayoutRegion]:
        """주요 콘텐츠 영역 조회"""
        for region in self.regions:
            if region.purpose == "primary":
                return region
        return None

    def get_heading_region(self) -> Optional[LayoutRegion]:
        """제목 영역 조회"""
        for region in self.regions:
            if region.purpose == "heading":
                return region
        return None

    def get_regions_by_type(self, region_type: str) -> List[LayoutRegion]:
        """타입으로 영역 목록 조회"""
        return [r for r in self.regions if r.type == region_type]

    def get_regions_by_purpose(self, purpose: str) -> List[LayoutRegion]:
        """목적으로 영역 목록 조회"""
        return [r for r in self.regions if r.purpose == purpose]

    def accepts_content_type(self, content_type: str) -> bool:
        """특정 콘텐츠 타입을 허용하는 영역이 있는지 확인"""
        for region in self.regions:
            if content_type in region.accepts:
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "layout_type": self.layout_type.value,
            "regions": [r.to_dict() for r in self.regions],
            "constraints": self.constraints,
            "animations": self.animations,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Layout":
        """딕셔너리에서 Layout 객체 생성"""
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

        return cls(
            id=data["id"],
            name=data["name"],
            category=LayoutCategory(data.get("category", "content")),
            layout_type=LayoutType(data.get("layout_type", data["id"])),
            regions=regions,
            constraints=data.get("constraints", {}),
            animations=data.get("animations"),
            description=data.get("description", "")
        )


# 기본 레이아웃 정의
DEFAULT_LAYOUTS: Dict[LayoutType, Layout] = {
    LayoutType.TITLE_CENTERED: Layout(
        id="title_centered",
        name="Centered Title",
        category=LayoutCategory.TITLE,
        layout_type=LayoutType.TITLE_CENTERED,
        regions=[
            LayoutRegion(
                id="title",
                type="text",
                purpose="heading",
                x=60, y=400, width=1800, height=120,
                accepts=["text"],
                style={"font_size": 54, "font_weight": 700, "align": "center"}
            ),
            LayoutRegion(
                id="subtitle",
                type="text",
                purpose="secondary",
                x=60, y=540, width=1800, height=60,
                accepts=["text"],
                style={"font_size": 28, "font_weight": 400, "align": "center"}
            )
        ],
        constraints={"max_title_length": 80},
        description="중앙 정렬 제목 슬라이드"
    ),

    LayoutType.SINGLE_COLUMN: Layout(
        id="single_column",
        name="Single Column",
        category=LayoutCategory.CONTENT,
        layout_type=LayoutType.SINGLE_COLUMN,
        regions=[
            LayoutRegion(
                id="title",
                type="text",
                purpose="heading",
                x=60, y=60, width=1800, height=80,
                accepts=["text"],
                style={"font_size": 44, "font_weight": 600, "align": "left"}
            ),
            LayoutRegion(
                id="content",
                type="content",
                purpose="primary",
                x=60, y=180, width=1800, height=800,
                accepts=["text", "bullet_points"]
            )
        ],
        constraints={"min_content_items": 1},
        description="단일 열 콘텐츠 레이아웃"
    ),

    LayoutType.TWO_COLUMN: Layout(
        id="two_column",
        name="Two Column Layout",
        category=LayoutCategory.CONTENT,
        layout_type=LayoutType.TWO_COLUMN,
        regions=[
            LayoutRegion(
                id="title",
                type="text",
                purpose="heading",
                x=60, y=60, width=1800, height=80,
                accepts=["text"],
                style={"font_size": 44, "font_weight": 600, "align": "left"}
            ),
            LayoutRegion(
                id="left_column",
                type="content",
                purpose="primary",
                x=60, y=180, width=880, height=800,
                accepts=["text", "bullet_points", "image"]
            ),
            LayoutRegion(
                id="right_column",
                type="content",
                purpose="secondary",
                x=980, y=180, width=880, height=800,
                accepts=["text", "bullet_points", "image", "chart"]
            )
        ],
        constraints={"min_content_items": 2, "balanced_columns": True},
        animations={"entrance": "fade_in_left_right", "sequence": ["title", "left_column", "right_column"]},
        description="좌우 2단 레이아웃"
    ),

    LayoutType.IMAGE_LEFT: Layout(
        id="image_left",
        name="Image Left",
        category=LayoutCategory.IMAGE,
        layout_type=LayoutType.IMAGE_LEFT,
        regions=[
            LayoutRegion(
                id="title",
                type="text",
                purpose="heading",
                x=980, y=60, width=880, height=80,
                accepts=["text"],
                style={"font_size": 44, "font_weight": 600, "align": "left"}
            ),
            LayoutRegion(
                id="image",
                type="image",
                purpose="accent",
                x=60, y=60, width=880, height=920,
                accepts=["image"]
            ),
            LayoutRegion(
                id="content",
                type="content",
                purpose="primary",
                x=980, y=180, width=880, height=800,
                accepts=["text", "bullet_points"]
            )
        ],
        constraints={"requires_image": True},
        description="왼쪽 이미지 + 오른쪽 콘텐츠"
    ),

    LayoutType.IMAGE_RIGHT: Layout(
        id="image_right",
        name="Image Right",
        category=LayoutCategory.IMAGE,
        layout_type=LayoutType.IMAGE_RIGHT,
        regions=[
            LayoutRegion(
                id="title",
                type="text",
                purpose="heading",
                x=60, y=60, width=880, height=80,
                accepts=["text"],
                style={"font_size": 44, "font_weight": 600, "align": "left"}
            ),
            LayoutRegion(
                id="content",
                type="content",
                purpose="primary",
                x=60, y=180, width=880, height=800,
                accepts=["text", "bullet_points"]
            ),
            LayoutRegion(
                id="image",
                type="image",
                purpose="accent",
                x=980, y=60, width=880, height=920,
                accepts=["image"]
            )
        ],
        constraints={"requires_image": True},
        description="왼쪽 콘텐츠 + 오른쪽 이미지"
    ),

    LayoutType.CHART_CENTERED: Layout(
        id="chart_centered",
        name="Chart Centered",
        category=LayoutCategory.DATA,
        layout_type=LayoutType.CHART_CENTERED,
        regions=[
            LayoutRegion(
                id="title",
                type="text",
                purpose="heading",
                x=60, y=60, width=1800, height=80,
                accepts=["text"],
                style={"font_size": 44, "font_weight": 600, "align": "left"}
            ),
            LayoutRegion(
                id="chart",
                type="chart",
                purpose="primary",
                x=160, y=180, width=1600, height=700,
                accepts=["chart"]
            ),
            LayoutRegion(
                id="caption",
                type="text",
                purpose="secondary",
                x=60, y=900, width=1800, height=60,
                accepts=["text"],
                style={"font_size": 18, "align": "center"}
            )
        ],
        constraints={"requires_chart": True},
        description="차트 중심 레이아웃"
    ),

    LayoutType.QUOTE: Layout(
        id="quote",
        name="Quote",
        category=LayoutCategory.SPECIAL,
        layout_type=LayoutType.QUOTE,
        regions=[
            LayoutRegion(
                id="quote",
                type="text",
                purpose="primary",
                x=160, y=300, width=1600, height=300,
                accepts=["text"],
                style={"font_size": 36, "font_weight": 400, "align": "center", "italic": True}
            ),
            LayoutRegion(
                id="attribution",
                type="text",
                purpose="secondary",
                x=160, y=620, width=1600, height=60,
                accepts=["text"],
                style={"font_size": 24, "align": "center"}
            )
        ],
        constraints={},
        description="인용문 레이아웃"
    ),

    LayoutType.CONTACT: Layout(
        id="contact",
        name="Contact",
        category=LayoutCategory.SPECIAL,
        layout_type=LayoutType.CONTACT,
        regions=[
            LayoutRegion(
                id="title",
                type="text",
                purpose="heading",
                x=60, y=300, width=1800, height=100,
                accepts=["text"],
                style={"font_size": 48, "font_weight": 700, "align": "center"}
            ),
            LayoutRegion(
                id="contact_info",
                type="content",
                purpose="primary",
                x=460, y=450, width=1000, height=400,
                accepts=["text", "bullet_points"]
            )
        ],
        constraints={},
        description="연락처 정보 레이아웃"
    )
}


def get_default_layout(layout_type: LayoutType) -> Layout:
    """기본 레이아웃 조회"""
    if layout_type in DEFAULT_LAYOUTS:
        return DEFAULT_LAYOUTS[layout_type]

    # 기본 단일 열 레이아웃 반환
    return DEFAULT_LAYOUTS[LayoutType.SINGLE_COLUMN]
