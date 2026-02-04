"""MCP (Model Context Protocol) 모듈

NanumSlide의 MCP 통합을 위한 클라이언트 및 유틸리티를 제공합니다.
MCP를 통해 PowerPoint, 웹 검색, 이미지 생성 등의 외부 서비스와 연동합니다.

주요 클래스:
- MCPClient: 기본 MCP 클라이언트
- MCPManager: MCP 서버 연결 관리자
- PowerPointMCPClient: PowerPoint MCP 클라이언트
- WebSearchMCPClient: 웹 검색 MCP 클라이언트
"""

# 기본 MCP 클라이언트
from .mcp_client import (
    MCPClient,
    MCPServerConfig,
    MCPToolInfo,
    MCPError,
)

# MCP 매니저
from .mcp_manager import MCPManager

# PowerPoint MCP 클라이언트
from .powerpoint_mcp import (
    PowerPointMCPClient,
    SlideLayout,
    ChartType,
    SmartArtType,
    AnimationType,
    TransitionType,
    Position,
    Size,
)

# 웹 검색 MCP 클라이언트
from .web_search_mcp import (
    WebSearchMCPClient,
    SearchResult,
)

__all__ = [
    # 기본 클라이언트
    "MCPClient",
    "MCPServerConfig",
    "MCPToolInfo",
    "MCPError",
    # 매니저
    "MCPManager",
    # PowerPoint
    "PowerPointMCPClient",
    "SlideLayout",
    "ChartType",
    "SmartArtType",
    "AnimationType",
    "TransitionType",
    "Position",
    "Size",
    # 웹 검색
    "WebSearchMCPClient",
    "SearchResult",
]
