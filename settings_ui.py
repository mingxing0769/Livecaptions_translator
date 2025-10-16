# E:/Python/PythonProject/settings_ui.py

import re
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
    QTextEdit, QFileDialog, QLabel, QHBoxLayout
)
from PyQt5.QtCore import pyqtSignal
import config  # 导入配置以读取默认值


class SettingsWindow(QWidget):
    # 定义一个信号，当用户点击“开始”时发射
    start_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle('实时翻译 - 参数设置 - V_0.01')
        self.setFixedSize(500, 400)  # 固定窗口大小

        # --- 创建UI控件 ---
        # 模型路径
        self.model_path_edit = QLineEdit()
        self.browse_button = QPushButton("浏览...")

        # GPU层数
        self.gpu_layers_spinbox = QSpinBox()
        self.gpu_layers_spinbox.setRange(-1, 100)  # -1 表示全部

        # 翻译间隔
        self.delay_time_spinbox = QDoubleSpinBox()
        self.delay_time_spinbox.setRange(0.1, 10.0)
        self.delay_time_spinbox.setSingleStep(0.1)

        # 系统提示
        self.sys_prompt_edit = QTextEdit()
        self.sys_prompt_edit.setAcceptRichText(False)

        # 开始和退出按钮
        self.save_button = QPushButton("保存")
        self.start_button = QPushButton("开始翻译")
        self.exit_button = QPushButton("退出")

        # --- 加载当前配置 ---
        self.load_settings()

        # --- 布局 ---
        main_layout = QVBoxLayout()
        form_layout = QFormLayout()

        model_layout = QHBoxLayout()
        model_layout.addWidget(self.model_path_edit)
        model_layout.addWidget(self.browse_button)

        form_layout.addRow(QLabel("<b>LLM 模型设置</b>"))
        form_layout.addRow("模型路径:", model_layout)
        form_layout.addRow("GPU层数:", self.gpu_layers_spinbox)

        form_layout.addRow(QLabel("<b>翻译逻辑设置</b>"))
        form_layout.addRow("翻译间隔 (秒):", self.delay_time_spinbox)
        form_layout.addRow("系统提示 (Prompt):", self.sys_prompt_edit)

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
        self.start_button.clicked.connect(self.start_translation)
        self.exit_button.clicked.connect(QApplication.instance().quit)

    def load_settings(self):
        """从 config.py 加载设置并显示在UI上"""
        self.model_path_edit.setText(config.LLAMA_CONFIG.get('model_path', ''))
        self.gpu_layers_spinbox.setValue(config.LLAMA_CONFIG.get('n_gpu_layers', 0))
        self.delay_time_spinbox.setValue(config.DELAY_TIME)
        self.sys_prompt_edit.setPlainText(config.SYS_PROMPT)

    def save_settings(self):
        """将UI上的设置保存回 config.py 文件 (更安全版本)"""
        try:
            with open('config.py', 'r', encoding='utf-8') as f:
                content = f.read()

            # --- 使用 lambda 表达式进行绝对安全的正则替换 ---

            # 模型路径
            model_path_str = self.model_path_edit.text()
            # 使用 lambda 确保 model_path_str 被当作纯文本
            content = re.sub(
                r"('model_path':\s*').*?(')",
                lambda m: m.group(1) + model_path_str.replace('\\', '\\\\') + m.group(2),
                content
            )

            # GPU层数
            gpu_layers = self.gpu_layers_spinbox.value()
            content = re.sub(
                r"('n_gpu_layers':\s*)-?\d+",
                lambda m: m.group(1) + str(gpu_layers),
                content
            )

            # 翻译间隔
            delay_time = self.delay_time_spinbox.value()
            content = re.sub(
                r"(DELAY_TIME\s*=\s*)[\d.]+",
                lambda m: m.group(1) + str(delay_time),
                content
            )

            # 系统提示
            sys_prompt = self.sys_prompt_edit.toPlainText()
            content = re.sub(
                r'(SYS_PROMPT\s*=\s*r""")[\s\S]*?(""")',
                lambda m: m.group(1) + sys_prompt + m.group(2),
                content,
                flags=re.DOTALL
            )

            with open('config.py', 'w', encoding='utf-8') as f:
                f.write(content)

            print("配置已成功保存到 config.py")

        except Exception as e:
            print(f"错误：保存配置失败！ {e}")

    def select_model_file(self):
        """打开文件对话框选择模型"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 GGUF 模型文件", "", "GGUF Files (*.gguf)"
        )
        if file_path:
            self.model_path_edit.setText(file_path)

    def save(self):
        """保存设置"""
        self.save_settings()

    def start_translation(self):
        """发射信号，并关闭自己"""
        self.start_requested.emit()
        self.close()  # 自动隐藏UI


if __name__ == '__main__':
    # 用于独立测试UI
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    sys.exit(app.exec())