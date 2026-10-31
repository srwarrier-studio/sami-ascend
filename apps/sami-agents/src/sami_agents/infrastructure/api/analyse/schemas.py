from pydantic import BaseModel, Field, field_validator


class AnalyseContext(BaseModel):
    metric: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,39}$")
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


class AnalyseRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    context: AnalyseContext | None = None

    @field_validator("question")
    @classmethod
    def trimmed(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question is empty")
        return value
