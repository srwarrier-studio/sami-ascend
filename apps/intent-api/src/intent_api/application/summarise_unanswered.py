from intent_api.domain.gateways.unanswered_log import UnansweredLog

NO_DOMAIN = "no nearby domain"


class SummariseUnanswered:
    def __init__(self, log: UnansweredLog):
        self.log = log

    def execute(self) -> str:
        groups: dict[str, list[dict]] = {}
        for entry in self.log.entries():
            nearest = entry["did_you_mean"][0] if entry["did_you_mean"] else NO_DOMAIN
            groups.setdefault(nearest, []).append(entry)
        if not groups:
            return "no refused questions"
        lines = []
        for nearest, entries in sorted(groups.items(), key=lambda item: -len(item[1])):
            lines.append(f"{nearest}: {len(entries)}")
            lines += [f"  [{entry['reason']}] {entry['question']}" for entry in entries]
        return "\n".join(lines)
