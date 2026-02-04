"""웹 검색 MCP 클라이언트 모듈

MCP를 통해 웹 검색 서비스를 사용하는 클라이언트입니다.
Brave Search 등의 검색 엔진을 통해 웹 검색, 콘텐츠 가져오기, 요약 기능을 제공합니다.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass

from .mcp_client import MCPClient


@dataclass
class SearchResult:
    """검색 결과

    웹 검색 결과를 나타내는 데이터 클래스입니다.

    Attributes:
        title: 검색 결과 제목
        url: 검색 결과 URL
        snippet: 검색 결과 요약/스니펫
        source: 소스 (예: "web", "news", "image")
    """
    title: str
    url: str
    snippet: str
    source: str

    def to_dict(self) -> Dict[str, str]:
        """딕셔너리로 변환"""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "SearchResult":
        """딕셔너리에서 생성"""
        return cls(
            title=data.get("title", ""),
            url=data.get("url", ""),
            snippet=data.get("description", data.get("snippet", "")),
            source=data.get("source", "web")
        )


class WebSearchMCPClient:
    """웹 검색 MCP 클라이언트

    MCP를 통해 웹 검색 기능을 제공하는 클라이언트입니다.
    검색, 콘텐츠 가져오기, 텍스트 요약 기능을 제공합니다.

    Attributes:
        mcp: 기본 MCP 클라이언트
    """

    def __init__(self, mcp_client: MCPClient):
        """WebSearchMCPClient 초기화

        Args:
            mcp_client: MCP 클라이언트 인스턴스
        """
        self.mcp = mcp_client

    async def search(
        self,
        query: str,
        max_results: int = 10,
        language: str = "ko"
    ) -> List[SearchResult]:
        """웹 검색 수행

        주어진 쿼리로 웹 검색을 수행합니다.

        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수 (기본값: 10)
            language: 검색 언어 (기본값: "ko")

        Returns:
            SearchResult 객체 리스트
        """
        result = await self.mcp.call_tool(
            "web-search",
            "search",
            {
                "query": query,
                "count": max_results,
                "language": language
            }
        )

        results = []
        for item in result.get("results", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("description", ""),
                source=item.get("source", "web")
            ))

        return results

    async def search_news(
        self,
        query: str,
        max_results: int = 10,
        language: str = "ko",
        freshness: str = "week"
    ) -> List[SearchResult]:
        """뉴스 검색 수행

        주어진 쿼리로 뉴스 검색을 수행합니다.

        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수 (기본값: 10)
            language: 검색 언어 (기본값: "ko")
            freshness: 검색 기간 ("day", "week", "month")

        Returns:
            SearchResult 객체 리스트
        """
        result = await self.mcp.call_tool(
            "web-search",
            "search_news",
            {
                "query": query,
                "count": max_results,
                "language": language,
                "freshness": freshness
            }
        )

        results = []
        for item in result.get("results", []):
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("description", ""),
                source="news"
            ))

        return results

    async def search_images(
        self,
        query: str,
        max_results: int = 10,
        size: Optional[str] = None,
        aspect_ratio: Optional[str] = None
    ) -> List[Dict]:
        """이미지 검색 수행

        주어진 쿼리로 이미지 검색을 수행합니다.

        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수 (기본값: 10)
            size: 이미지 크기 ("small", "medium", "large")
            aspect_ratio: 화면 비율 ("square", "wide", "tall")

        Returns:
            이미지 정보 딕셔너리 리스트
        """
        params = {
            "query": query,
            "count": max_results
        }

        if size:
            params["size"] = size
        if aspect_ratio:
            params["aspect_ratio"] = aspect_ratio

        result = await self.mcp.call_tool(
            "web-search",
            "search_images",
            params
        )

        return result.get("images", [])

    async def fetch_content(
        self,
        url: str,
        extract_text: bool = True
    ) -> Dict:
        """URL 콘텐츠 가져오기

        지정된 URL의 콘텐츠를 가져옵니다.

        Args:
            url: 가져올 URL
            extract_text: 텍스트만 추출할지 여부 (기본값: True)

        Returns:
            콘텐츠 정보 딕셔너리
        """
        return await self.mcp.call_tool(
            "web-search",
            "fetch",
            {
                "url": url,
                "extract_text": extract_text
            }
        )

    async def summarize(
        self,
        text: str,
        max_length: int = 500,
        language: str = "ko"
    ) -> str:
        """텍스트 요약

        긴 텍스트를 요약합니다.

        Args:
            text: 요약할 텍스트
            max_length: 최대 요약 길이 (기본값: 500)
            language: 출력 언어 (기본값: "ko")

        Returns:
            요약된 텍스트
        """
        result = await self.mcp.call_tool(
            "web-search",
            "summarize",
            {
                "text": text,
                "max_length": max_length,
                "language": language
            }
        )
        return result.get("summary", "")

    async def extract_key_points(
        self,
        text: str,
        max_points: int = 5,
        language: str = "ko"
    ) -> List[str]:
        """핵심 포인트 추출

        텍스트에서 핵심 포인트를 추출합니다.

        Args:
            text: 분석할 텍스트
            max_points: 최대 포인트 수 (기본값: 5)
            language: 출력 언어 (기본값: "ko")

        Returns:
            핵심 포인트 리스트
        """
        result = await self.mcp.call_tool(
            "web-search",
            "extract_key_points",
            {
                "text": text,
                "max_points": max_points,
                "language": language
            }
        )
        return result.get("key_points", [])

    async def get_related_topics(
        self,
        query: str,
        max_topics: int = 10
    ) -> List[str]:
        """관련 주제 가져오기

        주어진 쿼리와 관련된 주제들을 가져옵니다.

        Args:
            query: 검색 쿼리
            max_topics: 최대 주제 수 (기본값: 10)

        Returns:
            관련 주제 리스트
        """
        result = await self.mcp.call_tool(
            "web-search",
            "related_topics",
            {
                "query": query,
                "count": max_topics
            }
        )
        return result.get("topics", [])
