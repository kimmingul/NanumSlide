"""템플릿 시스템 모듈

NanumSlide의 템플릿 시스템을 제공합니다.
레이아웃, 색상 스키마, 템플릿 로딩 및 매칭 기능을 포함합니다.
"""

# 레이아웃 타입 및 정의
from .layout_types import (
    LayoutCategory,
    LayoutType,
    LayoutRegion,
    Layout,
    DEFAULT_LAYOUTS,
    get_default_layout,
)

# 색상 스키마
from .color_schemes import (
    ColorPalette,
    COLOR_SCHEMES,
    get_color_scheme,
    get_all_scheme_names,
    get_brightness,
    get_contrast_color,
    lighten_color,
    darken_color,
    create_custom_palette,
    get_schemes_by_style,
)

# 템플릿 로더
from .template_loader import (
    TemplateInfo,
    CategoryInfo,
    TemplateLoader,
)

# 레이아웃 매처
from .layout_matcher import (
    ContentAnalysis,
    LayoutMatcher,
    create_layout_matcher,
)

# 템플릿 엔진
from .template_engine import (
    SlideSpec,
    PresentationSpec,
    TemplateEngine,
)

# 템플릿 빌더
from .template_builder import (
    TemplateBuilder,
    create_pitch_deck_template,
    create_quarterly_report_template,
    create_lecture_template,
    create_product_launch_template,
)

__all__ = [
    # layout_types
    "LayoutCategory",
    "LayoutType",
    "LayoutRegion",
    "Layout",
    "DEFAULT_LAYOUTS",
    "get_default_layout",

    # color_schemes
    "ColorPalette",
    "COLOR_SCHEMES",
    "get_color_scheme",
    "get_all_scheme_names",
    "get_brightness",
    "get_contrast_color",
    "lighten_color",
    "darken_color",
    "create_custom_palette",
    "get_schemes_by_style",

    # template_loader
    "TemplateInfo",
    "CategoryInfo",
    "TemplateLoader",

    # layout_matcher
    "ContentAnalysis",
    "LayoutMatcher",
    "create_layout_matcher",

    # template_engine
    "SlideSpec",
    "PresentationSpec",
    "TemplateEngine",

    # template_builder
    "TemplateBuilder",
    "create_pitch_deck_template",
    "create_quarterly_report_template",
    "create_lecture_template",
    "create_product_launch_template",
]

__version__ = "1.0.0"
