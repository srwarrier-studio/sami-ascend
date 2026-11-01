from datetime import date

from fastapi import APIRouter, Depends, Request
from token_verification import Role
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE, AuthDependencies

from intent_api.application.answer_question import AnswerQuestion
from intent_api.infrastructure.api.answer.schemas import AnswerResponse
from intent_api.infrastructure.api.match.schemas import MatchRequest


def create_answer_router(answer: AnswerQuestion, auth: AuthDependencies, today=date.today) -> APIRouter:
    router = APIRouter(dependencies=[Depends(auth.require_roles(Role.MANAGEMENT, Role.ADMIN))])

    @router.post("/answer", response_model=AnswerResponse)
    def answer_question(body: MatchRequest, request: Request) -> AnswerResponse:
        return AnswerResponse.from_reply(answer.execute(body.question, request.cookies[ACCESS_TOKEN_COOKIE], today()))

    return router
