class ClassifierUnavailable(Exception):
    pass


class LibraryError(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


class GraphError(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


class PeriodNotSupported(Exception):
    def __init__(self, periods: list[str], reason: str):
        super().__init__(reason)
        self.periods = periods
        self.reason = reason


class DataUnavailable(Exception):
    pass


class MetricsUnavailable(Exception):
    pass
