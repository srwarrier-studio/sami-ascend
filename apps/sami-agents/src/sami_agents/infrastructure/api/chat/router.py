from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from token_verification import Role
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE, AuthDependencies

from sami_agents.application.answer_chat import AnswerChat
from sami_agents.infrastructure.api.chat.schemas import ChatRequest


def create_chat_router(answer_chat: AnswerChat, auth: AuthDependencies) -> APIRouter:
    router = APIRouter(dependencies=[Depends(auth.require_roles(Role.MANAGEMENT, Role.ADMIN))])

    @router.post("/chat", response_class=PlainTextResponse)
    def chat(body: ChatRequest, request: Request) -> PlainTextResponse:
        program = answer_chat.execute(body.message, request.cookies[ACCESS_TOKEN_COOKIE])
        return PlainTextResponse(program, media_type="text/plain; charset=utf-8")

    return router
