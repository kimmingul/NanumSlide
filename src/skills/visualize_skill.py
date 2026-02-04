# src/skills/visualize_skill.py

from typing import Dict, Any, List, Optional
import json

from .base_skill import (
    BaseSkill, SkillMetadata, SkillCategory,
    SkillParameter, SkillInput, SkillOutput
)


class VisualizeSkill(BaseSkill):
    """시각화 스킬 - 데이터 시각화 및 차트 생성"""

    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            name="visualize",
            display_name="데이터 시각화",
            description="데이터를 차트, 다이어그램, 인포그래픽으로 시각화합니다.",
            category=SkillCategory.DESIGN,
            command="/visualize",
            parameters=[
                SkillParameter(
                    name="data",
                    type=str,
                    description="시각화할 데이터 (텍스트 또는 JSON)",
                    required=True
                ),
                SkillParameter(
                    name="type",
                    type=str,
                    description="시각화 유형",
                    required=False,
                    default="auto",
                    choices=["auto", "bar", "line", "pie", "timeline", "process", "comparison"]
                ),
                SkillParameter(
                    name="title",
                    type=str,
                    description="차트 제목",
                    required=False
                ),
                SkillParameter(
                    name="style",
                    type=str,
                    description="시각화 스타일",
                    required=False,
                    default="clean",
                    choices=["clean", "colorful", "minimal", "bold"]
                ),
            ],
            examples=[
                '/visualize "매출: 100, 120, 150, 180" --type bar',
                '/visualize "A: 40%, B: 30%, C: 20%, D: 10%" --type pie',
            ],
            produces=["chart_data", "visualization"]
        )

    async def execute(self, input: SkillInput) -> SkillOutput:
        """시각화 실행"""
        data = input.parameters["data"]
        viz_type = input.parameters.get("type", "auto")
        title = input.parameters.get("title", "")
        style = input.parameters.get("style", "clean")

        # 데이터 파싱
        parsed_data = self._parse_data(data)

        # 시각화 유형 자동 결정
        if viz_type == "auto":
            viz_type = self._determine_visualization_type(parsed_data)

        # 시각화 데이터 생성
        chart_data = self._generate_chart_data(parsed_data, viz_type, title, style)

        return SkillOutput(
            success=True,
            data={
                "chart_type": viz_type,
                "chart_data": chart_data,
                "style": style,
                "recommended_size": self._get_recommended_size(viz_type)
            },
            metadata={"visualization_type": viz_type}
        )

    def _parse_data(self, data: str) -> Dict:
        """데이터 파싱"""
        # JSON 형식 시도
        try:
            return json.loads(data)
        except:
            pass

        # 간단한 키:값 형식 파싱
        parsed = {"labels": [], "values": []}

        # "A: 40%, B: 30%" 형식
        if ":" in data:
            pairs = data.split(",")
            for pair in pairs:
                if ":" in pair:
                    parts = pair.strip().split(":")
                    label = parts[0].strip()
                    value_str = parts[1].strip().replace("%", "")
                    try:
                        value = float(value_str)
                        parsed["labels"].append(label)
                        parsed["values"].append(value)
                    except:
                        pass

        # 숫자만 있는 경우
        elif any(c.isdigit() for c in data):
            numbers = []
            for part in data.replace(",", " ").split():
                try:
                    numbers.append(float(part))
                except:
                    pass

            if numbers:
                parsed["labels"] = [f"항목 {i+1}" for i in range(len(numbers))]
                parsed["values"] = numbers

        return parsed

    def _determine_visualization_type(self, data: Dict) -> str:
        """시각화 유형 자동 결정"""
        values = data.get("values", [])

        if not values:
            return "bar"

        # 비율 데이터 (합이 100에 가까움)
        total = sum(values)
        if 95 <= total <= 105:
            return "pie"

        # 시계열 데이터 (증가/감소 추세)
        if len(values) >= 4:
            diffs = [values[i+1] - values[i] for i in range(len(values)-1)]
            if all(d >= 0 for d in diffs) or all(d <= 0 for d in diffs):
                return "line"

        # 기본값
        return "bar"

    def _generate_chart_data(
        self,
        data: Dict,
        viz_type: str,
        title: str,
        style: str
    ) -> Dict:
        """차트 데이터 생성"""
        colors = self._get_color_palette(style)

        if viz_type == "pie":
            return {
                "type": "pie",
                "title": title,
                "data": {
                    "labels": data.get("labels", []),
                    "datasets": [{
                        "data": data.get("values", []),
                        "backgroundColor": colors[:len(data.get("values", []))]
                    }]
                }
            }

        elif viz_type == "line":
            return {
                "type": "line",
                "title": title,
                "data": {
                    "labels": data.get("labels", []),
                    "datasets": [{
                        "label": title or "데이터",
                        "data": data.get("values", []),
                        "borderColor": colors[0],
                        "fill": False
                    }]
                }
            }

        else:  # bar (기본)
            return {
                "type": "bar",
                "title": title,
                "data": {
                    "labels": data.get("labels", []),
                    "datasets": [{
                        "label": title or "데이터",
                        "data": data.get("values", []),
                        "backgroundColor": colors[:len(data.get("values", []))]
                    }]
                }
            }

    def _get_color_palette(self, style: str) -> List[str]:
        """스타일별 색상 팔레트"""
        palettes = {
            "clean": ["#3182ce", "#48bb78", "#ed8936", "#9f7aea", "#f56565"],
            "colorful": ["#e53e3e", "#38a169", "#3182ce", "#d69e2e", "#805ad5"],
            "minimal": ["#4a5568", "#718096", "#a0aec0", "#cbd5e0", "#e2e8f0"],
            "bold": ["#1a365d", "#2c7a7b", "#744210", "#553c9a", "#9b2c2c"]
        }
        return palettes.get(style, palettes["clean"])

    def _get_recommended_size(self, viz_type: str) -> Dict:
        """권장 크기 반환"""
        sizes = {
            "pie": {"width": 500, "height": 500},
            "bar": {"width": 700, "height": 400},
            "line": {"width": 800, "height": 400},
            "timeline": {"width": 900, "height": 300},
            "process": {"width": 800, "height": 200},
        }
        return sizes.get(viz_type, {"width": 600, "height": 400})
