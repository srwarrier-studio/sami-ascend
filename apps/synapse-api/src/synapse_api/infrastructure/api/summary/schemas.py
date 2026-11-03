from pydantic import BaseModel


class SummaryResponse(BaseModel):
    currency: str
    sentences: list[str]
