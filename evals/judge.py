"""LLM-as-judge (opus): is the claim chart faithful — each disclosure genuinely taught by the
reference, each 'not disclosed' genuinely absent, and the novelty verdict sound?"""

from __future__ import annotations

from pydantic import BaseModel, Field

from claim_chart.client import LLMClient
from claim_chart.config import Settings
from claim_chart.models import ChartResult


class ChartGrade(BaseModel):
    faithfulness: int = Field(ge=1, le=5, description="Are the 'disclosed' calls genuinely taught by the reference (no over-reading)?")
    completeness: int = Field(ge=1, le=5, description="Are genuinely-disclosed limitations correctly caught (not wrongly 'not disclosed')?")
    verdict_soundness: int = Field(ge=1, le=5, description="Is the anticipated / novel verdict correct given the mappings?")
    overall: int = Field(ge=1, le=5)
    comment: str = ""


JUDGE_SYSTEM = (
    "You grade an AI patent CLAIM CHART used for a novelty (anticipation) analysis. Given the CLAIM, "
    "the prior-art REFERENCE, and the produced CHART (each limitation marked disclosed/not-disclosed "
    "with a quote), score: faithfulness (are the 'disclosed' calls genuinely taught by the reference, "
    "with quotes that actually appear there — no over-reading), completeness (are truly-disclosed "
    "limitations correctly caught), and verdict_soundness (is 'anticipated' vs 'novel over the "
    "reference' correct — anticipated requires EVERY limitation disclosed in this single reference). "
    "Integer scores 1-5. This is educational, not legal advice."
)


def grade(result: ChartResult, claim: str, reference: str, settings: Settings, client: LLMClient | None = None) -> ChartGrade:
    client = client or LLMClient(settings)
    rows = "\n".join(
        f"- [{'disclosed' if m.disclosed else 'NOT disclosed'}] {m.limitation}"
        + (f"  quote: “{m.quote}”" if m.quote else "")
        for m in result.mappings
    ) or "(none)"
    user = (
        f"CLAIM:\n{claim}\n\n"
        f"PRIOR-ART REFERENCE:\n{reference}\n\n"
        f"CHART (verdict: {result.verdict}):\n{rows}"
    )
    return client.structured(schema=ChartGrade, system=JUDGE_SYSTEM, user=user, model=settings.judge_model)
