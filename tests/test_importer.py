"""Tests for feed_ursus.py"""
# pyright: reportUnknownArgumentType=false
# pyright: reportUnknownLambdaType=false
# pyright: reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false

import io
import json
from typing import cast
from unittest.mock import Mock

import pytest
from pysolr import Solr  # type: ignore

import feed_ursus.importer
from feed_ursus.importer import Importer
from feed_ursus.ursus_solr_record import UrsusSolrRecord
from feed_ursus.util import UnknownItemError
from tests.test_ursus_solr_record import MINIMAL_RECORD

from . import fixtures  # pylint: disable=wrong-import-order


@pytest.fixture
def importer(monkeypatch: pytest.MonkeyPatch) -> Importer:
    monkeypatch.setattr(Importer, "collection_names_from_solr", lambda _self: {})

    importer = Importer(solr_url="")
    importer.solr_client = Mock(Solr)
    importer.solr_client.url = "http://mock.url/solr/core"

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


class TestMapRecord:
    class TestThumbnailUrl:
        def test_from_access_copy(self, importer: Importer) -> None:
            result = importer.map_record(
                {
                    **MINIMAL_RECORD,
                    "IIIF Access URL": "https://iiif.library.ucla.edu/iiif/2/ark%3A%2F21198%2F123abc",
                }
            )
            assert (
                result.thumbnail_url_ss
                == "https://iiif.library.ucla.edu/iiif/2/ark%3A%2F21198%2F123abc/full/!200,200/0/default.jpg"
            )

        def test_with_bad_access_copy(self, importer: Importer) -> None:
            result = importer.map_record(
                {
                    **MINIMAL_RECORD,
                    "IIIF Access URL": "https://wowza.library.ucla.edu/iiif_av_public/definst/mp4:MEAP/pairtree_root/21/19/8=/z1/j7/7t/4n/21198=z1j77t4n/ark%2B=21198=z1j77t4n.mp4%7B%7D",
                }
            )

            assert result.thumbnail_url_ss is None

        def test_calls_thumbnail_from_manifest(
            self, importer: Importer, monkeypatch: pytest.MonkeyPatch
        ) -> None:
            row = {
                **MINIMAL_RECORD,
                "Type.typeOfResource": "still image",
                "IIIF Manifest URL": "https://nowhere.really/iiif/2/abcxyz",
            }
            expected = "https://test.url/thumbnail.jpg"
            monkeypatch.setattr(
                importer,
                "thumbnail_from_manifest",
                Mock(return_value=expected),
            )
            result = importer.map_record(row)
            assert result.thumbnail_url_ss == expected
            cast(Mock, importer.thumbnail_from_manifest).assert_called_once()

        def test_streaming_no_thumbnail_from_manifest(
            self, importer: Importer, monkeypatch: pytest.MonkeyPatch
        ) -> None:
            row = {
                **MINIMAL_RECORD,
                "Type.typeOfResource": "moving image",
                "IIIF Manifest URL": "https://nowhere.really/iiif/2/abcxyz",
            }
            monkeypatch.setattr(
                importer, "thumbnail_from_manifest", Mock(return_value="called")
            )

            result = importer.map_record(row)
            assert result.thumbnail_url_ss is None
            cast(Mock, importer.thumbnail_from_manifest).assert_not_called


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


class TestGetTitles:
    """Tests for Importer.get_titles"""

    def test_empty_and_missing_values_return_none(self, importer: Importer) -> None:
        assert importer.get_titles({"Parent ARK": ""}, "Parent ARK") is None
        assert importer.get_titles({"Parent ARK": None}, "Parent ARK") is None  # type: ignore
        assert importer.get_titles({}, "Parent ARK") is None

    def test_known_arks_are_resolved_from_cache(self, importer: Importer) -> None:
        importer.titles = {
            "ark:/21198/one": "One",
            "ark:/21198/two": "Two",
        }
        result = importer.get_titles(
            {"Parent ARK": "ark:/21198/one|~|ark:/21198/two"}, "Parent ARK"
        )

        assert result == ["One", "Two"]

    def test_fetches_missing_ark_titles_from_solr(
        self, importer: Importer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        importer.titles = {"ark:/21198/one": "One"}

        class FakeResponse:
            def json(self):
                return {
                    "response": {
                        "docs": [
                            {
                                "ark_ssi": "ark:/21198/two",
                                "title_tesim": ["Two"],
                            }
                        ]
                    }
                }

        monkeypatch.setattr(
            feed_ursus.importer.requests, "get", lambda *args, **kwargs: FakeResponse()
        )

        result = importer.get_titles(
            {"Parent ARK": "ark:/21198/one|~|ark:/21198/two"}, "Parent ARK"
        )

        assert result == ["One", "Two"]

    def test_missing_titles_raise_unknown_item_error(
        self, importer: Importer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        importer.titles = {"ark:/21198/one": "One"}

        class FakeResponse:
            def json(self):
                return {"response": {"docs": []}}

        monkeypatch.setattr(
            feed_ursus.importer.requests, "get", lambda *args, **kwargs: FakeResponse()
        )

        with pytest.raises(UnknownItemError):
            importer.get_titles(
                {"Parent ARK": "ark:/21198/one|~|ark:/21198/two"}, "Parent ARK"
            )
