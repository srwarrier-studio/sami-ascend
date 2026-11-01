from fastapi import APIRouter, Depends
from token_verification import Role
from token_verification.fastapi_deps import AuthDependencies

from intent_api.application.match_question import MatchQuestion
from intent_api.infrastructure.api.match.schemas import MatchRequest, MatchResponse


def create_match_router(matcher: MatchQuestion, auth: AuthDependencies) -> APIRouter:
    router = APIRouter(dependencies=[Depends(auth.require_roles(Role.MANAGEMENT, Role.ADMIN))])

    @router.post("/match", response_model=MatchResponse)
    def match(body: MatchRequest) -> MatchResponse:
        return MatchResponse.from_match(matcher.execute(body.question))

    return router
