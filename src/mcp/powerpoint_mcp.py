"""PowerPoint MCP 클라이언트 모듈

Microsoft PowerPoint를 MCP를 통해 제어하는 클라이언트입니다.
슬라이드 생성, 콘텐츠 추가, 애니메이션, 전환 효과 등을 지원합니다.
"""

import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from .mcp_client import MCPClient


class SlideLayout(Enum):
    """슬라이드 레이아웃 타입"""
    TITLE = "title"
    TITLE_CONTENT = "title_and_content"
    SECTION_HEADER = "section_header"
    TWO_CONTENT = "two_content"
    COMPARISON = "comparison"
    TITLE_ONLY = "title_only"
    BLANK = "blank"
    CONTENT_WITH_CAPTION = "content_with_caption"
    PICTURE_WITH_CAPTION = "picture_with_caption"


class ChartType(Enum):
    """차트 타입"""
    BAR = "bar"
    COLUMN = "column"
    LINE = "line"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    AREA = "area"
    SCATTER = "scatter"
    RADAR = "radar"


class SmartArtType(Enum):
    """SmartArt 타입"""
    PROCESS = "process"
    CYCLE = "cycle"
    HIERARCHY = "hierarchy"
    RELATIONSHIP = "relationship"
    MATRIX = "matrix"
    PYRAMID = "pyramid"
    PICTURE = "picture"


class AnimationType(Enum):
    """애니메이션 타입"""
    FADE = "fade"
    FLY_IN = "fly_in"
    FLOAT_IN = "float_in"
    WIPE = "wipe"
    ZOOM = "zoom"
    GROW_SHRINK = "grow_shrink"
    SPIN = "spin"


class TransitionType(Enum):
    """전환 효과 타입"""
    FADE = "fade"
    PUSH = "push"
    WIPE = "wipe"
    SPLIT = "split"
    REVEAL = "reveal"
    MORPH = "morph"
    CUBE = "cube"
    GALLERY = "gallery"


@dataclass
class Position:
    """위치 정보 (인치 단위)

    Attributes:
        x: X 좌표 (인치)
        y: Y 좌표 (인치)
    """
    x: float
    y: float

    def to_dict(self) -> Dict[str, float]:
        """딕셔너리로 변환"""
        return {"x": self.x, "y": self.y}


@dataclass
class Size:
    """크기 정보 (인치 단위)

    Attributes:
        width: 너비 (인치)
        height: 높이 (인치)
    """
    width: float
    height: float

    def to_dict(self) -> Dict[str, float]:
        """딕셔너리로 변환"""
        return {"width": self.width, "height": self.height}


class PowerPointMCPClient:
    """PowerPoint MCP 클라이언트

    MCP를 통해 Microsoft PowerPoint를 제어하는 클라이언트입니다.
    프레젠테이션 생성, 슬라이드 관리, 콘텐츠 추가, 애니메이션 등의
    기능을 제공합니다.

    Attributes:
        mcp: 기본 MCP 클라이언트
    """

    def __init__(self, mcp_client: MCPClient):
        """PowerPointMCPClient 초기화

        Args:
            mcp_client: MCP 클라이언트 인스턴스
        """
        self.mcp = mcp_client
        self._presentation_open = False

    @property
    def is_presentation_open(self) -> bool:
        """프레젠테이션 열림 상태"""
        return self._presentation_open

    # ========== 프레젠테이션 관리 ==========

    async def create_presentation(
        self,
        title: str,
        template: Optional[str] = None,
        aspect_ratio: str = "16:9"
    ) -> Dict[str, Any]:
        """새 프레젠테이션 생성

        Args:
            title: 프레젠테이션 제목
            template: 템플릿 파일 경로 (선택사항)
            aspect_ratio: 화면 비율 ("16:9" 또는 "4:3")

        Returns:
            생성된 프레젠테이션 정보
        """
        result = await self.mcp.call_tool(
            "powerpoint",
            "create_presentation",
            {
                "title": title,
                "template": template,
                "aspect_ratio": aspect_ratio
            }
        )
        self._presentation_open = True
        return result

    async def open_presentation(self, path: str) -> Dict[str, Any]:
        """기존 프레젠테이션 열기

        Args:
            path: 프레젠테이션 파일 경로

        Returns:
            열린 프레젠테이션 정보
        """
        result = await self.mcp.call_tool(
            "powerpoint",
            "open_presentation",
            {"path": path}
        )
        self._presentation_open = True
        return result

    async def save_presentation(self, path: str) -> Dict[str, Any]:
        """프레젠테이션 저장

        Args:
            path: 저장 경로

        Returns:
            저장 결과
        """
        return await self.mcp.call_tool(
            "powerpoint",
            "save_presentation",
            {"path": path}
        )

    async def close_presentation(self) -> Dict[str, Any]:
        """프레젠테이션 닫기

        Returns:
            닫기 결과
        """
        result = await self.mcp.call_tool(
            "powerpoint",
            "close_presentation",
            {}
        )
        self._presentation_open = False
        return result

    # ========== 슬라이드 관리 ==========

    async def add_slide(
        self,
        layout: SlideLayout,
        position: Optional[int] = None
    ) -> Dict[str, Any]:
        """슬라이드 추가

        Args:
            layout: 슬라이드 레이아웃
            position: 삽입 위치 (None이면 마지막에 추가)

        Returns:
            추가된 슬라이드 정보
        """
        params = {"layout": layout.value}
        if position is not None:
            params["position"] = position

        return await self.mcp.call_tool("powerpoint", "add_slide", params)

    async def delete_slide(self, index: int) -> Dict[str, Any]:
        """슬라이드 삭제

        Args:
            index: 슬라이드 인덱스

        Returns:
            삭제 결과
        """
        return await self.mcp.call_tool(
            "powerpoint",
            "delete_slide",
            {"index": index}
        )

    async def duplicate_slide(self, index: int) -> Dict[str, Any]:
        """슬라이드 복제

        Args:
            index: 복제할 슬라이드 인덱스

        Returns:
            복제된 슬라이드 정보
        """
        return await self.mcp.call_tool(
            "powerpoint",
            "duplicate_slide",
            {"index": index}
        )

    async def move_slide(self, from_index: int, to_index: int) -> Dict[str, Any]:
        """슬라이드 이동

        Args:
            from_index: 이동할 슬라이드 인덱스
            to_index: 목적지 인덱스

        Returns:
            이동 결과
        """
        return await self.mcp.call_tool(
            "powerpoint",
            "move_slide",
            {"from": from_index, "to": to_index}
        )

    # ========== 콘텐츠 추가 ==========

    async def add_text_box(
        self,
        slide_index: int,
        text: str,
        position: Position,
        size: Size,
        font_size: int = 24,
        font_name: str = "Pretendard",
        font_color: str = "#000000",
        bold: bool = False,
        align: str = "left"
    ) -> Dict[str, Any]:
        """텍스트 박스 추가

        Args:
            slide_index: 슬라이드 인덱스
            text: 텍스트 내용
            position: 위치
            size: 크기
            font_size: 폰트 크기 (기본값: 24)
            font_name: 폰트 이름 (기본값: "Pretendard")
            font_color: 폰트 색상 (기본값: "#000000")
            bold: 굵게 여부 (기본값: False)
            align: 정렬 ("left", "center", "right")

        Returns:
            추가된 텍스트 박스 정보
        """
        return await self.mcp.call_tool(
            "powerpoint",
            "add_text_box",
            {
                "slide_index": slide_index,
                "text": text,
                "position": position.to_dict(),
                "size": size.to_dict(),
                "style": {
                    "font_size": font_size,
                    "font_name": font_name,
                    "font_color": font_color,
                    "bold": bold,
                    "align": align
                }
            }
        )

    async def add_image(
        self,
        slide_index: int,
        image_path: str,
        position: Position,
        size: Optional[Size] = None
    ) -> Dict[str, Any]:
        """이미지 추가

        Args:
            slide_index: 슬라이드 인덱스
            image_path: 이미지 파일 경로
            position: 위치
            size: 크기 (None이면 원본 크기)

        Returns:
            추가된 이미지 정보
        """
        params = {
            "slide_index": slide_index,
            "image_path": image_path,
            "position": position.to_dict()
        }

        if size:
            params["size"] = size.to_dict()

        return await self.mcp.call_tool("powerpoint", "add_image", params)

    async def add_shape(
        self,
        slide_index: int,
        shape_type: str,
        position: Position,
        size: Size,
        fill_color: Optional[str] = None,
        line_color: Optional[str] = None
    ) -> Dict[str, Any]:
        """도형 추가

        Args:
            slide_index: 슬라이드 인덱스
            shape_type: 도형 타입
            position: 위치
            size: 크기
            fill_color: 채우기 색상 (선택사항)
            line_color: 선 색상 (선택사항)

        Returns:
            추가된 도형 정보
        """
        params = {
            "slide_index": slide_index,
            "shape_type": shape_type,
            "position": position.to_dict(),
            "size": size.to_dict()
        }

        if fill_color:
            params["fill_color"] = fill_color
        if line_color:
            params["line_color"] = line_color

        return await self.mcp.call_tool("powerpoint", "add_shape", params)

    # ========== 차트 및 SmartArt ==========

    async def add_chart(
        self,
        slide_index: int,
        chart_type: ChartType,
        title: str,
        categories: List[str],
        series: List[Dict[str, Any]],
        position: Position,
        size: Size
    ) -> Dict[str, Any]:
        """차트 추가

        Args:
            slide_index: 슬라이드 인덱스
            chart_type: 차트 타입
            title: 차트 제목
            categories: 카테고리 목록
            series: 시리즈 데이터 목록
            position: 위치
            size: 크기

        Returns:
            추가된 차트 정보
        """
        return await self.mcp.call_tool(
            "powerpoint",
            "add_chart",
            {
                "slide_index": slide_index,
                "chart_type": chart_type.value,
                "data": {
                    "title": title,
                    "categories": categories,
                    "series": series
                },
                "position": position.to_dict(),
                "size": size.to_dict()
            }
        )

    async def add_smartart(
        self,
        slide_index: int,
        smartart_type: SmartArtType,
        items: List[str],
        position: Position,
        size: Size
    ) -> Dict[str, Any]:
        """SmartArt 추가

        Args:
            slide_index: 슬라이드 인덱스
            smartart_type: SmartArt 타입
            items: 항목 목록
            position: 위치
            size: 크기

        Returns:
            추가된 SmartArt 정보
        """
        return await self.mcp.call_tool(
            "powerpoint",
            "add_smartart",
            {
                "slide_index": slide_index,
                "smartart_type": smartart_type.value,
                "items": items,
                "position": position.to_dict(),
                "size": size.to_dict()
            }
        )

    async def add_table(
        self,
        slide_index: int,
        data: List[List[str]],
        position: Position,
        size: Size,
        header_row: bool = True
    ) -> Dict[str, Any]:
        """테이블 추가

        Args:
            slide_index: 슬라이드 인덱스
            data: 테이블 데이터 (2D 리스트)
            position: 위치
            size: 크기
            header_row: 헤더 행 여부 (기본값: True)

        Returns:
            추가된 테이블 정보
        """
        return await self.mcp.call_tool(
            "powerpoint",
            "add_table",
            {
                "slide_index": slide_index,
                "rows": len(data),
                "columns": len(data[0]) if data else 0,
                "data": data,
                "position": position.to_dict(),
                "size": size.to_dict(),
                "header_row": header_row
            }
        )

    # ========== 디자인 및 테마 ==========

    async def apply_theme(self, theme_path: str) -> Dict[str, Any]:
        """테마 적용

        Args:
            theme_path: 테마 파일 경로

        Returns:
            적용 결과
        """
        return await self.mcp.call_tool(
            "powerpoint",
            "apply_theme",
            {"theme_path": theme_path}
        )

    async def set_slide_background(
        self,
        slide_index: int,
        background_type: str,
        value: Any
    ) -> Dict[str, Any]:
        """슬라이드 배경 설정

        Args:
            slide_index: 슬라이드 인덱스
            background_type: 배경 타입 ("solid", "gradient", "image")
            value: 배경 값 (색상, 그라데이션 설정, 이미지 경로)

        Returns:
            설정 결과
        """
        return await self.mcp.call_tool(
            "powerpoint",
            "set_slide_background",
            {
                "slide_index": slide_index,
                "type": background_type,
                "value": value
            }
        )

    async def apply_master_slide(
        self,
        slide_index: int,
        master_name: str
    ) -> Dict[str, Any]:
        """마스터 슬라이드 적용

        Args:
            slide_index: 슬라이드 인덱스
            master_name: 마스터 슬라이드 이름

        Returns:
            적용 결과
        """
        return await self.mcp.call_tool(
            "powerpoint",
            "apply_master_slide",
            {
                "slide_index": slide_index,
                "master_name": master_name
            }
        )

    # ========== 애니메이션 및 전환 ==========

    async def add_animation(
        self,
        slide_index: int,
        shape_index: int,
        animation_type: AnimationType,
        trigger: str = "on_click",
        duration: float = 0.5,
        delay: float = 0.0
    ) -> Dict[str, Any]:
        """애니메이션 추가

        Args:
            slide_index: 슬라이드 인덱스
            shape_index: 도형 인덱스
            animation_type: 애니메이션 타입
            trigger: 트리거 ("on_click", "with_previous", "after_previous")
            duration: 지속 시간 (초)
            delay: 지연 시간 (초)

        Returns:
            추가된 애니메이션 정보
        """
        return await self.mcp.call_tool(
            "powerpoint",
            "add_animation",
            {
                "slide_index": slide_index,
                "shape_index": shape_index,
                "animation_type": animation_type.value,
                "trigger": trigger,
                "duration": duration,
                "delay": delay
            }
        )

    async def set_transition(
        self,
        slide_index: int,
        transition_type: TransitionType,
        duration: float = 0.5,
        advance_on_click: bool = True,
        advance_after: Optional[float] = None
    ) -> Dict[str, Any]:
        """슬라이드 전환 효과 설정

        Args:
            slide_index: 슬라이드 인덱스
            transition_type: 전환 효과 타입
            duration: 전환 지속 시간 (초)
            advance_on_click: 클릭 시 진행 여부
            advance_after: 자동 진행 시간 (초, None이면 자동 진행 안함)

        Returns:
            설정 결과
        """
        params = {
            "slide_index": slide_index,
            "transition_type": transition_type.value,
            "duration": duration,
            "advance_on_click": advance_on_click
        }

        if advance_after is not None:
            params["advance_after"] = advance_after

        return await self.mcp.call_tool("powerpoint", "set_transition", params)

    async def add_morph_transition(
        self,
        slide_index: int,
        duration: float = 0.75
    ) -> Dict[str, Any]:
        """Morph 전환 효과 추가

        Args:
            slide_index: 슬라이드 인덱스
            duration: 전환 지속 시간 (초)

        Returns:
            설정 결과
        """
        return await self.mcp.call_tool(
            "powerpoint",
            "add_morph_transition",
            {
                "slide_index": slide_index,
                "duration": duration
            }
        )

    # ========== 발표자 노트 ==========

    async def set_speaker_notes(
        self,
        slide_index: int,
        notes: str
    ) -> Dict[str, Any]:
        """발표자 노트 설정

        Args:
            slide_index: 슬라이드 인덱스
            notes: 노트 내용

        Returns:
            설정 결과
        """
        return await self.mcp.call_tool(
            "powerpoint",
            "set_speaker_notes",
            {
                "slide_index": slide_index,
                "notes": notes
            }
        )

    # ========== 내보내기 ==========

    async def export_to_pdf(self, output_path: str) -> Dict[str, Any]:
        """PDF로 내보내기

        Args:
            output_path: 출력 파일 경로

        Returns:
            내보내기 결과
        """
        return await self.mcp.call_tool(
            "powerpoint",
            "export_to_pdf",
            {"output_path": output_path}
        )

    async def export_to_images(
        self,
        output_dir: str,
        format: str = "png"
    ) -> Dict[str, Any]:
        """이미지로 내보내기

        Args:
            output_dir: 출력 디렉토리
            format: 이미지 형식 ("png" 또는 "jpg")

        Returns:
            내보내기 결과 (생성된 이미지 경로 목록 포함)
        """
        return await self.mcp.call_tool(
            "powerpoint",
            "export_to_images",
            {
                "output_dir": output_dir,
                "format": format
            }
        )
