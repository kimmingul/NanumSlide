# src/skills/__init__.py
"""
NanumSlide Skill System

스킬 시스템은 프레젠테이션 생성 과정을 모듈화하여 재사용 가능한 단위로 분리합니다.
사용자는 슬래시 명령어(/research, /outline 등)로 특정 스킬을 호출하거나,
여러 스킬을 조합하여 커스텀 파이프라인을 구성할 수 있습니다.
"""

from .base_skill import (
    SkillCategory,
    SkillParameter,
    SkillMetadata,
    SkillInput,
    SkillOutput,
    SkillContext,
    BaseSkill,
)

from .skill_registry import (
    SkillRegistry,
    register_default_skills,
)

from .skill_pipeline import (
    PipelineStep,
    PipelineResult,
    SkillPipeline,
)

from .research_skill import ResearchSkill
from .outline_skill import OutlineSkill
from .visualize_skill import VisualizeSkill
from .enhance_skill import EnhanceSkill
from .export_skill import ExportSkill

__all__ = [
    # Base classes
    "SkillCategory",
    "SkillParameter",
    "SkillMetadata",
    "SkillInput",
    "SkillOutput",
    "SkillContext",
    "BaseSkill",
    # Registry
    "SkillRegistry",
    "register_default_skills",
    # Pipeline
    "PipelineStep",
    "PipelineResult",
    "SkillPipeline",
    # Skills
    "ResearchSkill",
    "OutlineSkill",
    "VisualizeSkill",
    "EnhanceSkill",
    "ExportSkill",
]
