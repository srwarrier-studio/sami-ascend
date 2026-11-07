from fastapi import FastAPI

from onnx_classifier.application.score_choice import ScoreChoice
from onnx_classifier.infrastructure.api.health.router import create_health_router
from onnx_classifier.infrastructure.api.systemone.router import create_systemone_router
from onnx_classifier.infrastructure.onnx_pair_scorer import OnnxPairScorer
from onnx_classifier.infrastructure.settings import Settings


def build_score_choice(settings: Settings) -> ScoreChoice:
    calibration = settings.calibration()
    scorer = OnnxPairScorer(settings.model_dir, calibration["max_length"], settings.threads)
    return ScoreChoice(scorer, calibration["temperature"])


def create_app(settings: Settings, score: ScoreChoice | None = None) -> FastAPI:
    app = FastAPI(title="onnx-classifier")
    app.include_router(create_health_router())
    app.include_router(create_systemone_router(score or build_score_choice(settings), settings.api_key))
    return app
