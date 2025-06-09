# livecpations_translator_to_sub
[中文说明]

本代码，使用Windows 11 自带的livecaptions程序识别语音，转录文本后用本地LLM模型翻译后输出到字幕

# 工作流程说明：

# 1.使用llama-cpp-python库加载量化版模型。

  个人建议使用qwen2.5，比较稳定，但翻译不够灵活，可能不太准确。
  
  使用deepseek-v2-lite模型翻译比较准确，但不稳定，会出现各种问题。
  
  其它模型测试不多。
  
# 2.启动windows内置的Livecaptions实时字幕程序
  经过文本处理断句，只返回最后3句。

# 3.模型翻译：

  获取实时字幕程序返回的最后三句，进行处理。
  
  1.已经翻译的中 英文保存到历史信息中。
  
  2.对收到的英文句子（最后一句可能不完整，单独处理），如果没有存在于历史信息中，用模型翻译后保存到历史信息中，并保存到对话历史。
  
  3.最后一句单独翻译，不加入历史信息及模型对话历史，当做即时信息处理。
  
  4.将历史信息中最后几句翻译和即时翻译合并，取最后三句（断句处理后），输出到字幕。

# 4.文本处理：

  1.英文按“.;?!”或使用nltk.sent_tokenize 库进行断句，各有千秋，都不是完全准确，目前暂用sent_tokenize库进行断句
  
    注：标点以Livecaptions自动生成的，并没有后续添加。有时Livecaptions会生成很长都没有标点的句子，会增加模型翻译的延时。可以和断句模型处理，但不稳定，所以暂时没加上。
    
  2.中文按“。；？！”进行断句，仅用时字幕显示，最后三句，避免显示文本太多。

# 5.对话历史维护。

  模型的对话历史，设置为小于模型设置的n_ctx * 75% total_tokens大于n_ctx*0.75时 仅保留最后3组对话及系统指令。

# 流程循环为：
  1.Livecaptions文本 --> 2.文本处理得到最后三句 --> 3.模型翻译（判断输入，翻译历史信息存储、对话信息处理，字幕文本处理) --> 4.输出到字幕程序 --> 1.

# 总体延时，
  正常情况下(Livecaptions断句合理),关键在翻译模型处理时间，目前最少设置为1秒，如果本地GPU处理能力强，可以看情况设置，但意义不大，因为0.5秒内可能就增加一两个单词，只会增加电费。

[EN]:

# Live Captions Translator to Subtitles  

This tool utilizes Windows 11's built-in Live Captions for speech recognition, transcribes the text, and translates it using a local LLM before outputting subtitles.  

## Workflow  

### 1. Model Loading  
- Uses `llama-cpp-python` to load a quantized LLM.  
- **Recommended models:**  
  - **Qwen2.5**: More stable but less flexible in translation (may be inaccurate).  
  - **Deepseek-v2-lite**: More accurate but prone to instability.  
  - Other models have limited testing.  

### 2. Live Captions Processing  
- Launches Windows' Live Captions and processes the text to extract the last **3 sentences**.  

### 3. Translation Process  
1. **History Storage**: Translated Chinese/English pairs are saved in history.  
2. **New Sentences**:  
   - If an English sentence (last one may be incomplete) isn’t in history, the model translates and stores it.  
3. **Last Sentence Handling**:  
   - Translated separately as real-time text (not added to history or model context).  
4. **Output**: Combines the latest translations (from history) and real-time translation, then displays the last **3 processed sentences** as subtitles.  

### 4. Text Segmentation  
- **English**: Split using `.;?!` or `nltk.sent_tokenize` (currently default).  
  - *Note*: Live Captions generates punctuation natively. Long, unpunctuated sentences may delay translation.  
- **Chinese**: Split by `。；？！` and limited to the last **3 sentences** for cleaner subtitles.  

### 5. Context Management  
- Model context is capped at **75% of `n_ctx` tokens**.  
- If exceeded, only the last **3 exchanges + system instructions** are retained.  

## Loop  
1. Live Captions → 2. Extract last 3 sentences → 3. Translate (history/real-time) → 4. Output subtitles → (Repeat)  

## Latency  
- Primary delay comes from model translation (minimum **1-second interval**).  
- GPU power can reduce this, but sub-0.5s updates may only add minor words at higher power cost.  
