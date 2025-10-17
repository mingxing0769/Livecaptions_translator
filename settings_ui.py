# E:/Python/PythonProject/settings_ui.py

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
    QTextEdit, QFileDialog, QLabel, QHBoxLayout, QCheckBox
)

from PyQt5.QtCore import pyqtSignal
import configparser


class SettingsWindow(QWidget):
    toggle_translation_requested: pyqtSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle('实时翻译 - 参数设置 - V_0.04')
        self.resize(550, 750)

        # --- 创建UI控件 ---
        # [LLM]
        self.model_path_edit = QLineEdit()
        self.browse_button = QPushButton("浏览...")
        self.gpu_layers_spinbox = QSpinBox()
        self.gpu_layers_spinbox.setRange(-1, 200)
        self.n_ctx_spinbox = QSpinBox()
        self.n_ctx_spinbox.setRange(512, 65536)
        self.n_ctx_spinbox.setSingleStep(1024)
        self.flash_attn_checkbox = QCheckBox("Flash Attention")
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
        # [Display_set]
        self.font_family_edit = QLineEdit()
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 72)
        self.display_lines_spinbox = QSpinBox()
        self.display_lines_spinbox.setRange(1, 20)
        self.scrollbar_policy_checkbox = QCheckBox("显示滚动条")
        self.livecaptions_window_policy_checkbox = QCheckBox("隐藏实时辅助字幕窗口")

        # [Prompt]
        self.sys_prompt_edit = QTextEdit()
        self.sys_prompt_edit.setAcceptRichText(False)
        # Buttons
        self.save_button = QPushButton("保存")
        self.start_button = QPushButton("开始翻译")
        self.exit_button = QPushButton("退出")
        self.input_widgets = [
            self.model_path_edit, self.browse_button, self.gpu_layers_spinbox,
            self.n_ctx_spinbox, self.flash_attn_checkbox, self.comp_temp_spinbox,
            self.comp_tokens_spinbox, self.live_temp_spinbox, self.live_tokens_spinbox,
            self.available_tokens_spinbox, self.delay_time_spinbox, self.font_family_edit,
            self.font_size_spinbox, self.display_lines_spinbox, self.scrollbar_policy_checkbox,
            self.livecaptions_window_policy_checkbox,
            self.sys_prompt_edit, self.save_button
        ]

        # --- 布局  ---
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
        model_layout = QHBoxLayout()
        model_layout.addWidget(self.model_path_edit)
        model_layout.addWidget(self.browse_button)
        llm_adv_layout = QHBoxLayout()
        llm_adv_layout.addWidget(QLabel("GPU层数:"))
        llm_adv_layout.addWidget(self.gpu_layers_spinbox)
        llm_adv_layout.addStretch()
        llm_adv_layout.addWidget(QLabel("上下文长度(n_ctx):"))
        llm_adv_layout.addWidget(self.n_ctx_spinbox)
        llm_adv_layout.addStretch()
        llm_adv_layout.addWidget(self.flash_attn_checkbox)
        form_layout.addRow(QLabel("<b>LLM 模型设置</b>"))
        form_layout.addRow("模型路径:", model_layout)
        form_layout.addRow(llm_adv_layout)

        # --- 添加空行 ---
        form_layout.addRow(QLabel())

        comp_layout = QHBoxLayout()
        comp_layout.addWidget(QLabel("温度(Temp):"))
        comp_layout.addWidget(self.comp_temp_spinbox)
        comp_layout.addStretch()
        comp_layout.addWidget(QLabel("最大Token数:"))
        comp_layout.addWidget(self.comp_tokens_spinbox)
        comp_layout.addStretch()
        form_layout.addRow(QLabel("<b>完整句子翻译 设置 (Completion)</b>"))
        form_layout.addRow(comp_layout)

        # --- 添加空行 ---
        form_layout.addRow(QLabel())

        live_layout = QHBoxLayout()
        live_layout.addWidget(QLabel("温度(Temp):"))
        live_layout.addWidget(self.live_temp_spinbox)
        live_layout.addStretch()
        live_layout.addWidget(QLabel("最大Token数:"))
        live_layout.addWidget(self.live_tokens_spinbox)
        live_layout.addStretch()
        form_layout.addRow(QLabel("<b>即时句子翻译 设置 (Live)</b>"))
        form_layout.addRow(live_layout)

        # --- 添加空行 ---
        form_layout.addRow(QLabel())

        logic_layout = QHBoxLayout()
        logic_layout.addWidget(QLabel("n_ctx重置余量:"))
        logic_layout.addWidget(self.available_tokens_spinbox)
        logic_layout.addStretch()
        logic_layout.addWidget(QLabel("翻译间隔(秒):"))
        logic_layout.addWidget(self.delay_time_spinbox)
        logic_layout.addStretch()
        form_layout.addRow(QLabel("<b>翻译逻辑设置</b>"))
        form_layout.addRow(logic_layout)

        # --- 添加空行 ---
        form_layout.addRow(QLabel())


        display_font_layout = QHBoxLayout()
        display_font_layout.addWidget(QLabel("字体:"))
        display_font_layout.addWidget(self.font_family_edit)
        display_font_layout.addStretch()
        display_font_layout.addWidget(QLabel("字号:"))
        display_font_layout.addWidget(self.font_size_spinbox)
        display_font_layout.addStretch()
        display_lines_layout = QHBoxLayout()
        display_lines_layout.addWidget(QLabel("显示行数:"))
        display_lines_layout.addWidget(self.display_lines_spinbox)
        display_lines_layout.addStretch()
        display_lines_layout.addWidget(self.livecaptions_window_policy_checkbox)
        display_lines_layout.addStretch()
        display_lines_layout.addWidget(self.scrollbar_policy_checkbox)
        form_layout.addRow(QLabel("<b>显示设置</b>"))
        form_layout.addRow(display_font_layout)
        form_layout.addRow(display_lines_layout)

        # --- 添加空行 ---
        form_layout.addRow(QLabel())

        form_layout.addRow(QLabel("<b>系统提示 (Prompt)</b>"))
        form_layout.addRow(self.sys_prompt_edit)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.exit_button)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        # --- 连接信号和槽 ---
        self.browse_button.clicked.connect(self.select_model_file)
        self.save_button.clicked.connect(self.save)
        self.start_button.clicked.connect(self.toggle_translation)
        self.exit_button.clicked.connect(QApplication.instance().quit)

        # --- 从 config.ini 加载当前配置 ---
        self.load_settings()

    def set_controls_enabled(self, enabled: bool):
        """启用或禁用所有输入控件"""
        for widget in self.input_widgets:
            widget.setEnabled(enabled)

        self.exit_button.setEnabled(True)

        if enabled:
            self.start_button.setText("开始翻译")
        else:
            self.start_button.setText("停止翻译")

    def toggle_translation(self):
        """处理“开始/停止”按钮的点击事件。"""
        self.save_settings()
        self.toggle_translation_requested.emit()

    def load_settings(self):
        """直接从 config.ini 加载设置，确保UI显示的是最新值"""
        parser = configparser.ConfigParser()
        config_path = 'config.ini'
        if not parser.read(config_path, encoding='utf-8'):
            print(f"{config_path} 未找到。UI将显示默认值。")
            return
        self.model_path_edit.setText(parser.get('LLM', 'model_path', fallback=''))
        self.gpu_layers_spinbox.setValue(parser.getint('LLM', 'n_gpu_layers', fallback=0))
        self.n_ctx_spinbox.setValue(parser.getint('LLM', 'n_ctx', fallback=4096))
        self.flash_attn_checkbox.setChecked(parser.getboolean('LLM', 'flash_attn', fallback=False))
        self.comp_temp_spinbox.setValue(parser.getfloat('COMPLETION_CONFIG', 'temperature', fallback=0.6))
        self.comp_tokens_spinbox.setValue(parser.getint('COMPLETION_CONFIG', 'max_tokens', fallback=128))
        self.live_temp_spinbox.setValue(parser.getfloat('LIVE_CONFIG', 'temperature', fallback=0.3))
        self.live_tokens_spinbox.setValue(parser.getint('LIVE_CONFIG', 'max_tokens', fallback=64))
        self.available_tokens_spinbox.setValue(parser.getint('Logic', 'AVAILABLE_TOKENS', fallback=256))
        self.delay_time_spinbox.setValue(parser.getfloat('Logic', 'delay_time', fallback=1.0))
        self.font_family_edit.setText(parser.get('Display_set', 'FONT_FAMILY', fallback='微软雅黑'))
        self.font_size_spinbox.setValue(parser.getint('Display_set', 'FONT_SIZE', fallback=16))
        self.display_lines_spinbox.setValue(parser.getint('Display_set', 'DISPLAY_LINES', fallback=3))
        self.scrollbar_policy_checkbox.setChecked(parser.getboolean('Display_set', 'ScrollBarPolicy', fallback=False))
        self.livecaptions_window_policy_checkbox.setChecked(parser.getboolean('Display_set', 'hide_livecaptions_window', fallback=False))
        raw_prompt = parser.get('Prompt', 'sys_prompt', fallback='').replace('|', '').strip()
        self.sys_prompt_edit.setPlainText(raw_prompt)


    def save_settings(self):
        """将UI上的所有设置保存回 config.ini 文件"""
        try:
            parser = configparser.ConfigParser()
            config_path = 'config.ini'
            parser.read(config_path, encoding='utf-8')
            sections = ['LLM', 'COMPLETION_CONFIG', 'LIVE_CONFIG', 'Logic', 'Display_set', 'Prompt']
            for section in sections:
                if not parser.has_section(section):
                    parser.add_section(section)
            parser.set('LLM', 'model_path', self.model_path_edit.text())
            parser.set('LLM', 'n_gpu_layers', str(self.gpu_layers_spinbox.value()))
            parser.set('LLM', 'n_ctx', str(self.n_ctx_spinbox.value()))
            parser.set('LLM', 'flash_attn', str(self.flash_attn_checkbox.isChecked()))
            parser.set('COMPLETION_CONFIG', 'temperature', str(self.comp_temp_spinbox.value()))
            parser.set('COMPLETION_CONFIG', 'max_tokens', str(self.comp_tokens_spinbox.value()))
            parser.set('LIVE_CONFIG', 'temperature', str(self.live_temp_spinbox.value()))
            parser.set('LIVE_CONFIG', 'max_tokens', str(self.live_tokens_spinbox.value()))
            parser.set('Logic', 'AVAILABLE_TOKENS', str(self.available_tokens_spinbox.value()))
            parser.set('Logic', 'delay_time', str(self.delay_time_spinbox.value()))
            parser.set('Display_set', 'FONT_FAMILY', self.font_family_edit.text())
            parser.set('Display_set', 'FONT_SIZE', str(self.font_size_spinbox.value()))
            parser.set('Display_set', 'DISPLAY_LINES', str(self.display_lines_spinbox.value()))
            parser.set('Display_set', 'ScrollBarPolicy', str(self.scrollbar_policy_checkbox.isChecked()))
            parser.set('Display_set', 'hide_livecaptions_window', str(self.livecaptions_window_policy_checkbox.isChecked()))
            sys_prompt = self.sys_prompt_edit.toPlainText()
            if sys_prompt:
                formatted_prompt = '\n|' + '\n|'.join(sys_prompt.split('\n'))
            else:
                formatted_prompt = ''
            parser.set('Prompt', 'sys_prompt', formatted_prompt)

            with open(config_path, 'w', encoding='utf-8') as f:
                parser.write(f)
            print(f"配置已成功保存到 {config_path}")
        except Exception as e:
            print(f"错误：保存配置失败！ {e}")


    def select_model_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择 GGUF 模型文件", "", "GGUF Files (*.gguf)")
        if file_path:
            self.model_path_edit.setText(file_path)


    def save(self):
        self.save_settings()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    sys.exit(app.exec())