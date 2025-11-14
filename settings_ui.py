# E:/Python/PythonProject/settings_ui.py
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
    QTextEdit, QLabel, QHBoxLayout, QCheckBox, QGroupBox, QComboBox
)
from PyQt5.QtCore import pyqtSignal
import configparser


class SettingsWindow(QWidget):
    toggle_translation_requested: pyqtSignal = pyqtSignal()
    CONFIG_PATH = 'config.ini'

    def __init__(self):
        super().__init__()

        self.setWindowTitle('实时翻译 - 参数设置 - V_0.05 (API版)')
        self.resize(550, 750)
        self.config_parser = configparser.ConfigParser()

        # --- 创建UI控件 ---
        # [Sever]
        self.base_url_edit = QLineEdit()
        self.api_key_edit = QLineEdit()
        self.model_name_edit = QLineEdit()
        self.model_context_spinbox = QSpinBox()
        self.model_context_spinbox.setRange(512, 65536)
        self.model_context_spinbox.setSingleStep(1024)

        # [COMPLETION_CONFIG]
        self.comp_temp_spinbox = QDoubleSpinBox()
        self.comp_temp_spinbox.setRange(0.0, 2.0)
        self.comp_temp_spinbox.setSingleStep(0.1)
        self.comp_tokens_spinbox = QSpinBox()
        self.comp_tokens_spinbox.setRange(16, 8192)
        self.comp_tokens_spinbox.setSingleStep(64)

        # [LIVE_CONFIG]
        self.live_temp_spinbox = QDoubleSpinBox()
        self.live_temp_spinbox.setRange(0.0, 2.0)
        self.live_temp_spinbox.setSingleStep(0.1)
        self.live_tokens_spinbox = QSpinBox()
        self.live_tokens_spinbox.setRange(16, 8192)
        self.live_tokens_spinbox.setSingleStep(32)

        # [Logic]
        self.available_tokens_spinbox = QSpinBox()
        self.available_tokens_spinbox.setRange(64, 8192)
        self.available_tokens_spinbox.setSingleStep(64)
        self.delay_time_spinbox = QDoubleSpinBox()
        self.delay_time_spinbox.setRange(0.1, 10.0)
        self.delay_time_spinbox.setSingleStep(0.1)
        self.max_input_words_spinbox = QSpinBox()
        self.max_input_words_spinbox.setRange(50,500)
        self.max_input_words_spinbox.setSingleStep(5)

        # [Display_set]
        self.font_family_edit = QLineEdit()
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 72)
        self.display_lines_spinbox = QSpinBox()
        self.display_lines_spinbox.setRange(1, 20)
        self.scrollbar_policy_checkbox = QCheckBox("显示滚动条")
        self.livecaptions_window_policy_checkbox = QCheckBox("隐藏实时辅助字幕窗口")

        # [Prompts]
        self.prompt_selector = QComboBox()
        self.prompt_name_edit = QLineEdit()
        self.prompt_content_edit = QTextEdit()
        self.prompt_content_edit.setAcceptRichText(False)

        # Buttons
        self.save_button = QPushButton("保存")
        self.start_button = QPushButton("开始翻译")
        self.exit_button = QPushButton("退出")

        # 控件列表，用于批量启用/禁用
        self.input_widgets = [
            self.base_url_edit, self.api_key_edit, self.model_name_edit, self.model_context_spinbox,
            self.comp_temp_spinbox, self.comp_tokens_spinbox,
            self.live_temp_spinbox, self.live_tokens_spinbox,
            self.available_tokens_spinbox, self.delay_time_spinbox,self.max_input_words_spinbox,
            self.font_family_edit, self.font_size_spinbox, self.display_lines_spinbox,
            self.scrollbar_policy_checkbox, self.livecaptions_window_policy_checkbox, self.save_button,
            self.prompt_selector, self.prompt_name_edit, self.prompt_content_edit
        ]

        self.setup_layout()
        self.connect_signals()
        self.load_settings()

    def setup_layout(self):
        """使用 QGroupBox 优化布局"""
        main_layout = QVBoxLayout()

        # API Server Group
        api_group = QGroupBox("API 服务器设置")
        api_layout = QFormLayout()
        api_layout.addRow("Base URL:", self.base_url_edit)
        api_layout.addRow("API Key:", self.api_key_edit)
        api_layout.addRow("模型名称:", self.model_name_edit)
        api_layout.addRow("最大上下文:", self.model_context_spinbox)
        api_group.setLayout(api_layout)

        # Translation Config Group
        trans_group = QGroupBox("翻译参数设置")
        trans_layout = QFormLayout()
        trans_layout.addRow("完整句 Temp:", self.comp_temp_spinbox)
        trans_layout.addRow("完整句 Max Tokens:", self.comp_tokens_spinbox)
        trans_layout.addRow("实时句 Temp:", self.live_temp_spinbox)
        trans_layout.addRow("实时句 Max Tokens:", self.live_tokens_spinbox)
        trans_group.setLayout(trans_layout)

        # Logic Group
        logic_group = QGroupBox("逻辑设置")
        logic_layout = QFormLayout()
        logic_layout.addRow("上下文重置阈值:", self.available_tokens_spinbox)
        logic_layout.addRow("翻译间隔 (秒):", self.delay_time_spinbox)
        logic_layout.addRow("输入字数:", self.max_input_words_spinbox)
        logic_group.setLayout(logic_layout)

        # Display Group
        display_group = QGroupBox("显示设置")
        display_layout = QFormLayout()
        display_layout.addRow("字体:", self.font_family_edit)
        display_layout.addRow("字号:", self.font_size_spinbox)
        display_layout.addRow("显示行数:", self.display_lines_spinbox)
        display_layout.addRow(self.scrollbar_policy_checkbox, self.livecaptions_window_policy_checkbox)
        display_group.setLayout(display_layout)

        # Prompt Group
        prompt_group = QGroupBox("系统提示 (Prompt)")
        prompt_layout = QVBoxLayout()
        prompt_selector_layout = QHBoxLayout()
        prompt_selector_layout.addWidget(QLabel("选择模板:"))
        prompt_selector_layout.addWidget(self.prompt_selector)
        prompt_selector_layout.addWidget(QLabel("模板名称:"))
        prompt_selector_layout.addWidget(self.prompt_name_edit)
        prompt_layout.addLayout(prompt_selector_layout)
        prompt_layout.addWidget(self.prompt_content_edit)
        prompt_group.setLayout(prompt_layout)

        main_layout.addWidget(api_group)
        main_layout.addWidget(trans_group)
        main_layout.addWidget(logic_group)
        main_layout.addWidget(display_group)
        main_layout.addWidget(prompt_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.exit_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def connect_signals(self):
        """连接所有信号和槽，实现自动保存"""
        self.start_button.clicked.connect(self.toggle_translation)
        self.save_button.clicked.connect(self.save_settings)
        self.exit_button.clicked.connect(QApplication.instance().quit)

        self.prompt_selector.currentIndexChanged.connect(self.on_prompt_selected)

    def set_controls_enabled(self, enabled: bool):
        """启用或禁用所有输入控件"""
        for widget in self.input_widgets:
            widget.setEnabled(enabled)
        self.exit_button.setEnabled(True)
        self.start_button.setText("开始翻译" if enabled else "停止翻译")

    def toggle_translation(self):
        """处理“开始/停止”按钮的点击事件。"""
        self.save_settings()  # 在启动/停止前，强制保存一次所有设置
        self.toggle_translation_requested.emit()

    def load_settings(self):
        """直接从 config.ini 加载设置，确保UI显示的是最新值"""
        if not self.config_parser.read(self.CONFIG_PATH, encoding='utf-8'):
            print(f"{self.CONFIG_PATH} 未找到。UI将显示默认值。")
            return

        # API
        self.base_url_edit.setText(self.config_parser.get('Sever', 'base_url', fallback=''))
        self.api_key_edit.setText(self.config_parser.get('Sever', 'api_key', fallback=''))
        self.model_name_edit.setText(self.config_parser.get('Sever', 'model', fallback=''))
        self.model_context_spinbox.setValue(self.config_parser.getint('Sever', 'model_context_window', fallback=4096))
        # Completion
        self.comp_temp_spinbox.setValue(self.config_parser.getfloat('COMPLETION_CONFIG', 'temperature', fallback=0.8))
        self.comp_tokens_spinbox.setValue(self.config_parser.getint('COMPLETION_CONFIG', 'max_tokens', fallback=128))
        # Live
        self.live_temp_spinbox.setValue(self.config_parser.getfloat('LIVE_CONFIG', 'temperature', fallback=0.2))
        self.live_tokens_spinbox.setValue(self.config_parser.getint('LIVE_CONFIG', 'max_tokens', fallback=64))
        # Logic
        self.available_tokens_spinbox.setValue(self.config_parser.getint('Logic', 'available_tokens', fallback=256))
        self.delay_time_spinbox.setValue(self.config_parser.getfloat('Logic', 'delay_time', fallback=1.0))
        self.max_input_words_spinbox.setValue(self.config_parser.getint('Logic', 'max_input_words', fallback=300))
        # Display
        self.font_family_edit.setText(self.config_parser.get('Display_set', 'font_family', fallback='微软雅黑'))
        self.font_size_spinbox.setValue(self.config_parser.getint('Display_set', 'font_size', fallback=15))
        self.display_lines_spinbox.setValue(self.config_parser.getint('Display_set', 'display_lines', fallback=3))
        self.scrollbar_policy_checkbox.setChecked(self.config_parser.getboolean('Display_set', 'scrollbarpolicy', fallback=False))
        self.livecaptions_window_policy_checkbox.setChecked(self.config_parser.getboolean('Display_set', 'hide_livecaptions_window', fallback=True))

        # Prompts
        self.prompt_selector.blockSignals(True)
        self.prompt_selector.clear()
        prompt_sections = [s for s in self.config_parser.sections() if s.startswith('Prompt_')]
        for section in prompt_sections:
            self.prompt_selector.addItem(self.config_parser.get(section, 'name', fallback=section), userData=section)

        active_prompt_section = self.config_parser.get('Logic', 'active_prompt', fallback=prompt_sections[0] if prompt_sections else '')
        index = self.prompt_selector.findData(active_prompt_section)
        if index != -1:
            self.prompt_selector.setCurrentIndex(index)
        self.prompt_selector.blockSignals(False)
        self.on_prompt_selected()

    def save_settings(self):
        """将UI上的所有设置保存回 config.ini 文件"""
        try:
            # API
            self.config_parser.set('Sever', 'base_url', self.base_url_edit.text())
            self.config_parser.set('Sever', 'api_key', self.api_key_edit.text())
            self.config_parser.set('Sever', 'model', self.model_name_edit.text())
            self.config_parser.set('Sever', 'model_context_window', str(self.model_context_spinbox.value()))
            # Completion
            self.config_parser.set('COMPLETION_CONFIG', 'temperature', str(self.comp_temp_spinbox.value()))
            self.config_parser.set('COMPLETION_CONFIG', 'max_tokens', str(self.comp_tokens_spinbox.value()))
            # Live
            self.config_parser.set('LIVE_CONFIG', 'temperature', str(self.live_temp_spinbox.value()))
            self.config_parser.set('LIVE_CONFIG', 'max_tokens', str(self.live_tokens_spinbox.value()))
            # Logic
            self.config_parser.set('Logic', 'available_tokens', str(self.available_tokens_spinbox.value()))
            self.config_parser.set('Logic', 'delay_time', str(self.delay_time_spinbox.value()))
            self.config_parser.set('Logic', 'max_input_words', str(self.max_input_words_spinbox.value()))

            # 确保写入的值是字符串
            active_prompt_data = self.prompt_selector.currentData()
            self.config_parser.set('Logic', 'active_prompt', str(active_prompt_data) if active_prompt_data is not None else '')

            # Display
            self.config_parser.set('Display_set', 'font_family', self.font_family_edit.text())
            self.config_parser.set('Display_set', 'font_size', str(self.font_size_spinbox.value()))
            self.config_parser.set('Display_set', 'display_lines', str(self.display_lines_spinbox.value()))
            self.config_parser.set('Display_set', 'scrollbarpolicy', str(self.scrollbar_policy_checkbox.isChecked()))
            self.config_parser.set('Display_set', 'hide_livecaptions_window', str(self.livecaptions_window_policy_checkbox.isChecked()))
            # Prompt
            current_prompt_section = self.prompt_selector.currentData()
            if current_prompt_section:
                self.config_parser.set(current_prompt_section, 'name', self.prompt_name_edit.text())
                content = self.prompt_content_edit.toPlainText()
                formatted_content = '\n|' + '\n|'.join(content.split('\n')) if content else ''
                self.config_parser.set(current_prompt_section, 'content', formatted_content)

            with open(self.CONFIG_PATH, 'w', encoding='utf-8') as f:
                self.config_parser.write(f)
            print(f"配置已保存到 {self.CONFIG_PATH}")
        except Exception as e:
            print(f"错误：保存配置失败！ {e}")

    def on_prompt_selected(self):
        """当用户从下拉框选择新的 prompt 时，更新编辑框内容"""
        current_section = self.prompt_selector.currentData()
        if not current_section:
            return

        # 更新UI，临时禁用信号防止循环触发保存
        widgets_to_block = [self.prompt_name_edit, self.prompt_content_edit]
        for w in widgets_to_block: w.blockSignals(True)

        self.prompt_name_edit.setText(self.config_parser.get(current_section, 'name', fallback=current_section))
        raw_content = self.config_parser.get(current_section, 'content', fallback='').replace('|', '').strip()
        self.prompt_content_edit.setPlainText(raw_content)

        for w in widgets_to_block: w.blockSignals(False)

    def closeEvent(self, event):
        """重写窗口关闭事件，确保在关闭前保存设置。"""
        self.save_settings()
        super().closeEvent(event)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    sys.exit(app.exec())