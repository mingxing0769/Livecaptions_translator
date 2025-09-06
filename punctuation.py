from transformers import pipeline
import re


class PunctuationModel:
    def __init__(self, model_id="models/punctuate-all") -> None:
        self.pipe = pipeline("token-classification", model=model_id, device='cuda')

    @staticmethod
    def preprocess(text):
        # remove markers except for markers in numbers
        return  re.sub(r"(?<!\d)[.,;:!?](?!\d)", "", text).split()

    def restore_punctuation(self, text):
        result = self.predict(self.preprocess(text))
        return self.prediction_to_text(result)

    def predict(self, words):
        text = " ".join(words)
        try:
            result = self.pipe(text)
        except Exception as e:
            print(f"标点恢复模型出错: {e}，可能输入文本过长。")
            return []

        # 检查模型是否因为某些原因截断了文本
        if result and len(text) != result[-1]["end"]:
            print(f"警告: 标点恢复模型可能截断了文本。输入长度: {len(text)}, 模型处理长度: {result[-1]['end']}")

        tagged_words = []
        char_index = 0
        result_index = 0
        for word in words:
            char_index += len(word) + 1
            label = "O"
            score = 0.0

            while result_index < len(result) and char_index > result[result_index]["end"]:
                label = result[result_index]['entity']
                score = result[result_index]['score']
                result_index += 1

            tagged_words.append([word, label, score])

        assert len(tagged_words) == len(words)
        return tagged_words

    @staticmethod
    def prediction_to_text(prediction):
        result = ""
        for word, label, _ in prediction:
            result += word
            if label == "0":
                result += " "
            if label in ".,?-:":
                result += label + " "
        return result.strip()