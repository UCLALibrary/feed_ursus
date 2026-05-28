from typing import Any

import pytest
from dateutil.parser import isoparse

from feed_ursus.ursus_solr_record import UrsusSolrRecord

MOCK_NOW = "2026-05-19T19:20:00Z"


@pytest.fixture(autouse=True)
def patch_now(monkeypatch: pytest.MonkeyPatch):
    def mock_now(*args: Any, **kwargs: Any):
        return isoparse(MOCK_NOW)

    monkeypatch.setattr(UrsusSolrRecord, "_now", mock_now)


@pytest.fixture
def minimal_csv_record():
    return {
        "Item ARK": "ark:/123/test",
        "Title": "Test Item",
    }


@pytest.fixture
def minimal_solr_record():
    return {
        "ark_ssi": "ark:/123/test",
        "title_tesim": "Test Item",
    }
