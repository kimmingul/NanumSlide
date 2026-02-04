"""NanumSlide 애플리케이션 진입점"""

import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from src.ui.main_window import MainWindow
from src.ui.ui_theme import get_ui_theme_manager


def main():
    """애플리케이션 시작"""
    # High DPI 지원
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    # 애플리케이션 정보 설정
    app.setApplicationName("NanumSlide")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("NanumSlide")

    # 기본 폰트 설정 (한글 지원)
    font = QFont("Malgun Gothic", 10)
    app.setFont(font)

    # UI 테마 적용 (기본: 라이트 모드)
    theme_manager = get_ui_theme_manager()
    theme_manager.apply_initial_theme(dark_mode=False)

    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
