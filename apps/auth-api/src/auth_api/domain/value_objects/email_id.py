from dataclasses import dataclass



@dataclass(frozen=True)
class EmailID:
    value: str

    def __post_init__(self):
        if '@' not in self.value:
            raise ValueError(f"Invalid Email ID. Value: {self.value}")