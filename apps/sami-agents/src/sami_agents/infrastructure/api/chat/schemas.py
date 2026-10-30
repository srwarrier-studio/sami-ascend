from typing import Annotated

from pydantic import BaseModel, StringConstraints

MAX_MESSAGE = 500


class ChatRequest(BaseModel):
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_MESSAGE)]
