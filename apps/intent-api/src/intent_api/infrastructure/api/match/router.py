from fastapi import APIRouter, Depends
from token_verification import Role
from token_verification.fastapi_deps import AuthDependencies

from intent_api.application.match_question import MatchQuestion
from intent_api.infrastructure.api.match.schemas import MatchRequest, MatchResponse, SelectedScenario

CANNOT_ANSWER = "cannot_answer"


def create_match_router(matcher: MatchQuestion, auth: AuthDependencies) -> APIRouter:
    router = APIRouter(dependencies=[Depends(auth.require_roles(Role.MANAGEMENT, Role.ADMIN))])

    @router.post("/match", response_model=MatchResponse)
    def match(body: MatchRequest) -> MatchResponse:
        result = matcher.execute(body.question)
        return MatchResponse(
            problem=None if result.answered else CANNOT_ANSWER,
            reason=result.reason,
            domain=result.domain,
            domain_probability=result.domain_probability,
            domain_scores=result.domain_scores,
            offered=list(result.offered),
            scenarios=[SelectedScenario(id=item.scenario, probability=item.probability, clause=item.clause) for item in result.selected],
            did_you_mean=list(result.did_you_mean),
        )

    return router
