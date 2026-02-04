"""Agent Progress Dialog for NanumSlide."""

from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QWidget,
    QFrame,
    QScrollArea,
    QTextEdit,
    QGroupBox,
    QSplitter,
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor, QPalette


class AgentStatus(Enum):
    """Status of an agent."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    WAITING = "waiting"


@dataclass
class AgentState:
    """State of a single agent."""
    agent_id: str
    name: str
    name_ko: str
    status: AgentStatus = AgentStatus.IDLE
    progress: float = 0.0
    current_task: str = ""
    messages: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class AgentCard(QFrame):
    """Card widget showing status of a single agent."""

    def __init__(
        self,
        agent_state: AgentState,
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.agent_state = agent_state
        self._setup_ui()

    def _setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel)
        self.setFixedHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Header row
        header_layout = QHBoxLayout()

        # Status indicator
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(12, 12)
        header_layout.addWidget(self.status_indicator)

        # Agent name
        self.name_label = QLabel(self.agent_state.name_ko)
        self.name_label.setFont(QFont("Pretendard", 11, QFont.Bold))
        header_layout.addWidget(self.name_label)

        header_layout.addStretch()

        # Status text
        self.status_label = QLabel()
        self.status_label.setFont(QFont("Pretendard", 9))
        header_layout.addWidget(self.status_label)

        layout.addLayout(header_layout)

        # Current task
        self.task_label = QLabel()
        self.task_label.setStyleSheet("color: #666;")
        self.task_label.setFont(QFont("Pretendard", 9))
        self.task_label.setWordWrap(True)
        layout.addWidget(self.task_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #e0e0e0;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #2196f3;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        self.update_display()

    def update_state(self, state: AgentState):
        self.agent_state = state
        self.update_display()

    def update_display(self):
        status = self.agent_state.status

        # Update status indicator color
        colors = {
            AgentStatus.IDLE: "#9e9e9e",
            AgentStatus.RUNNING: "#2196f3",
            AgentStatus.COMPLETED: "#4caf50",
            AgentStatus.ERROR: "#f44336",
            AgentStatus.WAITING: "#ff9800",
        }
        color = colors.get(status, "#9e9e9e")
        self.status_indicator.setStyleSheet(
            f"background-color: {color}; border-radius: 6px;"
        )

        # Update status text
        status_texts = {
            AgentStatus.IDLE: "대기 중",
            AgentStatus.RUNNING: "실행 중",
            AgentStatus.COMPLETED: "완료",
            AgentStatus.ERROR: "오류",
            AgentStatus.WAITING: "대기",
        }
        self.status_label.setText(status_texts.get(status, ""))
        self.status_label.setStyleSheet(f"color: {color};")

        # Update task label
        if self.agent_state.current_task:
            self.task_label.setText(self.agent_state.current_task)
        else:
            self.task_label.setText("")

        # Update progress bar
        self.progress_bar.setValue(int(self.agent_state.progress * 100))

        # Update card style based on status
        if status == AgentStatus.RUNNING:
            self.setStyleSheet("AgentCard { background-color: #e3f2fd; border-radius: 8px; }")
        elif status == AgentStatus.COMPLETED:
            self.setStyleSheet("AgentCard { background-color: #e8f5e9; border-radius: 8px; }")
        elif status == AgentStatus.ERROR:
            self.setStyleSheet("AgentCard { background-color: #ffebee; border-radius: 8px; }")
        else:
            self.setStyleSheet("AgentCard { background-color: #fafafa; border-radius: 8px; }")


class AgentProgressDialog(QDialog):
    """Dialog showing progress of multi-agent presentation generation."""

    cancelled = Signal()

    def __init__(
        self,
        title: str = "프레젠테이션 생성 중",
        parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.agent_cards: Dict[str, AgentCard] = {}
        self._setup_ui(title)

    def _setup_ui(self, title: str):
        self.setWindowTitle(title)
        self.setMinimumSize(600, 500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Header
        header_label = QLabel(title)
        header_label.setFont(QFont("Pretendard", 14, QFont.Bold))
        layout.addWidget(header_label)

        # Overall progress
        overall_group = QGroupBox("전체 진행률")
        overall_layout = QVBoxLayout(overall_group)

        self.overall_progress = QProgressBar()
        self.overall_progress.setFixedHeight(20)
        self.overall_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #e0e0e0;
                border-radius: 10px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4caf50;
                border-radius: 10px;
            }
        """)
        overall_layout.addWidget(self.overall_progress)

        self.overall_status_label = QLabel("초기화 중...")
        self.overall_status_label.setAlignment(Qt.AlignCenter)
        overall_layout.addWidget(self.overall_status_label)

        layout.addWidget(overall_group)

        # Splitter for agents and logs
        splitter = QSplitter(Qt.Vertical)

        # Agent cards container
        agents_widget = QWidget()
        agents_layout = QVBoxLayout(agents_widget)
        agents_layout.setContentsMargins(0, 0, 0, 0)

        agents_label = QLabel("에이전트 상태")
        agents_label.setFont(QFont("Pretendard", 11, QFont.Bold))
        agents_layout.addWidget(agents_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.agents_container = QWidget()
        self.agents_layout = QVBoxLayout(self.agents_container)
        self.agents_layout.setSpacing(8)
        self.agents_layout.addStretch()

        scroll_area.setWidget(self.agents_container)
        agents_layout.addWidget(scroll_area)

        splitter.addWidget(agents_widget)

        # Log output
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)

        log_label = QLabel("로그")
        log_label.setFont(QFont("Pretendard", 11, QFont.Bold))
        log_layout.addWidget(log_label)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Consolas", 9))
        self.log_output.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        log_layout.addWidget(self.log_output)

        splitter.addWidget(log_widget)
        splitter.setSizes([300, 150])

        layout.addWidget(splitter, 1)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("취소")
        self.cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(self.cancel_btn)

        self.close_btn = QPushButton("닫기")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setEnabled(False)
        self.close_btn.setStyleSheet(
            "QPushButton { background-color: #2196f3; color: white; padding: 8px 24px; }"
        )
        button_layout.addWidget(self.close_btn)

        layout.addLayout(button_layout)

    def add_agent(self, state: AgentState):
        """Add a new agent to track."""
        card = AgentCard(state)
        self.agent_cards[state.agent_id] = card

        # Insert before the stretch
        count = self.agents_layout.count()
        self.agents_layout.insertWidget(count - 1, card)

    def update_agent(self, agent_id: str, state: AgentState):
        """Update an agent's state."""
        if agent_id in self.agent_cards:
            self.agent_cards[agent_id].update_state(state)

    def set_agent_status(
        self,
        agent_id: str,
        status: AgentStatus,
        progress: float = 0.0,
        current_task: str = ""
    ):
        """Convenience method to update agent status."""
        if agent_id in self.agent_cards:
            card = self.agent_cards[agent_id]
            card.agent_state.status = status
            card.agent_state.progress = progress
            card.agent_state.current_task = current_task
            card.update_display()

    def set_overall_progress(self, progress: float, status_text: str = ""):
        """Update overall progress."""
        self.overall_progress.setValue(int(progress * 100))
        if status_text:
            self.overall_status_label.setText(status_text)

    def add_log(self, message: str, level: str = "info"):
        """Add a log message."""
        timestamp = datetime.now().strftime("%H:%M:%S")

        colors = {
            "info": "#d4d4d4",
            "success": "#4caf50",
            "warning": "#ff9800",
            "error": "#f44336",
        }
        color = colors.get(level, "#d4d4d4")

        html = f'<span style="color: #888;">[{timestamp}]</span> <span style="color: {color};">{message}</span>'
        self.log_output.append(html)

        # Auto-scroll to bottom
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def set_completed(self, success: bool = True):
        """Mark the generation as completed."""
        self.cancel_btn.setEnabled(False)
        self.close_btn.setEnabled(True)

        if success:
            self.overall_progress.setValue(100)
            self.overall_status_label.setText("프레젠테이션 생성 완료!")
            self.overall_progress.setStyleSheet("""
                QProgressBar {
                    border: none;
                    background-color: #e0e0e0;
                    border-radius: 10px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #4caf50;
                    border-radius: 10px;
                }
            """)
        else:
            self.overall_status_label.setText("생성 중 오류가 발생했습니다.")
            self.overall_progress.setStyleSheet("""
                QProgressBar {
                    border: none;
                    background-color: #e0e0e0;
                    border-radius: 10px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #f44336;
                    border-radius: 10px;
                }
            """)

    def _on_cancel(self):
        self.cancelled.emit()
        self.reject()


# Factory function to create dialog with default agents
def create_generation_progress_dialog(
    parent: Optional[QWidget] = None
) -> AgentProgressDialog:
    """Create a progress dialog with the default multi-agent setup."""
    dialog = AgentProgressDialog("프레젠테이션 생성 중", parent)

    # Add default agents
    agents = [
        AgentState("research", "Research Agent", "리서치 에이전트"),
        AgentState("content", "Content Agent", "콘텐츠 에이전트"),
        AgentState("design", "Design Agent", "디자인 에이전트"),
        AgentState("image", "Image Agent", "이미지 에이전트"),
        AgentState("review", "Review Agent", "리뷰 에이전트"),
    ]

    for agent in agents:
        dialog.add_agent(agent)

    return dialog
