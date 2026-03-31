"""Tests for feed_ursus.py"""
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false

import io
import json
from typing import Any, cast
from unittest.mock import Mock

import pytest
from httpx import AsyncClient, Response
from pysolr import Solr  # type: ignore

import feed_ursus.importer
from feed_ursus.importer import Importer
from feed_ursus.solr_record import UrsusSolrRecord

from . import fixtures  # pylint: disable=wrong-import-order


@pytest.fixture
def importer(monkeypatch: pytest.MonkeyPatch) -> Importer:
    monkeypatch.setattr(Importer, "collection_names_from_solr", lambda _self: {})

    importer = Importer(solr_url="")
    importer.solr_client = Mock(Solr)
    importer.async_client = Mock(AsyncClient)

    def mock_post(url: str, json: list[dict[Any, Any]]) -> Response:
        response = Mock(Response)
        response.is_error = False
        return response

    importer.async_client.post.side_effect = mock_post  # type: ignore

    return importer


class TestLoadCsv:
    """Tests for function load_csv"""

    def test_file_exists(self, importer: Importer) -> None:
        """gets the contents of a CSV file"""

        importer.load_csv(filenames=["tests/csv/anais_collection.csv"], batch=True)
        cast(Mock, importer.solr_client.add).assert_called_once()

    def test_file_does_not_exist(self, importer: Importer) -> None:
        """raises an error if file does not exist"""

        with pytest.raises(FileNotFoundError):
            importer.load_csv(filenames=["tests/fixtures/nonexistent.csv"], batch=True)


@pytest.fixture
def record() -> UrsusSolrRecord:
    return UrsusSolrRecord(
        ark_ssi="ark:/123/abc",
        title_tesim=["Title"],
        iiif_manifest_url_ssi="http://test.manifest/url/",
    )


class TestThumbnailFromManifest:
    """Function thumbnail_from_manifest"""

    def test_picks_folio_1r(
        self,
        monkeypatch: pytest.MonkeyPatch,
        importer: Importer,
        record: UrsusSolrRecord,
    ) -> None:
        "uses the page titled 'f. 001r', if found"
        monkeypatch.setattr(
            feed_ursus.importer.requests, "get", lambda x: fixtures.GOOD_MANIFEST
        )

        result = importer.thumbnail_from_manifest(record)
        assert (
            result
            == "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fzw07hs0c/full/!200,200/0/default.jpg"  # pylint: disable=line-too-long
        )

    def test_picks_first_page(
        self,
        monkeypatch: pytest.MonkeyPatch,
        importer: Importer,
        record: UrsusSolrRecord,
    ) -> None:
        "uses the first image if 'f. 001r' is not found"
        monkeypatch.setattr(
            feed_ursus.importer.requests,
            "get",
            lambda x: fixtures.MANIFEST_WITHOUT_F001R,
        )

        result = importer.thumbnail_from_manifest(record)
        assert (
            result
            == "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fhm957748/full/!200,200/0/default.jpg"  # pylint: disable=line-too-long
        )

    def test_request_fails(
        self,
        monkeypatch: pytest.MonkeyPatch,
        importer: Importer,
        record: UrsusSolrRecord,
    ) -> None:
        "returns None if HTTP request fails"

        monkeypatch.setattr(
            feed_ursus.importer.requests,
            "get",
            lambda x: fixtures.MockResponse(None, 404),
        )

        result = importer.thumbnail_from_manifest(record)
        assert result is None

    def test_manifest_without_images(
        self,
        monkeypatch: pytest.MonkeyPatch,
        importer: Importer,
        record: UrsusSolrRecord,
    ) -> None:
        "returns None if manifest contains no images"

        monkeypatch.setattr(
            feed_ursus.importer.requests,
            "get",
            lambda x: fixtures.MANIFEST_WITHOUT_IMAGES,
        )

        result = importer.thumbnail_from_manifest(record)
        assert result is None

    def test_bad_data(
        self,
        monkeypatch: pytest.MonkeyPatch,
        importer: Importer,
        record: UrsusSolrRecord,
    ) -> None:
        "returns None if manifest isn't parsable"

        monkeypatch.setattr(
            feed_ursus.importer.requests, "get", lambda x: fixtures.BAD_MANIFEST
        )

        result = importer.thumbnail_from_manifest(record)
        assert result is None

    def test_no_manifest_url(self, importer: Importer, record: UrsusSolrRecord) -> None:
        "returns None if the record doesn't include field 'iiif_manifest_url_ssi'"

        record.iiif_manifest_url_ssi = None
        result = importer.thumbnail_from_manifest(record)
        assert result is None


@pytest.mark.xfail
def test_collection_names_from_solr() -> None:
    raise NotImplementedError


class TestDump:
    def test_dump_calls_search_and_save_record(self, importer: Importer) -> None:
        output = io.StringIO()
        # Mock the solr search to return some hits and docs
        mock_docs = [
            {
                "id": "54321-89112",
                "title_tesim": ["Title"],
                "ark_ssi": "ark:/21198/12345",
            },
            {
                "id": "09876-89112",
                "title_tesim": ["Title"],
                "ark_ssi": "ark:/21198/67890",
            },
        ]
        mock_result = Mock()
        mock_result.docs = mock_docs
        mock_result.hits = 2
        mock_result.__iter__ = Mock(return_value=iter(mock_docs))
        cast(Mock, importer.solr_client).search.side_effect = [
            Mock(hits=2),  # First call for hits
            mock_result,  # Second call for docs
        ]

        importer.dump(output)

        # Check that search was called correctly
        assert cast(Mock, importer.solr_client).search.call_count == 2
        cast(Mock, importer.solr_client).search.assert_any_call("*:*", rows=0)
        cast(Mock, importer.solr_client).search.assert_any_call(
            "*:*",
            start=0,
            rows=250,
        )

        # Check output
        output_str = output.getvalue().strip()
        output_lines = output_str.split("\n")
        assert len(output_lines) == 2  # Two records

        # Parse JSON and check
        for line in output_lines:
            record = json.loads(line)
            assert "id" in record

    def test_save_record_valid(self, importer: Importer) -> None:
        output = io.StringIO()
        valid_record = {
            "id": "54321-89112",
            "title_tesim": ["Title"],
            "ark_ssi": "ark:/21198/12345",
        }

        importer.save_record(valid_record, output)

        output_str = output.getvalue().strip()
        assert output_str  # Should have output now

        parsed = json.loads(output_str)
        assert parsed == {
            **valid_record,
            "discover_access_group_ssim": ["public"],
            "download_access_person_ssim": ["public"],
            "has_model_ssim": "Work",
            "read_access_group_ssim": ["public"],
            "sort_title_ssort": "Title",
            "title_sim": ["Title"],
            "visibility_ssi": "open",
        }

    def test_save_record_invalid(self, importer: Importer) -> None:
        output = io.StringIO()
        invalid_record = {
            "id": None,  # Invalid id
        }

        importer.save_record(invalid_record, output)

        output_str = output.getvalue().strip()
        assert output_str == ""  # Since validation fails, no output
