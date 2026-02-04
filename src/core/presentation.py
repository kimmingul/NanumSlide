"""프레젠테이션 데이터 모델"""

from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class SlideLayoutType(str, Enum):
    """슬라이드 레이아웃 유형"""
    TITLE = "title"                    # 제목 슬라이드
    TITLE_CONTENT = "title_content"    # 제목 + 내용
    TWO_COLUMN = "two_column"          # 2단 레이아웃
    TITLE_IMAGE = "title_image"        # 제목 + 이미지
    IMAGE_FULL = "image_full"          # 전체 이미지
    BULLET_POINTS = "bullet_points"    # 글머리 기호
    CHART = "chart"                    # 차트
    QUOTE = "quote"                    # 인용문
    BLANK = "blank"                    # 빈 슬라이드


class TextStyle(BaseModel):
    """텍스트 스타일"""
    font_name: str = "Malgun Gothic"
    font_size: int = 12
    font_color: str = "333333"
    bold: bool = False
    italic: bool = False
    underline: bool = False


class SlideElement(BaseModel):
    """슬라이드 요소 기본 클래스"""
    x: float = 0          # X 좌표 (pt)
    y: float = 0          # Y 좌표 (pt)
    width: float = 100    # 너비 (pt)
    height: float = 100   # 높이 (pt)


class TextElement(SlideElement):
    """텍스트 요소"""
    text: str = ""
    style: TextStyle = Field(default_factory=TextStyle)
    alignment: str = "left"  # left, center, right


class ImageElement(SlideElement):
    """이미지 요소"""
    path: str = ""
    alt_text: str = ""
    fit: str = "contain"  # contain, cover, fill


class ShapeElement(SlideElement):
    """도형 요소"""
    shape_type: str = "rectangle"
    fill_color: Optional[str] = None
    stroke_color: Optional[str] = None
    stroke_width: float = 1


class Slide(BaseModel):
    """슬라이드 모델"""
    id: str = ""
    layout: SlideLayoutType = SlideLayoutType.TITLE_CONTENT
    title: str = ""
    subtitle: str = ""
    content: str = ""
    bullet_points: list[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    image_prompt: Optional[str] = None
    notes: str = ""
    background_color: str = "ffffff"
    elements: list[SlideElement] = Field(default_factory=list)

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "Slide":
        """딕셔너리에서 생성"""
        return cls(**data)


class Presentation(BaseModel):
    """프레젠테이션 모델"""
    id: str = ""
    title: str = ""
    author: str = ""
    description: str = ""
    slides: list[Slide] = Field(default_factory=list)
    theme: str = "default"
    language: str = "ko"

    # 메타데이터
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    prompt: Optional[str] = None  # 생성에 사용된 프롬프트

    def add_slide(self, slide: Slide) -> None:
        """슬라이드 추가"""
        if not slide.id:
            slide.id = f"slide_{len(self.slides) + 1}"
        self.slides.append(slide)

    def remove_slide(self, index: int) -> Optional[Slide]:
        """슬라이드 삭제"""
        if 0 <= index < len(self.slides):
            return self.slides.pop(index)
        return None

    def move_slide(self, from_index: int, to_index: int) -> bool:
        """슬라이드 이동"""
        if 0 <= from_index < len(self.slides) and 0 <= to_index < len(self.slides):
            slide = self.slides.pop(from_index)
            self.slides.insert(to_index, slide)
            return True
        return False

    def get_slide(self, index: int) -> Optional[Slide]:
        """슬라이드 가져오기"""
        if 0 <= index < len(self.slides):
            return self.slides[index]
        return None

    @property
    def slide_count(self) -> int:
        """슬라이드 수"""
        return len(self.slides)

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "Presentation":
        """딕셔너리에서 생성"""
        return cls(**data)

    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return self.model_dump_json(indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "Presentation":
        """JSON 문자열에서 생성"""
        return cls.model_validate_json(json_str)
