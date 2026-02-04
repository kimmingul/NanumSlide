# src/agents/agent_context.py
"""에이전트 간 공유 컨텍스트 정의"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime
from enum import Enum

if TYPE_CHECKING:
    from .base_agent import AgentMessage


class ContextStatus(Enum):
    """컨텍스트 상태"""
    INITIALIZING = "initializing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class UserInput:
    """사용자 입력"""
    topic: str
    slide_count: int = 10
    language: str = "ko"
    theme: str = "default"
    template_id: Optional[str] = None
    reference_content: Optional[str] = None

    # 고급 옵션
    audience: Optional[str] = None          # "전문가", "일반인", "학생"
    purpose: Optional[str] = None           # "설득", "교육", "보고"
    duration_minutes: Optional[int] = None  # 예상 발표 시간
    style: Optional[str] = None             # "formal", "casual", "creative"
    include_charts: bool = True
    include_images: bool = True


@dataclass
class ResearchContext:
    """리서치 에이전트 출력"""
    key_points: List[str] = field(default_factory=list)
    statistics: List[Dict[str, Any]] = field(default_factory=list)
    quotes: List[Dict[str, str]] = field(default_factory=list)
    sources: List[Dict[str, str]] = field(default_factory=list)
    trends: List[str] = field(default_factory=list)
    related_topics: List[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class SlideContent:
    """개별 슬라이드 콘텐츠"""
    index: int
    title: str
    content: str = ""
    bullet_points: List[str] = field(default_factory=list)
    notes: str = ""
    transition_text: str = ""  # 이전 슬라이드에서 전환 문구
    key_message: str = ""      # 핵심 메시지


@dataclass
class ContentContext:
    """콘텐츠 에이전트 출력"""
    title: str
    subtitle: str = ""
    slides: List[SlideContent] = field(default_factory=list)
    overall_narrative: str = ""  # 전체 스토리라인
    key_takeaways: List[str] = field(default_factory=list)


@dataclass
class SlideDesign:
    """개별 슬라이드 디자인"""
    index: int
    layout_type: str          # "title", "two_column", "image_left" 등
    color_emphasis: str = ""  # 강조 색상
    visualization_type: Optional[str] = None  # "chart", "diagram", "timeline"
    image_position: Optional[str] = None      # "left", "right", "background"
    animation_suggestion: Optional[str] = None


@dataclass
class DesignContext:
    """디자인 에이전트 출력"""
    template_id: str
    color_scheme: str
    font_pairing: Dict[str, str] = field(default_factory=dict)
    slides: List[SlideDesign] = field(default_factory=list)
    master_slide_suggestions: List[str] = field(default_factory=list)


@dataclass
class SlideMedia:
    """개별 슬라이드 미디어"""
    index: int
    images: List[Dict[str, Any]] = field(default_factory=list)
    icons: List[Dict[str, Any]] = field(default_factory=list)
    charts: List[Dict[str, Any]] = field(default_factory=list)
    diagrams: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MediaContext:
    """이미지 에이전트 출력"""
    slides: List[SlideMedia] = field(default_factory=list)
    image_style: str = ""  # "photo", "illustration", "icon"
    color_filter: Optional[str] = None


@dataclass
class ReviewIssue:
    """리뷰 이슈"""
    slide_index: Optional[int]
    issue_type: str     # "consistency", "quality", "accessibility", "style"
    severity: str       # "critical", "warning", "suggestion"
    description: str
    suggestion: str


@dataclass
class ReviewResult:
    """리뷰 에이전트 출력"""
    passed: bool
    overall_score: float  # 0.0 ~ 1.0
    issues: List[ReviewIssue] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)


@dataclass
class AgentContext:
    """에이전트 간 공유 컨텍스트"""

    # 사용자 입력
    user_input: UserInput

    # 각 에이전트 출력 (순차적으로 채워짐)
    research: Optional[ResearchContext] = None
    content: Optional[ContentContext] = None
    design: Optional[DesignContext] = None
    media: Optional[MediaContext] = None
    review: Optional[ReviewResult] = None

    # 메타데이터
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: ContextStatus = ContextStatus.INITIALIZING

    # 에이전트 메시지 로그
    messages: List["AgentMessage"] = field(default_factory=list)

    # 진행 상태
    current_phase: str = ""
    progress_percent: float = 0.0

    def update(self) -> None:
        """업데이트 시간 갱신"""
        self.updated_at = datetime.now()

    def set_phase(self, phase: str, progress: float) -> None:
        """현재 단계 설정"""
        self.current_phase = phase
        self.progress_percent = progress
        self.update()
