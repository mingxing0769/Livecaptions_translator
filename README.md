## `README.md`

````markdown
# 单模型实时字幕翻译器（Single-Model Live Caption Translator）

## 项目简介 | Project Overview

本项目是一个基于本地大语言模型（如 DeepSeek、Qwen2.5）实现的**英文语音字幕实时翻译工具**。它通过读取 Windows 实时字幕（Live Captions）窗口中的英文内容，分句处理后发送给本地模型翻译，最终以半透明字幕的形式显示中文结果。适合会议、视频或直播内容的实时辅助翻译。

This project is a **real-time English-to-Chinese subtitle translator** based on local large language models. It captures text from Windows Live Captions, sends it to the local LLM (e.g., DeepSeek, Qwen2.5) for translation, and displays Chinese subtitles in a semi-transparent overlay.

---

## 功能特点 | Features

- 🎯 实时捕捉 Windows 实时字幕内容
- 🧠 使用本地 LLM 进行上下文感知的精准翻译
- 🖼️ 可定制的浮动字幕窗口（字体、尺寸、透明度等）
- 🧩 多句缓存机制，避免重复翻译
- 📈 分词优化与句子识别（支持 NLTK）

---

## 环境依赖 | Requirements

确保使用 Python 3.8+。以下依赖可通过 pip 安装：

```bash
pip install -r requirements.txt
````

`requirements.txt` 示例：

```
pyqt5
pywinauto
nltk
llama-cpp-python
```

> ⚠️ 初次运行需下载 `punkt` 分句器：

```python
import nltk
nltk.download('punkt')
```

---

## 文件结构 | File Structure

```text
.
├── 单模型翻译.py           # 主程序，启动翻译和字幕显示逻辑
├── config.py              # 配置文件，模型、字幕UI、LLM参数等
├── models/                # 存放本地量化的 GGUF 模型文件
└── README.md              # 本文件
```

---

## 使用方法 | Usage

### 1️⃣ 准备模型文件

将 GGUF 格式的模型文件放入 `models/` 文件夹，并修改 `config.py` 中的路径：

```python
MODEL_PATH = 'models/deepseek-v2-lite-chat-q4_k_m.gguf'
```

支持任何 llama.cpp 兼容模型。

### 2️⃣ 启动 Windows 实时字幕

前往设置：
**设置 > 无障碍 > 听力 > 实时字幕**
启用并设置为 **“英语 (美国)”**。

### 3️⃣ 运行程序

```bash
python 单模型翻译.py
```

程序将自动：

* 打开 Live Captions（如未打开）
* 启动本地 LLM
* 捕捉并翻译字幕
* 显示浮动中文翻译窗口

---

## 注意事项 | Notes

* 请确认 `config.py` 中的路径与你的实际环境一致：

  * `caption_path`: Live Captions 的路径（Windows 11 默认无需修改）
  * `model_path`: 本地模型路径
* 模型占用较高，建议使用性能较好的 CPU 或 GPU 环境。
* 若字幕识别异常或程序无响应，请尝试关闭并重启实时字幕。
* 当前仅支持英文到中文翻译（后续可拓展为双向翻译）。

---

## 自定义配置 | Customization

可在 `config.py` 中调整以下内容：

* 🔧 模型设置（上下文窗口、token设置）
* 🎨 字幕窗口大小、字体、颜色、行数
* 🧠 翻译缓存策略、最大句数等

---

## 许可协议 | License

MIT License - 可自由修改、使用和分发。

---

## 联系方式 | Contact

欢迎提出建议或参与改进本项目。

Issues | Discussions | Pull Requests 欢迎提交 🙌

