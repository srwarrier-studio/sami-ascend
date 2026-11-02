import re

FALL = re.compile(r"\b(?:fall|fell|falling|drop|dropped|dropping|decline|declined|declining|decrease|decreased|down|lower|lowest|dip|dipped)\b")
RISE = re.compile(r"\b(?:rise|rose|rising|increase|increased|increasing|jump|jumped|up|higher|growth|grew|surge|surged)\b")


def read_direction(text: str) -> str:
    lowered = text.lower()
    fall, rise = bool(FALL.search(lowered)), bool(RISE.search(lowered))
    if fall and not rise:
        return "fall"
    if rise and not fall:
        return "rise"
    return "change"
