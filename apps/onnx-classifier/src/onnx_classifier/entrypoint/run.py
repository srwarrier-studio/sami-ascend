import uvicorn

from onnx_classifier.entrypoint.app import create_app
from onnx_classifier.infrastructure.settings import Settings


def main() -> None:
    settings = Settings()
    uvicorn.run(create_app(settings), host="0.0.0.0", port=settings.port)
