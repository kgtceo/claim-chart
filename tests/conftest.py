"""Offline test doubles — no API key, no network."""

from __future__ import annotations

import pytest

from claim_chart.config import Settings


class FakeClient:
    """Returns a scripted schema instance so the grounding pass runs offline.

    `payload` is whatever the caller's `schema` should validate to — for the chart pipeline that is
    a `_MappingList`. We just hand it back, mimicking a successful structured call.
    """

    def __init__(self, payload) -> None:
        self._payload = payload
        self.calls = 0

    def structured(self, *, schema, system, user, model=None):
        self.calls += 1
        return self._payload


@pytest.fixture
def settings() -> Settings:
    return Settings(anthropic_api_key="test-key")
