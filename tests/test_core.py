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


def test_segmentation_does_not_split_on_bare_and():
    """'and' inside a single limitation ('a processor and a memory') must NOT fracture it —
    only semicolons / newlines / 'wherein' / ', and' separate limitations."""
    claim = (
        "An apparatus comprising: a processor and a memory coupled to the processor; "
        "and a display that renders output from the processor and the memory."
    )
    lims = segment_claim(claim)
    assert [l.text for l in lims] == [
        "a processor and a memory coupled to the processor",
        "a display that renders output from the processor and the memory",
    ]


def test_segmentation_real_patent_claim_us5960411():
    """Claim 1 of US 5,960,411 (Amazon '1-Click', granted 1999, expired) — real granted claim
    language must segment into its actual method steps."""
    claim = (
        "A method of placing an order for an item comprising: under control of a client system, "
        "displaying information identifying the item; and in response to only a single action "
        "being performed, sending a request to order the item along with an identifier of a "
        "purchaser of the item to a server system; under control of a single-action ordering "
        "component of the server system, receiving the request; retrieving additional information "
        "previously stored for the purchaser identified by the identifier in the received request; "
        "and generating an order to purchase the requested item for the purchaser identified by "
        "the identifier in the received request using the retrieved additional information; and "
        "fulfilling the generated order to complete purchase of the item whereby the item is "
        "ordered without using a shopping cart ordering model."
    )
    lims = segment_claim(claim)
    texts = [l.text for l in lims]
    assert len(texts) == 6
    assert texts[0].startswith("under control of a client system")
    assert texts[1].startswith("in response to only a single action")
    assert texts[2].startswith("under control of a single-action ordering component")
    assert texts[3].startswith("retrieving additional information")
    assert texts[4].startswith("generating an order to purchase")
    assert texts[5].startswith("fulfilling the generated order")
    # No fragment starts with a leftover connector, and none fractured on a bare "and".
    assert not any(t.lower().startswith("and ") for t in texts)


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
