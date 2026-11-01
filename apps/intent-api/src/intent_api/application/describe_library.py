from intent_api.domain.entities.scenario import Library


class DescribeLibrary:
    def __init__(self, library: Library):
        self.library = library

    def summary(self) -> str:
        return f"ok: {len(self.library.domains)} domains, {len(self.library.scenarios)} scenarios"

    def show(self) -> str:
        lines = []
        for domain, description in self.library.domains.items():
            lines.append(f"{domain}: {description}")
            for scenario in self.library.scenarios.values():
                if scenario.domain == domain:
                    needs = ", ".join(scenario.needs) or "nothing"
                    covers = f"; covers {', '.join(scenario.covers)}" if scenario.covers else ""
                    lines.append(f"  {scenario.id}: {scenario.description} (needs {needs}{covers}; {len(scenario.examples)} examples)")
        return "\n".join(lines)
