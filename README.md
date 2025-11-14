# 实时同声传译工具 (Real-time Simultaneous Interpretation Tool)

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/UI-PyQt5-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

本项目是一个运行于 Windows 平台的桌面应用程序，旨在提供实时的同声传译功能。它能够捕捉系统内置“实时辅助字幕”功能所转录的英文文本，将其发送至一个大型语言模型（LLM）进行翻译，并将翻译结果显示在一个可自定义的、置顶的字幕窗口中。

![项目截图](https://github.com/mingxing0769/Livecaptions_translator/blob/main/images/livecaption_demo.png)

![项目截图](https://github.com/mingxing0769/Livecaptions_translator/blob/main/images/ui.png)


---

## ✨ 主要功能

- **实时捕捉**: 从 Windows 11 的“实时辅助字幕”功能中实时获取系统音频的转录文本。
- **通用 API 支持**: 可连接到任何兼容 OpenAI API 规范的语言模型服务（如 LM Studio, Ollama, 或其他本地/云端 API）。
- **自定义字幕窗口**: 提供一个可自由移动、缩放、背景透明的置顶字幕窗口，不干扰其他工作。
- **图形化设置界面**: 拥有完整的设置窗口，用于管理 API 连接、模型参数、显示样式以及翻译逻辑。
- **多场景提示词**: 支持多个可切换的系统提示词（System Prompt），以适应不同的翻译场景（例如：通用翻译、F1 赛事解说）。
- **智能文本处理**: 内置先进的上下文锚点算法，能够智能处理连续、修正、跳跃的实时文本流，确保翻译的连贯性。
- **独立打包**: 支持使用 PyInstaller 打包成单个 `.exe` 文件，方便在任何 Windows 电脑上分发和使用，无需安装 Python 环境。

## 📋 环境要求

- **操作系统**: Windows 11 (项目依赖其内置的“实时辅助字幕”功能)。
- **Python**: 3.9 或更高版本。
- **LLM 服务**: 一个可访问的、兼容 OpenAI API 的语言模型服务。

## 🚀 安装与配置

#### 1. 克隆项目

#### 2. 创建并激活虚拟环境

#### 3. 安装依赖

项目所需的所有依赖都已在 `requirements.txt` 文件中列出。


#### 4. 下载 NLTK 数据包

项目使用 NLTK 库进行英文分句，需要下载 `punkt` 数据模型。


#### 5. 配置 `config.ini`

在首次运行前，请打开项目根目录下的 `config.ini` 文件，并至少完成以下核心配置：
你可以根据需要调整 [Sever] [COMPLETION_CONFIG], [LIVE_CONFIG], [Prompt_...] 等其他部分的参数

## ▶️ 如何使用

1.  确保你的语言模型服务正在运行。
2.  在 Windows 中启动“实时辅助字幕”（快捷键 `Win + Ctrl + L`）。
3.  运行主程序：main.py
4.  程序会首先启动“参数设置”窗口。检查配置无误后，点击 **“开始翻译”**。
5.  一个半透明的字幕窗口会出现在屏幕上，开始显示实时翻译结果。
6.  你可以随时在设置窗口中修改参数，点击 **“保存”**，然后“停止”再“开始”翻译以应用新设置。

## 📦 打包为 .exe

如果你希望将项目打包成一个独立的可执行文件，可以按照以下步骤操作：

1.  确保 `pyinstaller` 已安装：pip install pyinstaller
2.  找到 NLTK `punkt` 数据包的本地路径。运行 `find_nltk_path.py` 脚本： python find_nltk_path.py
    复制输出的完整路径。
    "C:\Users\***\AppData\Roaming\nltk_data\tokenizers\punkt"    

3.  在项目根目录执行以下打包命令（**请务必将 NLTK 路径替换为你自己的**）：
    **示例:**
     pyinstaller --name "实时翻译" --onefile --windowed --icon="logo/t.png" --add-data "config.ini;." --add-data "C:\Users\***\AppData\Roaming\nltk_data\tokenizers\punkt;nltk_data/tokenizers/punkt" main.py

    
## 📄 许可证


本项目采用 MIT License 授权。


