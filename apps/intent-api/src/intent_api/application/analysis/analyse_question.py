import calendar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from intent_api.application.analysis.walk_graph import WalkGraph
from intent_api.domain.analysis.analysis import Analysis, Cause, Finding
from intent_api.domain.analysis.finding import Start, Step, Window
from intent_api.domain.entities.graph import ANOMALY_KINDS, Graph, Node
from intent_api.domain.analysis.measure import Comparison, MoverRow
from intent_api.domain.analysis.question import Question
from intent_api.domain.errors import DataUnavailable
from intent_api.domain.analysis.data_source import DataSource

OTHER = "other"
HUNDRED = Decimal(100)


@dataclass(frozen=True)
class Thresholds:
    significant_percent: float = 5
    mover_min_percent: float = 10
    mover_min_share: float = 2
    price_majority_percent: float = 50
    top: int = 10


def month_end(first: date) -> date:
    return date(first.year, first.month, calendar.monthrange(first.year, first.month)[1])


def window_of(month: date) -> Window:
    before = date(month.year - 1, 12, 1) if month.month == 1 else date(month.year, month.month - 1, 1)
    return Window(month, month_end(month), before, month_end(before))


def percent(part: Decimal, whole: Decimal) -> Decimal | None:
    return (part / whole * HUNDRED).quantize(Decimal("0.01")) if whole else None


def path_explains(path: tuple[Step, ...]) -> bool:
    return len(path) >= 2 or any(ANOMALY_KINDS[step.kind]["explains"] for step in path)


class AnalyseQuestion:
    def __init__(self, source: DataSource, graph: Graph, thresholds: Thresholds = Thresholds()):
        self.source = source
        self.graph = graph
        self.thresholds = thresholds

    def execute(self, question: Question, token: str, today: date) -> Analysis:
        info = next((m for m in self.source.metrics(token) if m.name == question.metric), None)
        if info is None:
            raise DataUnavailable(f"metric '{question.metric}' is not registered")
        window = window_of(question.month)
        totals = self.source.compare(token, question.metric, window, None, self.thresholds.top)
        if not totals:
            return Analysis(question, window, "", Decimal(0), Decimal(0), Decimal(0), None, False, limits=["There is no data for this metric in these months."])
        total = self.pick(totals, question.currency)
        if total is None:
            return Analysis(question, window, "", Decimal(0), Decimal(0), Decimal(0), None, False, limits=[f"There is no data in {question.currency} for these months."])
        analysis = Analysis(question, window, total.currency, total.current, total.previous, total.change, total.change_percent, self.significant(total))
        analysis.other_currencies = [(other.currency, other.change_percent) for other in totals if other is not total and self.significant(other)]
        truncated = False
        for dimension in info.dimensions:
            rows = self.rows_of(question, token, window, dimension.name, total.currency)
            analysis.tables[dimension.name] = rows
            for row in rows:
                if row.key == OTHER or not self.notable(row, total):
                    continue
                finding, cut = self.finding(question, dimension.name, row, token, window, today)
                truncated = truncated or cut
                (analysis.findings if self.in_direction(question.direction, row) else analysis.offsets).append(finding)
        if truncated:
            analysis.limits.append("A search stopped at its limit, so there may be more behind this.")
        if not analysis.significant:
            analysis.findings = [f for f in analysis.findings if f.kind == "price" or f.paths]
            analysis.offsets = []
        analysis.findings.sort(key=lambda f: f.share_percent if f.share_percent is not None else Decimal(-1000), reverse=True)
        explained = self.explained(analysis)
        analysis.explained_percent, analysis.unexplained_percent = explained, HUNDRED - explained
        return analysis

    def pick(self, totals: list[Comparison], named: str | None) -> Comparison | None:
        if named:
            return next((t for t in totals if t.currency == named), None)
        return max(totals, key=lambda t: abs(t.change_percent) if t.change_percent is not None else Decimal(0))

    def significant(self, total: Comparison) -> bool:
        if total.change_percent is None:
            return total.current > 0
        return abs(total.change_percent) >= Decimal(str(self.thresholds.significant_percent))

    def rows_of(self, question: Question, token: str, window: Window, dimension: str, currency: str) -> list[MoverRow]:
        for comparison in self.source.compare(token, question.metric, window, dimension, self.thresholds.top):
            if comparison.currency == currency:
                return comparison.rows or []
        return []

    def notable(self, row: MoverRow, total: Comparison) -> bool:
        own = percent(row.change, row.previous)
        big_enough = own is None or abs(own) >= Decimal(str(self.thresholds.mover_min_percent))
        share_ok = total.previous == 0 or abs(row.change) * HUNDRED >= Decimal(str(self.thresholds.mover_min_share)) * abs(total.previous)
        return big_enough and share_ok and row.change != 0

    def in_direction(self, direction: str, row: MoverRow) -> bool:
        return direction == "change" or (direction == "fall") == (row.change < 0)

    def finding(self, question: Question, dimension: str, row: MoverRow, token: str, window: Window, today: date) -> tuple[Finding, bool]:
        t = self.thresholds
        price = row.price_effect is not None and abs(row.price_effect) * HUNDRED >= Decimal(str(t.price_majority_percent)) * abs(row.change)
        finding = Finding(
            dimension, row.key, row.name, row.current, row.previous, row.change, percent(row.change, row.previous), row.share_percent,
            "price" if price else "volume", row.unit, row.volume_effect, row.price_effect,
        )
        if price:
            finding.causes = [Cause(f"metric:{question.metric}.{dimension}", "price_effect", row.key)]
            finding.explained = True
            return finding, False
        node = self.node_for(question.metric, dimension)
        if node is None:
            return finding, False
        result = WalkGraph(self.graph, self.source).execute("root_cause", [Start(node.name, row.key)], window, token, today)
        finding.paths = result.paths
        finding.causes = [self.cause(step) for path in result.paths for step in path]
        finding.explained = any(path_explains(path) for path in result.paths)
        return finding, result.truncated

    def node_for(self, metric: str, dimension: str) -> Node | None:
        return next((n for n in self.graph.nodes.values() if n.source_kind == "metric" and n.source == metric and n.dimension == dimension), None)

    def cause(self, step: Step) -> Cause:
        node = self.graph.nodes[step.node]
        source = f"{node.source_kind}:{node.source}" + (f".{node.dimension}" if node.dimension else "")
        per_row = ANOMALY_KINDS[step.kind]["per_row"]
        key = str(step.rows[0][node.id]) if per_row and node.id and step.rows else step.keys[0]
        return Cause(source, step.kind, key)

    def explained(self, analysis: Analysis) -> Decimal:
        per_dimension = {}
        for finding in analysis.findings:
            if finding.explained and finding.share_percent is not None:
                per_dimension[finding.dimension] = per_dimension.get(finding.dimension, Decimal(0)) + finding.share_percent
        best = max(per_dimension.values(), default=Decimal(0))
        return max(Decimal(0), min(HUNDRED, best))
