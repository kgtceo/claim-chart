"""Deterministic eval metrics for claim-chart.

A planted case labels which limitation INDICES (1-based) the reference actually discloses. We score
the produced claim chart against those labels:

  • RECALL     — of the limitations the reference DOES disclose, how many did we mark disclosed?
  • PRECISION  — of the limitations we marked disclosed, how many are truly disclosed (labelled)?
                 (No false disclosure — the killer safety property.)
  • GROUNDING  — every 'disclosed' mapping's quote is a real substring of the reference.
"""

from __future__ import annotations

from claim_chart.models import ChartResult


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def disclosed_indices(result: ChartResult) -> set[int]:
    """1-based indices of limitations the chart marked disclosed."""
    out: set[int] = set()
    for lim, m in zip(result.limitations, result.mappings):
        if m.disclosed:
            out.add(lim.index)
    return out


def recall(result: ChartResult, planted: list[int]) -> float:
    """Fraction of truly-disclosed limitations that were marked disclosed."""
    planted_set = set(planted)
    if not planted_set:
        return 1.0
    got = disclosed_indices(result) & planted_set
    return len(got) / len(planted_set)


def precision(result: ChartResult, planted: list[int]) -> float:
    """Fraction of marked-disclosed limitations that are truly disclosed (no false disclosure)."""
    planted_set = set(planted)
    marked = disclosed_indices(result)
    if not marked:
        return 1.0
    correct = marked & planted_set
    return len(correct) / len(marked)


def no_false_disclosure(result: ChartResult, planted: list[int]) -> bool:
    """No limitation OUTSIDE the planted set was marked disclosed (precision == 1.0)."""
    return disclosed_indices(result).issubset(set(planted))


def is_grounded(result: ChartResult, reference: str) -> bool:
    """Every 'disclosed' mapping's quote is a verbatim substring of the reference."""
    hay = _norm(reference)
    for m in result.mappings:
        if m.disclosed:
            quote = (m.quote or "").strip()
            if not quote or _norm(quote) not in hay:
                return False
    return True


def verdict_correct(result: ChartResult, planted: list[int]) -> bool:
    """Verdict should be 'anticipated' iff every limitation is disclosed."""
    all_disclosed = len(set(planted)) == len(result.limitations)
    said_anticipated = result.verdict.startswith("anticipated")
    return all_disclosed == said_anticipated
