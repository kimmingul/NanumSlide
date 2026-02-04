"""색상 스키마 시스템 모듈

프레젠테이션에 사용되는 색상 팔레트와 색상 스키마를 정의합니다.
"""

from dataclasses import dataclass
from typing import Dict, Optional, List


@dataclass
class ColorPalette:
    """색상 팔레트

    프레젠테이션의 색상 구성을 정의합니다.
    주요 색상, 보조 색상, 강조 색상 등을 포함합니다.
    """
    primary: str        # 주요 색상
    secondary: str      # 보조 색상
    accent: str         # 강조 색상
    background: str     # 배경 색상
    text: str           # 텍스트 색상
    text_light: str     # 밝은 텍스트
    success: str = "#48bb78"
    warning: str = "#ed8936"
    error: str = "#f56565"

    def to_dict(self) -> Dict[str, str]:
        """딕셔너리로 변환"""
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "background": self.background,
            "text": self.text,
            "text_light": self.text_light,
            "success": self.success,
            "warning": self.warning,
            "error": self.error
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "ColorPalette":
        """딕셔너리에서 ColorPalette 생성"""
        return cls(
            primary=data.get("primary", "#1a365d"),
            secondary=data.get("secondary", "#2c5282"),
            accent=data.get("accent", "#3182ce"),
            background=data.get("background", "#ffffff"),
            text=data.get("text", "#1a202c"),
            text_light=data.get("text_light", "#718096"),
            success=data.get("success", "#48bb78"),
            warning=data.get("warning", "#ed8936"),
            error=data.get("error", "#f56565")
        )

    def is_dark_background(self) -> bool:
        """배경이 어두운 색인지 확인"""
        return get_brightness(self.background) < 128

    def get_text_color_for_background(self, bg_color: Optional[str] = None) -> str:
        """배경색에 적합한 텍스트 색상 반환"""
        bg = bg_color or self.background
        return get_contrast_color(bg)

    def get_complementary_colors(self) -> List[str]:
        """보색 목록 반환"""
        return [self.primary, self.secondary, self.accent]


# 기본 색상 스키마
COLOR_SCHEMES: Dict[str, ColorPalette] = {
    "professional": ColorPalette(
        primary="#1a365d",
        secondary="#2c5282",
        accent="#3182ce",
        background="#ffffff",
        text="#1a202c",
        text_light="#718096"
    ),

    "bold": ColorPalette(
        primary="#e53e3e",
        secondary="#c53030",
        accent="#fc8181",
        background="#1a202c",
        text="#ffffff",
        text_light="#a0aec0"
    ),

    "tech": ColorPalette(
        primary="#805ad5",
        secondary="#6b46c1",
        accent="#9f7aea",
        background="#1a202c",
        text="#ffffff",
        text_light="#a0aec0"
    ),

    "nature": ColorPalette(
        primary="#276749",
        secondary="#2f855a",
        accent="#48bb78",
        background="#f7fafc",
        text="#1a202c",
        text_light="#718096"
    ),

    "ocean": ColorPalette(
        primary="#0077b6",
        secondary="#0096c7",
        accent="#00b4d8",
        background="#ffffff",
        text="#1a202c",
        text_light="#718096"
    ),

    "sunset": ColorPalette(
        primary="#c2410c",
        secondary="#ea580c",
        accent="#fb923c",
        background="#fffbeb",
        text="#1a202c",
        text_light="#78716c"
    ),

    "monochrome": ColorPalette(
        primary="#1a202c",
        secondary="#2d3748",
        accent="#4a5568",
        background="#ffffff",
        text="#1a202c",
        text_light="#718096"
    ),

    "dark": ColorPalette(
        primary="#60a5fa",
        secondary="#3b82f6",
        accent="#93c5fd",
        background="#0f172a",
        text="#f1f5f9",
        text_light="#94a3b8"
    ),

    "pastel": ColorPalette(
        primary="#a78bfa",
        secondary="#c4b5fd",
        accent="#ddd6fe",
        background="#faf5ff",
        text="#4c1d95",
        text_light="#7c3aed"
    ),

    "corporate": ColorPalette(
        primary="#1e40af",
        secondary="#1d4ed8",
        accent="#3b82f6",
        background="#f8fafc",
        text="#0f172a",
        text_light="#64748b"
    ),

    # 추가 색상 스키마
    "warm": ColorPalette(
        primary="#b45309",
        secondary="#d97706",
        accent="#f59e0b",
        background="#fffbeb",
        text="#1c1917",
        text_light="#78716c"
    ),

    "cool": ColorPalette(
        primary="#0e7490",
        secondary="#0891b2",
        accent="#06b6d4",
        background="#f0fdfa",
        text="#134e4a",
        text_light="#5eead4"
    ),

    "elegant": ColorPalette(
        primary="#4c1d95",
        secondary="#5b21b6",
        accent="#7c3aed",
        background="#faf5ff",
        text="#1e1b4b",
        text_light="#a78bfa"
    ),

    "fresh": ColorPalette(
        primary="#059669",
        secondary="#10b981",
        accent="#34d399",
        background="#ecfdf5",
        text="#064e3b",
        text_light="#6ee7b7"
    ),

    "minimal_light": ColorPalette(
        primary="#374151",
        secondary="#6b7280",
        accent="#9ca3af",
        background="#ffffff",
        text="#111827",
        text_light="#9ca3af"
    ),

    "minimal_dark": ColorPalette(
        primary="#d1d5db",
        secondary="#9ca3af",
        accent="#6b7280",
        background="#111827",
        text="#f9fafb",
        text_light="#d1d5db"
    )
}


def get_color_scheme(name: str) -> ColorPalette:
    """색상 스키마 조회

    Args:
        name: 색상 스키마 이름

    Returns:
        ColorPalette 객체. 이름이 없으면 'professional' 반환
    """
    return COLOR_SCHEMES.get(name, COLOR_SCHEMES["professional"])


def get_all_scheme_names() -> List[str]:
    """모든 색상 스키마 이름 목록 반환"""
    return list(COLOR_SCHEMES.keys())


def get_brightness(hex_color: str) -> float:
    """HEX 색상의 밝기 계산

    Args:
        hex_color: HEX 색상 코드 (예: "#ffffff")

    Returns:
        밝기 값 (0-255)
    """
    hex_color = hex_color.lstrip('#')
    if len(hex_color) != 6:
        return 128  # 기본값

    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        # 인간의 눈에 맞춘 밝기 계산 (ITU-R BT.601)
        return (r * 299 + g * 587 + b * 114) / 1000
    except ValueError:
        return 128


def get_contrast_color(background: str) -> str:
    """배경색에 맞는 대비 색상 반환

    Args:
        background: 배경 HEX 색상 코드

    Returns:
        대비되는 텍스트 색상 ("#ffffff" 또는 "#1a202c")
    """
    brightness = get_brightness(background)
    return "#ffffff" if brightness < 128 else "#1a202c"


def lighten_color(hex_color: str, factor: float = 0.2) -> str:
    """색상을 밝게 만들기

    Args:
        hex_color: HEX 색상 코드
        factor: 밝기 증가 비율 (0.0 - 1.0)

    Returns:
        밝아진 HEX 색상 코드
    """
    hex_color = hex_color.lstrip('#')
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))

        return f"#{r:02x}{g:02x}{b:02x}"
    except ValueError:
        return hex_color


def darken_color(hex_color: str, factor: float = 0.2) -> str:
    """색상을 어둡게 만들기

    Args:
        hex_color: HEX 색상 코드
        factor: 밝기 감소 비율 (0.0 - 1.0)

    Returns:
        어두워진 HEX 색상 코드
    """
    hex_color = hex_color.lstrip('#')
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))

        return f"#{r:02x}{g:02x}{b:02x}"
    except ValueError:
        return hex_color


def create_custom_palette(
    primary: str,
    background: str = "#ffffff",
    auto_generate: bool = True
) -> ColorPalette:
    """커스텀 팔레트 생성

    Args:
        primary: 주요 색상
        background: 배경 색상
        auto_generate: 나머지 색상 자동 생성 여부

    Returns:
        ColorPalette 객체
    """
    if auto_generate:
        secondary = darken_color(primary, 0.15)
        accent = lighten_color(primary, 0.3)
        text = get_contrast_color(background)
        text_light = lighten_color(text, 0.4) if get_brightness(text) < 128 else darken_color(text, 0.4)
    else:
        secondary = primary
        accent = primary
        text = "#1a202c"
        text_light = "#718096"

    return ColorPalette(
        primary=primary,
        secondary=secondary,
        accent=accent,
        background=background,
        text=text,
        text_light=text_light
    )


def get_schemes_by_style(style: str) -> List[str]:
    """스타일에 맞는 색상 스키마 목록 반환

    Args:
        style: 스타일 이름 (professional, creative, dark, light, colorful)

    Returns:
        해당 스타일에 맞는 스키마 이름 목록
    """
    style_mapping = {
        "professional": ["professional", "corporate", "monochrome", "minimal_light"],
        "creative": ["bold", "pastel", "sunset", "warm", "elegant"],
        "dark": ["dark", "tech", "bold", "minimal_dark"],
        "light": ["professional", "nature", "ocean", "fresh", "minimal_light", "pastel"],
        "colorful": ["bold", "tech", "sunset", "ocean", "fresh", "warm", "cool"]
    }

    return style_mapping.get(style, list(COLOR_SCHEMES.keys())[:5])
