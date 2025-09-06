## 🧠 本地模型实时字幕翻译器（Live Captions Translator）

> 基于 Windows 11 的 Live Captions 功能，结合本地大语言模型，实现英文语音字幕的实时翻译与中文浮窗显示。

---

### 📌 项目简介

本项目通过读取 Windows 实时字幕窗口中的英文内容，使用本地部署的 LLM（如 DeepSeek、Qwen2.5）进行翻译，并以半透明浮窗形式显示中文字幕。适用于会议、视频、直播等场景的实时辅助翻译。

---

### 🚀 功能亮点

- 🎯 实时捕捉 Windows Live Captions 内容
- 🧠 使用本地 LLM 实现上下文感知的精准翻译
- 🖼️ 可定制的字幕窗口（字体、大小、透明度）
- 🔁 翻译缓存机制，避免重复处理
- ✂️ 分句优化，支持 NLTK 分词器

---

### 🛠️ 环境依赖

- Python 3.8+
- 推荐使用 GPU（如 RTX 2060）或高性能 CPU

安装依赖：

```bash
pip install -r requirements.txt
```

首次运行需下载 NLTK 分句器：

```python
import nltk
nltk.download('punkt')
```

---

### 📁 项目结构

```
livecpations_translator_to_sub/
├── main.py               # 主程序入口
├── config.py             # 模型与字幕配置
├── translator.py         # 翻译逻辑
├── subtitlewindow.py     # 字幕窗口显示
├── punctuation.py        # 标点重置模块
├── requirements.txt      # 依赖列表
├── models/               # 存放 GGUF 模型文件
└── README.md             # 项目说明文件
```

---

### 📦 使用方法

#### 1️⃣ 准备模型文件

将 GGUF 格式的模型文件放入 `models/` 文件夹，并在 `config.py` 中设置路径：

```python
MODEL_PATH = "models/你的模型文件名.gguf"
```

支持任何 llama.cpp 兼容模型。

#### 2️⃣ 启用 Windows 实时字幕

路径：  
`设置 > 无障碍 > 听力 > 实时字幕`  
语言设置为 **英语（美国）**。

#### 3️⃣ 启动程序

```bash
python main.py
```

程序将自动：

- 打开 Live Captions（如未打开）
- 启动本地模型
- 捕捉并翻译字幕
- 显示中文浮窗字幕

双击字幕窗口可关闭，右上角可调整大小，鼠标滚轮可查看历史记录。

---

### ⚙️ 自定义配置

在 `config.py` 中可调整以下参数：

- 模型设置（上下文窗口大小、token 限制）
- 字幕窗口样式（字体、颜色、行数、透明度）
- 翻译缓存策略（最大句数、去重逻辑）

---

### 🧩 注意事项

- 模型占用资源较高，建议使用性能较好的硬件。
- 若字幕识别异常或程序无响应，可尝试重启 Live Captions。
- 当前提示词仅支持英文到中文翻译，可自行扩展其他语言。

---

### 📜 许可协议

本项目采用 MIT License，欢迎自由使用、修改与分发。  
如有建议或改进，欢迎提交 Issues 或 Pull Requests！
