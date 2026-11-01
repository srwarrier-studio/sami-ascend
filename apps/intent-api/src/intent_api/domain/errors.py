class ClassifierUnavailable(Exception):
    pass


class LibraryError(Exception):
    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems
