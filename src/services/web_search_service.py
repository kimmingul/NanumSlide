"""Web Search Service for NanumSlide.

Provides web search functionality using various search APIs
to support research agents in gathering information.
"""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus

import aiohttp
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SearchResult:
    """A single search result."""
    title: str
    url: str
    snippet: str
    source: str = ""
    published_date: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResponse:
    """Response from a search query."""
    query: str
    results: List[SearchResult]
    total_results: int = 0
    search_time: float = 0.0
    source: str = ""


class BaseSearchProvider(ABC):
    """Base class for search providers."""

    @abstractmethod
    async def search(
        self,
        query: str,
        num_results: int = 10,
        **kwargs
    ) -> SearchResponse:
        """Execute a search query."""
        pass


class GoogleSearchProvider(BaseSearchProvider):
    """Google Custom Search API provider."""

    def __init__(self, api_key: str, search_engine_id: str):
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    async def search(
        self,
        query: str,
        num_results: int = 10,
        language: str = "ko",
        **kwargs
    ) -> SearchResponse:
        import time
        start_time = time.time()

        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "num": min(num_results, 10),
            "lr": f"lang_{language}",
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        logger.error(
                            "Google search failed",
                            status=response.status,
                            query=query
                        )
                        return SearchResponse(query=query, results=[], source="google")

                    data = await response.json()

                    results = []
                    for item in data.get("items", []):
                        results.append(SearchResult(
                            title=item.get("title", ""),
                            url=item.get("link", ""),
                            snippet=item.get("snippet", ""),
                            source="google",
                            metadata=item.get("pagemap", {})
                        ))

                    return SearchResponse(
                        query=query,
                        results=results,
                        total_results=int(data.get("searchInformation", {}).get("totalResults", 0)),
                        search_time=time.time() - start_time,
                        source="google"
                    )

            except Exception as e:
                logger.error("Google search error", error=str(e), query=query)
                return SearchResponse(query=query, results=[], source="google")


class BingSearchProvider(BaseSearchProvider):
    """Bing Search API provider."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.bing.microsoft.com/v7.0/search"

    async def search(
        self,
        query: str,
        num_results: int = 10,
        market: str = "ko-KR",
        **kwargs
    ) -> SearchResponse:
        import time
        start_time = time.time()

        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        params = {
            "q": query,
            "count": min(num_results, 50),
            "mkt": market,
            "responseFilter": "Webpages",
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    self.base_url,
                    headers=headers,
                    params=params
                ) as response:
                    if response.status != 200:
                        logger.error(
                            "Bing search failed",
                            status=response.status,
                            query=query
                        )
                        return SearchResponse(query=query, results=[], source="bing")

                    data = await response.json()

                    results = []
                    web_pages = data.get("webPages", {})
                    for item in web_pages.get("value", []):
                        results.append(SearchResult(
                            title=item.get("name", ""),
                            url=item.get("url", ""),
                            snippet=item.get("snippet", ""),
                            source="bing",
                            published_date=item.get("dateLastCrawled"),
                            metadata={}
                        ))

                    return SearchResponse(
                        query=query,
                        results=results,
                        total_results=web_pages.get("totalEstimatedMatches", 0),
                        search_time=time.time() - start_time,
                        source="bing"
                    )

            except Exception as e:
                logger.error("Bing search error", error=str(e), query=query)
                return SearchResponse(query=query, results=[], source="bing")


class DuckDuckGoSearchProvider(BaseSearchProvider):
    """DuckDuckGo search provider (no API key required)."""

    def __init__(self):
        self.base_url = "https://api.duckduckgo.com/"

    async def search(
        self,
        query: str,
        num_results: int = 10,
        **kwargs
    ) -> SearchResponse:
        import time
        start_time = time.time()

        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        logger.error(
                            "DuckDuckGo search failed",
                            status=response.status,
                            query=query
                        )
                        return SearchResponse(query=query, results=[], source="duckduckgo")

                    data = await response.json()

                    results = []

                    # Instant answer
                    if data.get("Abstract"):
                        results.append(SearchResult(
                            title=data.get("Heading", query),
                            url=data.get("AbstractURL", ""),
                            snippet=data.get("Abstract", ""),
                            source="duckduckgo"
                        ))

                    # Related topics
                    for topic in data.get("RelatedTopics", [])[:num_results]:
                        if isinstance(topic, dict) and "Text" in topic:
                            results.append(SearchResult(
                                title=topic.get("Text", "")[:100],
                                url=topic.get("FirstURL", ""),
                                snippet=topic.get("Text", ""),
                                source="duckduckgo"
                            ))

                    return SearchResponse(
                        query=query,
                        results=results[:num_results],
                        total_results=len(results),
                        search_time=time.time() - start_time,
                        source="duckduckgo"
                    )

            except Exception as e:
                logger.error("DuckDuckGo search error", error=str(e), query=query)
                return SearchResponse(query=query, results=[], source="duckduckgo")


class WebSearchService:
    """Main service for web searches."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._providers: Dict[str, BaseSearchProvider] = {}
        self._default_provider: Optional[str] = None
        self._setup_providers()

    def _setup_providers(self):
        """Setup available search providers based on config."""
        # Google
        if self.config.get("google_api_key") and self.config.get("google_search_engine_id"):
            self._providers["google"] = GoogleSearchProvider(
                self.config["google_api_key"],
                self.config["google_search_engine_id"]
            )
            self._default_provider = "google"

        # Bing
        if self.config.get("bing_api_key"):
            self._providers["bing"] = BingSearchProvider(self.config["bing_api_key"])
            if not self._default_provider:
                self._default_provider = "bing"

        # DuckDuckGo (always available)
        self._providers["duckduckgo"] = DuckDuckGoSearchProvider()
        if not self._default_provider:
            self._default_provider = "duckduckgo"

    async def search(
        self,
        query: str,
        provider: Optional[str] = None,
        num_results: int = 10,
        **kwargs
    ) -> SearchResponse:
        """Execute a search using the specified or default provider."""
        provider_name = provider or self._default_provider

        if provider_name not in self._providers:
            logger.warning(
                "Provider not available, using default",
                requested=provider_name,
                using=self._default_provider
            )
            provider_name = self._default_provider

        provider_instance = self._providers[provider_name]
        return await provider_instance.search(query, num_results, **kwargs)

    async def multi_search(
        self,
        query: str,
        providers: Optional[List[str]] = None,
        num_results: int = 10,
        **kwargs
    ) -> Dict[str, SearchResponse]:
        """Search across multiple providers."""
        if providers is None:
            providers = list(self._providers.keys())

        tasks = []
        valid_providers = []

        for provider in providers:
            if provider in self._providers:
                tasks.append(
                    self._providers[provider].search(query, num_results, **kwargs)
                )
                valid_providers.append(provider)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            provider: result if not isinstance(result, Exception) else SearchResponse(
                query=query, results=[], source=provider
            )
            for provider, result in zip(valid_providers, results)
        }

    def get_available_providers(self) -> List[str]:
        """Get list of available search providers."""
        return list(self._providers.keys())


# Convenience function
async def search_web(
    query: str,
    config: Optional[Dict[str, Any]] = None,
    num_results: int = 10
) -> SearchResponse:
    """Quick search function."""
    service = WebSearchService(config)
    return await service.search(query, num_results=num_results)
