"""Claim-chart prompt. Map each claim limitation to the prior-art reference, grounding every
'disclosed' finding in a verbatim quote from the reference — never invent a disclosure."""

from __future__ import annotations

CHART_SYSTEM = (
    "You are building a patent CLAIM CHART for a novelty (anticipation) analysis. You are given an "
    "independent patent claim, a list of its LIMITATIONS (elements / steps), and a single prior-art "
    "REFERENCE (free text). For EACH limitation, decide whether the reference discloses it.\n\n"
    "Rules:\n"
    "1. A limitation is 'disclosed' ONLY if the reference actually teaches it. If it is disclosed, "
    "you MUST provide a short VERBATIM quote copied exactly from the REFERENCE (the `quote` field) "
    "that shows the disclosure. If you cannot quote it from the reference, it is NOT disclosed and "
    "`quote` must be null.\n"
    "2. Do NOT paraphrase in the quote. Copy the words exactly as they appear in the reference.\n"
    "3. Anticipation is strict: every element must be found in this single reference. Do not import "
    "knowledge from outside the reference and do not reason about obviousness.\n"
    "4. Return exactly one mapping per limitation, using the limitation text as the `limitation` "
    "field.\n"
    "5. This is educational, not legal advice."
)


def chart_user(claim: str, limitations: list[str], reference: str) -> str:
    lims = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(limitations))
    return (
        f"CLAIM:\n{claim}\n\n"
        f"LIMITATIONS (map each one):\n{lims}\n\n"
        f"PRIOR-ART REFERENCE:\n{reference}\n\n"
        "For every limitation above, return {limitation, disclosed, quote}. The quote must be an "
        "exact substring of the REFERENCE, or null if not disclosed."
    )
