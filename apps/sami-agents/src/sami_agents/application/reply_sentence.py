import re

MAX_LENGTH = 200
MIN_WORDS = 4
MIN_OTHER_WORDS = 2
FORBIDDEN = re.compile(r"[<>`*#_\[\]{}|\\]|\d|https?:|www\.", re.IGNORECASE)


def other_words(sentence: str, titles: list[str]) -> int:
    rest = sentence.lower()
    for title in titles:
        rest = rest.replace(title.lower(), " ")
    return len(re.findall(r"[a-z']+", rest))


def accept_sentence(text: str, titles: list[str] | None = None) -> str | None:
    sentence = text.strip().strip('"').strip()
    if not sentence or len(sentence) > MAX_LENGTH or "\n" in sentence or "\r" in sentence:
        return None
    if len(sentence.split()) < MIN_WORDS or FORBIDDEN.search(sentence):
        return None
    if titles is not None and (not any(title.lower() in sentence.lower() for title in titles) or other_words(sentence, titles) < MIN_OTHER_WORDS):
        return None
    return sentence
