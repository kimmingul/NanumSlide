"""설정 다이얼로그"""

import os
import json
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QCheckBox,
    QApplication,
    QFrame,
    QScrollArea,
    QSlider,
    QSpinBox,
    QGridLayout,
    QListWidget,
    QListWidgetItem,
    QSplitter,
    QTextEdit,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont

from src.config import LLMProvider, ImageProvider
from src.services.llm_client import fetch_openai_models, fetch_anthropic_models
from src.mcp.mcp_config import get_mcp_config_manager, MCPConfigManager


class ApiValidationWorker(QThread):
    """API 키 검증 워커 스레드"""
    finished = Signal(bool, str, list)  # (성공여부, 메시지, 모델목록)

    def __init__(self, provider: str, api_key: str):
        super().__init__()
        self.provider = provider
        self.api_key = api_key

    def run(self):
        if self.provider == "openai":
            success, message, models = fetch_openai_models(self.api_key)
            self.finished.emit(success, message, models)
        elif self.provider == "anthropic":
            success, message, models = fetch_anthropic_models(self.api_key)
            self.finished.emit(success, message, models)
        else:
            self.finished.emit(False, "지원하지 않는 프로바이더", [])


class SettingsDialog(QDialog):
    """설정 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("설정")
        self.setMinimumSize(500, 600)
        self.resize(600, 700)

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)

        # 탭 위젯
        tab_widget = QTabWidget()

        # AI 설정 탭
        ai_tab = self._create_ai_tab()
        tab_widget.addTab(ai_tab, "AI 설정")

        # 에이전트 설정 탭
        agent_tab = self._create_agent_tab()
        tab_widget.addTab(agent_tab, "에이전트")

        # 템플릿 설정 탭
        template_tab = self._create_template_tab()
        tab_widget.addTab(template_tab, "템플릿")

        # MCP 설정 탭
        mcp_tab = self._create_mcp_tab()
        tab_widget.addTab(mcp_tab, "MCP 연결")

        # 이미지 설정 탭
        image_tab = self._create_image_tab()
        tab_widget.addTab(image_tab, "이미지")

        # 일반 설정 탭
        general_tab = self._create_general_tab()
        tab_widget.addTab(general_tab, "일반")

        layout.addWidget(tab_widget)

        # 버튼
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def _create_ai_tab(self) -> QWidget:
        """AI 설정 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # LLM 프로바이더 선택
        provider_group = QGroupBox("LLM 프로바이더")
        provider_layout = QFormLayout(provider_group)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["OpenAI", "Google", "Anthropic", "Ollama"])
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_layout.addRow("프로바이더:", self.provider_combo)

        layout.addWidget(provider_group)

        # OpenAI 설정
        self.openai_group = QGroupBox("OpenAI 설정")
        openai_layout = QVBoxLayout(self.openai_group)

        # API 키 입력 행
        openai_key_layout = QHBoxLayout()
        openai_key_layout.addWidget(QLabel("API 키:"))
        self.openai_api_key = QLineEdit()
        self.openai_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_api_key.setPlaceholderText("sk-...")
        openai_key_layout.addWidget(self.openai_api_key)
        self.openai_validate_btn = QPushButton("검증")
        self.openai_validate_btn.setFixedWidth(60)
        self.openai_validate_btn.clicked.connect(self._validate_openai_key)
        openai_key_layout.addWidget(self.openai_validate_btn)
        openai_layout.addLayout(openai_key_layout)

        # 검증 상태 레이블
        self.openai_status_label = QLabel("")
        self.openai_status_label.setWordWrap(True)
        openai_layout.addWidget(self.openai_status_label)

        # 모델 선택
        openai_model_layout = QHBoxLayout()
        openai_model_layout.addWidget(QLabel("모델:"))
        self.openai_model = QComboBox()
        self.openai_model.setEditable(True)
        self.openai_model.setMinimumWidth(250)
        openai_model_layout.addWidget(self.openai_model)
        openai_model_layout.addStretch()
        openai_layout.addLayout(openai_model_layout)

        layout.addWidget(self.openai_group)

        # Google 설정
        self.google_group = QGroupBox("Google Gemini 설정")
        google_layout = QFormLayout(self.google_group)

        self.google_api_key = QLineEdit()
        self.google_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        google_layout.addRow("API 키:", self.google_api_key)

        self.google_model = QComboBox()
        self.google_model.addItems(["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"])
        self.google_model.setEditable(True)
        google_layout.addRow("모델:", self.google_model)

        self.google_group.hide()
        layout.addWidget(self.google_group)

        # Anthropic 설정
        self.anthropic_group = QGroupBox("Anthropic Claude 설정")
        anthropic_layout = QVBoxLayout(self.anthropic_group)

        # API 키 입력 행
        anthropic_key_layout = QHBoxLayout()
        anthropic_key_layout.addWidget(QLabel("API 키:"))
        self.anthropic_api_key = QLineEdit()
        self.anthropic_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.anthropic_api_key.setPlaceholderText("sk-ant-...")
        anthropic_key_layout.addWidget(self.anthropic_api_key)
        self.anthropic_validate_btn = QPushButton("검증")
        self.anthropic_validate_btn.setFixedWidth(60)
        self.anthropic_validate_btn.clicked.connect(self._validate_anthropic_key)
        anthropic_key_layout.addWidget(self.anthropic_validate_btn)
        anthropic_layout.addLayout(anthropic_key_layout)

        # 검증 상태 레이블
        self.anthropic_status_label = QLabel("")
        self.anthropic_status_label.setWordWrap(True)
        anthropic_layout.addWidget(self.anthropic_status_label)

        # 모델 선택
        anthropic_model_layout = QHBoxLayout()
        anthropic_model_layout.addWidget(QLabel("모델:"))
        self.anthropic_model = QComboBox()
        self.anthropic_model.setEditable(True)
        self.anthropic_model.setMinimumWidth(250)
        anthropic_model_layout.addWidget(self.anthropic_model)
        anthropic_model_layout.addStretch()
        anthropic_layout.addLayout(anthropic_model_layout)

        self.anthropic_group.hide()
        layout.addWidget(self.anthropic_group)

        # Ollama 설정
        self.ollama_group = QGroupBox("Ollama 설정 (로컬 AI)")
        ollama_layout = QFormLayout(self.ollama_group)

        self.ollama_url = QLineEdit()
        self.ollama_url.setPlaceholderText("http://localhost:11434")
        ollama_layout.addRow("서버 URL:", self.ollama_url)

        self.ollama_model = QComboBox()
        self.ollama_model.addItems(["llama3.2", "llama3.1", "mistral", "gemma2"])
        self.ollama_model.setEditable(True)
        ollama_layout.addRow("모델:", self.ollama_model)

        self.ollama_group.hide()
        layout.addWidget(self.ollama_group)

        layout.addStretch()

        # 검증 워커 참조 초기화
        self.validation_worker = None

        return widget

    def _validate_openai_key(self):
        """OpenAI API 키 검증"""
        api_key = self.openai_api_key.text().strip()
        if not api_key:
            self.openai_status_label.setText("API 키를 입력하세요.")
            self.openai_status_label.setStyleSheet("color: orange;")
            return

        self.openai_validate_btn.setEnabled(False)
        self.openai_status_label.setText("검증 중...")
        self.openai_status_label.setStyleSheet("color: gray;")
        QApplication.processEvents()

        self.validation_worker = ApiValidationWorker("openai", api_key)
        self.validation_worker.finished.connect(self._on_openai_validation_done)
        self.validation_worker.start()

    def _on_openai_validation_done(self, success: bool, message: str, models: list):
        """OpenAI 검증 완료 처리"""
        self.openai_validate_btn.setEnabled(True)
        self.openai_status_label.setText(message)

        if success:
            self.openai_status_label.setStyleSheet("color: green;")
            # 모델 목록 업데이트 (최신순)
            current_model = self.openai_model.currentText()
            self.openai_model.clear()
            self.openai_model.addItems(models)
            # 기존 선택 복원 또는 첫 번째 모델 선택
            if current_model in models:
                self.openai_model.setCurrentText(current_model)
            elif models:
                self.openai_model.setCurrentIndex(0)
        else:
            self.openai_status_label.setStyleSheet("color: red;")

    def _validate_anthropic_key(self):
        """Anthropic API 키 검증"""
        api_key = self.anthropic_api_key.text().strip()
        if not api_key:
            self.anthropic_status_label.setText("API 키를 입력하세요.")
            self.anthropic_status_label.setStyleSheet("color: orange;")
            return

        self.anthropic_validate_btn.setEnabled(False)
        self.anthropic_status_label.setText("검증 중...")
        self.anthropic_status_label.setStyleSheet("color: gray;")
        QApplication.processEvents()

        self.validation_worker = ApiValidationWorker("anthropic", api_key)
        self.validation_worker.finished.connect(self._on_anthropic_validation_done)
        self.validation_worker.start()

    def _on_anthropic_validation_done(self, success: bool, message: str, models: list):
        """Anthropic 검증 완료 처리"""
        self.anthropic_validate_btn.setEnabled(True)
        self.anthropic_status_label.setText(message)

        if success:
            self.anthropic_status_label.setStyleSheet("color: green;")
            # 모델 목록 업데이트 (최신순)
            current_model = self.anthropic_model.currentText()
            self.anthropic_model.clear()
            self.anthropic_model.addItems(models)
            # 기존 선택 복원 또는 첫 번째 모델 선택
            if current_model in models:
                self.anthropic_model.setCurrentText(current_model)
            elif models:
                self.anthropic_model.setCurrentIndex(0)
        else:
            self.anthropic_status_label.setStyleSheet("color: red;")

    def _create_image_tab(self) -> QWidget:
        """이미지 설정 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 이미지 프로바이더 선택
        provider_group = QGroupBox("이미지 프로바이더")
        provider_layout = QFormLayout(provider_group)

        self.image_provider_combo = QComboBox()
        self.image_provider_combo.addItems(["DALL-E (OpenAI)", "Pexels", "Pixabay", "비활성화"])
        provider_layout.addRow("프로바이더:", self.image_provider_combo)

        # DALL-E 설명
        dalle_info = QLabel("DALL-E는 OpenAI API 키를 사용합니다. AI 설정 탭에서 OpenAI API 키를 설정하세요.")
        dalle_info.setStyleSheet("color: gray; font-size: 11px;")
        dalle_info.setWordWrap(True)
        provider_layout.addRow("", dalle_info)

        layout.addWidget(provider_group)

        # Pexels 설정
        pexels_group = QGroupBox("Pexels 설정")
        pexels_layout = QFormLayout(pexels_group)

        self.pexels_api_key = QLineEdit()
        self.pexels_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        pexels_layout.addRow("API 키:", self.pexels_api_key)

        layout.addWidget(pexels_group)

        # Pixabay 설정
        pixabay_group = QGroupBox("Pixabay 설정")
        pixabay_layout = QFormLayout(pixabay_group)

        self.pixabay_api_key = QLineEdit()
        self.pixabay_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        pixabay_layout.addRow("API 키:", self.pixabay_api_key)

        layout.addWidget(pixabay_group)

        layout.addStretch()

        return widget

    def _create_general_tab(self) -> QWidget:
        """일반 설정 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 언어 설정
        lang_group = QGroupBox("언어")
        lang_layout = QFormLayout(lang_group)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["한국어", "English", "日本語", "中文"])
        lang_layout.addRow("기본 언어:", self.language_combo)

        layout.addWidget(lang_group)

        # 기본 설정
        default_group = QGroupBox("기본값")
        default_layout = QFormLayout(default_group)

        self.default_slide_count = QComboBox()
        self.default_slide_count.addItems(["5", "8", "10", "12", "15"])
        self.default_slide_count.setCurrentText("8")
        default_layout.addRow("기본 슬라이드 수:", self.default_slide_count)

        layout.addWidget(default_group)

        layout.addStretch()

        return widget

    def _create_agent_tab(self) -> QWidget:
        """에이전트 설정 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 설명
        info_label = QLabel(
            "Multi-Agent 시스템은 여러 전문 에이전트가 협력하여 프레젠테이션을 생성합니다.\n"
            "각 에이전트를 활성화/비활성화하고 역할을 조정할 수 있습니다."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # 에이전트 목록
        agents_group = QGroupBox("에이전트 구성")
        agents_layout = QVBoxLayout(agents_group)

        # Research Agent
        self.research_agent_check = QCheckBox("리서치 에이전트")
        self.research_agent_check.setChecked(True)
        self.research_agent_check.setToolTip("주제에 대한 정보를 검색하고 수집합니다")
        agents_layout.addWidget(self.research_agent_check)

        research_desc = QLabel("  └ 웹 검색, 자료 수집, 키워드 추출")
        research_desc.setStyleSheet("color: gray; font-size: 11px; margin-left: 20px;")
        agents_layout.addWidget(research_desc)

        # Content Agent
        self.content_agent_check = QCheckBox("콘텐츠 에이전트")
        self.content_agent_check.setChecked(True)
        self.content_agent_check.setToolTip("슬라이드 내용을 구조화하고 작성합니다")
        agents_layout.addWidget(self.content_agent_check)

        content_desc = QLabel("  └ 슬라이드 구조화, 텍스트 작성, 스토리 구성")
        content_desc.setStyleSheet("color: gray; font-size: 11px; margin-left: 20px;")
        agents_layout.addWidget(content_desc)

        # Design Agent
        self.design_agent_check = QCheckBox("디자인 에이전트")
        self.design_agent_check.setChecked(True)
        self.design_agent_check.setToolTip("레이아웃과 디자인을 결정합니다")
        agents_layout.addWidget(self.design_agent_check)

        design_desc = QLabel("  └ 레이아웃 선택, 색상 배치, 시각적 구성")
        design_desc.setStyleSheet("color: gray; font-size: 11px; margin-left: 20px;")
        agents_layout.addWidget(design_desc)

        # Image Agent
        self.image_agent_check = QCheckBox("이미지 에이전트")
        self.image_agent_check.setChecked(True)
        self.image_agent_check.setToolTip("이미지를 검색하거나 생성합니다")
        agents_layout.addWidget(self.image_agent_check)

        image_desc = QLabel("  └ 이미지 검색, AI 이미지 생성, 아이콘 선택")
        image_desc.setStyleSheet("color: gray; font-size: 11px; margin-left: 20px;")
        agents_layout.addWidget(image_desc)

        # Review Agent
        self.review_agent_check = QCheckBox("리뷰 에이전트")
        self.review_agent_check.setChecked(True)
        self.review_agent_check.setToolTip("생성된 프레젠테이션을 검토하고 개선합니다")
        agents_layout.addWidget(self.review_agent_check)

        review_desc = QLabel("  └ 품질 검토, 일관성 확인, 개선 제안")
        review_desc.setStyleSheet("color: gray; font-size: 11px; margin-left: 20px;")
        agents_layout.addWidget(review_desc)

        layout.addWidget(agents_group)

        # 고급 설정
        advanced_group = QGroupBox("고급 설정")
        advanced_layout = QFormLayout(advanced_group)

        # 에이전트 병렬 실행
        self.parallel_agents_check = QCheckBox()
        self.parallel_agents_check.setChecked(True)
        advanced_layout.addRow("에이전트 병렬 실행:", self.parallel_agents_check)

        # 최대 반복 횟수
        self.max_iterations_spin = QSpinBox()
        self.max_iterations_spin.setRange(1, 10)
        self.max_iterations_spin.setValue(3)
        advanced_layout.addRow("최대 반복 횟수:", self.max_iterations_spin)

        # 에이전트 상세 로그
        self.agent_verbose_check = QCheckBox()
        self.agent_verbose_check.setChecked(False)
        advanced_layout.addRow("상세 로그 표시:", self.agent_verbose_check)

        layout.addWidget(advanced_group)
        layout.addStretch()

        return widget

    def _create_template_tab(self) -> QWidget:
        """템플릿 설정 탭 생성"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 설명
        info_label = QLabel(
            "프레젠테이션 템플릿을 선택하고 기본값을 설정합니다."
        )
        info_label.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # 템플릿 설정
        template_group = QGroupBox("기본 템플릿")
        template_layout = QFormLayout(template_group)

        self.default_template_combo = QComboBox()
        self.default_template_combo.addItems([
            "자동 선택",
            "Pitch Deck (투자 유치용)",
            "Quarterly Report (분기 보고서)",
            "Lecture (강의 자료)",
            "Product Launch (제품 출시)",
            "Clean Minimal (미니멀)"
        ])
        self.default_template_combo.currentTextChanged.connect(self._on_template_changed)
        template_layout.addRow("기본 템플릿:", self.default_template_combo)

        layout.addWidget(template_group)

        # 템플릿 미리보기
        preview_group = QGroupBox("템플릿 미리보기")
        preview_layout = QVBoxLayout(preview_group)

        self.template_preview_frame = QFrame()
        self.template_preview_frame.setFixedHeight(120)
        self.template_preview_frame.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            "stop:0 #1a365d, stop:1 #2c5282); border-radius: 8px;"
        )
        preview_layout.addWidget(self.template_preview_frame)

        self.template_info_label = QLabel(
            "Pitch Deck: 스타트업 투자 유치를 위한 전문적인 피치덱 템플릿\n"
            "권장 슬라이드: 12장 | 색상 테마: professional, bold, tech"
        )
        self.template_info_label.setStyleSheet("font-size: 11px; color: gray;")
        self.template_info_label.setWordWrap(True)
        preview_layout.addWidget(self.template_info_label)

        layout.addWidget(preview_group)

        # 색상 스키마 설정
        color_group = QGroupBox("기본 색상 스키마")
        color_layout = QVBoxLayout(color_group)

        self.color_scheme_combo = QComboBox()
        self.color_scheme_combo.addItems([
            "Professional (전문적인 파란색)",
            "Bold (강렬한 빨간색)",
            "Tech (보라색 테크)",
            "Minimal (모노크롬)",
            "Dark (다크 모드)"
        ])
        color_layout.addWidget(self.color_scheme_combo)

        # 색상 미리보기
        color_preview_layout = QHBoxLayout()
        self.color_previews = []
        for color in ["#1a365d", "#2c5282", "#3182ce", "#ffffff", "#1a202c"]:
            preview = QFrame()
            preview.setFixedSize(40, 40)
            preview.setStyleSheet(f"background-color: {color}; border-radius: 4px; border: 1px solid #ccc;")
            color_preview_layout.addWidget(preview)
            self.color_previews.append(preview)
        color_preview_layout.addStretch()
        color_layout.addLayout(color_preview_layout)

        layout.addWidget(color_group)
        layout.addStretch()

        return widget

    def _create_mcp_tab(self) -> QWidget:
        """MCP 연결 설정 탭 생성"""
        # MCP 설정 관리자 참조
        self._mcp_manager = get_mcp_config_manager()

        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 설명
        info_label = QLabel(
            "MCP(Model Context Protocol)를 통해 외부 서비스와 연동합니다.\n"
            "PowerPoint 고급 기능, 웹 검색 등을 사용할 수 있습니다."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # PowerPoint MCP
        pptx_group = QGroupBox("PowerPoint MCP")
        pptx_layout = QVBoxLayout(pptx_group)

        self.pptx_mcp_check = QCheckBox("PowerPoint MCP 사용")
        self.pptx_mcp_check.setChecked(False)
        self.pptx_mcp_check.setToolTip("고급 PowerPoint 기능 (차트, SmartArt, 애니메이션 등)")
        pptx_layout.addWidget(self.pptx_mcp_check)

        pptx_desc = QLabel("  └ 차트 생성, SmartArt, 애니메이션, 전환 효과")
        pptx_desc.setStyleSheet("color: gray; font-size: 11px; margin-left: 20px;")
        pptx_layout.addWidget(pptx_desc)

        layout.addWidget(pptx_group)

        # Web Search MCP
        search_group = QGroupBox("웹 검색 MCP")
        search_layout = QVBoxLayout(search_group)

        self.search_mcp_check = QCheckBox("웹 검색 MCP 사용")
        self.search_mcp_check.setChecked(True)
        self.search_mcp_check.setToolTip("리서치 에이전트가 웹 검색을 수행합니다")
        search_layout.addWidget(self.search_mcp_check)

        search_desc = QLabel("  └ DuckDuckGo 무료 검색 지원")
        search_desc.setStyleSheet("color: gray; font-size: 11px; margin-left: 20px;")
        search_layout.addWidget(search_desc)

        # 검색 엔진 선택
        search_engine_layout = QHBoxLayout()
        search_engine_layout.addWidget(QLabel("검색 엔진:"))
        self.search_provider_combo = QComboBox()
        self.search_provider_combo.addItems(["DuckDuckGo (무료)", "Google", "Bing"])
        search_engine_layout.addWidget(self.search_provider_combo)
        search_engine_layout.addStretch()
        search_layout.addLayout(search_engine_layout)

        layout.addWidget(search_group)

        # Image Generation MCP
        image_group = QGroupBox("이미지 생성 MCP")
        image_layout = QVBoxLayout(image_group)

        self.image_mcp_check = QCheckBox("이미지 생성 MCP 사용")
        self.image_mcp_check.setChecked(False)
        self.image_mcp_check.setToolTip("AI 이미지 생성 기능을 사용합니다")
        image_layout.addWidget(self.image_mcp_check)

        image_desc = QLabel("  └ DALL-E 3, Stable Diffusion 지원")
        image_desc.setStyleSheet("color: gray; font-size: 11px; margin-left: 20px;")
        image_layout.addWidget(image_desc)

        # 이미지 생성기 선택
        image_gen_layout = QHBoxLayout()
        image_gen_layout.addWidget(QLabel("이미지 생성기:"))
        self.image_gen_provider_combo = QComboBox()
        self.image_gen_provider_combo.addItems(["DALL-E 3", "Stable Diffusion", "Midjourney API"])
        image_gen_layout.addWidget(self.image_gen_provider_combo)
        image_gen_layout.addStretch()
        image_layout.addLayout(image_gen_layout)

        layout.addWidget(image_group)

        # 고급 설정
        advanced_group = QGroupBox("고급 설정")
        advanced_layout = QFormLayout(advanced_group)

        self.mcp_auto_connect_check = QCheckBox()
        self.mcp_auto_connect_check.setChecked(True)
        advanced_layout.addRow("시작 시 자동 연결:", self.mcp_auto_connect_check)

        self.mcp_verbose_check = QCheckBox()
        self.mcp_verbose_check.setChecked(False)
        advanced_layout.addRow("상세 로그:", self.mcp_verbose_check)

        layout.addWidget(advanced_group)
        layout.addStretch()

        # 더미 속성 (호환성)
        self.pptx_mcp_status = QLabel()
        self.search_mcp_status = QLabel()
        self.image_mcp_status = QLabel()
        self.search_api_key_input = QLineEdit()
        self.mcp_server_url = QLineEdit()

        return widget


    def _on_template_changed(self, template_name: str):
        """템플릿 변경 시 미리보기 업데이트"""
        templates_info = {
            "자동 선택": {
                "gradient": "#4a5568, #718096",
                "info": "AI가 주제에 맞는 최적의 템플릿을 자동으로 선택합니다."
            },
            "Pitch Deck (투자 유치용)": {
                "gradient": "#1a365d, #2c5282",
                "info": "스타트업 투자 유치를 위한 전문적인 피치덱 템플릿\n권장 슬라이드: 12장 | 색상: professional, bold, tech"
            },
            "Quarterly Report (분기 보고서)": {
                "gradient": "#0f4c81, #1e6eb8",
                "info": "분기별 실적 보고를 위한 깔끔한 비즈니스 템플릿\n권장 슬라이드: 15장 | 색상: corporate, minimal"
            },
            "Lecture (강의 자료)": {
                "gradient": "#2d6a4f, #40916c",
                "info": "교육 및 강의용 프레젠테이션 템플릿\n권장 슬라이드: 20장 | 색상: nature, ocean, minimal"
            },
            "Product Launch (제품 출시)": {
                "gradient": "#e63946, #f72585",
                "info": "제품 출시 및 마케팅 발표용 템플릿\n권장 슬라이드: 12장 | 색상: bold, vibrant, modern"
            },
            "Clean Minimal (미니멀)": {
                "gradient": "#374151, #4b5563",
                "info": "깔끔하고 단순한 미니멀 디자인 템플릿\n권장 슬라이드: 10장 | 색상: monochrome, minimal, dark"
            }
        }

        info = templates_info.get(template_name, templates_info["자동 선택"])
        self.template_preview_frame.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
            f"stop:0 {info['gradient'].split(', ')[0]}, stop:1 {info['gradient'].split(', ')[1]}); "
            f"border-radius: 8px;"
        )
        self.template_info_label.setText(info["info"])


    def _on_provider_changed(self, provider: str):
        """프로바이더 변경 처리"""
        self.openai_group.hide()
        self.google_group.hide()
        self.anthropic_group.hide()
        self.ollama_group.hide()

        if provider == "OpenAI":
            self.openai_group.show()
        elif provider == "Google":
            self.google_group.show()
        elif provider == "Anthropic":
            self.anthropic_group.show()
        elif provider == "Ollama":
            self.ollama_group.show()

    def _load_settings(self):
        """설정 로드"""
        env_path = Path(".env")
        if not env_path.exists():
            return

        env_vars = {}
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()

        # LLM 프로바이더
        provider = env_vars.get("LLM_PROVIDER", "openai").lower()
        provider_map = {"openai": "OpenAI", "google": "Google", "anthropic": "Anthropic", "ollama": "Ollama"}
        self.provider_combo.setCurrentText(provider_map.get(provider, "OpenAI"))

        # OpenAI
        self.openai_api_key.setText(env_vars.get("OPENAI_API_KEY", ""))
        if "OPENAI_MODEL" in env_vars:
            self.openai_model.setCurrentText(env_vars["OPENAI_MODEL"])

        # Google
        self.google_api_key.setText(env_vars.get("GOOGLE_API_KEY", ""))
        if "GOOGLE_MODEL" in env_vars:
            self.google_model.setCurrentText(env_vars["GOOGLE_MODEL"])

        # Anthropic
        self.anthropic_api_key.setText(env_vars.get("ANTHROPIC_API_KEY", ""))
        if "ANTHROPIC_MODEL" in env_vars:
            self.anthropic_model.setCurrentText(env_vars["ANTHROPIC_MODEL"])

        # Ollama
        self.ollama_url.setText(env_vars.get("OLLAMA_URL", "http://localhost:11434"))
        if "OLLAMA_MODEL" in env_vars:
            self.ollama_model.setCurrentText(env_vars["OLLAMA_MODEL"])

        # 이미지 프로바이더
        image_provider = env_vars.get("IMAGE_PROVIDER", "dall-e-3").lower()
        image_map = {"dall-e-3": "DALL-E (OpenAI)", "pexels": "Pexels", "pixabay": "Pixabay", "disabled": "비활성화"}
        self.image_provider_combo.setCurrentText(image_map.get(image_provider, "DALL-E (OpenAI)"))

        self.pexels_api_key.setText(env_vars.get("PEXELS_API_KEY", ""))
        self.pixabay_api_key.setText(env_vars.get("PIXABAY_API_KEY", ""))

        # MCP 설정 로드
        self._load_mcp_settings()

    def _load_mcp_settings(self):
        """MCP 설정 로드"""
        try:
            mcp_config = self._mcp_manager.config

            # PowerPoint MCP
            self.pptx_mcp_check.setChecked(mcp_config.powerpoint.enabled)

            # Web Search MCP
            self.search_mcp_check.setChecked(mcp_config.web_search.enabled)

            # 검색 엔진 프로바이더
            provider = mcp_config.web_search.options.get("provider", "duckduckgo")
            provider_map = {
                "duckduckgo": "DuckDuckGo (무료)",
                "google": "Google",
                "bing": "Bing"
            }
            self.search_provider_combo.setCurrentText(provider_map.get(provider, "DuckDuckGo (무료)"))

            # Image Generation MCP
            self.image_mcp_check.setChecked(mcp_config.image_generation.enabled)

            # 이미지 생성기 프로바이더
            img_provider = mcp_config.image_generation.options.get("provider", "dalle3")
            img_provider_map = {
                "dalle3": "DALL-E 3",
                "stable_diffusion": "Stable Diffusion",
                "midjourney": "Midjourney API"
            }
            self.image_gen_provider_combo.setCurrentText(img_provider_map.get(img_provider, "DALL-E 3"))

            # 고급 설정
            self.mcp_auto_connect_check.setChecked(mcp_config.auto_connect)
            self.mcp_verbose_check.setChecked(mcp_config.verbose_logging)

        except Exception as e:
            import structlog
            logger = structlog.get_logger(__name__)
            logger.error("Failed to load MCP settings", error=str(e))

    def _save_settings(self):
        """설정 저장"""
        env_lines = []

        # LLM 설정
        provider = self.provider_combo.currentText()
        provider_map = {"OpenAI": "openai", "Google": "google", "Anthropic": "anthropic", "Ollama": "ollama"}
        env_lines.append(f"LLM_PROVIDER={provider_map.get(provider, 'openai')}")
        env_lines.append("")

        # OpenAI
        env_lines.append("# OpenAI")
        if self.openai_api_key.text():
            env_lines.append(f"OPENAI_API_KEY={self.openai_api_key.text()}")
        env_lines.append(f"OPENAI_MODEL={self.openai_model.currentText()}")
        env_lines.append("")

        # Google
        env_lines.append("# Google Gemini")
        if self.google_api_key.text():
            env_lines.append(f"GOOGLE_API_KEY={self.google_api_key.text()}")
        env_lines.append(f"GOOGLE_MODEL={self.google_model.currentText()}")
        env_lines.append("")

        # Anthropic
        env_lines.append("# Anthropic Claude")
        if self.anthropic_api_key.text():
            env_lines.append(f"ANTHROPIC_API_KEY={self.anthropic_api_key.text()}")
        env_lines.append(f"ANTHROPIC_MODEL={self.anthropic_model.currentText()}")
        env_lines.append("")

        # Ollama
        env_lines.append("# Ollama")
        env_lines.append(f"OLLAMA_URL={self.ollama_url.text() or 'http://localhost:11434'}")
        env_lines.append(f"OLLAMA_MODEL={self.ollama_model.currentText()}")
        env_lines.append("")

        # 이미지 프로바이더
        env_lines.append("# Image Provider")
        image_provider = self.image_provider_combo.currentText()
        image_map = {"DALL-E (OpenAI)": "dall-e-3", "Pexels": "pexels", "Pixabay": "pixabay", "비활성화": "disabled"}
        env_lines.append(f"IMAGE_PROVIDER={image_map.get(image_provider, 'dall-e-3')}")
        if self.pexels_api_key.text():
            env_lines.append(f"PEXELS_API_KEY={self.pexels_api_key.text()}")
        if self.pixabay_api_key.text():
            env_lines.append(f"PIXABAY_API_KEY={self.pixabay_api_key.text()}")

        try:
            with open(".env", "w", encoding="utf-8") as f:
                f.write("\n".join(env_lines))

            # 설정 다시 로드
            from src.config import reload_settings
            reload_settings()

            # MCP 설정 저장
            self._save_mcp_settings()

            QMessageBox.information(self, "저장 완료", "설정이 저장되었습니다.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 저장 실패:\n{e}")

    def _save_mcp_settings(self):
        """MCP 설정 저장"""
        try:
            # PowerPoint MCP
            self._mcp_manager.update_service(
                "powerpoint",
                enabled=self.pptx_mcp_check.isChecked()
            )

            # Web Search MCP
            provider_map = {
                "DuckDuckGo (무료)": "duckduckgo",
                "Google": "google",
                "Bing": "bing"
            }
            search_provider = provider_map.get(
                self.search_provider_combo.currentText(),
                "duckduckgo"
            )

            # 웹 검색 옵션 업데이트
            web_search_options = self._mcp_manager.config.web_search.options.copy()
            web_search_options["provider"] = search_provider

            self._mcp_manager.update_service(
                "web_search",
                enabled=self.search_mcp_check.isChecked(),
                api_key=self.search_api_key_input.text() if self.search_api_key_input.text() else None,
                options=web_search_options
            )

            # Image Generation MCP
            img_provider_map = {
                "DALL-E 3": "dalle3",
                "Stable Diffusion": "stable_diffusion",
                "Midjourney API": "midjourney"
            }
            img_provider = img_provider_map.get(
                self.image_gen_provider_combo.currentText(),
                "dalle3"
            )

            # 이미지 생성 옵션 업데이트
            image_options = self._mcp_manager.config.image_generation.options.copy()
            image_options["provider"] = img_provider

            self._mcp_manager.update_service(
                "image_generation",
                enabled=self.image_mcp_check.isChecked(),
                options=image_options
            )

            # 글로벌 설정
            self._mcp_manager.config.auto_connect = self.mcp_auto_connect_check.isChecked()
            self._mcp_manager.config.verbose_logging = self.mcp_verbose_check.isChecked()
            self._mcp_manager.save()

        except Exception as e:
            import structlog
            logger = structlog.get_logger(__name__)
            logger.error("Failed to save MCP settings", error=str(e))
