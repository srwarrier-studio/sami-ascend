import json
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", frozen=True)
    model_dir: Path = Path("/models/serve")
    threads: int = 2
    api_key: str = ""
    port: int = 8011

    def calibration(self) -> dict:
        return json.loads((self.model_dir / "calibration.json").read_text())
