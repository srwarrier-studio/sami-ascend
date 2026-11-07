from fastapi import APIRouter


def create_health_router() -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return router
