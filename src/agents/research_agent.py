# src/agents/research_agent.py
"""리서치 에이전트 - 주제 조사 및 정보 수집"""

from typing import Dict, List, Optional, Any, TYPE_CHECKING
import json
import time

from .base_agent import BaseAgent, AgentResult, AgentStatus
from .agent_context import AgentContext, ResearchContext

if TYPE_CHECKING:
    from src.services.llm_client import BaseLLMClient


class ResearchAgent(BaseAgent):
    """리서치 에이전트 - 주제 조사 및 정보 수집"""

    def __init__(
        self,
        llm_client: "BaseLLMClient",
        web_search_service: Optional[Any] = None,
        config: Optional[Dict] = None
    ):
        super().__init__(
            name="research_agent",
            llm_client=llm_client,
            config=config
        )
        self.web_search_service = web_search_service

    def get_system_prompt(self) -> str:
        return """당신은 프레젠테이션 리서치 전문가입니다.
주어진 주제에 대해 깊이 있는 조사를 수행하고, 프레젠테이션에 활용할 수 있는
핵심 정보, 통계, 인용구, 트렌드를 추출합니다.

다음을 수행합니다:
1. 주제의 핵심 포인트 파악
2. 관련 통계 및 데이터 수집
3. 인용할 만한 전문가 의견 또는 명언 찾기
4. 최신 트렌드 및 동향 파악
5. 청중에게 유용한 인사이트 도출

결과는 구조화된 형태로 제공합니다."""

    async def run(self, context: AgentContext) -> AgentResult:
        """리서치 실행"""
        start_time = time.time()

        try:
            self.update_status(AgentStatus.RUNNING)

            user_input = context.user_input
            research_context = ResearchContext()

            # 1. 웹 검색 수행 (서비스가 있는 경우)
            if self.web_search_service:
                search_results = await self._perform_web_search(
                    user_input.topic,
                    user_input.language
                )
                research_context.sources = search_results

            # 2. 참고 자료 분석 (있는 경우)
            if user_input.reference_content:
                reference_insights = await self._analyze_reference(
                    user_input.reference_content,
                    user_input.topic
                )
                research_context.key_points.extend(
                    reference_insights.get("key_points", [])
                )

            # 3. LLM을 통한 종합 리서치
            research_prompt = self._build_research_prompt(user_input)
            research_response = await self.call_llm(
                prompt=research_prompt,
                json_schema=self._get_research_schema()
            )

            # 응답 파싱
            research_data = json.loads(research_response)
            research_context.key_points.extend(research_data.get("key_points", []))
            research_context.statistics = research_data.get("statistics", [])
            research_context.quotes = research_data.get("quotes", [])
            research_context.trends = research_data.get("trends", [])
            research_context.related_topics = research_data.get("related_topics", [])
            research_context.summary = research_data.get("summary", "")

            self.update_status(AgentStatus.COMPLETED)

            return AgentResult(
                success=True,
                data=research_context,
                duration_ms=int((time.time() - start_time) * 1000)
            )

        except Exception as e:
            self.update_status(AgentStatus.FAILED)
            return AgentResult(
                success=False,
                data=None,
                error=str(e)
            )

    async def _perform_web_search(
        self,
        topic: str,
        language: str
    ) -> List[Dict[str, str]]:
        """웹 검색 수행"""
        if not self.web_search_service:
            return []

        # 검색 쿼리 생성
        queries = [
            topic,
            f"{topic} 통계",
            f"{topic} 트렌드 2026",
        ]

        results = []
        for query in queries:
            try:
                search_results = await self.web_search_service.search(query)
                results.extend(search_results[:3])  # 쿼리당 상위 3개
            except Exception:
                pass  # 검색 실패 시 무시

        return results

    async def _analyze_reference(
        self,
        reference_content: str,
        topic: str
    ) -> Dict[str, Any]:
        """참고 자료 분석"""
        prompt = f"""다음 참고 자료를 분석하여 "{topic}" 주제의 프레젠테이션에
활용할 수 있는 핵심 포인트를 추출하세요.

참고 자료:
{reference_content[:8000]}

JSON 형식으로 응답하세요:
{{
    "key_points": ["핵심 포인트 1", "핵심 포인트 2", ...],
    "useful_quotes": ["인용문 1", ...],
    "data_points": ["데이터 포인트 1", ...]
}}"""

        response = await self.call_llm(prompt)

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"key_points": [], "useful_quotes": [], "data_points": []}

    def _build_research_prompt(self, user_input: "UserInput") -> str:
        """리서치 프롬프트 생성"""
        from .agent_context import UserInput

        audience_context = ""
        if user_input.audience:
            audience_context = f"\n대상 청중: {user_input.audience}"

        purpose_context = ""
        if user_input.purpose:
            purpose_context = f"\n발표 목적: {user_input.purpose}"

        return f"""다음 주제에 대해 프레젠테이션 리서치를 수행하세요.

주제: {user_input.topic}
언어: {user_input.language}
슬라이드 수: {user_input.slide_count}장{audience_context}{purpose_context}

다음 정보를 수집하세요:
1. 핵심 포인트 (5-7개)
2. 관련 통계/수치 (가능한 경우)
3. 인용할 만한 명언/전문가 의견
4. 최신 트렌드
5. 관련 주제

JSON 형식으로 응답하세요."""

    def _get_research_schema(self) -> Dict:
        """리서치 응답 스키마"""
        return {
            "type": "object",
            "properties": {
                "key_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "주제의 핵심 포인트 목록"
                },
                "statistics": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "value": {"type": "string"},
                            "description": {"type": "string"},
                            "source": {"type": "string"}
                        }
                    }
                },
                "quotes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "author": {"type": "string"}
                        }
                    }
                },
                "trends": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "related_topics": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "summary": {
                    "type": "string",
                    "description": "주제에 대한 간략한 요약"
                }
            },
            "required": ["key_points", "summary"]
        }
