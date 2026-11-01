import re

NAMES = {"inr": "INR", "rupee": "INR", "rupees": "INR", "rs": "INR", "₹": "INR", "usd": "USD", "dollar": "USD", "dollars": "USD", "$": "USD"}
WORD = re.compile(r"₹|\$|\b(?:inr|usd|rupees?|dollars?|rs)\b")


def read_currency(text: str) -> str | None:
    found = {NAMES[word] for word in WORD.findall(text.lower())}
    return found.pop() if len(found) == 1 else None
