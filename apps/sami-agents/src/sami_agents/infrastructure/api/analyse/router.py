from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from token_verification import Role
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE, AuthDependencies

from sami_agents.application.answer_question import AnswerQuestion
from sami_agents.domain.entities.question import Context
from sami_agents.infrastructure.api.analyse.schemas import AnalyseRequest


def create_analyse_router(answer: AnswerQuestion, auth: AuthDependencies, today=date.today) -> APIRouter:
    router = APIRouter(dependencies=[Depends(auth.require_roles(Role.MANAGEMENT, Role.ADMIN))])

    @router.post("/analyse")
    def analyse(body: AnalyseRequest, request: Request) -> JSONResponse:
        context = Context(body.context.metric, date(int(body.context.month[:4]), int(body.context.month[5:]), 1)) if body.context else None
        return JSONResponse(answer.execute(body.question, request.cookies[ACCESS_TOKEN_COOKIE], today(), context))

    return router
