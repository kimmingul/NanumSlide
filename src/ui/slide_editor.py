"""슬라이드 에디터 위젯"""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QLineEdit,
    QTextEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QComboBox,
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QPainter, QColor, QFont, QPixmap, QImage
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from src.core.presentation import Slide, SlideLayoutType
from src.core.themes import Theme


class SlidePreview(QFrame):
    """슬라이드 미리보기 캔버스"""

    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")

        # 16:9 비율
        self.aspect_ratio = 16 / 9
        self.setMinimumSize(640, 360)

        self.title = ""
        self.subtitle = ""
        self.content = ""
        self.bullet_points: list[str] = []
        self.layout_type = SlideLayoutType.TITLE_CONTENT
        self.theme_color = "#007acc"

        # 이미지 관련
        self.image_url: Optional[str] = None
        self.image_pixmap: Optional[QPixmap] = None
        self.network_manager = QNetworkAccessManager()
        self.network_manager.finished.connect(self._on_image_loaded)

    def resizeEvent(self, event):
        """크기 변경 시 비율 유지"""
        super().resizeEvent(event)
        parent = self.parent()
        if parent:
            available_width = parent.width() - 40
            available_height = parent.height() - 40

            if available_width / self.aspect_ratio <= available_height:
                new_width = available_width
                new_height = int(available_width / self.aspect_ratio)
            else:
                new_height = available_height
                new_width = int(available_height * self.aspect_ratio)

            self.setFixedSize(max(480, new_width), max(270, new_height))

    def paintEvent(self, event):
        """슬라이드 렌더링"""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 배경
        painter.fillRect(self.rect(), QColor("#ffffff"))

        # 레이아웃에 따른 렌더링
        if self.layout_type == SlideLayoutType.TITLE:
            self._draw_title_slide(painter)
        elif self.layout_type == SlideLayoutType.BULLET_POINTS:
            self._draw_bullet_slide(painter)
        else:
            self._draw_content_slide(painter)

        painter.end()

    def _draw_title_slide(self, painter: QPainter):
        """제목 슬라이드 렌더링"""
        w, h = self.width(), self.height()

        # 악센트 바
        painter.fillRect(0, int(h * 0.45), w, 4, QColor(self.theme_color))

        # 제목 (중앙 정렬)
        title_font = QFont("Malgun Gothic", int(h * 0.08), QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor("#333333"))

        title_rect = painter.fontMetrics().boundingRect(self.title)
        x = (w - title_rect.width()) // 2
        y = int(h * 0.4)
        painter.drawText(x, y, self.title)

        # 부제목
        if self.subtitle:
            subtitle_font = QFont("Malgun Gothic", int(h * 0.04))
            painter.setFont(subtitle_font)
            painter.setPen(QColor("#666666"))

            subtitle_rect = painter.fontMetrics().boundingRect(self.subtitle)
            x = (w - subtitle_rect.width()) // 2
            y = int(h * 0.55)
            painter.drawText(x, y, self.subtitle)

    def _draw_content_slide(self, painter: QPainter):
        """제목+내용 슬라이드 렌더링"""
        w, h = self.width(), self.height()
        margin = int(w * 0.05)

        # 제목
        title_font = QFont("Malgun Gothic", int(h * 0.06), QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor("#333333"))
        painter.drawText(margin, int(h * 0.12), self.title)

        # 제목 아래 라인
        painter.setPen(QColor(self.theme_color))
        painter.drawLine(margin, int(h * 0.16), w - margin, int(h * 0.16))

        # 이미지가 있으면 오른쪽에 표시
        content_width = w - margin * 2
        if self.image_pixmap:
            image_width = int(w * 0.4)
            image_height = int(h * 0.5)
            image_x = w - margin - image_width
            image_y = int(h * 0.22)

            # 이미지를 비율 유지하며 그리기
            scaled_pixmap = self.image_pixmap.scaled(
                image_width, image_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            img_x = image_x + (image_width - scaled_pixmap.width()) // 2
            img_y = image_y + (image_height - scaled_pixmap.height()) // 2
            painter.drawPixmap(img_x, img_y, scaled_pixmap)

            # 텍스트 영역 줄이기
            content_width = int(w * 0.45)

        # 내용
        content_font = QFont("Malgun Gothic", int(h * 0.035))
        painter.setFont(content_font)
        painter.setPen(QColor("#444444"))

        y = int(h * 0.25)
        line_height = int(h * 0.06)
        for line in self.content.split("\n")[:10]:
            # 텍스트가 content_width를 초과하면 잘라내기
            if len(line) > 40 and self.image_pixmap:
                line = line[:37] + "..."
            painter.drawText(margin, y, line)
            y += line_height

    def _draw_bullet_slide(self, painter: QPainter):
        """글머리 기호 슬라이드 렌더링"""
        w, h = self.width(), self.height()
        margin = int(w * 0.05)

        # 제목
        title_font = QFont("Malgun Gothic", int(h * 0.06), QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor("#333333"))
        painter.drawText(margin, int(h * 0.12), self.title)

        # 제목 아래 라인
        painter.setPen(QColor(self.theme_color))
        painter.drawLine(margin, int(h * 0.16), w - margin, int(h * 0.16))

        # 이미지가 있으면 오른쪽에 표시
        max_bullet_width = w - margin * 2
        if self.image_pixmap:
            image_width = int(w * 0.35)
            image_height = int(h * 0.55)
            image_x = w - margin - image_width
            image_y = int(h * 0.22)

            scaled_pixmap = self.image_pixmap.scaled(
                image_width, image_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            img_x = image_x + (image_width - scaled_pixmap.width()) // 2
            img_y = image_y + (image_height - scaled_pixmap.height()) // 2
            painter.drawPixmap(img_x, img_y, scaled_pixmap)

            max_bullet_width = int(w * 0.5)

        # 글머리 기호
        content_font = QFont("Malgun Gothic", int(h * 0.04))
        painter.setFont(content_font)
        painter.setPen(QColor("#444444"))

        y = int(h * 0.26)
        line_height = int(h * 0.08)
        bullet_margin = int(w * 0.08)

        for bullet in self.bullet_points[:8]:
            # 불릿 포인트
            painter.setBrush(QColor(self.theme_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(margin, y - int(h * 0.015), int(h * 0.02), int(h * 0.02))

            # 텍스트 (이미지가 있으면 잘라내기)
            painter.setPen(QColor("#444444"))
            text = bullet
            if self.image_pixmap and len(text) > 30:
                text = text[:27] + "..."
            painter.drawText(bullet_margin, y, text)
            y += line_height

    def set_slide_data(self, slide: Slide):
        """슬라이드 데이터 설정"""
        self.title = slide.title
        self.subtitle = slide.subtitle
        self.content = slide.content
        self.bullet_points = slide.bullet_points
        self.layout_type = slide.layout

        # 이미지 로드
        new_image_url = slide.image_url
        if new_image_url != self.image_url:
            self.image_url = new_image_url
            self.image_pixmap = None
            if self.image_url:
                self._load_image(self.image_url)

        self.update()

    def _load_image(self, url: str):
        """URL에서 이미지 로드"""
        request = QNetworkRequest(QUrl(url))
        self.network_manager.get(request)

    def _on_image_loaded(self, reply: QNetworkReply):
        """이미지 로드 완료 처리"""
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            image = QImage()
            if image.loadFromData(data):
                self.image_pixmap = QPixmap.fromImage(image)
                self.update()
        else:
            print(f"이미지 로드 실패: {reply.errorString()}")
        reply.deleteLater()

    def clear(self):
        """초기화"""
        self.title = ""
        self.subtitle = ""
        self.content = ""
        self.bullet_points = []
        self.layout_type = SlideLayoutType.TITLE_CONTENT
        self.image_url = None
        self.image_pixmap = None
        self.update()

    def set_theme_color(self, color: str):
        """테마 색상 설정"""
        self.theme_color = color
        self.update()


class SlideEditor(QWidget):
    """슬라이드 에디터"""

    slide_changed = Signal(dict)  # 슬라이드 변경 시그널

    def __init__(self):
        super().__init__()
        self.current_slide: Optional[Slide] = None
        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 상단: 미리보기 영역
        preview_container = QWidget()
        preview_container.setObjectName("preview_container")
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(20, 20, 20, 10)

        # 미리보기 캔버스
        preview_scroll = QScrollArea()
        preview_scroll.setWidgetResizable(True)
        preview_scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_scroll.setObjectName("preview_scroll")

        preview_widget = QWidget()
        preview_widget_layout = QVBoxLayout(preview_widget)
        preview_widget_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.preview = SlidePreview()
        preview_widget_layout.addWidget(self.preview)

        preview_scroll.setWidget(preview_widget)
        preview_layout.addWidget(preview_scroll)

        layout.addWidget(preview_container, stretch=2)

        # 하단: 편집 영역
        edit_container = QWidget()
        edit_container.setObjectName("edit_container")
        edit_layout = QVBoxLayout(edit_container)
        edit_layout.setContentsMargins(20, 15, 20, 15)
        edit_layout.setSpacing(10)

        # 레이아웃 선택
        layout_row = QHBoxLayout()
        layout_row.addWidget(QLabel("레이아웃:"))
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["제목 슬라이드", "제목 + 내용", "글머리 기호", "제목 + 이미지"])
        self.layout_combo.currentIndexChanged.connect(self._on_layout_changed)
        layout_row.addWidget(self.layout_combo)
        layout_row.addStretch()
        edit_layout.addLayout(layout_row)

        # 제목 입력
        title_row = QHBoxLayout()
        title_row.addWidget(QLabel("제목:"))
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("슬라이드 제목을 입력하세요")
        self.title_edit.textChanged.connect(self._on_title_changed)
        title_row.addWidget(self.title_edit)
        edit_layout.addLayout(title_row)

        # 부제목 입력 (제목 슬라이드용)
        self.subtitle_row = QHBoxLayout()
        self.subtitle_row.addWidget(QLabel("부제목:"))
        self.subtitle_edit = QLineEdit()
        self.subtitle_edit.setPlaceholderText("부제목을 입력하세요")
        self.subtitle_edit.textChanged.connect(self._on_subtitle_changed)
        self.subtitle_row.addWidget(self.subtitle_edit)

        self.subtitle_widget = QWidget()
        self.subtitle_widget.setLayout(self.subtitle_row)
        edit_layout.addWidget(self.subtitle_widget)

        # 내용 입력 (스택 위젯으로 전환)
        self.content_stack = QStackedWidget()

        # 일반 내용 편집기
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addWidget(QLabel("내용:"))
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("슬라이드 내용을 입력하세요")
        self.content_edit.setMaximumHeight(100)
        self.content_edit.textChanged.connect(self._on_content_changed)
        content_layout.addWidget(self.content_edit)
        self.content_stack.addWidget(content_widget)

        # 글머리 기호 편집기
        bullet_widget = QWidget()
        bullet_layout = QVBoxLayout(bullet_widget)
        bullet_layout.setContentsMargins(0, 0, 0, 0)

        bullet_header = QHBoxLayout()
        bullet_header.addWidget(QLabel("글머리 기호:"))
        add_bullet_btn = QPushButton("+ 항목 추가")
        add_bullet_btn.clicked.connect(self._add_bullet_point)
        bullet_header.addWidget(add_bullet_btn)
        bullet_header.addStretch()
        bullet_layout.addLayout(bullet_header)

        self.bullet_list = QListWidget()
        self.bullet_list.setMaximumHeight(120)
        self.bullet_list.itemChanged.connect(self._on_bullet_changed)
        bullet_layout.addWidget(self.bullet_list)

        self.content_stack.addWidget(bullet_widget)

        edit_layout.addWidget(self.content_stack)

        layout.addWidget(edit_container, stretch=1)

    def load_slide(self, slide: Slide):
        """슬라이드 로드"""
        self.current_slide = slide

        # 편집 위젯 업데이트 (시그널 블록)
        self.title_edit.blockSignals(True)
        self.subtitle_edit.blockSignals(True)
        self.content_edit.blockSignals(True)
        self.layout_combo.blockSignals(True)

        self.title_edit.setText(slide.title)
        self.subtitle_edit.setText(slide.subtitle)
        self.content_edit.setPlainText(slide.content)

        # 레이아웃 콤보박스 설정
        layout_index = {
            SlideLayoutType.TITLE: 0,
            SlideLayoutType.TITLE_CONTENT: 1,
            SlideLayoutType.BULLET_POINTS: 2,
            SlideLayoutType.TITLE_IMAGE: 3,
        }.get(slide.layout, 1)
        self.layout_combo.setCurrentIndex(layout_index)

        # 글머리 기호 로드
        self.bullet_list.clear()
        for bullet in slide.bullet_points:
            item = QListWidgetItem(bullet)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            self.bullet_list.addItem(item)

        self.title_edit.blockSignals(False)
        self.subtitle_edit.blockSignals(False)
        self.content_edit.blockSignals(False)
        self.layout_combo.blockSignals(False)

        # UI 상태 업데이트
        self._update_ui_for_layout(slide.layout)

        # 미리보기 업데이트
        self.preview.set_slide_data(slide)

    def clear(self):
        """편집기 초기화"""
        self.current_slide = None

        self.title_edit.blockSignals(True)
        self.subtitle_edit.blockSignals(True)
        self.content_edit.blockSignals(True)

        self.title_edit.clear()
        self.subtitle_edit.clear()
        self.content_edit.clear()
        self.bullet_list.clear()
        self.layout_combo.setCurrentIndex(1)

        self.title_edit.blockSignals(False)
        self.subtitle_edit.blockSignals(False)
        self.content_edit.blockSignals(False)

        self.preview.clear()

    def get_slide_data(self) -> dict:
        """현재 슬라이드 데이터 반환"""
        bullet_points = []
        for i in range(self.bullet_list.count()):
            item = self.bullet_list.item(i)
            if item and item.text().strip():
                bullet_points.append(item.text())

        return {
            "title": self.title_edit.text(),
            "subtitle": self.subtitle_edit.text(),
            "content": self.content_edit.toPlainText(),
            "bullet_points": bullet_points,
        }

    def _update_ui_for_layout(self, layout_type: SlideLayoutType):
        """레이아웃에 따른 UI 업데이트"""
        # 제목 슬라이드: 부제목 표시, 내용 숨김
        if layout_type == SlideLayoutType.TITLE:
            self.subtitle_widget.show()
            self.content_stack.hide()
        # 글머리 기호: 부제목 숨김, 글머리 기호 편집기
        elif layout_type == SlideLayoutType.BULLET_POINTS:
            self.subtitle_widget.hide()
            self.content_stack.show()
            self.content_stack.setCurrentIndex(1)
        # 기타: 부제목 숨김, 일반 내용 편집기
        else:
            self.subtitle_widget.hide()
            self.content_stack.show()
            self.content_stack.setCurrentIndex(0)

    def _on_layout_changed(self, index: int):
        """레이아웃 변경"""
        layout_map = {
            0: SlideLayoutType.TITLE,
            1: SlideLayoutType.TITLE_CONTENT,
            2: SlideLayoutType.BULLET_POINTS,
            3: SlideLayoutType.TITLE_IMAGE,
        }
        layout_type = layout_map.get(index, SlideLayoutType.TITLE_CONTENT)

        if self.current_slide:
            self.current_slide.layout = layout_type
            self._update_ui_for_layout(layout_type)
            self.preview.set_slide_data(self.current_slide)
            self._emit_change()

    def _on_title_changed(self, text: str):
        """제목 변경"""
        if self.current_slide:
            self.current_slide.title = text
            self.preview.set_slide_data(self.current_slide)
            self._emit_change()

    def _on_subtitle_changed(self, text: str):
        """부제목 변경"""
        if self.current_slide:
            self.current_slide.subtitle = text
            self.preview.set_slide_data(self.current_slide)
            self._emit_change()

    def _on_content_changed(self):
        """내용 변경"""
        if self.current_slide:
            self.current_slide.content = self.content_edit.toPlainText()
            self.preview.set_slide_data(self.current_slide)
            self._emit_change()

    def _on_bullet_changed(self, item: QListWidgetItem):
        """글머리 기호 변경"""
        if self.current_slide:
            self.current_slide.bullet_points = []
            for i in range(self.bullet_list.count()):
                list_item = self.bullet_list.item(i)
                if list_item and list_item.text().strip():
                    self.current_slide.bullet_points.append(list_item.text())
            self.preview.set_slide_data(self.current_slide)
            self._emit_change()

    def _add_bullet_point(self):
        """글머리 기호 추가"""
        item = QListWidgetItem("새 항목")
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.bullet_list.addItem(item)
        self.bullet_list.editItem(item)

        if self.current_slide:
            self.current_slide.bullet_points.append("새 항목")
            self.preview.set_slide_data(self.current_slide)
            self._emit_change()

    def _emit_change(self):
        """변경 시그널 발생"""
        self.slide_changed.emit(self.get_slide_data())

    def set_theme(self, theme: Theme):
        """테마 적용"""
        self.preview.set_theme_color(theme.colors.primary)
