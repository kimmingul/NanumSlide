# src/skills/skill_pipeline.py

from typing import List, Dict, Any, Optional, Callable, TYPE_CHECKING
from dataclasses import dataclass, field

from .base_skill import BaseSkill, SkillInput, SkillOutput, SkillContext
from .skill_registry import SkillRegistry

if TYPE_CHECKING:
    from ..services.llm_client import BaseLLMClient


@dataclass
class PipelineStep:
    """파이프라인 단계"""
    skill_name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    condition: Optional[str] = None  # 실행 조건


@dataclass
class PipelineResult:
    """파이프라인 실행 결과"""
    success: bool
    steps_completed: int
    total_steps: int
    outputs: Dict[str, SkillOutput]
    error: Optional[str] = None


class SkillPipeline:
    """스킬 파이프라인"""

    def __init__(self, llm_client: Optional["BaseLLMClient"] = None):
        self.llm_client = llm_client
        self.steps: List[PipelineStep] = []
        self._context = SkillContext()

    def add_step(
        self,
        skill_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        condition: Optional[str] = None
    ) -> "SkillPipeline":
        """단계 추가"""
        self.steps.append(PipelineStep(
            skill_name=skill_name,
            parameters=parameters or {},
            condition=condition
        ))
        return self

    def set_context(self, context: SkillContext) -> "SkillPipeline":
        """컨텍스트 설정"""
        self._context = context
        return self

    async def execute(
        self,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> PipelineResult:
        """파이프라인 실행"""
        outputs: Dict[str, SkillOutput] = {}
        steps_completed = 0

        for i, step in enumerate(self.steps):
            # 진행 상태 콜백
            if progress_callback:
                progress = (i / len(self.steps)) * 100
                progress_callback(progress, f"실행 중: {step.skill_name}")

            # 조건 확인
            if step.condition and not self._evaluate_condition(step.condition):
                continue

            # 스킬 인스턴스 가져오기
            skill = SkillRegistry.get_instance(step.skill_name, self.llm_client)
            if not skill:
                return PipelineResult(
                    success=False,
                    steps_completed=steps_completed,
                    total_steps=len(self.steps),
                    outputs=outputs,
                    error=f"스킬을 찾을 수 없음: {step.skill_name}"
                )

            # 입력 준비
            skill_input = SkillInput(
                parameters=step.parameters,
                context=self._context
            )

            # 스킬 실행
            try:
                output = await skill.run(skill_input)
            except Exception as e:
                return PipelineResult(
                    success=False,
                    steps_completed=steps_completed,
                    total_steps=len(self.steps),
                    outputs=outputs,
                    error=f"스킬 실행 오류 ({step.skill_name}): {str(e)}"
                )

            # 결과 저장
            outputs[step.skill_name] = output
            self._context.previous_outputs[step.skill_name] = output

            if not output.success:
                return PipelineResult(
                    success=False,
                    steps_completed=steps_completed,
                    total_steps=len(self.steps),
                    outputs=outputs,
                    error=output.error
                )

            steps_completed += 1

        # 완료 콜백
        if progress_callback:
            progress_callback(100, "완료")

        return PipelineResult(
            success=True,
            steps_completed=steps_completed,
            total_steps=len(self.steps),
            outputs=outputs
        )

    def _evaluate_condition(self, condition: str) -> bool:
        """조건 평가"""
        # 간단한 조건 평가
        # 예: "research.success" -> research 스킬이 성공했는지 확인
        try:
            parts = condition.split(".")
            if len(parts) == 2:
                skill_name, attr = parts
                output = self._context.previous_outputs.get(skill_name)
                if output:
                    return getattr(output, attr, False)
            return False
        except:
            return True

    @classmethod
    def create_default_pipeline(
        cls,
        topic: str,
        slide_count: int = 10,
        llm_client: Optional["BaseLLMClient"] = None
    ) -> "SkillPipeline":
        """기본 파이프라인 생성"""
        pipeline = cls(llm_client=llm_client)

        pipeline.add_step("research", {"topic": topic})
        pipeline.add_step("outline", {"topic": topic, "slide_count": slide_count})
        pipeline.add_step("enhance", {"target": "all"})
        pipeline.add_step("export", {"format": "pptx"})

        return pipeline

    def get_context(self) -> SkillContext:
        """현재 컨텍스트 반환"""
        return self._context

    def reset(self) -> "SkillPipeline":
        """파이프라인 상태 초기화"""
        self.steps.clear()
        self._context = SkillContext()
        return self


# 사용 예시
async def example_pipeline_usage():
    """파이프라인 사용 예시"""
    from ..services.llm_client import create_llm_client

    llm_client = create_llm_client()

    # 기본 파이프라인 생성
    pipeline = SkillPipeline.create_default_pipeline(
        topic="2026년 AI 트렌드",
        slide_count=12,
        llm_client=llm_client
    )

    # 진행 상태 콜백
    def on_progress(progress: float, message: str):
        print(f"[{progress:.0f}%] {message}")

    # 실행
    result = await pipeline.execute(progress_callback=on_progress)

    if result.success:
        print(f"파이프라인 완료: {result.steps_completed}/{result.total_steps} 단계")
        export_output = result.outputs.get('export')
        if export_output and export_output.data:
            print(f"  출력 파일: {export_output.data.get('output_path', 'N/A')}")
    else:
        print(f"파이프라인 실패: {result.error}")
