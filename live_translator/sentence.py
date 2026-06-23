import re


_ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "vs",
    "etc", "e.g", "i.e", "u.s", "u.k", "fia", "f1",
}


def split_english_sentences(text: str) -> list[str]:
    """Lightweight sentence splitter used instead of NLTK."""
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []

    sentences: list[str] = []
    start = 0
    length = len(text)
    index = 0

    while index < length:
        char = text[index]
        if char not in ".!?":
            index += 1
            continue

        if char == ".":
            prev_char = text[index - 1] if index > 0 else ""
            next_char = text[index + 1] if index + 1 < length else ""
            if prev_char.isdigit() and next_char.isdigit():
                index += 1
                continue

            token = _previous_token(text, index).lower().rstrip(".")
            if token in _ABBREVIATIONS:
                index += 1
                continue

        end = index + 1
        while end < length and text[end] in ".!?":
            end += 1
        while end < length and text[end] in "\"')]}":
            end += 1

        if end == length or text[end].isspace():
            sentence = text[start:end].strip()
            if sentence:
                sentences.append(sentence)
            start = end
            while start < length and text[start].isspace():
                start += 1
            index = start
            continue

        index += 1

    tail = text[start:].strip()
    if tail:
        sentences.append(tail)
    return sentences


def _previous_token(text: str, dot_index: int) -> str:
    prefix = text[:dot_index].rstrip()
    if not prefix:
        return ""
    return prefix.split()[-1]

