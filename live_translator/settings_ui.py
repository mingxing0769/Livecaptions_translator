import configparser

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .config import CONFIG_PATH, SERVER_SECTION, load_config, normalize_config, write_config


class SettingsWindow(QWidget):
    toggle_translation_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("实时翻译 - 参数设置")
        self.resize(720, 620)
        self.setMinimumSize(640, 560)
        self.config_parser = configparser.ConfigParser()

        self.base_url_edit = QLineEdit()
        self.api_key_edit = QLineEdit()
        self.model_name_edit = QLineEdit()
        self.model_context_spinbox = QSpinBox()
        self.model_context_spinbox.setRange(512, 81920)
        self.model_context_spinbox.setSingleStep(1024)

        self.comp_temp_spinbox = QDoubleSpinBox()
        self.comp_temp_spinbox.setRange(0.0, 2.0)
        self.comp_temp_spinbox.setSingleStep(0.1)
        self.comp_tokens_spinbox = QSpinBox()
        self.comp_tokens_spinbox.setRange(16, 8192)
        self.comp_tokens_spinbox.setSingleStep(64)

        self.live_temp_spinbox = QDoubleSpinBox()
        self.live_temp_spinbox.setRange(0.0, 2.0)
        self.live_temp_spinbox.setSingleStep(0.1)
        self.live_tokens_spinbox = QSpinBox()
        self.live_tokens_spinbox.setRange(16, 8192)
        self.live_tokens_spinbox.setSingleStep(32)

        self.available_tokens_spinbox = QSpinBox()
        self.available_tokens_spinbox.setRange(64, 8192)
        self.available_tokens_spinbox.setSingleStep(64)
        self.delay_time_spinbox = QDoubleSpinBox()
        self.delay_time_spinbox.setRange(0.1, 10.0)
        self.delay_time_spinbox.setSingleStep(0.1)
        self.max_input_words_spinbox = QSpinBox()
        self.max_input_words_spinbox.setRange(50, 2000)
        self.max_input_words_spinbox.setSingleStep(50)

        self.font_family_edit = QLineEdit()
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 72)
        self.display_lines_spinbox = QSpinBox()
        self.display_lines_spinbox.setRange(1, 20)
        self.scrollbar_policy_checkbox = QCheckBox("显示滚动条")
        self.livecaptions_window_policy_checkbox = QCheckBox("隐藏 实时辅助字幕")

        self.prompt_selector = QComboBox()
        self.prompt_name_edit = QLineEdit()
        self.prompt_content_edit = QTextEdit()
        self.prompt_content_edit.setAcceptRichText(False)

        self.token_progress = QProgressBar()
        self.token_progress.setTextVisible(True)
        self.token_label = QLabel("当前上下文: 0 / 0 Tokens")
        self.status_label = QLabel("就绪")
        self.status_label.setObjectName("statusLabel")

        self.save_button = QPushButton("保存")
        self.start_button = QPushButton("开始翻译")
        self.start_button.setObjectName("primaryButton")
        self.exit_button = QPushButton("退出")

        self.input_widgets = [
            self.base_url_edit,
            self.api_key_edit,
            self.model_name_edit,
            self.model_context_spinbox,
            self.comp_temp_spinbox,
            self.comp_tokens_spinbox,
            self.live_temp_spinbox,
            self.live_tokens_spinbox,
            self.available_tokens_spinbox,
            self.delay_time_spinbox,
            self.max_input_words_spinbox,
            self.font_family_edit,
            self.font_size_spinbox,
            self.display_lines_spinbox,
            self.scrollbar_policy_checkbox,
            self.livecaptions_window_policy_checkbox,
            self.save_button,
            self.prompt_selector,
            self.prompt_name_edit,
            self.prompt_content_edit,
        ]

        self.apply_style()
        self.setup_layout()
        self.connect_signals()
        self.load_settings()

    def apply_style(self) -> None:
        self.setStyleSheet("""
            QWidget {
                background: #f6f7f9;
                color: #1f2937;
                font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI";
                font-size: 13px;
            }
            QGroupBox {
                background: #ffffff;
                border: 1px solid #dfe3ea;
                border-radius: 8px;
                margin-top: 18px;
                padding: 16px 14px 14px 14px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #334155;
                background: #f6f7f9;
            }
            QLabel {
                background: transparent;
            }
            QLabel#statusLabel {
                color: #0f172a;
                font-weight: 600;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
                background: #ffffff;
                border: 1px solid #ccd3dd;
                border-radius: 6px;
                padding: 6px 8px;
                selection-background-color: #2563eb;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus {
                border-color: #2563eb;
            }
            QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled,
            QComboBox:disabled, QTextEdit:disabled, QCheckBox:disabled {
                color: #8792a2;
                background: #eef1f5;
            }
            QTextEdit {
                line-height: 1.35;
            }
            QTabWidget::pane {
                border: 1px solid #dfe3ea;
                border-radius: 8px;
                background: #ffffff;
                top: -1px;
            }
            QTabBar::tab {
                background: #e9edf3;
                color: #475569;
                border: 1px solid #d6dce6;
                border-bottom: none;
                padding: 8px 18px;
                margin-right: 4px;
                border-top-left-radius: 7px;
                border-top-right-radius: 7px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #0f172a;
                font-weight: 600;
            }
            QProgressBar {
                border: 1px solid #d1d8e3;
                border-radius: 6px;
                background: #eef2f7;
                height: 18px;
                text-align: center;
                color: #1f2937;
            }
            QProgressBar::chunk {
                border-radius: 5px;
                background: #16a34a;
            }
            QPushButton {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 7px 18px;
                min-width: 78px;
            }
            QPushButton:hover {
                background: #f1f5f9;
                border-color: #94a3b8;
            }
            QPushButton:pressed {
                background: #e2e8f0;
            }
            QPushButton#primaryButton {
                color: white;
                background: #2563eb;
                border-color: #2563eb;
                font-weight: 600;
            }
            QPushButton#primaryButton:hover {
                background: #1d4ed8;
                border-color: #1d4ed8;
            }
            QCheckBox {
                spacing: 8px;
                background: transparent;
            }
        """)

    def setup_layout(self) -> None:
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(14, 14, 14, 12)
        main_layout.setSpacing(12)

        header_layout = QHBoxLayout()
        title_label = QLabel("实时翻译控制台")
        title_label.setStyleSheet("font-size: 20px; font-weight: 700; color: #0f172a;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)
        main_layout.addLayout(header_layout)

        monitor_group = QGroupBox("实时状态")
        monitor_layout = QVBoxLayout()
        monitor_layout.setSpacing(8)
        monitor_layout.addWidget(self.token_label)
        monitor_layout.addWidget(self.token_progress)
        monitor_group.setLayout(monitor_layout)
        main_layout.addWidget(monitor_group)

        tabs = QTabWidget()
        tabs.addTab(self.build_server_tab(), "连接")
        tabs.addTab(self.build_translation_tab(), "翻译")
        tabs.addTab(self.build_display_tab(), "显示")
        tabs.addTab(self.build_prompt_tab(), "提示词")
        main_layout.addWidget(tabs, 1)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.exit_button)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def build_server_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 10, 12, 12)

        api_group = QGroupBox("API 服务器")
        api_layout = QFormLayout()
        self.tune_form(api_layout)
        api_layout.addRow("Base URL:", self.base_url_edit)
        api_layout.addRow("API Key:", self.api_key_edit)
        api_layout.addRow("模型名称:", self.model_name_edit)
        api_layout.addRow("最大上下文:", self.model_context_spinbox)
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        layout.addStretch()
        return tab

    def build_translation_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 10, 12, 12)

        trans_group = QGroupBox("模型参数")
        trans_layout = QFormLayout()
        self.tune_form(trans_layout)
        trans_layout.addRow("完整句 Temp:", self.comp_temp_spinbox)
        trans_layout.addRow("完整句 Max Tokens:", self.comp_tokens_spinbox)
        trans_layout.addRow("实时句 Temp:", self.live_temp_spinbox)
        trans_layout.addRow("实时句 Max Tokens:", self.live_tokens_spinbox)
        trans_group.setLayout(trans_layout)

        logic_group = QGroupBox("处理逻辑")
        logic_layout = QFormLayout()
        self.tune_form(logic_layout)
        logic_layout.addRow("上下文压缩阈值(Token预留):", self.available_tokens_spinbox)
        logic_layout.addRow("翻译间隔 (秒):", self.delay_time_spinbox)
        logic_layout.addRow("最大输入单词数:", self.max_input_words_spinbox)
        logic_group.setLayout(logic_layout)
        layout.addWidget(trans_group)
        layout.addWidget(logic_group)
        layout.addStretch()
        return tab

    def build_display_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 10, 12, 12)

        display_group = QGroupBox("显示设置")
        display_layout = QFormLayout()
        self.tune_form(display_layout)
        display_layout.addRow("字体:", self.font_family_edit)
        display_layout.addRow("字号:", self.font_size_spinbox)
        display_layout.addRow("显示行数:", self.display_lines_spinbox)
        display_layout.addRow(self.scrollbar_policy_checkbox, self.livecaptions_window_policy_checkbox)
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        layout.addStretch()
        return tab

    def build_prompt_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 10, 12, 12)
        prompt_group = QGroupBox("系统提示 (Prompt)")
        prompt_layout = QVBoxLayout()
        prompt_layout.setSpacing(10)
        prompt_selector_layout = QHBoxLayout()
        prompt_selector_layout.setSpacing(8)
        prompt_selector_layout.addWidget(QLabel("选择模板:"))
        prompt_selector_layout.addWidget(self.prompt_selector)
        prompt_selector_layout.addWidget(QLabel("模板名称:"))
        prompt_selector_layout.addWidget(self.prompt_name_edit)
        prompt_layout.addLayout(prompt_selector_layout)
        prompt_layout.addWidget(self.prompt_content_edit)
        prompt_group.setLayout(prompt_layout)
        layout.addWidget(prompt_group, 1)
        return tab

    @staticmethod
    def tune_form(layout: QFormLayout) -> None:
        layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.setFormAlignment(Qt.AlignLeft)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(10)
        layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

    def connect_signals(self) -> None:
        self.start_button.clicked.connect(self.toggle_translation)
        self.save_button.clicked.connect(self.save_settings)
        self.exit_button.clicked.connect(QApplication.instance().quit)
        self.prompt_selector.currentIndexChanged.connect(self.on_prompt_selected)

    def load_settings(self) -> None:
        app_config = load_config(CONFIG_PATH)
        self.config_parser = app_config.parser
        self.base_url_edit.setText(app_config.server.base_url)
        self.api_key_edit.setText(app_config.server.api_key)
        self.model_name_edit.setText(app_config.server.model)
        self.model_context_spinbox.setValue(app_config.server.model_context_window)
        self.comp_temp_spinbox.setValue(float(app_config.completion_config.get("temperature", 0.8)))
        self.comp_tokens_spinbox.setValue(int(app_config.completion_config.get("max_tokens", 512)))
        self.live_temp_spinbox.setValue(float(app_config.live_config.get("temperature", 0.6)))
        self.live_tokens_spinbox.setValue(int(app_config.live_config.get("max_tokens", 512)))
        self.available_tokens_spinbox.setValue(app_config.logic.available_tokens)
        self.delay_time_spinbox.setValue(app_config.logic.delay_time)
        self.max_input_words_spinbox.setValue(app_config.logic.max_input_words)
        self.font_family_edit.setText(app_config.display.font_family)
        self.font_size_spinbox.setValue(app_config.display.font_size)
        self.display_lines_spinbox.setValue(app_config.display.display_lines)
        self.scrollbar_policy_checkbox.setChecked(app_config.display.scrollbar_policy)
        self.livecaptions_window_policy_checkbox.setChecked(app_config.display.hide_livecaptions_window)

        self.prompt_selector.blockSignals(True)
        self.prompt_selector.clear()
        for section in app_config.prompt_sections():
            self.prompt_selector.addItem(
                self.config_parser.get(section, "name", fallback=section),
                userData=section,
            )
        index = self.prompt_selector.findData(app_config.logic.active_prompt)
        if index != -1:
            self.prompt_selector.setCurrentIndex(index)
        self.prompt_selector.blockSignals(False)
        self.on_prompt_selected()

    def save_settings(self) -> None:
        normalize_config(self.config_parser)
        self.config_parser.set(SERVER_SECTION, "base_url", self.base_url_edit.text())
        self.config_parser.set(SERVER_SECTION, "api_key", self.api_key_edit.text())
        self.config_parser.set(SERVER_SECTION, "model", self.model_name_edit.text())
        self.config_parser.set(SERVER_SECTION, "model_context_window", str(self.model_context_spinbox.value()))
        self.config_parser.set("COMPLETION_CONFIG", "temperature", str(self.comp_temp_spinbox.value()))
        self.config_parser.set("COMPLETION_CONFIG", "max_tokens", str(self.comp_tokens_spinbox.value()))
        self.config_parser.set("LIVE_CONFIG", "temperature", str(self.live_temp_spinbox.value()))
        self.config_parser.set("LIVE_CONFIG", "max_tokens", str(self.live_tokens_spinbox.value()))
        self.config_parser.set("Logic", "available_tokens", str(self.available_tokens_spinbox.value()))
        self.config_parser.set("Logic", "delay_time", str(self.delay_time_spinbox.value()))
        self.config_parser.set("Logic", "max_input_words", str(self.max_input_words_spinbox.value()))
        self.config_parser.set("Logic", "active_prompt", str(self.prompt_selector.currentData() or ""))
        self.config_parser.set("Display_set", "font_family", self.font_family_edit.text())
        self.config_parser.set("Display_set", "font_size", str(self.font_size_spinbox.value()))
        self.config_parser.set("Display_set", "display_lines", str(self.display_lines_spinbox.value()))
        self.config_parser.set("Display_set", "scrollbarpolicy", str(self.scrollbar_policy_checkbox.isChecked()))
        self.config_parser.set(
            "Display_set",
            "hide_livecaptions_window",
            str(self.livecaptions_window_policy_checkbox.isChecked()),
        )

        current_prompt_section = self.prompt_selector.currentData()
        if current_prompt_section:
            self.config_parser.set(current_prompt_section, "name", self.prompt_name_edit.text())
            self.config_parser.set(current_prompt_section, "content", self.prompt_content_edit.toPlainText())
        write_config(self.config_parser, CONFIG_PATH)
        self.set_status("配置已保存")

    def toggle_translation(self) -> None:
        self.save_settings()
        self.toggle_translation_requested.emit()

    def set_controls_enabled(self, enabled: bool) -> None:
        for widget in self.input_widgets:
            widget.setEnabled(enabled)
        self.exit_button.setEnabled(True)
        self.start_button.setText("开始翻译" if enabled else "停止翻译")

    def update_token_usage(self, current: int, total: int) -> None:
        self.token_progress.setMaximum(total)
        self.token_progress.setValue(min(current, total))
        self.token_label.setText(f"当前上下文: {current} / {total} Tokens")
        percentage = (current / total) * 100 if total > 0 else 0
        if percentage > 85:
            color = "#ff4d4d"
        elif percentage > 60:
            color = "#ffa64d"
        else:
            color = "#4CAF50"
        self.token_progress.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")

    def set_status(self, message: str, is_error: bool = False) -> None:
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #c62828;" if is_error else "")

    def on_prompt_selected(self) -> None:
        current_section = self.prompt_selector.currentData()
        if not current_section:
            return
        self.prompt_name_edit.blockSignals(True)
        self.prompt_content_edit.blockSignals(True)
        self.prompt_name_edit.setText(self.config_parser.get(current_section, "name", fallback=current_section))
        self.prompt_content_edit.setPlainText(self.config_parser.get(current_section, "content", fallback=""))
        self.prompt_name_edit.blockSignals(False)
        self.prompt_content_edit.blockSignals(False)

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)
