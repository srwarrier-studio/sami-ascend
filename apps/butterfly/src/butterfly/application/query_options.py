from butterfly.domain.errors import InvalidQuery

DEFAULT_TOP = 100
MAX_TOP = 1000


def parse_select(text: str | None, fields: dict) -> list[str]:
    if text is None:
        return list(fields)
    names = [name.strip() for name in text.split(",")]
    for name in names:
        if name not in fields:
            raise InvalidQuery(f"Unknown field {name or '(empty)'} in $select.", "$select")
    return [name for name in fields if name in names]


def parse_orderby(text: str | None, fields: dict) -> list[tuple[str, bool]]:
    if text is None:
        return []
    keys = []
    for part in text.split(","):
        words = part.split()
        if len(words) not in (1, 2) or words[0] not in fields:
            raise InvalidQuery(f"Cannot sort by '{part.strip()}' in $orderby.", "$orderby")
        direction = words[1] if len(words) == 2 else "asc"
        if direction not in ("asc", "desc"):
            raise InvalidQuery("Sort direction must be asc or desc in $orderby.", "$orderby")
        keys.append((words[0], direction == "desc"))
    return keys


def parse_whole_number(text: str | None, name: str, default: int) -> int:
    if text is None:
        return default
    if not text.isascii() or not text.isdigit():
        raise InvalidQuery(f"{name} must be a whole number of 0 or more.", name)
    return int(text)


def parse_top(text: str | None) -> int:
    top = parse_whole_number(text, "$top", DEFAULT_TOP)
    if top > MAX_TOP:
        raise InvalidQuery(f"$top cannot be more than {MAX_TOP}.", "$top")
    return top


def parse_skip(text: str | None) -> int:
    return parse_whole_number(text, "$skip", 0)


def parse_count(text: str | None) -> bool:
    if text is None or text == "false":
        return False
    if text == "true":
        return True
    raise InvalidQuery("$count must be true or false.", "$count")


def parse_expand(text: str | None) -> bool:
    if text is None:
        return False
    for name in text.split(","):
        if name.strip() != "_Item":
            raise InvalidQuery(f"Cannot expand {name.strip() or '(empty)'} in $expand.", "$expand")
    return True
