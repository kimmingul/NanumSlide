# src/agents/__init__.py
"""Multi-Agent System for NanumSlide"""

from .base_agent import (
    BaseAgent,
    AgentStatus,
    AgentResult,
    AgentMessage,
)

from .agent_context import (
    AgentContext,
    ContextStatus,
    UserInput,
    ResearchContext,
    SlideContent,
    ContentContext,
    SlideDesign,
    DesignContext,
    SlideMedia,
    MediaContext,
    ReviewIssue,
    ReviewResult,
)

from .agent_config import AgentConfig

from .research_agent import ResearchAgent
from .content_agent import ContentAgent
from .design_agent import DesignAgent
from .image_agent import ImageAgent
from .review_agent import ReviewAgent

from .orchestrator import AgentOrchestrator, ExecutionPhase

__all__ = [
    # Base classes
    "BaseAgent",
    "AgentStatus",
    "AgentResult",
    "AgentMessage",

    # Context classes
    "AgentContext",
    "ContextStatus",
    "UserInput",
    "ResearchContext",
    "SlideContent",
    "ContentContext",
    "SlideDesign",
    "DesignContext",
    "SlideMedia",
    "MediaContext",
    "ReviewIssue",
    "ReviewResult",

    # Config
    "AgentConfig",

    # Agents
    "ResearchAgent",
    "ContentAgent",
    "DesignAgent",
    "ImageAgent",
    "ReviewAgent",

    # Orchestrator
    "AgentOrchestrator",
    "ExecutionPhase",
]
