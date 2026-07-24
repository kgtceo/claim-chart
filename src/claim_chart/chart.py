"""patent claim + prior-art reference -> a grounded claim chart.

Pipeline:
  1. Segment the independent claim into its LIMITATIONS (elements / steps) deterministically.
  2. Ask the LLM to map each limitation to the reference: {disclosed, quote}.
  3. GROUNDING PASS — for any mapping marked disclosed, if its `quote` (whitespace-normalised,
     case-insensitive) is not a substring of the reference, force disclosed=False and drop the
     quote. The model can never claim a disclosure it can't quote verbatim from the reference.
  4. Verdict — "anticipated" if every limitation is disclosed, else "novel over the reference".

Educational only — not legal advice.
"""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from . import prompts
from .client import LLMClient
from .models import ChartResult, Limitation, Mapping


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


# --- claim segmentation -------------------------------------------------------------------------

# Split points: semicolons, newlines, and clause connectors that typically separate limitations in
# claim drafting ("wherein", "; and", ", and"). Deliberately NOT bare "and" — real claim language
# uses "and" inside a single limitation constantly ("a processor and a memory"), and splitting on it
# fractures the element the whole analysis rests on.
_SPLIT_RE = re.compile(r";|\n|(?<=\s)wherein\s|(?<=,)\s+and\s", re.IGNORECASE)

# A fragment that starts with a leftover connector ("; and generating…" → "and generating…") gets
# the connector stripped so the limitation reads as the element/step itself.
_LEADING_CONNECTOR_RE = re.compile(r"^(?:and|or)\s+", re.IGNORECASE)


def segment_claim(claim: str) -> list[Limitation]:
    """Break an independent claim into limitations.

    Drops the boilerplate preamble up to the first ':' or 'comprising'/'consisting' cue so the
    limitations are the actual elements/steps, not the "A method comprising:" lead-in.
    """
    body = claim.strip()
    # Strip a preamble like "A method comprising:" / "An apparatus comprising:".
    m = re.search(r"(?:comprising|consisting of|including|which comprises)\s*:?\s*", body, re.IGNORECASE)
    if m:
        body = body[m.end():]
    else:
        # No cue: fall back to text after the first colon, if any.
        if ":" in body:
            body = body.split(":", 1)[1]

    parts = [p.strip(" \t\r\n,.;") for p in _SPLIT_RE.split(body)]
    parts = [_LEADING_CONNECTOR_RE.sub("", p) for p in parts]
    parts = [p for p in parts if len(p) >= 3]  # drop empties / stray connector fragments
    if not parts:
        parts = [claim.strip()]
    return [Limitation(index=i + 1, text=p) for i, p in enumerate(parts)]


# --- LLM mapping schema -------------------------------------------------------------------------


class _MappingList(BaseModel):
    """What the LLM returns: one entry per limitation."""

    mappings: list[Mapping] = Field(default_factory=list)


def _verdict(mappings: list[Mapping]) -> tuple[str, list[str]]:
    novel_because = [m.limitation for m in mappings if not m.disclosed]
    if not novel_because:
        return "anticipated", []
    joined = "; ".join(novel_because)
    return f"novel over the reference (limitation(s) not disclosed: {joined})", novel_because


class ChartBuilder:
    def __init__(self, client: LLMClient) -> None:
        self._client = client

    def chart(self, claim: str, reference: str) -> ChartResult:
        limitations = segment_claim(claim)
        raw = self._client.structured(
            schema=_MappingList,
            system=prompts.CHART_SYSTEM,
            user=prompts.chart_user(claim, [lim.text for lim in limitations], reference),
        )
        mappings = self._align(limitations, raw.mappings)
        mappings = self._ground(mappings, reference)
        verdict, novel_because = _verdict(mappings)
        return ChartResult(
            limitations=limitations,
            mappings=mappings,
            verdict=verdict,
            novel_because=novel_because,
        )

    @staticmethod
    def _align(limitations: list[Limitation], mappings: list[Mapping]) -> list[Mapping]:
        """Ensure exactly one mapping per limitation, in claim order.

        The LLM is asked to return one mapping per limitation, but we don't trust that: we key its
        mappings by normalised limitation text and rebuild the list from our deterministic
        limitations. Any limitation the model didn't map defaults to NOT disclosed.
        """
        by_text = {_norm(m.limitation): m for m in mappings}
        aligned: list[Mapping] = []
        for lim in limitations:
            m = by_text.get(_norm(lim.text))
            if m is None:
                aligned.append(Mapping(limitation=lim.text, disclosed=False, quote=None))
            else:
                # Normalise the limitation label back to our canonical text.
                aligned.append(m.model_copy(update={"limitation": lim.text}))
        return aligned

    @staticmethod
    def _ground(mappings: list[Mapping], reference: str) -> list[Mapping]:
        """Drop any disclosure whose quote isn't a verbatim substring of the reference."""
        hay = _norm(reference)
        grounded: list[Mapping] = []
        for m in mappings:
            if m.disclosed:
                quote = (m.quote or "").strip()
                if not quote or _norm(quote) not in hay:
                    grounded.append(m.model_copy(update={"disclosed": False, "quote": None}))
                    continue
            # not disclosed -> ensure no stray quote survives
            if not m.disclosed:
                grounded.append(m.model_copy(update={"quote": None}))
            else:
                grounded.append(m)
        return grounded


def chart(claim: str, reference: str, client: LLMClient) -> ChartResult:
    """Build a grounded claim chart for `claim` against prior-art `reference`."""
    return ChartBuilder(client).chart(claim, reference)
