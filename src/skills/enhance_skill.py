# src/skills/enhance_skill.py

from typing import Dict, Any, List, Optional
import json

from .base_skill import (
    BaseSkill, SkillMetadata, SkillCategory,
    SkillParameter, SkillInput, SkillOutput
)


class EnhanceSkill(BaseSkill):
    """개선 스킬 - 프레젠테이션 품질 향상"""

    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="enhance",
            display_name="품질 개선",
            description="프레젠테이션의 콘텐츠, 디자인, 전달력을 개선합니다.",
            category=SkillCategory.ENHANCEMENT,
            command="/enhance",
            parameters=[
                SkillParameter(
                    name="target",
                    type=str,
                    description="개선 대상",
                    required=False,
                    default="all",
                    choices=["all", "content", "design", "flow", "language"]
                ),
                SkillParameter(
                    name="slide_index",
                    type=int,
                    description="특정 슬라이드 인덱스 (전체는 -1)",
                    required=False,
                    default=-1
                ),
                SkillParameter(
                    name="intensity",
                    type=str,
                    description="개선 강도",
                    required=False,
                    default="normal",
                    choices=["light", "normal", "aggressive"]
                ),
            ],
            examples=[
                '/enhance --target content',
                '/enhance --slide_index 3 --target language',
                '/enhance --intensity aggressive',
            ],
            requires=["outline"],
            produces=["enhanced_content"]
        )

    async def execute(self, input: SkillInput) -> SkillOutput:
        """개선 실행"""
        target = input.parameters.get("target", "all")
        slide_index = input.parameters.get("slide_index", -1)
        intensity = input.parameters.get("intensity", "normal")

        # 현재 프레젠테이션 상태 가져오기
        presentation = None
        if input.context:
            presentation = input.context.presentation

        if not presentation:
            # 이전 개요에서 생성
            outline_output = input.context.get_previous_output("outline") if input.context else None
            if outline_output and outline_output.success:
                presentation = self._create_presentation_from_outline(outline_output.data)

        if not presentation:
            return SkillOutput(
                success=False,
                data=None,
                error="개선할 프레젠테이션이 없습니다"
            )

        # 개선 수행
        if target == "all":
            improvements = await self._enhance_all(presentation, intensity)
        elif target == "content":
            improvements = await self._enhance_content(presentation, slide_index, intensity)
        elif target == "design":
            improvements = await self._enhance_design(presentation, slide_index, intensity)
        elif target == "flow":
            improvements = await self._enhance_flow(presentation, intensity)
        elif target == "language":
            improvements = await self._enhance_language(presentation, slide_index, intensity)
        else:
            improvements = []

        return SkillOutput(
            success=True,
            data={
                "improvements": improvements,
                "enhanced_presentation": presentation,
                "improvement_count": len(improvements)
            },
            metadata={"target": target, "intensity": intensity}
        )

    async def _enhance_all(
        self,
        presentation: Any,
        intensity: str
    ) -> List[Dict]:
        """전체 개선"""
        all_improvements = []

        # 콘텐츠 개선
        content_improvements = await self._enhance_content(presentation, -1, intensity)
        all_improvements.extend(content_improvements)

        # 흐름 개선
        flow_improvements = await self._enhance_flow(presentation, intensity)
        all_improvements.extend(flow_improvements)

        # 언어 개선
        language_improvements = await self._enhance_language(presentation, -1, intensity)
        all_improvements.extend(language_improvements)

        return all_improvements

    async def _enhance_content(
        self,
        presentation: Any,
        slide_index: int,
        intensity: str
    ) -> List[Dict]:
        """콘텐츠 개선"""
        improvements = []

        prompt = f"""다음 프레젠테이션 콘텐츠를 개선하세요.

개선 강도: {intensity}
개선 방향:
- 명확성: 모호한 표현 제거
- 간결성: 불필요한 내용 삭제
- 임팩트: 핵심 메시지 강화

현재 콘텐츠:
{json.dumps(self._extract_content(presentation), ensure_ascii=False)}

JSON 형식으로 개선 사항을 응답하세요:
[{{"slide_index": 0, "type": "content", "original": "...", "improved": "...", "reason": "..."}}]"""

        response = await self.llm_client.generate(prompt)

        try:
            improvements = json.loads(response)
            # 개선 사항 적용
            self._apply_improvements(presentation, improvements)
        except:
            pass

        return improvements

    async def _enhance_flow(
        self,
        presentation: Any,
        intensity: str
    ) -> List[Dict]:
        """흐름 개선"""
        prompt = f"""프레젠테이션의 논리적 흐름을 분석하고 개선하세요.

개선 강도: {intensity}
분석 항목:
- 슬라이드 순서의 논리성
- 전환의 자연스러움
- 스토리텔링 구조

현재 구조:
{json.dumps(self._extract_structure(presentation), ensure_ascii=False)}

JSON 형식으로 응답하세요:
[{{"type": "flow", "issue": "...", "suggestion": "...", "priority": "high|medium|low"}}]"""

        response = await self.llm_client.generate(prompt)

        try:
            return json.loads(response)
        except:
            return []

    async def _enhance_language(
        self,
        presentation: Any,
        slide_index: int,
        intensity: str
    ) -> List[Dict]:
        """언어 개선"""
        prompt = f"""프레젠테이션의 언어와 표현을 개선하세요.

개선 강도: {intensity}
개선 항목:
- 문법 오류 수정
- 전문적인 표현으로 변경
- 청중에게 적합한 톤

현재 텍스트:
{json.dumps(self._extract_text(presentation), ensure_ascii=False)}

JSON 형식으로 응답하세요:
[{{"slide_index": 0, "type": "language", "original": "...", "improved": "...", "reason": "..."}}]"""

        response = await self.llm_client.generate(prompt)

        try:
            improvements = json.loads(response)
            self._apply_improvements(presentation, improvements)
            return improvements
        except:
            return []

    async def _enhance_design(
        self,
        presentation: Any,
        slide_index: int,
        intensity: str
    ) -> List[Dict]:
        """디자인 개선 제안"""
        return [
            {
                "type": "design",
                "suggestion": "시각적 다양성을 위해 레이아웃 변경 권장",
                "slides": []
            }
        ]

    def _extract_content(self, presentation: Any) -> List[Dict]:
        """콘텐츠 추출"""
        # 프레젠테이션에서 콘텐츠 추출
        if isinstance(presentation, dict):
            slides = presentation.get("slides", [])
            return [
                {
                    "index": i,
                    "title": slide.get("title", ""),
                    "content": slide.get("description", "") or slide.get("content", "")
                }
                for i, slide in enumerate(slides)
            ]
        return []

    def _extract_structure(self, presentation: Any) -> List[Dict]:
        """구조 추출"""
        if isinstance(presentation, dict):
            slides = presentation.get("slides", [])
            return [
                {
                    "index": i,
                    "title": slide.get("title", ""),
                    "type": slide.get("type", "content")
                }
                for i, slide in enumerate(slides)
            ]
        return []

    def _extract_text(self, presentation: Any) -> List[Dict]:
        """텍스트 추출"""
        if isinstance(presentation, dict):
            slides = presentation.get("slides", [])
            return [
                {
                    "index": i,
                    "texts": [
                        slide.get("title", ""),
                        slide.get("description", ""),
                        slide.get("key_message", "")
                    ]
                }
                for i, slide in enumerate(slides)
            ]
        return []

    def _apply_improvements(self, presentation: Any, improvements: List[Dict]) -> None:
        """개선 사항 적용"""
        if not isinstance(presentation, dict):
            return

        slides = presentation.get("slides", [])
        for improvement in improvements:
            idx = improvement.get("slide_index", -1)
            if 0 <= idx < len(slides):
                improved_text = improvement.get("improved", "")
                improvement_type = improvement.get("type", "content")

                if improvement_type == "content":
                    slides[idx]["description"] = improved_text
                elif improvement_type == "language":
                    # 언어 개선은 해당 텍스트 필드에 적용
                    original = improvement.get("original", "")
                    for key in ["title", "description", "key_message"]:
                        if slides[idx].get(key) == original:
                            slides[idx][key] = improved_text
                            break

    def _create_presentation_from_outline(self, outline_data: Dict) -> Any:
        """개요에서 프레젠테이션 생성"""
        return outline_data
