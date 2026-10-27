from butterfly.application.dto.list_query_dto import ListQuery, ListResult
from butterfly.application.filter.parser import parse_filter
from butterfly.application.query_options import (
    parse_count,
    parse_orderby,
    parse_select,
    parse_skip,
    parse_top,
)


def sort_key(attribute: str):
    def key(row):
        value = getattr(row, attribute)
        return (value is not None, value)

    return key


def apply_list_query(rows: list, query: ListQuery, fields: dict) -> ListResult:
    select = parse_select(query.select, fields)
    orderby = parse_orderby(query.orderby, fields)
    top = parse_top(query.top)
    skip = parse_skip(query.skip)
    count = parse_count(query.count)
    condition = None if query.filter is None else parse_filter(query.filter, fields)

    if condition is not None:
        rows = [row for row in rows if condition.matches(row)]
    for name, descending in reversed(orderby):
        rows = sorted(rows, key=sort_key(fields[name][0]), reverse=descending)
    return ListResult(
        rows=rows[skip : skip + top],
        total=len(rows) if count else None,
        select=select,
    )
