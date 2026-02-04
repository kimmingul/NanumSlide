"""프레젠테이션 테마 정의"""

from typing import Optional
from pydantic import BaseModel


class ThemeColors(BaseModel):
    """테마 색상"""
    primary: str = "#007acc"      # 주 색상
    secondary: str = "#5c5c5c"    # 보조 색상
    accent: str = "#0ea5e9"       # 강조 색상
    background: str = "#ffffff"   # 배경색
    text_primary: str = "#333333" # 기본 텍스트
    text_secondary: str = "#666666"  # 보조 텍스트


class ThemeFonts(BaseModel):
    """테마 폰트"""
    title: str = "Malgun Gothic"
    body: str = "Malgun Gothic"
    title_size: int = 32
    body_size: int = 18


class Theme(BaseModel):
    """프레젠테이션 테마"""
    name: str
    display_name: str
    colors: ThemeColors = ThemeColors()
    fonts: ThemeFonts = ThemeFonts()


# 기본 테마 정의
THEMES: dict[str, Theme] = {
    "default": Theme(
        name="default",
        display_name="기본",
        colors=ThemeColors(
            primary="#007acc",
            secondary="#5c5c5c",
            accent="#0ea5e9",
            background="#ffffff",
            text_primary="#333333",
            text_secondary="#666666",
        ),
    ),
    "business": Theme(
        name="business",
        display_name="비즈니스",
        colors=ThemeColors(
            primary="#1e3a5f",
            secondary="#2c5282",
            accent="#3182ce",
            background="#ffffff",
            text_primary="#1a202c",
            text_secondary="#4a5568",
        ),
    ),
    "education": Theme(
        name="education",
        display_name="교육",
        colors=ThemeColors(
            primary="#2d5016",
            secondary="#48bb78",
            accent="#68d391",
            background="#ffffff",
            text_primary="#22543d",
            text_secondary="#276749",
        ),
    ),
    "minimal": Theme(
        name="minimal",
        display_name="미니멀",
        colors=ThemeColors(
            primary="#171717",
            secondary="#525252",
            accent="#737373",
            background="#fafafa",
            text_primary="#171717",
            text_secondary="#525252",
        ),
    ),
    "creative": Theme(
        name="creative",
        display_name="크리에이티브",
        colors=ThemeColors(
            primary="#7c3aed",
            secondary="#a78bfa",
            accent="#c4b5fd",
            background="#ffffff",
            text_primary="#4c1d95",
            text_secondary="#6d28d9",
        ),
    ),
    "dark": Theme(
        name="dark",
        display_name="다크",
        colors=ThemeColors(
            primary="#60a5fa",
            secondary="#93c5fd",
            accent="#3b82f6",
            background="#1e293b",
            text_primary="#f1f5f9",
            text_secondary="#cbd5e1",
        ),
    ),
    "warm": Theme(
        name="warm",
        display_name="따뜻한",
        colors=ThemeColors(
            primary="#ea580c",
            secondary="#fb923c",
            accent="#fdba74",
            background="#fffbeb",
            text_primary="#7c2d12",
            text_secondary="#9a3412",
        ),
    ),
    "cool": Theme(
        name="cool",
        display_name="시원한",
        colors=ThemeColors(
            primary="#0891b2",
            secondary="#22d3ee",
            accent="#67e8f9",
            background="#ecfeff",
            text_primary="#164e63",
            text_secondary="#155e75",
        ),
    ),
}


def get_theme(name: str) -> Theme:
    """테마 가져오기"""
    return THEMES.get(name, THEMES["default"])


def get_theme_by_display_name(display_name: str) -> Theme:
    """표시 이름으로 테마 가져오기"""
    for theme in THEMES.values():
        if theme.display_name == display_name:
            return theme
    return THEMES["default"]


def get_all_themes() -> list[Theme]:
    """모든 테마 목록 반환"""
    return list(THEMES.values())


def get_theme_names() -> list[str]:
    """테마 표시 이름 목록 반환"""
    return [theme.display_name for theme in THEMES.values()]
