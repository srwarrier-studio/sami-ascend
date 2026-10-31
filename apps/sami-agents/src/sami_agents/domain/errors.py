class RelevanceUnavailable(Exception):
    pass


class CatalogUnavailable(Exception):
    pass


class ReplyUnavailable(Exception):
    pass


class GraphError(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


class DataUnavailable(Exception):
    pass
