"""외부 서비스 연동 모듈 (LLM, 이미지 등)"""

from .llm_client import BaseLLMClient, OpenAIClient, AnthropicClient, OllamaClient
from .image_service import search_image, fetch_images_for_slides
from .web_search_service import WebSearchService, SearchResult, SearchResponse, search_web
from .chart_service import ChartService, ChartType, ChartData, ChartDataSeries, generate_chart

__all__ = [
    # LLM clients
    "BaseLLMClient",
    "OpenAIClient",
    "AnthropicClient",
    "OllamaClient",
    # Image service
    "search_image",
    "fetch_images_for_slides",
    # Web search
    "WebSearchService",
    "SearchResult",
    "SearchResponse",
    "search_web",
    # Chart service
    "ChartService",
    "ChartType",
    "ChartData",
    "ChartDataSeries",
    "generate_chart",
]
