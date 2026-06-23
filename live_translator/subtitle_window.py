from queue import Queue

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QGraphicsDropShadowEffect,
    QSizeGrip,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .config import AppConfig


class SubtitleWindow(QWidget):
    def __init__(self, config: AppConfig, text_data: Queue):
        super().__init__()
        self.config = config
        self.text_data = text_data
        self.background_widget = None
        self.size_grip = None
        self.drag_position = None
        self.text_display = None
        self.setup_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_text)
        self.timer.start(config.display.update_interval_ms)

    def setup_ui(self) -> None:
        display = self.config.display
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(display.x, display.y, display.width, display.height)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.background_widget = QWidget()
        self.background_widget.setStyleSheet(
            f"background-color: rgba({display.background_color}); border-radius: 5px;"
        )
        self.background_widget.setMaximumWidth(display.max_window_width)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(3, 3)
        self.background_widget.setGraphicsEffect(shadow)
        main_layout.addWidget(self.background_widget)

        inner_layout = QVBoxLayout(self.background_widget)
        inner_layout.setContentsMargins(15, 10, 15, 10)

        self.size_grip = QSizeGrip(self.background_widget)
        inner_layout.addWidget(self.size_grip, 0, Qt.AlignTop | Qt.AlignRight)

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setTextInteractionFlags(Qt.NoTextInteraction)
        self.text_display.setFont(QFont(display.font_family, display.font_size))
        self.text_display.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded if display.scrollbar_policy else Qt.ScrollBarAlwaysOff
        )
        self.text_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        font_metrics = self.text_display.fontMetrics()
        initial_height = int(font_metrics.lineSpacing() * display.display_lines) + 4
        self.text_display.setMinimumHeight(initial_height)
        self.text_display.setStyleSheet("""
            QTextEdit {
                color: white;
                background-color: transparent;
                border: none;
                padding: 0px;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.4);
                min-height: 25px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.7);
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        inner_layout.addWidget(self.text_display)

    def update_text(self) -> None:
        latest = None
        while not self.text_data.empty():
            latest = self.text_data.get()
        if latest is None:
            return

        text_block = latest.get("subtitle", "") if isinstance(latest, dict) else str(latest)
        if self.text_display.toPlainText() == text_block:
            return

        scrollbar = self.text_display.verticalScrollBar()
        is_at_bottom = scrollbar.value() >= scrollbar.maximum() - 2
        self.text_display.setText(text_block)
        if is_at_bottom:
            scrollbar.setValue(scrollbar.maximum())

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.size_grip.geometry().contains(event.pos()):
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            else:
                self.drag_position = None

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)

    def mouseReleaseEvent(self, event):
        self.drag_position = None

