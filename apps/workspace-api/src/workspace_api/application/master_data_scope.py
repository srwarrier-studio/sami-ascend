from workspace_api.domain.errors import InvalidQuery

MAX_TOP = 50
MAX_QUERY = 40


def plants_of(companies: list[str], plants_by_company: dict[str, tuple[str, ...]]) -> list[str]:
    return [plant for company in companies for plant in plants_by_company.get(company, ())]


def company_of(plant: str, plants_by_company: dict[str, tuple[str, ...]]) -> str:
    return next((code for code, plants in plants_by_company.items() if plant in plants), "")


def checked(query: str | None, top: int, skip: int) -> str | None:
    if not 1 <= top <= MAX_TOP:
        raise InvalidQuery(f"top must be between 1 and {MAX_TOP}")
    if skip < 0:
        raise InvalidQuery("skip must be 0 or more")
    text = (query or "").strip()
    if len(text) > MAX_QUERY:
        raise InvalidQuery(f"q must be at most {MAX_QUERY} characters")
    return text or None
