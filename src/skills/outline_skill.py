# src/skills/outline_skill.py

from typing import Dict, Any, List, Optional
import json

from .base_skill import (
    BaseSkill, SkillMetadata, SkillCategory,
    SkillParameter, SkillInput, SkillOutput
)


class OutlineSkill(BaseSkill):
    """개요 스킬 - 프레젠테이션 구조 생성"""

    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="outline",
            display_name="개요 생성",
            description="주제와 리서치 결과를 바탕으로 프레젠테이션 개요를 생성합니다.",
            category=SkillCategory.CONTENT,
            command="/outline",
            parameters=[
                SkillParameter(
                    name="topic",
                    type=str,
                    description="프레젠테이션 주제",
                    required=True
                ),
                SkillParameter(
                    name="slide_count",
                    type=int,
                    description="슬라이드 수",
                    required=False,
                    default=10
                ),
                SkillParameter(
                    name="purpose",
                    type=str,
                    description="발표 목적",
                    required=False,
                    default="inform",
                    choices=["inform", "persuade", "educate", "inspire"]
                ),
                SkillParameter(
                    name="audience",
                    type=str,
                    description="대상 청중",
                    required=False
                ),
                SkillParameter(
                    name="template",
                    type=str,
                    description="템플릿 ID",
                    required=False
                ),
            ],
            examples=[
                '/outline "AI 트렌드" --slide_count 12',
                '/outline "투자 제안" --purpose persuade --template pitch_deck',
            ],
            requires=["research"],
            produces=["outline"]
        )

    async def execute(self, input: SkillInput) -> SkillOutput:
        """개요 생성 실행"""
        topic = input.parameters["topic"]
        slide_count = input.parameters.get("slide_count", 10)
        purpose = input.parameters.get("purpose", "inform")
        audience = input.parameters.get("audience")
        template = input.parameters.get("template")

        # 이전 리서치 결과 가져오기
        research_data = None
        if input.context:
            research_output = input.context.get_previous_output("research")
            if research_output and research_output.success:
                research_data = research_output.data

        # 템플릿 구조 가져오기
        template_structure = None
        if template:
            template_structure = self._get_template_structure(template)

        # 프롬프트 구성
        prompt = self._build_outline_prompt(
            topic, slide_count, purpose, audience,
            research_data, template_structure
        )

        # LLM 호출
        response = await self.llm_client.generate(prompt)

        # 결과 파싱
        try:
            outline_data = json.loads(response)
        except:
            outline_data = self._parse_text_outline(response, slide_count)

        return SkillOutput(
            success=True,
            data={
                "title": outline_data.get("title", topic),
                "subtitle": outline_data.get("subtitle", ""),
                "slides": outline_data.get("slides", []),
                "narrative": outline_data.get("narrative", ""),
                "key_takeaways": outline_data.get("takeaways", [])
            },
            metadata={"slide_count": len(outline_data.get("slides", []))}
        )

    def _build_outline_prompt(
        self,
        topic: str,
        slide_count: int,
        purpose: str,
        audience: Optional[str],
        research_data: Optional[Dict],
        template_structure: Optional[List]
    ) -> str:
        """개요 프롬프트 생성"""
        purpose_instruction = {
            "inform": "정보를 명확하게 전달",
            "persuade": "청중을 설득하고 행동 유도",
            "educate": "교육적이고 이해하기 쉽게",
            "inspire": "영감을 주고 동기 부여"
        }.get(purpose, "")

        research_section = ""
        if research_data:
            research_section = f"""

리서치 결과:
- 핵심 포인트: {', '.join(research_data.get('key_points', [])[:5])}
- 주요 트렌드: {', '.join(research_data.get('trends', [])[:3])}
- 요약: {research_data.get('summary', '')[:300]}
"""

        template_section = ""
        if template_structure:
            template_section = f"""

권장 슬라이드 구조:
{json.dumps(template_structure, ensure_ascii=False, indent=2)}
"""

        return f"""프레젠테이션 개요를 생성하세요.

주제: {topic}
슬라이드 수: {slide_count}장
발표 목적: {purpose_instruction}
대상 청중: {audience or '일반'}{research_section}{template_section}

다음 형식으로 JSON 응답하세요:
{{
    "title": "프레젠테이션 제목",
    "subtitle": "부제목",
    "slides": [
        {{
            "index": 0,
            "title": "슬라이드 제목",
            "type": "title|content|bullets|chart|quote|conclusion",
            "description": "슬라이드 내용 설명",
            "key_message": "핵심 메시지"
        }}
    ],
    "narrative": "전체 스토리라인",
    "takeaways": ["핵심 takeaway 1", "핵심 takeaway 2"]
}}"""

    def _get_template_structure(self, template_id: str) -> Optional[List]:
        """템플릿 구조 조회"""
        # 템플릿 로더에서 구조 가져오기
        # 실제 구현에서는 TemplateLoader 사용
        template_structures = {
            "pitch_deck": [
                {"type": "title", "name": "표지"},
                {"type": "problem", "name": "문제 정의"},
                {"type": "solution", "name": "해결책"},
                {"type": "market", "name": "시장 규모"},
                {"type": "business_model", "name": "비즈니스 모델"},
                {"type": "team", "name": "팀 소개"},
                {"type": "ask", "name": "투자 요청"}
            ],
            "quarterly_report": [
                {"type": "title", "name": "표지"},
                {"type": "highlights", "name": "주요 성과"},
                {"type": "metrics", "name": "핵심 지표"},
                {"type": "analysis", "name": "분석"},
                {"type": "challenges", "name": "도전 과제"},
                {"type": "next_steps", "name": "다음 단계"}
            ]
        }
        return template_structures.get(template_id)

    def _parse_text_outline(self, text: str, slide_count: int) -> Dict:
        """텍스트 개요 파싱"""
        slides = []
        lines = text.strip().split('\n')

        for i, line in enumerate(lines[:slide_count]):
            if line.strip():
                slides.append({
                    "index": i,
                    "title": line.strip(),
                    "type": "title" if i == 0 else "content",
                    "description": "",
                    "key_message": ""
                })

        return {
            "title": slides[0]["title"] if slides else "Untitled",
            "slides": slides
        }
