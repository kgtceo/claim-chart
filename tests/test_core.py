"""Core offline tests — segmentation, the grounding pass (drops fabricated quotes), verdict logic.

All tests run with a FAKE client (no API key, no network). The grounding filter is the killer
safety feature: a 'disclosed' mapping whose quote isn't a verbatim substring of the reference is
forced to NOT disclosed.
"""

from __future__ import annotations

from conftest import FakeClient

from claim_chart.chart import ChartBuilder, _MappingList, segment_claim
from claim_chart.models import Mapping

CLAIM = (
    "A method comprising: storing data in an encrypted vault; "
    "deriving a key from a passphrase; and syncing the vault across devices."
)


def _limits():
    return segment_claim(CLAIM)


def _payload(mappings):
    return _MappingList(mappings=mappings)


def test_segmentation_splits_limitations():
    lims = _limits()
    assert [l.text for l in lims] == [
        "storing data in an encrypted vault",
        "deriving a key from a passphrase",
        "syncing the vault across devices",
    ]
    assert [l.index for l in lims] == [1, 2, 3]


def test_grounded_disclosure_kept():
    reference = "The system stores data in an encrypted vault and derives a key from a passphrase, but never syncs."
    lims = _limits()
    payload = _payload([
        Mapping(limitation=lims[0].text, disclosed=True, quote="stores data in an encrypted vault"),
        Mapping(limitation=lims[1].text, disclosed=True, quote="derives a key from a passphrase"),
        Mapping(limitation=lims[2].text, disclosed=False, quote=None),
    ])
    result = ChartBuilder(FakeClient(payload)).chart(CLAIM, reference)
    disclosed = [m.disclosed for m in result.mappings]
    assert disclosed == [True, True, False]
    # Grounded quotes survive.
    assert result.mappings[0].quote == "stores data in an encrypted vault"


def test_fabricated_quote_dropped():
    """A 'disclosed' mapping whose quote is NOT in the reference is forced to not-disclosed."""
    reference = "The system stores data in an encrypted vault and derives a key from a passphrase, but never syncs."
    lims = _limits()
    payload = _payload([
        Mapping(limitation=lims[0].text, disclosed=True, quote="stores data in an encrypted vault"),
        Mapping(limitation=lims[1].text, disclosed=True, quote="derives a key from a passphrase"),
        # Hallucinated: this phrase is nowhere in the reference.
        Mapping(limitation=lims[2].text, disclosed=True, quote="syncs the vault across all your devices in real time"),
    ])
    result = ChartBuilder(FakeClient(payload)).chart(CLAIM, reference)
    # The fabricated disclosure is dropped: not disclosed, no quote.
    assert result.mappings[2].disclosed is False
    assert result.mappings[2].quote is None
    # And the verdict reflects the surviving gap.
    assert result.verdict.startswith("novel over the reference")
    assert lims[2].text in result.novel_because


def test_case_insensitive_whitespace_grounding():
    """Grounding normalises case + whitespace, so a real quote with different casing/spacing holds."""
    reference = "The apparatus STORES   data in an encrypted vault."
    lims = _limits()
    payload = _payload([
        Mapping(limitation=lims[0].text, disclosed=True, quote="stores data in an encrypted vault"),
        Mapping(limitation=lims[1].text, disclosed=False, quote=None),
        Mapping(limitation=lims[2].text, disclosed=False, quote=None),
    ])
    result = ChartBuilder(FakeClient(payload)).chart(CLAIM, reference)
    assert result.mappings[0].disclosed is True


def test_verdict_anticipated_when_all_disclosed():
    reference = (
        "The system stores data in an encrypted vault, derives a key from a passphrase, "
        "and syncs the vault across devices continuously."
    )
    lims = _limits()
    payload = _payload([
        Mapping(limitation=lims[0].text, disclosed=True, quote="stores data in an encrypted vault"),
        Mapping(limitation=lims[1].text, disclosed=True, quote="derives a key from a passphrase"),
        Mapping(limitation=lims[2].text, disclosed=True, quote="syncs the vault across devices"),
    ])
    result = ChartBuilder(FakeClient(payload)).chart(CLAIM, reference)
    assert result.verdict == "anticipated"
    assert result.novel_because == []


def test_missing_mapping_defaults_to_not_disclosed():
    """If the model omits a limitation, alignment defaults it to NOT disclosed (fail-safe)."""
    reference = "The system stores data in an encrypted vault."
    lims = _limits()
    payload = _payload([
        Mapping(limitation=lims[0].text, disclosed=True, quote="stores data in an encrypted vault"),
        # limitations 2 and 3 omitted entirely
    ])
    result = ChartBuilder(FakeClient(payload)).chart(CLAIM, reference)
    assert len(result.mappings) == 3
    assert result.mappings[1].disclosed is False
    assert result.mappings[2].disclosed is False
    assert result.verdict.startswith("novel over the reference")
