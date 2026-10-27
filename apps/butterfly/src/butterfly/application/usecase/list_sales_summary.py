from typing import Callable

from butterfly.application.dto.list_query_dto import ListQuery, ListResult
from butterfly.application.list_query import apply_list_query


class ListSalesSummary:
    def __init__(self, summarize: Callable[[], list], fields: dict):
        self.summarize = summarize
        self.fields = fields

    def execute(self, query: ListQuery | None = None) -> ListResult:
        return apply_list_query(self.summarize(), query or ListQuery(), self.fields)
