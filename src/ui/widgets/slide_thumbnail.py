"""슬라이드 썸네일 목록 위젯"""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QLabel,
    QFrame,
    QPushButton,
    QHBoxLayout,
    QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal, QSize

from src.core.presentation import Slide, SlideLayoutType


class SlideThumbnailItem(QFrame):
    """개별 슬라이드 썸네일"""

    def __init__(self, slide_number: int, title: str = "", layout: SlideLayoutType = SlideLayoutType.TITLE_CONTENT):
        super().__init__()
        self.slide_number = slide_number
        self.title = title or f"슬라이드 {slide_number}"
        self.layout_type = layout

        self.setFixedSize(180, 100)
        self.setFrameStyle(QFrame.Shape.Box)
        self._set_default_style()
        self._setup_ui()

    def _set_default_style(self):
        """기본 스타일 설정"""
        self.setProperty("selected", False)
        self.style().unpolish(self)
        self.style().polish(self)

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # 상단: 슬라이드 번호 + 레이아웃 표시
        top_layout = QHBoxLayout()

        self.number_label = QLabel(str(self.slide_number))
        self.number_label.setStyleSheet("font-weight: bold; font-size: 11px;")
        top_layout.addWidget(self.number_label)

        top_layout.addStretch()

        # 레이아웃 표시
        layout_icon = self._get_layout_icon()
        self.layout_label = QLabel(layout_icon)
        self.layout_label.setStyleSheet("font-size: 10px; opacity: 0.6;")
        top_layout.addWidget(self.layout_label)

        layout.addLayout(top_layout)

        # 제목 (축약)
        self.title_label = QLabel(self._truncate_title(self.title))
        self.title_label.setStyleSheet("font-size: 11px;")
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        layout.addStretch()

    def _get_layout_icon(self) -> str:
        """레이아웃 아이콘 반환"""
        icons = {
            SlideLayoutType.TITLE: "[제목]",
            SlideLayoutType.TITLE_CONTENT: "[내용]",
            SlideLayoutType.BULLET_POINTS: "[목록]",
            SlideLayoutType.TITLE_IMAGE: "[이미지]",
            SlideLayoutType.TWO_COLUMN: "[2단]",
        }
        return icons.get(self.layout_type, "")

    def _truncate_title(self, title: str) -> str:
        """제목 축약"""
        if len(title) > 25:
            return title[:22] + "..."
        return title

    def update_data(self, slide_number: int, title: str, layout: SlideLayoutType):
        """데이터 업데이트"""
        self.slide_number = slide_number
        self.title = title
        self.layout_type = layout

        self.number_label.setText(str(slide_number))
        self.title_label.setText(self._truncate_title(title))
        self.layout_label.setText(self._get_layout_icon())

    def set_selected(self, selected: bool):
        """선택 상태 설정"""
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)


class SlideThumbnailList(QWidget):
    """슬라이드 썸네일 목록"""

    slide_selected = Signal(int)  # 슬라이드 선택 시그널
    slide_reordered = Signal(int, int)  # 슬라이드 순서 변경 시그널

    def __init__(self):
        super().__init__()
        self.slides: list[dict] = []
        self.current_index = -1

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(4)

        # 헤더
        header = QLabel("슬라이드")
        header.setStyleSheet("font-weight: bold; font-size: 12px; padding-left: 4px;")
        layout.addWidget(header)

        # 슬라이드 리스트
        self.list_widget = QListWidget()
        self.list_widget.setSpacing(4)
        self.list_widget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.list_widget.currentRowChanged.connect(self._on_selection_changed)
        self.list_widget.model().rowsMoved.connect(self._on_rows_moved)
        self.list_widget.setObjectName("slide_list")
        layout.addWidget(self.list_widget)

        # 버튼 영역
        button_layout = QHBoxLayout()

        add_btn = QPushButton("+")
        add_btn.setFixedSize(32, 32)
        add_btn.setToolTip("슬라이드 추가")
        button_layout.addWidget(add_btn)

        delete_btn = QPushButton("-")
        delete_btn.setFixedSize(32, 32)
        delete_btn.setToolTip("슬라이드 삭제")
        button_layout.addWidget(delete_btn)

        button_layout.addStretch()

        layout.addLayout(button_layout)

    def add_slide(self, title: str = "", content: str = ""):
        """슬라이드 추가 (기본)"""
        slide_number = len(self.slides) + 1
        slide_data = {
            "number": slide_number,
            "title": title or f"슬라이드 {slide_number}",
            "content": content,
            "layout": SlideLayoutType.TITLE_CONTENT,
        }
        self.slides.append(slide_data)
        self._add_thumbnail_item(slide_data)
        self.list_widget.setCurrentRow(len(self.slides) - 1)

    def add_slide_from_data(self, slide: Slide):
        """Slide 객체에서 슬라이드 추가"""
        slide_number = len(self.slides) + 1
        slide_data = {
            "number": slide_number,
            "title": slide.title,
            "content": slide.content,
            "layout": slide.layout,
            "bullet_points": slide.bullet_points,
        }
        self.slides.append(slide_data)
        self._add_thumbnail_item(slide_data)

    def _add_thumbnail_item(self, slide_data: dict):
        """썸네일 아이템 추가"""
        thumbnail = SlideThumbnailItem(
            slide_data["number"],
            slide_data["title"],
            slide_data.get("layout", SlideLayoutType.TITLE_CONTENT),
        )

        item = QListWidgetItem(self.list_widget)
        item.setSizeHint(QSize(160, 108))
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, thumbnail)

    def delete_current_slide(self):
        """현재 선택된 슬라이드 삭제"""
        current_row = self.list_widget.currentRow()
        if current_row >= 0 and len(self.slides) > 0:
            self.slides.pop(current_row)
            self.list_widget.takeItem(current_row)
            self._renumber_slides()

    def clear_slides(self):
        """모든 슬라이드 삭제"""
        self.slides.clear()
        self.list_widget.clear()
        self.current_index = -1

    def select_slide(self, index: int):
        """특정 슬라이드 선택"""
        if 0 <= index < self.list_widget.count():
            self.list_widget.setCurrentRow(index)

    def get_current_index(self) -> int:
        """현재 선택된 슬라이드 인덱스 반환"""
        return self.list_widget.currentRow()

    def update_slide_thumbnail(self, index: int, slide: Slide):
        """슬라이드 썸네일 업데이트"""
        if 0 <= index < self.list_widget.count():
            item = self.list_widget.item(index)
            widget = self.list_widget.itemWidget(item)
            if isinstance(widget, SlideThumbnailItem):
                widget.update_data(index + 1, slide.title, slide.layout)

            # 내부 데이터도 업데이트
            if 0 <= index < len(self.slides):
                self.slides[index]["title"] = slide.title
                self.slides[index]["layout"] = slide.layout

    def _renumber_slides(self):
        """슬라이드 번호 재정렬"""
        for i, slide in enumerate(self.slides):
            slide["number"] = i + 1

        # 썸네일 위젯도 업데이트
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if isinstance(widget, SlideThumbnailItem) and i < len(self.slides):
                widget.update_data(
                    i + 1,
                    self.slides[i]["title"],
                    self.slides[i].get("layout", SlideLayoutType.TITLE_CONTENT),
                )

    def _on_selection_changed(self, row: int):
        """선택 변경 처리"""
        # 이전 선택 해제
        if self.current_index >= 0:
            item = self.list_widget.item(self.current_index)
            if item:
                widget = self.list_widget.itemWidget(item)
                if isinstance(widget, SlideThumbnailItem):
                    widget.set_selected(False)

        # 새 선택
        self.current_index = row
        if row >= 0:
            item = self.list_widget.item(row)
            if item:
                widget = self.list_widget.itemWidget(item)
                if isinstance(widget, SlideThumbnailItem):
                    widget.set_selected(True)

            self.slide_selected.emit(row)

    def _on_rows_moved(self, parent, start, end, destination, row):
        """드래그앤드롭으로 순서 변경됨"""
        if start != row:
            moved_slide = self.slides.pop(start)
            insert_pos = row if row < start else row - 1
            self.slides.insert(insert_pos, moved_slide)
            self._renumber_slides()
            self.slide_reordered.emit(start, insert_pos)

    def count(self) -> int:
        """슬라이드 수 반환"""
        return len(self.slides)

    def get_slide(self, index: int) -> Optional[dict]:
        """특정 슬라이드 데이터 반환"""
        if 0 <= index < len(self.slides):
            return self.slides[index]
        return None

    def get_all_slides(self) -> list[dict]:
        """모든 슬라이드 데이터 반환"""
        return self.slides.copy()
