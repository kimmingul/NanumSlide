"""UI 테마 시스템 (다크/라이트 모드)"""

from dataclasses import dataclass
from typing import Optional
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal


@dataclass
class UIColors:
    """UI 색상 정의"""
    # 배경색
    background: str
    surface: str
    surface_hover: str

    # 텍스트
    text_primary: str
    text_secondary: str
    text_muted: str

    # 테두리
    border: str
    border_light: str

    # 강조색
    accent: str
    accent_hover: str
    accent_pressed: str

    # 상태
    success: str
    warning: str
    error: str

    # 기타
    selection: str
    scrollbar: str
    scrollbar_hover: str


# 라이트 모드 색상
LIGHT_COLORS = UIColors(
    background="#f5f5f5",
    surface="#ffffff",
    surface_hover="#f0f0f0",

    text_primary="#1a1a1a",
    text_secondary="#4a4a4a",
    text_muted="#808080",

    border="#d0d0d0",
    border_light="#e5e5e5",

    accent="#007acc",
    accent_hover="#005a9e",
    accent_pressed="#004578",

    success="#28a745",
    warning="#ffc107",
    error="#dc3545",

    selection="#cce5ff",
    scrollbar="#c0c0c0",
    scrollbar_hover="#a0a0a0",
)

# 다크 모드 색상
DARK_COLORS = UIColors(
    background="#1e1e1e",
    surface="#2d2d2d",
    surface_hover="#3d3d3d",

    text_primary="#e0e0e0",
    text_secondary="#b0b0b0",
    text_muted="#808080",

    border="#404040",
    border_light="#505050",

    accent="#0098ff",
    accent_hover="#33adff",
    accent_pressed="#0078cc",

    success="#4caf50",
    warning="#ffb74d",
    error="#f44336",

    selection="#264f78",
    scrollbar="#505050",
    scrollbar_hover="#606060",
)


def get_stylesheet(colors: UIColors) -> str:
    """전체 애플리케이션 스타일시트 생성"""
    return f"""
    /* 기본 위젯 */
    QWidget {{
        background-color: {colors.background};
        color: {colors.text_primary};
        font-family: "Malgun Gothic", "Segoe UI", sans-serif;
    }}

    QMainWindow {{
        background-color: {colors.background};
    }}

    /* 메뉴바 */
    QMenuBar {{
        background-color: {colors.surface};
        color: {colors.text_primary};
        border-bottom: 1px solid {colors.border};
        padding: 2px;
    }}

    QMenuBar::item {{
        padding: 6px 12px;
        background-color: transparent;
    }}

    QMenuBar::item:selected {{
        background-color: {colors.surface_hover};
    }}

    QMenu {{
        background-color: {colors.surface};
        color: {colors.text_primary};
        border: 1px solid {colors.border};
    }}

    QMenu::item {{
        padding: 8px 30px;
    }}

    QMenu::item:selected {{
        background-color: {colors.accent};
        color: white;
    }}

    QMenu::separator {{
        height: 1px;
        background-color: {colors.border};
        margin: 4px 10px;
    }}

    /* 툴바 */
    QToolBar {{
        background-color: {colors.surface};
        border-bottom: 1px solid {colors.border};
        padding: 4px;
        spacing: 4px;
    }}

    QToolBar::separator {{
        width: 1px;
        background-color: {colors.border};
        margin: 4px 8px;
    }}

    QToolButton {{
        background-color: transparent;
        color: {colors.text_primary};
        border: none;
        border-radius: 4px;
        padding: 6px 12px;
    }}

    QToolButton:hover {{
        background-color: {colors.surface_hover};
    }}

    QToolButton:pressed {{
        background-color: {colors.border};
    }}

    /* 상태바 */
    QStatusBar {{
        background-color: {colors.surface};
        color: {colors.text_secondary};
        border-top: 1px solid {colors.border};
    }}

    /* 스플리터 */
    QSplitter::handle {{
        background-color: {colors.border};
    }}

    QSplitter::handle:horizontal {{
        width: 1px;
    }}

    /* 스크롤바 */
    QScrollBar:vertical {{
        background-color: {colors.background};
        width: 12px;
        border: none;
    }}

    QScrollBar::handle:vertical {{
        background-color: {colors.scrollbar};
        border-radius: 4px;
        min-height: 30px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {colors.scrollbar_hover};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background-color: {colors.background};
        height: 12px;
        border: none;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {colors.scrollbar};
        border-radius: 4px;
        min-width: 30px;
        margin: 2px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {colors.scrollbar_hover};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* 입력 필드 */
    QLineEdit {{
        background-color: {colors.surface};
        color: {colors.text_primary};
        border: 1px solid {colors.border};
        border-radius: 4px;
        padding: 6px 10px;
        selection-background-color: {colors.selection};
    }}

    QLineEdit:focus {{
        border-color: {colors.accent};
    }}

    QTextEdit {{
        background-color: {colors.surface};
        color: {colors.text_primary};
        border: 1px solid {colors.border};
        border-radius: 4px;
        padding: 6px;
        selection-background-color: {colors.selection};
    }}

    QTextEdit:focus {{
        border-color: {colors.accent};
    }}

    QPlainTextEdit {{
        background-color: {colors.surface};
        color: {colors.text_primary};
        border: 1px solid {colors.border};
        border-radius: 4px;
        padding: 6px;
        selection-background-color: {colors.selection};
    }}

    /* 콤보박스 */
    QComboBox {{
        background-color: {colors.surface};
        color: {colors.text_primary};
        border: 1px solid {colors.border};
        border-radius: 4px;
        padding: 6px 10px;
        min-width: 100px;
    }}

    QComboBox:hover {{
        border-color: {colors.accent};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid {colors.text_secondary};
        margin-right: 5px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {colors.surface};
        color: {colors.text_primary};
        border: 1px solid {colors.border};
        selection-background-color: {colors.accent};
        selection-color: white;
    }}

    /* 스핀박스 */
    QSpinBox {{
        background-color: {colors.surface};
        color: {colors.text_primary};
        border: 1px solid {colors.border};
        border-radius: 4px;
        padding: 6px 10px;
    }}

    QSpinBox:focus {{
        border-color: {colors.accent};
    }}

    /* 버튼 */
    QPushButton {{
        background-color: {colors.surface};
        color: {colors.text_primary};
        border: 1px solid {colors.border};
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: 500;
    }}

    QPushButton:hover {{
        background-color: {colors.surface_hover};
        border-color: {colors.accent};
    }}

    QPushButton:pressed {{
        background-color: {colors.border};
    }}

    QPushButton:disabled {{
        background-color: {colors.background};
        color: {colors.text_muted};
    }}

    /* 그룹박스 */
    QGroupBox {{
        background-color: {colors.surface};
        border: 1px solid {colors.border};
        border-radius: 6px;
        margin-top: 12px;
        padding: 12px;
        padding-top: 24px;
        font-weight: bold;
    }}

    QGroupBox::title {{
        color: {colors.text_primary};
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        padding: 0 6px;
        background-color: {colors.surface};
    }}

    /* 프레임 */
    QFrame {{
        border: none;
    }}

    /* 레이블 */
    QLabel {{
        color: {colors.text_primary};
        background-color: transparent;
    }}

    /* 리스트 위젯 */
    QListWidget {{
        background-color: {colors.surface};
        color: {colors.text_primary};
        border: 1px solid {colors.border};
        border-radius: 4px;
        outline: none;
    }}

    QListWidget::item {{
        padding: 8px;
        border-bottom: 1px solid {colors.border_light};
    }}

    QListWidget::item:selected {{
        background-color: {colors.accent};
        color: white;
    }}

    QListWidget::item:hover {{
        background-color: {colors.surface_hover};
    }}

    /* 프로그레스바 */
    QProgressBar {{
        background-color: {colors.border};
        border-radius: 4px;
        text-align: center;
        color: {colors.text_primary};
    }}

    QProgressBar::chunk {{
        background-color: {colors.accent};
        border-radius: 4px;
    }}

    /* 탭 위젯 */
    QTabWidget::pane {{
        background-color: {colors.surface};
        border: 1px solid {colors.border};
        border-radius: 4px;
    }}

    QTabBar::tab {{
        background-color: {colors.background};
        color: {colors.text_secondary};
        border: 1px solid {colors.border};
        border-bottom: none;
        padding: 8px 16px;
        margin-right: 2px;
    }}

    QTabBar::tab:selected {{
        background-color: {colors.surface};
        color: {colors.text_primary};
        border-bottom: 2px solid {colors.accent};
    }}

    QTabBar::tab:hover {{
        background-color: {colors.surface_hover};
    }}

    /* 스크롤 영역 */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}

    /* 다이얼로그 */
    QDialog {{
        background-color: {colors.background};
    }}

    /* 메시지박스 */
    QMessageBox {{
        background-color: {colors.surface};
    }}

    QMessageBox QLabel {{
        color: {colors.text_primary};
    }}

    /* 슬라이드 에디터 전용 스타일 */
    QWidget#preview_container {{
        background-color: {colors.background};
    }}

    QScrollArea#preview_scroll {{
        background-color: {colors.background};
        border: none;
    }}

    QWidget#edit_container {{
        background-color: {colors.surface};
        border-top: 1px solid {colors.border};
    }}

    /* 슬라이드 미리보기 (항상 흰색 배경 유지) */
    SlidePreview {{
        background-color: white;
        border: 1px solid {colors.border};
    }}

    /* 슬라이드 썸네일 */
    SlideThumbnailItem {{
        background-color: {colors.surface};
        border: 2px solid {colors.border};
        border-radius: 4px;
    }}

    SlideThumbnailItem:hover {{
        border-color: {colors.accent};
    }}

    SlideThumbnailItem[selected="true"] {{
        background-color: {colors.selection};
        border: 2px solid {colors.accent};
    }}

    /* 슬라이드 목록 */
    QListWidget#slide_list {{
        background-color: transparent;
        border: none;
        outline: none;
    }}

    QListWidget#slide_list::item {{
        background-color: transparent;
        border: none;
    }}

    QListWidget#slide_list::item:selected {{
        background-color: transparent;
    }}
    """


class UIThemeManager(QObject):
    """UI 테마 관리자 (싱글톤)"""

    theme_changed = Signal(bool)  # is_dark_mode

    _instance: Optional["UIThemeManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self._is_dark_mode = False
        self._initialized = True

    @property
    def is_dark_mode(self) -> bool:
        return self._is_dark_mode

    @property
    def colors(self) -> UIColors:
        return DARK_COLORS if self._is_dark_mode else LIGHT_COLORS

    def toggle_theme(self):
        """테마 토글"""
        self.set_dark_mode(not self._is_dark_mode)

    def set_dark_mode(self, dark_mode: bool):
        """다크 모드 설정"""
        if self._is_dark_mode == dark_mode:
            return

        self._is_dark_mode = dark_mode
        self._apply_theme()
        self.theme_changed.emit(dark_mode)

    def _apply_theme(self):
        """테마 적용"""
        app = QApplication.instance()
        if app:
            colors = self.colors
            stylesheet = get_stylesheet(colors)
            app.setStyleSheet(stylesheet)

    def apply_initial_theme(self, dark_mode: bool = False):
        """초기 테마 적용"""
        self._is_dark_mode = dark_mode
        self._apply_theme()


def get_ui_theme_manager() -> UIThemeManager:
    """UI 테마 관리자 인스턴스 반환"""
    return UIThemeManager()
