"""설정 다이얼로그"""

import os
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
)
from PySide6.QtCore import Qt, QThread, Signal

from src.config import LLMProvider, ImageProvider
from src.services.llm_client import fetch_openai_models, fetch_anthropic_models


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
        self.setMinimumSize(500, 400)
        self.resize(550, 450)

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

            QMessageBox.information(self, "저장 완료", "설정이 저장되었습니다.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 저장 실패:\n{e}")
