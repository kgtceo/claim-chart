"""claim-chart — an AI patent claim-chart / prior-art anticipation tool.

Paste an independent patent claim and a prior-art reference; it splits the claim into its
limitations and, for each one, either finds a verbatim quote in the reference (disclosed) or marks
it not disclosed — then gives a novelty verdict. A grounding pass drops any 'disclosed' mapping
whose quote isn't actually in the reference, so it can't invent a disclosure. Ships a planted-case
eval harness. Educational only — not legal advice."""

from .chart import ChartBuilder, chart, segment_claim
from .client import LLMClient
from .config import Settings
from .models import ChartResult, Limitation, Mapping

__all__ = [
    "LLMClient",
    "Settings",
    "Limitation",
    "Mapping",
    "ChartResult",
    "ChartBuilder",
    "chart",
    "segment_claim",
]
