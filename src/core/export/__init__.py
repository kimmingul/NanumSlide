"""프레젠테이션 내보내기 모듈 (PPTX, PDF, MCP)

이 모듈은 프레젠테이션을 다양한 형식으로 내보내는 기능을 제공합니다.

- PptxExporter: python-pptx 기반 PPTX 내보내기
- MCPExporter: MCP 기반 PowerPoint 내보내기 (고급 기능 지원)
- ExportManager: 내보내기 관리자 (MCP 우선, 자동 폴백)
"""

from .pptx_exporter import PptxExporter, export_to_pptx
from .mcp_exporter import MCPExporter, export_with_mcp
from .export_manager import (
    ExportManager,
    export_presentation,
    export_presentation_async,
)

__all__ = [
    # python-pptx 기반
    "PptxExporter",
    "export_to_pptx",
    # MCP 기반
    "MCPExporter",
    "export_with_mcp",
    # 관리자
    "ExportManager",
    "export_presentation",
    "export_presentation_async",
]
