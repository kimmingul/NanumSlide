# src/agents/agent_config.py
"""에이전트 설정 정의"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class AgentConfig:
    """에이전트 설정"""

    # Research Agent
    research_enabled: bool = True
    max_search_results: int = 10
    search_timeout_seconds: int = 30

    # Content Agent
    content_max_retries: int = 3
    content_temperature: float = 0.7

    # Design Agent
    design_auto_layout: bool = True
    design_variety_threshold: int = 3  # 연속 동일 레이아웃 제한

    # Image Agent
    image_enabled: bool = True
    image_parallel_limit: int = 5
    image_fallback_enabled: bool = True

    # Review Agent
    review_enabled: bool = True
    review_auto_fix: bool = True
    review_pass_threshold: float = 0.7

    @classmethod
    def from_dict(cls, config: Dict) -> "AgentConfig":
        """딕셔너리에서 설정 생성"""
        return cls(**{k: v for k, v in config.items() if hasattr(cls, k)})
