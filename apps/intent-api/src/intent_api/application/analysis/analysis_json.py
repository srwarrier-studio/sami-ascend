from datetime import date
from decimal import Decimal
from typing import Any

from intent_api.domain.analysis.analysis import Analysis, Finding
from intent_api.domain.analysis.finding import Step
from intent_api.domain.analysis.measure import MoverRow


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


def finding_json(finding: Finding) -> dict:
    return {
        "dimension": finding.dimension, "key": finding.key, "name": finding.name, "kind": finding.kind, "unit": finding.unit,
        "current": plain(finding.current), "previous": plain(finding.previous), "change": plain(finding.change),
        "change_percent": plain(finding.change_percent), "share_percent": plain(finding.share_percent),
        "volume_effect": plain(finding.volume_effect), "price_effect": plain(finding.price_effect),
        "explained": finding.explained,
        "paths": [[step_json(step) for step in path] for path in finding.paths],
        "causes": [{"source": c.source, "kind": c.kind, "key": c.key} for c in finding.causes],
    }


def row_json(row: MoverRow) -> dict:
    return plain({
        "key": row.key, "name": row.name, "current": row.current, "previous": row.previous, "change": row.change,
        "share_percent": row.share_percent, "unit": row.unit, "volume_effect": row.volume_effect, "price_effect": row.price_effect,
    })


def analysis_json(analysis: Analysis) -> dict:
    return {
        "currency": analysis.currency,
        "current": plain(analysis.current), "previous": plain(analysis.previous), "change": plain(analysis.change),
        "change_percent": plain(analysis.change_percent), "significant": analysis.significant,
        "findings": [finding_json(f) for f in analysis.findings],
        "offsets": [finding_json(f) for f in analysis.offsets],
        "explained_percent": plain(analysis.explained_percent), "unexplained_percent": plain(analysis.unexplained_percent),
        "limits": list(analysis.limits),
    }
