# find_nltk_path.py
import nltk

# 这会找到 punkt tokenizer 所在的文件夹
punkt_path = nltk.data.find("tokenizers/punkt")
print(f"NLTK 'punkt' 文件夹的完整路径是:\n{punkt_path}")


# pyinstaller --name "实时翻译" --onefile --windowed --icon="logo/t.png" --add-data "config.ini;." --add-data "C:\Users\28206\AppData\Roaming\nltk_data\tokenizers\punkt;nltk_data/tokenizers/punkt" main.py