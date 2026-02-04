# src/skills/base_skill.py

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ..services.llm_client import BaseLLMClient
    from ..core.presentation import Presentation


class SkillCategory(Enum):
    """스킬 카테고리"""
    RESEARCH = "research"       # 리서치/정보 수집
    CONTENT = "content"         # 콘텐츠 생성
    DESIGN = "design"           # 디자인/시각화
    ENHANCEMENT = "enhancement" # 개선/최적화
    EXPORT = "export"           # 내보내기
    UTILITY = "utility"         # 유틸리티


@dataclass
class SkillParameter:
    """스킬 파라미터 정의"""
    name: str
    type: Type
    description: str
    required: bool = True
    default: Any = None
    choices: Optional[List[Any]] = None


@dataclass
class SkillMetadata:
    """스킬 메타데이터"""
    name: str                              # 스킬 이름 (예: "research")
    display_name: str                      # 표시 이름 (예: "주제 리서치")
    description: str                       # 설명
    category: SkillCategory                # 카테고리
    command: str                           # 명령어 (예: "/research")
    parameters: List[SkillParameter]       # 파라미터 목록
    examples: List[str] = field(default_factory=list)  # 사용 예시
    requires: List[str] = field(default_factory=list)  # 필요한 다른 스킬
    produces: List[str] = field(default_factory=list)  # 생성하는 출력 타입


@dataclass
class SkillInput:
    """스킬 입력"""
    parameters: Dict[str, Any]
    context: Optional["SkillContext"] = None


@dataclass
class SkillOutput:
    """스킬 출력"""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SkillContext:
    """스킬 실행 컨텍스트"""
    # 이전 스킬 출력
    previous_outputs: Dict[str, SkillOutput] = field(default_factory=dict)

    # 공유 데이터
    shared_data: Dict[str, Any] = field(default_factory=dict)

    # 현재 프레젠테이션 상태
    presentation: Optional["Presentation"] = None

    # 설정
    language: str = "ko"
    theme: str = "default"

    def get_previous_output(self, skill_name: str) -> Optional[SkillOutput]:
        """이전 스킬 출력 조회"""
        return self.previous_outputs.get(skill_name)

    def set_shared_data(self, key: str, value: Any) -> None:
        """공유 데이터 설정"""
        self.shared_data[key] = value

    def get_shared_data(self, key: str, default: Any = None) -> Any:
        """공유 데이터 조회"""
        return self.shared_data.get(key, default)


class BaseSkill(ABC):
    """스킬 기본 클래스"""

    def __init__(
        self,
        llm_client: Optional["BaseLLMClient"] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.llm_client = llm_client
        self.config = config or {}

    @property
    @abstractmethod
    def metadata(self) -> SkillMetadata:
        """스킬 메타데이터 반환"""
        pass

    @abstractmethod
    async def execute(self, input: SkillInput) -> SkillOutput:
        """스킬 실행"""
        pass

    def validate_input(self, input: SkillInput) -> Optional[str]:
        """입력 유효성 검사"""
        for param in self.metadata.parameters:
            if param.required and param.name not in input.parameters:
                return f"필수 파라미터 누락: {param.name}"

            if param.name in input.parameters:
                value = input.parameters[param.name]

                # 타입 검사
                if not isinstance(value, param.type):
                    return f"파라미터 타입 오류: {param.name}은(는) {param.type.__name__}이어야 합니다"

                # 선택지 검사
                if param.choices and value not in param.choices:
                    return f"파라미터 값 오류: {param.name}은(는) {param.choices} 중 하나여야 합니다"

        return None

    async def run(self, input: SkillInput) -> SkillOutput:
        """스킬 실행 (유효성 검사 포함)"""
        # 입력 유효성 검사
        error = self.validate_input(input)
        if error:
            return SkillOutput(success=False, data=None, error=error)

        # 기본값 적용
        for param in self.metadata.parameters:
            if param.name not in input.parameters and param.default is not None:
                input.parameters[param.name] = param.default

        # 실행
        try:
            return await self.execute(input)
        except Exception as e:
            return SkillOutput(success=False, data=None, error=str(e))

    def get_help(self) -> str:
        """도움말 반환"""
        meta = self.metadata

        help_text = f"""
## {meta.command} - {meta.display_name}

{meta.description}

### 파라미터
"""
        for param in meta.parameters:
            required = "(필수)" if param.required else "(선택)"
            default = f" [기본값: {param.default}]" if param.default else ""
            help_text += f"- **{param.name}** {required}: {param.description}{default}\n"

        if meta.examples:
            help_text += "\n### 사용 예시\n"
            for example in meta.examples:
                help_text += f"```\n{example}\n```\n"

        return help_text
