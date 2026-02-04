"""NanumSlide - AI 기반 프레젠테이션 생성기

NanumSlide는 AI를 활용하여 프레젠테이션을 자동으로 생성하는 도구입니다.

주요 기능:
- Multi-Agent 시스템을 통한 지능형 콘텐츠 생성
- 다양한 템플릿과 레이아웃 지원
- MCP 통합을 통한 외부 서비스 연동
- 슬래시 명령어 기반의 스킬 시스템
"""

__version__ = "0.2.0"

# Core models
from .core.presentation import (
    Presentation,
    Slide,
    SlideLayoutType,
)

# Agents
from .agents import (
    BaseAgent,
    AgentOrchestrator,
    ResearchAgent,
    ContentAgent,
    DesignAgent,
    ImageAgent,
    ReviewAgent,
    AgentContext,
)

# Templates
from .templates import (
    TemplateEngine,
    TemplateLoader,
    LayoutMatcher,
    ColorPalette,
    get_color_scheme,
)

# MCP Integration
from .mcp import (
    MCPClient,
    MCPManager,
    PowerPointMCPClient,
)

# Skills
from .skills import (
    BaseSkill,
    SkillRegistry,
    SkillPipeline,
    ResearchSkill,
    OutlineSkill,
    VisualizeSkill,
    EnhanceSkill,
    ExportSkill,
)

# Services
from .services import (
    WebSearchService,
    ChartService,
)

__all__ = [
    # Version
    "__version__",
    # Core
    "Presentation",
    "Slide",
    "SlideLayoutType",
    # Agents
    "BaseAgent",
    "AgentOrchestrator",
    "ResearchAgent",
    "ContentAgent",
    "DesignAgent",
    "ImageAgent",
    "ReviewAgent",
    "AgentContext",
    # Templates
    "TemplateEngine",
    "TemplateLoader",
    "LayoutMatcher",
    "ColorPalette",
    "get_color_scheme",
    # MCP
    "MCPClient",
    "MCPManager",
    "PowerPointMCPClient",
    # Skills
    "BaseSkill",
    "SkillRegistry",
    "SkillPipeline",
    "ResearchSkill",
    "OutlineSkill",
    "VisualizeSkill",
    "EnhanceSkill",
    "ExportSkill",
    # Services
    "WebSearchService",
    "ChartService",
]
