"""Typed contracts for claim-chart.

The tool takes an independent patent CLAIM and a prior-art REFERENCE, splits the claim into its
LIMITATIONS (elements/steps), and for each limitation the LLM either finds a supporting verbatim
QUOTE in the reference (disclosed) or marks it NOT disclosed. A deterministic grounding pass drops
any "disclosed" mapping whose quote isn't actually in the reference, so it can't invent a
disclosure. Educational only — this is not legal advice.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Limitation(BaseModel):
    index: int = Field(description="1-based position of this limitation within the claim.")
    text: str = Field(description="The verbatim text of this claim element / step.")


class Mapping(BaseModel):
    limitation: str = Field(description="The limitation text this mapping is about.")
    disclosed: bool = Field(description="True if the reference discloses this limitation.")
    quote: str | None = Field(
        default=None,
        description="A short VERBATIM span from the reference that discloses the limitation, or "
        "null if not disclosed.",
    )


class ChartResult(BaseModel):
    """A claim chart: each limitation mapped (or not) to the prior-art reference."""

    limitations: list[Limitation] = Field(default_factory=list)
    mappings: list[Mapping] = Field(default_factory=list)
    verdict: str = Field(
        description="'anticipated' if every limitation is disclosed, else 'novel over the "
        "reference (limitation(s) X not disclosed)'.",
    )
    novel_because: list[str] = Field(
        default_factory=list,
        description="Texts of the limitations that are NOT disclosed by the reference.",
    )
    disclaimer: str = (
        "Educational tool, not legal advice. It builds a claim chart against a single reference to "
        "illustrate anticipation analysis; it does not assess obviousness, validity, or "
        "infringement. Consult a qualified patent attorney for anything that matters."
    )
