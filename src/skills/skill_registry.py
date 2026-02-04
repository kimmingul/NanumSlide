# src/skills/skill_registry.py

from typing import Dict, List, Optional, Type, TYPE_CHECKING

from .base_skill import BaseSkill, SkillMetadata

if TYPE_CHECKING:
    from ..services.llm_client import BaseLLMClient


class SkillRegistry:
    """스킬 레지스트리"""

    _skills: Dict[str, Type[BaseSkill]] = {}
    _instances: Dict[str, BaseSkill] = {}

    @classmethod
    def register(cls, skill_class: Type[BaseSkill]) -> None:
        """스킬 등록"""
        # 임시 인스턴스로 메타데이터 조회
        temp_instance = skill_class()
        name = temp_instance.metadata.name
        cls._skills[name] = skill_class

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseSkill]]:
        """스킬 클래스 조회"""
        return cls._skills.get(name)

    @classmethod
    def get_instance(
        cls,
        name: str,
        llm_client: Optional["BaseLLMClient"] = None
    ) -> Optional[BaseSkill]:
        """스킬 인스턴스 조회/생성"""
        if name not in cls._instances:
            skill_class = cls._skills.get(name)
            if skill_class:
                cls._instances[name] = skill_class(llm_client=llm_client)

        return cls._instances.get(name)

    @classmethod
    def list_skills(cls) -> List[SkillMetadata]:
        """등록된 스킬 목록"""
        skills = []
        for skill_class in cls._skills.values():
            temp = skill_class()
            skills.append(temp.metadata)
        return skills

    @classmethod
    def get_by_command(cls, command: str) -> Optional[Type[BaseSkill]]:
        """명령어로 스킬 조회"""
        for skill_class in cls._skills.values():
            temp = skill_class()
            if temp.metadata.command == command:
                return skill_class
        return None

    @classmethod
    def search(cls, query: str) -> List[SkillMetadata]:
        """스킬 검색"""
        query_lower = query.lower()
        results = []

        for skill_class in cls._skills.values():
            temp = skill_class()
            meta = temp.metadata

            if (query_lower in meta.name.lower() or
                query_lower in meta.display_name.lower() or
                query_lower in meta.description.lower()):
                results.append(meta)

        return results

    @classmethod
    def clear(cls) -> None:
        """레지스트리 초기화 (테스트용)"""
        cls._skills.clear()
        cls._instances.clear()

    @classmethod
    def clear_instances(cls) -> None:
        """인스턴스 캐시 초기화"""
        cls._instances.clear()


def register_default_skills() -> None:
    """기본 스킬 등록"""
    from .research_skill import ResearchSkill
    from .outline_skill import OutlineSkill
    from .visualize_skill import VisualizeSkill
    from .enhance_skill import EnhanceSkill
    from .export_skill import ExportSkill

    SkillRegistry.register(ResearchSkill)
    SkillRegistry.register(OutlineSkill)
    SkillRegistry.register(VisualizeSkill)
    SkillRegistry.register(EnhanceSkill)
    SkillRegistry.register(ExportSkill)


# 모듈 로드 시 기본 스킬 자동 등록
register_default_skills()
