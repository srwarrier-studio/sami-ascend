import hmac

from fastapi import APIRouter, Depends, Header, HTTPException

from onnx_classifier.application.score_choice import ScoreChoice
from onnx_classifier.infrastructure.api.systemone.schemas import ChoiceAnswer, SystemOneRequest, SystemOneResponse

QUESTION_FIELD = "question"


def create_systemone_router(score: ScoreChoice, api_key: str) -> APIRouter:
    router = APIRouter()

    def authorised(authorization: str = Header(default="")) -> None:
        if api_key and not hmac.compare_digest(authorization, f"Bearer {api_key}"):
            raise HTTPException(status_code=401, detail="unauthorised")

    @router.post("/v1/systemone", response_model=SystemOneResponse, dependencies=[Depends(authorised)])
    def systemone(request: SystemOneRequest) -> SystemOneResponse:
        text = request.state.get(QUESTION_FIELD)
        if text is None:
            raise HTTPException(status_code=422, detail=f"state needs a '{QUESTION_FIELD}' text")
        answers = {name: ChoiceAnswer(probabilities=score.execute(text, question.instructions, question.criteria)) for name, question in request.questions.items()}
        return SystemOneResponse(answers=answers)

    return router
