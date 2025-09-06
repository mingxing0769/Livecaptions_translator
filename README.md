# 🧠 本地模型实时字幕翻译器 | Local LLM Live Captions Translator

结合 Windows 11 的 Live Captions 功能与本地大语言模型，实现英文语音字幕的实时翻译，并以中文浮窗形式显示。  
This project integrates Windows 11's Live Captions with a locally deployed LLM to provide real-time translation of English speech into Chinese subtitles.

---

## 📌 项目简介 | Project Overview

本项目通过读取 Windows 实时字幕窗口中的英文内容，调用本地部署的 LLM（如 DeepSeek、Qwen2.5）进行翻译，并以半透明浮窗形式展示中文字幕。  
It captures English text from the Live Captions window, translates it using a local LLM (e.g., DeepSeek, Qwen2.5), and displays the result in a floating Chinese subtitle window.

适用于会议、直播、教学等场景的辅助翻译。  
Ideal for meetings, livestreams, and educational scenarios.

---

## 🖼️ 使用效果预览 | Demo Preview

![中文浮窗字幕演示](images/livecaption_demo.png)

---

## 🚀 功能亮点 | Key Features

- 🎯 实时捕捉 Windows Live Captions 内容  
  Real-time capture of Windows Live Captions

- 🧠 使用本地 LLM 实现上下文感知的精准翻译  
  Context-aware translation using local LLM

- 🖼️ 可定制的字幕窗口（字体、大小、透明度）  
  Customizable subtitle window (font, size, transparency)

- 🔁 翻译缓存机制，避免重复处理  
  Translation caching to avoid redundant processing

- ✂️ 分句优化，支持 NLTK 分词器  
  Sentence segmentation with NLTK support

---

## 🛠️ 环境依赖 | Requirements

- Python 3.8+
- 推荐 GPU：RTX 2060 12G 或更高性能  
  Recommended GPU: RTX 2060 12G or better

安装依赖 | Install dependencies:

```bash
pip install -r requirements.txt
```

首次运行需下载 NLTK 分句器 | First-time setup:

```python
import nltk
nltk.download('punkt')
```

---

## 📁 项目结构 | Project Structure

```
livecaptions_translator/
├── main.py              # 主程序入口 | Main entry point
├── config.py            # 模型与字幕配置 | Configuration
├── translator.py        # 翻译逻辑 | Translation logic
├── subtitlewindow.py    # 字幕窗口显示 | Subtitle window
├── punctuation.py       # 标点重置模块 | Punctuation handler
├── requirements.txt     # 依赖列表 | Dependencies
├── models/              # 存放 GGUF 模型文件 | GGUF model storage
└── README.md            # 项目说明文件 | Project documentation
```

---

## 📦 使用方法 | How to Use

1️⃣ 准备模型文件 | Prepare your model  
Place your GGUF model file in the `models/` folder and set the path in `config.py`:

```python
MODEL_PATH = "models/your_model.gguf"
```

2️⃣ 启用 Windows 实时字幕 | Enable Live Captions  
路径：设置 > 无障碍 > 听力 > 实时字幕  
Language: English (United States)

3️⃣ 启动程序 | Run the program

```bash
python main.py
```

程序将自动：  
The program will automatically:

- 打开 Live Captions（如未打开）  
  Launch Live Captions (if not already open)

- 启动本地模型  
  Start the local LLM

- 捕捉并翻译字幕  
  Capture and translate captions

- 显示中文浮窗字幕  
  Display Chinese subtitles in a floating window

双击字幕窗口可关闭，右上角可调整大小，鼠标滚轮可查看历史记录。  
Double-click to close the window, resize from the corner, and scroll to view history.

---

## ⚙️ 自定义配置 | Customization

在 `config.py` 中可调整以下参数：  
You can modify the following in `config.py`:

- 模型设置（上下文窗口大小、token 限制）  
  Model settings (context size, token limits)

- 字幕窗口样式（字体、颜色、行数、透明度）  
  Subtitle style (font, color, line count, transparency)

- 翻译缓存策略（最大句数、去重逻辑）  
  Translation cache (max sentences, deduplication)

---

## 🧩 注意事项 | Notes

- 模型占用资源较高，建议使用性能较好的硬件  
  High resource usage—use a capable GPU

- 若字幕识别异常或程序无响应，可尝试重启 Live Captions  
  Restart Live Captions if recognition fails

- 当前提示词仅支持英文到中文翻译，可自行扩展其他语言  
  Currently supports English-to-Chinese; extendable to other languages

---

## 📜 许可协议 | License

本项目采用 MIT License，欢迎自由使用、修改与分发。  
Licensed under the MIT License—feel free to use, modify, and distribute.

如有建议或改进，欢迎提交 Issues 或 Pull Requests！  
Suggestions and contributions are welcome via Issues or Pull Requests!



