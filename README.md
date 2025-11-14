# 实时同声传译工具 (Real-time Simultaneous Interpretation Tool)

## 🚀 安装与配置

### 1. 克隆项目
```bash
git clone https://github.com/mingxing0769/Livecaptions_translator.git
cd Livecaptions_translator
```

### 2. 创建并激活虚拟环境
```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

### 3. 安装依赖
项目所需的所有依赖都已在 `requirements.txt` 文件中列出：
```bash
pip install -r requirements.txt
```

### 4. 下载 NLTK 数据包
项目使用 NLTK 库进行英文分句，需要下载 `punkt` 数据模型：
```python
import nltk
nltk.download('punkt')
```

### 5. 配置 `config.ini`
在首次运行前，请打开项目根目录下的 `config.ini` 文件，并至少完成以下核心配置：
- [Server]
- [COMPLETION_CONFIG]
- [LIVE_CONFIG]
- [Prompt_...]

你可以根据需要调整其他参数。

---

## ▶️ 使用方法

1. 确保你的语言模型服务正在运行  
2. 运行主程序：
   ```bash
   python main.py
   ```
3. 程序会启动“参数设置”窗口，检查配置无误后点击 **开始翻译**  
4. 一个半透明的字幕窗口会出现在屏幕上，显示实时翻译结果  
5. 你可以随时在设置窗口中修改参数，点击 **保存**，然后“停止”再“开始”翻译以应用新设置  

---

## 📦 打包为 .exe

如果你希望将项目打包成一个独立的可执行文件，可以按照以下步骤操作：

1. 确保 `pyinstaller` 已安装：
   ```bash
   pip install pyinstaller
   ```
2. 找到 NLTK `punkt` 数据包的本地路径，运行：
   ```bash
   python find_nltk_path.py
   ```
   复制输出的完整路径，如：
   ```
   C:\Users\***\AppData\Roaming\nltk_data\tokenizers\punkt
   ```
3. 在项目根目录执行以下打包命令（请替换为你自己的路径）：
   ```bash
   pyinstaller --name "实时翻译" --onefile --windowed --icon="logo/t.png" \
   --add-data "config.ini;." \
   --add-data "C:\Users\***\AppData\Roaming\nltk_data\tokenizers\punkt;nltk_data/tokenizers/punkt" \
   main.py
   ```

### 打包好的文件下载：
[实时翻译.zip](https://kkioikk.top/实时翻译.zip)

---

## 📄 许可证
本项目采用 **MIT License** 授权。
```

---

这样排版后，README 会更清晰、易读，GitHub 上也会显示漂亮的标题、代码块和分隔线。  

要不要我帮你再加一个 **中英文双语版本**，让国际用户也能快速上手？

