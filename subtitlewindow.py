from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizeGrip, QTextEdit, QSizePolicy, \
    QGraphicsDropShadowEffect

import config

class SubtitleWindow(QWidget):
    def __init__(self, text_data):
        super().__init__()
        self.background_widget = None
        self.size_grip = None
        self.drag_position = None
        self.text_display = None

        self.text_data = text_data
        self.setup_ui()

        self.timer: QTimer = QTimer()
        self.timer.timeout.connect(self.update_text)
        self.timer.start(config.UPDATE_INTERVAL_MS)

    def setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(*config.INITIAL_WINDOW_GEOMETRY)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.background_widget = QWidget()
        self.background_widget.setStyleSheet(f"""
            background-color: rgba{config.BACKGROUND_COLOR};
            border-radius: 5px;
        """)
        self.background_widget.setMaximumWidth(config.MAX_WINDOW_WIDTH)

        # 添加阴影效果
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(3, 3)
        self.background_widget.setGraphicsEffect(shadow)

        main_layout.addWidget(self.background_widget)

        inner_layout = QVBoxLayout(self.background_widget)
        inner_layout.setContentsMargins(15, 10, 15, 10)

        # 创建尺寸调节控件
        self.size_grip = QSizeGrip(self.background_widget)
        inner_layout.addWidget(self.size_grip, 0, Qt.AlignTop | Qt.AlignRight)

        # 创建文本显示控件
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setTextInteractionFlags(Qt.NoTextInteraction)
        self.text_display.setFont(QFont(config.FONT_FAMILY, config.FONT_SIZE))

        #是否显示 滚动条
        if config.ScrollBarPolicy:
            self.text_display.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        else:
            self.text_display.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # 设置尺寸策略
        self.text_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 设置初始高度
        font_metrics = self.text_display.fontMetrics()
        initial_height = int(font_metrics.height() * config.DISPLAY_LINES)
        self.text_display.setMinimumHeight(initial_height)

        # 设置样式
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

    def update_text(self):
        """更新文本并实现智能滚动"""
        if not self.text_data.empty():
            scrollbar = self.text_display.verticalScrollBar()
            is_at_bottom = scrollbar.value() >= scrollbar.maximum() - 2

            # 仅当有新内容时才更新
            text_block = self.text_data.get()
            if self.text_display.toPlainText() != text_block:
                self.text_display.setText(text_block)

                if is_at_bottom:
                    scrollbar.setValue(scrollbar.maximum())

    # 在 SubtitleWindow 类中
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 只要鼠标不在尺寸调节器上，就启动拖动
            if not self.size_grip.geometry().contains(event.pos()):
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            else:
                self.drag_position = None  # 确保在点击size_grip时不拖动

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)

    def mouseReleaseEvent(self, event):
        self.drag_position = None

    def mouseDoubleClickEvent(self, event):
        """双击关闭窗口"""
        if event.button() == Qt.LeftButton:
            self.close()

    def resizeEvent(self, event):
        super().resizeEvent(event)

