class SalesOrderNotFound(Exception):
    def __init__(self, sales_order: str):
        super().__init__(sales_order)
        self.sales_order = sales_order


class InvalidQuery(Exception):
    def __init__(self, message: str, target: str):
        super().__init__(message)
        self.message = message
        self.target = target


class UnsupportedQueryOption(InvalidQuery): ...
