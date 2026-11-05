KEY_LENGTH = 10


def external(value: str) -> str:
    return (value.lstrip("0") or "0") if value.isdigit() else value


def internal(value: str, length: int = KEY_LENGTH) -> str:
    return value.zfill(length) if value.isdigit() else value
