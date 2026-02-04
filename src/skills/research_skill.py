# src/skills/research_skill.py

from typing import Dict, Any, List
import json

from .base_skill import (
    BaseSkill, SkillMetadata, SkillCategory,
    SkillParameter, SkillInput, SkillOutput
)


class ResearchSkill(BaseSkill):
    """리서치 스킬 - 주제에 대한 정보 수집"""

    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="research",
            display_name="주제 리서치",
            description="주어진 주제에 대해 웹 검색, 참고자료 분석을 수행하여 핵심 정보를 수집합니다.",
            category=SkillCategory.RESEARCH,
            command="/research",
            parameters=[
                SkillParameter(
                    name="topic",
                    type=str,
                    description="리서치할 주제",
                    required=True
                ),
                SkillParameter(
                    name="depth",
                    type=str,
                    description="리서치 깊이",
                    required=False,
                    default="normal",
                    choices=["quick", "normal", "deep"]
                ),
                SkillParameter(
                    name="language",
                    type=str,
                    description="결과 언어",
                    required=False,
                    default="ko"
                ),
                SkillParameter(
                    name="reference",
                    type=str,
                    description="참고 자료 텍스트",
                    required=False
                ),
            ],
            examples=[
                '/research "2026년 AI 트렌드"',
                '/research "기후 변화" --depth deep',
                '/research "스타트업 펀딩" --language en',
            ],
            produces=["research_context"]
        )

    async def execute(self, input: SkillInput) -> SkillOutput:
        """리서치 실행"""
        topic = input.parameters["topic"]
        depth = input.parameters.get("depth", "normal")
        language = input.parameters.get("language", "ko")
        reference = input.parameters.get("reference")

        # 리서치 깊이에 따른 검색 수 조정
        search_count = {"quick": 3, "normal": 7, "deep": 15}.get(depth, 7)

        # 프롬프트 구성
        prompt = self._build_research_prompt(topic, language, reference, depth)

        # LLM 호출
        response = await self.llm_client.generate(prompt)

        # 결과 파싱
        try:
            research_data = json.loads(response)
        except:
            research_data = self._parse_text_response(response)

        return SkillOutput(
            success=True,
            data={
                "topic": topic,
                "key_points": research_data.get("key_points", []),
                "statistics": research_data.get("statistics", []),
                "quotes": research_data.get("quotes", []),
                "trends": research_data.get("trends", []),
                "sources": research_data.get("sources", []),
                "summary": research_data.get("summary", "")
            },
            metadata={"depth": depth, "language": language}
        )

    def _build_research_prompt(
        self,
        topic: str,
        language: str,
        reference: str,
        depth: str
    ) -> str:
        """리서치 프롬프트 생성"""
        depth_instruction = {
            "quick": "핵심 포인트 3-5개만 빠르게 정리",
            "normal": "주요 정보, 통계, 트렌드를 균형있게 조사",
            "deep": "심층적인 분석, 다양한 관점, 상세한 데이터 포함"
        }.get(depth, "")

        reference_section = ""
        if reference:
            reference_section = f"""

참고 자료:
{reference[:5000]}
"""

        return f"""다음 주제에 대해 프레젠테이션용 리서치를 수행하세요.

주제: {topic}
리서치 깊이: {depth_instruction}
결과 언어: {language}{reference_section}

다음 정보를 수집하세요:
1. 핵심 포인트 (key_points): 주제의 핵심 내용
2. 통계/수치 (statistics): 관련 데이터
3. 인용구 (quotes): 인용할 만한 문구
4. 트렌드 (trends): 최신 동향
5. 요약 (summary): 전체 요약

JSON 형식으로 응답하세요."""

    def _parse_text_response(self, text: str) -> Dict:
        """텍스트 응답 파싱"""
        return {
            "key_points": [],
            "statistics": [],
            "quotes": [],
            "trends": [],
            "summary": text[:500]
        }
