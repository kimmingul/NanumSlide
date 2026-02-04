"""메인 윈도우"""

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QToolBar,
    QLabel,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QKeySequence

from src.core.presentation import Presentation, Slide, SlideLayoutType
from src.core.themes import Theme, get_theme_by_display_name
from src.ui.slide_editor import SlideEditor
from src.ui.widgets.slide_thumbnail import SlideThumbnailList
from src.ui.widgets.prompt_panel import PromptPanel
from src.ui.dialogs.settings_dialog import SettingsDialog
from src.ui.ui_theme import get_ui_theme_manager
from src.services.generation_worker import MockGenerationWorker, GenerationWorker
from src.core.export.pptx_exporter import export_to_pptx
from src.config import get_settings


class MainWindow(QMainWindow):
    """NanumSlide 메인 윈도우"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NanumSlide - AI 프레젠테이션 생성기")
        self.setMinimumSize(1280, 720)
        self.resize(1440, 900)

        # 현재 프레젠테이션
        self.presentation: Optional[Presentation] = None
        self.current_file_path: Optional[str] = None
        self.generation_worker: Optional[GenerationWorker] = None
        self.current_theme: Optional[Theme] = None

        self._setup_ui()
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()

    def _setup_ui(self):
        """UI 구성"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 메인 스플리터 (3단 구성)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # 1. 좌측: 슬라이드 썸네일 목록
        self.thumbnail_list = SlideThumbnailList()
        self.thumbnail_list.setFixedWidth(196)
        splitter.addWidget(self.thumbnail_list)

        # 2. 중앙: 슬라이드 에디터
        self.slide_editor = SlideEditor()
        splitter.addWidget(self.slide_editor)

        # 3. 우측: AI 프롬프트 패널
        self.prompt_panel = PromptPanel()
        self.prompt_panel.setFixedWidth(450)
        splitter.addWidget(self.prompt_panel)

        # 스플리터 비율 설정
        splitter.setStretchFactor(0, 0)  # 썸네일 고정
        splitter.setStretchFactor(1, 1)  # 에디터 확장
        splitter.setStretchFactor(2, 0)  # 프롬프트 패널 고정

        main_layout.addWidget(splitter)

    def _connect_signals(self):
        """시그널 연결"""
        # 프롬프트 패널 시그널
        self.prompt_panel.generation_requested.connect(self._on_generation_requested)
        self.prompt_panel.generation_cancelled.connect(self._on_generation_cancelled)
        self.prompt_panel.theme_changed.connect(self._on_theme_changed)

        # 썸네일 리스트 시그널
        self.thumbnail_list.slide_selected.connect(self._on_slide_selected)

        # 슬라이드 에디터 시그널
        self.slide_editor.slide_changed.connect(self._on_slide_changed)

        # 초기 테마 적용
        self.current_theme = self.prompt_panel.get_current_theme()
        self.slide_editor.set_theme(self.current_theme)

    def _setup_menubar(self):
        """메뉴바 구성"""
        menubar = self.menuBar()

        # 파일 메뉴
        file_menu = menubar.addMenu("파일(&F)")

        new_action = QAction("새 프레젠테이션(&N)", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._new_presentation)
        file_menu.addAction(new_action)

        open_action = QAction("열기(&O)...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._open_presentation)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        save_action = QAction("저장(&S)", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._save_presentation)
        file_menu.addAction(save_action)

        save_as_action = QAction("다른 이름으로 저장(&A)...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.triggered.connect(self._save_presentation_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        # 내보내기 서브메뉴
        export_menu = file_menu.addMenu("내보내기(&E)")

        export_pptx = QAction("PowerPoint (.pptx)", self)
        export_pptx.triggered.connect(self._export_pptx)
        export_menu.addAction(export_pptx)

        export_pdf = QAction("PDF (.pdf)", self)
        export_pdf.triggered.connect(self._export_pdf)
        export_menu.addAction(export_pdf)

        file_menu.addSeparator()

        exit_action = QAction("종료(&X)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 편집 메뉴
        edit_menu = menubar.addMenu("편집(&E)")

        undo_action = QAction("실행 취소(&U)", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("다시 실행(&R)", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        add_slide_action = QAction("슬라이드 추가(&A)", self)
        add_slide_action.setShortcut(QKeySequence("Ctrl+M"))
        add_slide_action.triggered.connect(self._add_slide)
        edit_menu.addAction(add_slide_action)

        delete_slide_action = QAction("슬라이드 삭제(&D)", self)
        delete_slide_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_slide_action.triggered.connect(self._delete_slide)
        edit_menu.addAction(delete_slide_action)

        # 보기 메뉴
        view_menu = menubar.addMenu("보기(&V)")

        self.dark_mode_action = QAction("다크 모드(&D)", self)
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.setShortcut(QKeySequence("Ctrl+D"))
        self.dark_mode_action.triggered.connect(self._toggle_ui_theme)
        view_menu.addAction(self.dark_mode_action)

        # AI 메뉴
        ai_menu = menubar.addMenu("AI(&A)")

        generate_action = QAction("프레젠테이션 생성(&G)...", self)
        generate_action.setShortcut(QKeySequence("Ctrl+G"))
        generate_action.triggered.connect(self._show_generation_dialog)
        ai_menu.addAction(generate_action)

        ai_menu.addSeparator()

        settings_action = QAction("AI 설정(&S)...", self)
        settings_action.triggered.connect(self._show_ai_settings)
        ai_menu.addAction(settings_action)

        # 도움말 메뉴
        help_menu = menubar.addMenu("도움말(&H)")

        about_action = QAction("NanumSlide 정보(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self):
        """툴바 구성"""
        toolbar = QToolBar("메인 툴바")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        # 새로 만들기
        new_action = toolbar.addAction("새로 만들기")
        new_action.triggered.connect(self._new_presentation)

        # 열기
        open_action = toolbar.addAction("열기")
        open_action.triggered.connect(self._open_presentation)

        # 저장
        save_action = toolbar.addAction("저장")
        save_action.triggered.connect(self._save_presentation)

        toolbar.addSeparator()

        # 슬라이드 추가
        add_slide_action = toolbar.addAction("슬라이드 추가")
        add_slide_action.triggered.connect(self._add_slide)

        toolbar.addSeparator()

        # PPTX 내보내기
        export_action = toolbar.addAction("PPTX 내보내기")
        export_action.triggered.connect(self._export_pptx)

        toolbar.addSeparator()

        # 설정
        settings_action = toolbar.addAction("설정")
        settings_action.triggered.connect(self._show_ai_settings)

        toolbar.addSeparator()

        # 다크/라이트 모드 토글
        self.theme_toggle_action = toolbar.addAction("🌙 다크 모드")
        self.theme_toggle_action.triggered.connect(self._toggle_ui_theme)

        # 테마 변경 시그널 연결
        ui_theme = get_ui_theme_manager()
        ui_theme.theme_changed.connect(self._on_ui_theme_changed)

    def _setup_statusbar(self):
        """상태바 구성"""
        statusbar = self.statusBar()
        self.status_label = QLabel("준비")
        statusbar.addWidget(self.status_label)

        self.slide_count_label = QLabel("슬라이드: 0")
        statusbar.addPermanentWidget(self.slide_count_label)

    # === 파일 작업 ===

    def _new_presentation(self):
        """새 프레젠테이션"""
        self.presentation = None
        self.current_file_path = None
        self.thumbnail_list.clear_slides()
        self.slide_editor.clear()
        self._update_slide_count()
        self.status_label.setText("새 프레젠테이션")

    def _open_presentation(self):
        """프레젠테이션 열기"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "프레젠테이션 열기",
            "",
            "NanumSlide 파일 (*.nslide);;모든 파일 (*.*)",
        )
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    json_str = f.read()
                self.presentation = Presentation.from_json(json_str)
                self.current_file_path = file_path
                self._load_presentation_to_ui()
                self.status_label.setText(f"열림: {Path(file_path).name}")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"파일을 열 수 없습니다:\n{e}")

    def _save_presentation(self):
        """프레젠테이션 저장"""
        if not self.presentation:
            QMessageBox.warning(self, "경고", "저장할 프레젠테이션이 없습니다.")
            return

        if self.current_file_path:
            self._save_to_file(self.current_file_path)
        else:
            self._save_presentation_as()

    def _save_presentation_as(self):
        """다른 이름으로 저장"""
        if not self.presentation:
            QMessageBox.warning(self, "경고", "저장할 프레젠테이션이 없습니다.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "프레젠테이션 저장",
            f"{self.presentation.title}.nslide",
            "NanumSlide 파일 (*.nslide);;모든 파일 (*.*)",
        )
        if file_path:
            self._save_to_file(file_path)
            self.current_file_path = file_path

    def _save_to_file(self, file_path: str):
        """파일에 저장"""
        try:
            self._sync_presentation_from_ui()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.presentation.to_json())
            self.status_label.setText(f"저장됨: {Path(file_path).name}")
        except Exception as e:
            QMessageBox.critical(self, "오류", f"저장 실패:\n{e}")

    def _export_pptx(self):
        """PowerPoint로 내보내기"""
        if not self.presentation or not self.presentation.slides:
            QMessageBox.warning(self, "경고", "내보낼 프레젠테이션이 없습니다.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "PowerPoint로 내보내기",
            f"{self.presentation.title}.pptx",
            "PowerPoint 파일 (*.pptx)",
        )
        if file_path:
            self._sync_presentation_from_ui()
            self.status_label.setText("PPTX 내보내기 중...")

            try:
                success = export_to_pptx(self.presentation, Path(file_path))
                if success:
                    self.status_label.setText(f"내보내기 완료: {Path(file_path).name}")
                    QMessageBox.information(
                        self, "완료", f"PowerPoint 파일이 저장되었습니다:\n{file_path}"
                    )
                else:
                    raise Exception("내보내기 실패")
            except Exception as e:
                self.status_label.setText("내보내기 실패")
                QMessageBox.critical(self, "오류", f"PPTX 내보내기 실패:\n{e}")

    def _export_pdf(self):
        """PDF로 내보내기"""
        QMessageBox.information(self, "알림", "PDF 내보내기는 준비 중입니다.")

    # === 슬라이드 작업 ===

    def _add_slide(self):
        """슬라이드 추가"""
        if not self.presentation:
            self.presentation = Presentation(title="새 프레젠테이션")

        new_slide = Slide(
            id=f"slide_{self.presentation.slide_count + 1}",
            title=f"슬라이드 {self.presentation.slide_count + 1}",
            layout=SlideLayoutType.TITLE_CONTENT,
        )
        self.presentation.add_slide(new_slide)
        self.thumbnail_list.add_slide_from_data(new_slide)
        self._update_slide_count()

    def _delete_slide(self):
        """슬라이드 삭제"""
        current_index = self.thumbnail_list.get_current_index()
        if current_index >= 0 and self.presentation:
            self.presentation.remove_slide(current_index)
            self.thumbnail_list.delete_current_slide()
            self._update_slide_count()

            # 다음 슬라이드 선택
            if self.presentation.slides:
                new_index = min(current_index, len(self.presentation.slides) - 1)
                self.thumbnail_list.select_slide(new_index)
                self._on_slide_selected(new_index)
            else:
                self.slide_editor.clear()

    def _update_slide_count(self):
        """슬라이드 수 업데이트"""
        count = self.presentation.slide_count if self.presentation else 0
        self.slide_count_label.setText(f"슬라이드: {count}")

    def _on_slide_selected(self, index: int):
        """슬라이드 선택 처리"""
        if self.presentation and 0 <= index < len(self.presentation.slides):
            slide = self.presentation.slides[index]
            self.slide_editor.load_slide(slide)

    def _on_slide_changed(self, slide_data: dict):
        """슬라이드 변경 처리"""
        current_index = self.thumbnail_list.get_current_index()
        if self.presentation and 0 <= current_index < len(self.presentation.slides):
            slide = self.presentation.slides[current_index]
            slide.title = slide_data.get("title", slide.title)
            slide.content = slide_data.get("content", slide.content)
            slide.bullet_points = slide_data.get("bullet_points", slide.bullet_points)
            self.thumbnail_list.update_slide_thumbnail(current_index, slide)

    def _on_theme_changed(self, theme: Theme):
        """테마 변경 처리"""
        self.current_theme = theme
        self.slide_editor.set_theme(theme)

        # 프레젠테이션에도 테마 적용
        if self.presentation:
            self.presentation.theme = theme.name

        self.status_label.setText(f"테마 변경: {theme.display_name}")

    # === AI 작업 ===

    def _on_generation_requested(self, prompt: str):
        """AI 생성 요청 처리"""
        if not prompt.strip():
            return

        options = self.prompt_panel.get_options()
        selected_model = options["model"]

        self.status_label.setText("AI 프레젠테이션 생성 중...")

        # 선택된 모델의 프로바이더에 맞는 API 키 확인
        settings = get_settings()
        has_valid_key = False

        if selected_model.startswith("[OpenAI]"):
            has_valid_key = bool(settings.openai_api_key)
        elif selected_model.startswith("[Anthropic]"):
            has_valid_key = bool(settings.anthropic_api_key)
        elif not selected_model.startswith("("):  # "(설정에서 API 키를 입력하세요)" 제외
            has_valid_key = bool(settings.openai_api_key or settings.anthropic_api_key)

        if has_valid_key:
            # 실제 AI 생성
            self.generation_worker = GenerationWorker(
                prompt=prompt,
                slide_count=options["slide_count"],
                language=options["language"],
                template=options["template"],
                model=options["model"],
                reference_content=options.get("reference_content", ""),
            )
        else:
            # API 키 없음 - 오류 메시지 표시
            self.prompt_panel.generation_complete()
            self.status_label.setText("API 키 필요")

            if selected_model.startswith("("):
                QMessageBox.warning(
                    self,
                    "API 키 필요",
                    "설정에서 OpenAI 또는 Anthropic API 키를 입력한 후\n"
                    "'검증' 버튼을 눌러 모델 목록을 불러와주세요."
                )
            else:
                provider = "OpenAI" if selected_model.startswith("[OpenAI]") else "Anthropic"
                QMessageBox.warning(
                    self,
                    "API 키 필요",
                    f"{provider} API 키가 설정되지 않았습니다.\n"
                    f"설정에서 {provider} API 키를 입력해주세요."
                )
            return

        # 시그널 연결
        self.generation_worker.progress.connect(self._on_generation_progress)
        self.generation_worker.finished.connect(self._on_generation_finished)
        self.generation_worker.error.connect(self._on_generation_error)

        # 워커 시작
        self.generation_worker.start()

    def _on_generation_cancelled(self):
        """생성 취소 처리"""
        if self.generation_worker:
            self.generation_worker.cancel()
            self.generation_worker = None
        self.status_label.setText("생성 취소됨")

    def _on_generation_progress(self, message: str, percent: int):
        """생성 진행률 처리"""
        self.status_label.setText(message)
        self.prompt_panel.set_progress(message, percent)

    def _on_generation_finished(self, presentation: Presentation):
        """생성 완료 처리"""
        self.presentation = presentation
        self._load_presentation_to_ui()
        self.prompt_panel.generation_complete()
        self.status_label.setText(f"생성 완료: {presentation.slide_count}개 슬라이드")
        self.generation_worker = None

    def _on_generation_error(self, error_message: str):
        """생성 오류 처리"""
        self.prompt_panel.generation_complete()
        self.status_label.setText("생성 실패")
        QMessageBox.critical(self, "생성 오류", f"프레젠테이션 생성 실패:\n{error_message}")
        self.generation_worker = None

    def _load_presentation_to_ui(self):
        """프레젠테이션을 UI에 로드"""
        if not self.presentation:
            return

        self.thumbnail_list.clear_slides()

        for slide in self.presentation.slides:
            self.thumbnail_list.add_slide_from_data(slide)

        self._update_slide_count()

        # 첫 번째 슬라이드 선택
        if self.presentation.slides:
            self.thumbnail_list.select_slide(0)
            self._on_slide_selected(0)

    def _sync_presentation_from_ui(self):
        """UI에서 프레젠테이션 데이터 동기화"""
        # 현재 편집 중인 슬라이드 저장
        current_index = self.thumbnail_list.get_current_index()
        if self.presentation and 0 <= current_index < len(self.presentation.slides):
            slide_data = self.slide_editor.get_slide_data()
            slide = self.presentation.slides[current_index]
            slide.title = slide_data.get("title", slide.title)
            slide.content = slide_data.get("content", slide.content)

    def _show_generation_dialog(self):
        """AI 생성 다이얼로그 표시"""
        self.prompt_panel.focus_prompt_input()

    def _show_ai_settings(self):
        """AI 설정 다이얼로그"""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # 설정 저장 후 모델 목록 새로고침
            self.prompt_panel.refresh_models()

    # === UI 테마 ===

    def _toggle_ui_theme(self):
        """UI 테마 토글 (다크/라이트)"""
        ui_theme = get_ui_theme_manager()
        ui_theme.toggle_theme()

    def _on_ui_theme_changed(self, is_dark: bool):
        """UI 테마 변경 시 처리"""
        # 메뉴 체크박스 업데이트
        self.dark_mode_action.setChecked(is_dark)

        if is_dark:
            self.theme_toggle_action.setText("☀️ 라이트 모드")
            self.status_label.setText("다크 모드로 전환됨")
        else:
            self.theme_toggle_action.setText("🌙 다크 모드")
            self.status_label.setText("라이트 모드로 전환됨")

    # === 기타 ===

    def _show_about(self):
        """프로그램 정보"""
        QMessageBox.about(
            self,
            "NanumSlide 정보",
            "<h2>NanumSlide</h2>"
            "<p>버전 0.1.0</p>"
            "<p>AI 기반 프레젠테이션 생성기</p>"
            "<p>Apache 2.0 라이선스</p>",
        )

    def closeEvent(self, event):
        """창 닫기 이벤트"""
        if self.generation_worker and self.generation_worker.isRunning():
            self.generation_worker.cancel()
            self.generation_worker.wait()
        event.accept()
