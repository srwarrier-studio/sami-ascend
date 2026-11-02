from pydantic import BaseModel


class SummaryResponse(BaseModel):
    asOf: str
    currency: str
    sentences: list[str]
