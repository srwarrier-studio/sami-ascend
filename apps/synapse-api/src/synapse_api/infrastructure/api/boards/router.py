from typing import Annotated

from fastapi import APIRouter, Depends, Response
from token_verification.fastapi_deps import AuthDependencies
from token_verification.token_claims import TokenClaims

from synapse_api.application.boards import Boards
from synapse_api.domain.entities.widget_access import WidgetAccess
from synapse_api.domain.gateways.board_store import BoardStore
from synapse_api.domain.gateways.widget_catalog import WidgetCatalog
from synapse_api.infrastructure.api.boards.schemas import BoardResponse, ChangeBoardBody, CreateBoardBody, SaveWidgetsBody


def create_boards_router(store: BoardStore, catalog: WidgetCatalog, access: WidgetAccess, auth: AuthDependencies) -> APIRouter:
    router = APIRouter(prefix="/boards")
    Claims = Annotated[TokenClaims, Depends(auth.require_roles(*access.entry_roles()))]
    categories = {entry.id: entry.category for entry in catalog.entries()}

    def boards_for(claims: TokenClaims) -> Boards:
        return Boards(store, lambda catalog_id: catalog_id in categories and access.allows(claims.roles, categories[catalog_id]))

    @router.get("")
    def list_own(claims: Claims) -> list[BoardResponse]:
        return [BoardResponse.from_domain(board) for board in boards_for(claims).mine(claims.userid)]

    @router.get("/shared")
    def list_shared(claims: Claims) -> list[BoardResponse]:
        return [BoardResponse.from_domain(board, shared=True) for board in boards_for(claims).shared(claims.userid)]

    @router.post("/shared/{board_id}/copy", status_code=201)
    def copy_shared(claims: Claims, board_id: str) -> BoardResponse:
        return BoardResponse.from_domain(boards_for(claims).copy_shared(board_id, claims.userid, claims.sap_username))

    @router.post("", status_code=201)
    def create(claims: Claims, body: CreateBoardBody) -> BoardResponse:
        board = boards_for(claims).create(claims.userid, claims.sap_username, body.name, body.is_public, [w.to_domain() for w in body.widgets])
        return BoardResponse.from_domain(board)

    @router.patch("/{board_id}")
    def change(claims: Claims, board_id: str, body: ChangeBoardBody) -> BoardResponse:
        return BoardResponse.from_domain(boards_for(claims).change(board_id, claims.userid, body.name, body.is_public))

    @router.put("/{board_id}/widgets")
    def save_widgets(claims: Claims, board_id: str, body: SaveWidgetsBody) -> BoardResponse:
        return BoardResponse.from_domain(boards_for(claims).save_widgets(board_id, claims.userid, [w.to_domain() for w in body.widgets]))

    @router.delete("/{board_id}", status_code=204)
    def delete(claims: Claims, board_id: str) -> Response:
        boards_for(claims).delete(board_id, claims.userid)
        return Response(status_code=204)

    return router
