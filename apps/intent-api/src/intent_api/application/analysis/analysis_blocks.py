from datetime import date
from decimal import Decimal
from typing import Any

from intent_api.application.analysis import why_wording
from intent_api.domain.analysis.analysis import Analysis, Finding
from intent_api.domain.analysis.finding import Step
from intent_api.domain.analysis.measure import MoverRow, TrendPoint

TABLE_COLUMNS = ["Name", "Current", "Previous", "Change", "Share of change", "Volume effect", "Price effect"]


def plain(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    return value


def step_json(step: Step) -> dict:
    return {"node": step.node, "edge": step.edge, "lookup_field": step.lookup_field, "keys": list(step.keys), "kind": step.kind, "at": plain(step.at), "numbers": plain(step.numbers), "rows": plain(step.rows)}


def row_json(row: MoverRow) -> dict:
    return plain({
        "key": row.key, "name": row.name, "current": row.current, "previous": row.previous, "change": row.change,
        "share_percent": row.share_percent, "unit": row.unit, "volume_effect": row.volume_effect, "price_effect": row.price_effect,
    })


def trend_block(analysis: Analysis, points: list[TrendPoint]) -> dict:
    marked = [analysis.window.compare_start.strftime("%Y-%m"), analysis.window.start.strftime("%Y-%m")]
    return {"metric": analysis.question.metric, "currency": analysis.currency, "points": [{"month": p.month, "value": str(p.amount)} for p in points], "marked": marked}


def table_blocks(analysis: Analysis) -> list[dict]:
    return [
        {"title": f"By {dimension}", "columns": TABLE_COLUMNS, "rows": [row_json(row) for row in rows]}
        for dimension, rows in analysis.tables.items() if rows
    ]


def finding_item(analysis: Analysis, finding: Finding, role: str) -> dict:
    return {
        "name": finding.name, "dimension": why_wording.DIMENSION_LABELS.get(finding.dimension, finding.dimension), "role": role,
        "direction": why_wording.direction(finding.change), "detail": why_wording.detail_text(analysis, finding, with_share=role == "mover"),
        "price_text": why_wording.price_text(analysis, finding) if role == "mover" else None, "reasons": why_wording.reasons(finding),
    }


def findings_block(analysis: Analysis, company: str) -> dict:
    return {
        "headline": why_wording.plain_headline(analysis, company),
        "items": [finding_item(analysis, f, "mover") for f in analysis.findings] + [finding_item(analysis, f, "offset") for f in analysis.offsets],
        "coverage": {"explained_percent": str(analysis.explained_percent), "text": why_wording.plain_coverage(analysis)},
        "notes": why_wording.notes(analysis, company),
    }


def evidence_blocks(analysis: Analysis) -> list[dict]:
    blocks = []
    for finding in analysis.findings:
        offset = 0
        for path in finding.paths:
            steps = [{**step_json(step), "summary": why_wording.step_sentence(step, finding.causes[offset + i].key)} for i, step in enumerate(path)]
            offset += len(path)
            blocks.append({"finding": finding.name, "steps": steps})
    return blocks
