# mypy: disallow_untyped_defs=False
"""Tests for feed_ursus.py"""

# pylint: disable=no-self-use

from unittest.mock import Mock, call

import pytest  # type: ignore
from httpx import AsyncClient, Response
from pysolr import Solr  # type: ignore

import feed_ursus.importer
from feed_ursus.importer import Importer, collate_child_works, get_bare_field_name

from . import fixtures  # pylint: disable=wrong-import-order


@pytest.fixture
def importer() -> Importer:
    importer = Importer(solr_url="", mapper_name="dlp")
    importer.solr_client = Mock(Solr)
    importer.async_client = Mock(AsyncClient)

    def mock_post(url: str, json: list[dict]):
        response = Mock(Response)
        response.is_error = False
        return response

    importer.async_client.post.side_effect = mock_post  # type: ignore

    return importer


class TestLoadCsv:
    """Tests for function load_csv"""

    def test_file_exists(self, importer):
        """gets the contents of a CSV file"""

        importer.load_csv(filenames=["tests/csv/anais_collection.csv"], batch=True)
        importer.solr_client.add.assert_called_once()

    def test_file_does_not_exist(self, importer):
        """raises an error if file does not exist"""

        with pytest.raises(FileNotFoundError):
            importer.load_csv(filenames=["tests/fixtures/nonexistent.csv"], batch=True)


class TestLoadCsvAsync:
    """Tests for function load_csv"""

    @pytest.mark.asyncio
    async def test_file_exists(self, importer):
        """gets the contents of a CSV file"""

        await importer.load_csv_async(filenames=["tests/csv/anais_collection.csv"])
        importer.async_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_file_does_not_exist(self, importer):
        """raises an error if file does not exist"""

        with pytest.raises(FileNotFoundError):
            await importer.load_csv_async(filenames=["tests/fixtures/nonexistent.csv"])


class TestAddToSolr:
    @pytest.mark.asyncio
    async def test_divides_batch_and_retries(self, importer: Importer, capfd):
        batch = [{"id": n} for n in range(4)]

        def mock_post(url: str, json: list[dict]):
            response = Mock(Response)
            if batch[2] in json:
                response.is_error = True
                response.json = lambda: {"error": {"msg": "abcxyz"}}
                return response
            else:
                response.is_error = False
                return response

        importer.async_client.post.side_effect = mock_post  # type: ignore

        await importer.add_to_solr(batch)

        importer.async_client.post.assert_has_calls(  # type: ignore
            [
                call("/update?commit=true", json=batch),
                call("/update?commit=true", json=batch[0:2]),
                call("/update?commit=true", json=batch[2:4]),
                call("/update?commit=true", json=[batch[2]]),
                call("/update?commit=true", json=[batch[3]]),
            ]
        )
        assert "Error adding record 2:" in capfd.readouterr().out


class TestMapFieldValue:
    """tests for function map_field_value"""

    def test_parses_array(self, monkeypatch, importer):
        """parses value to an array of strings separated by '|~|'"""

        monkeypatch.setitem(
            importer.mapper.FIELD_MAPPING, "test_ursus_field_tesim", "Test DLCS Field"
        )
        input_record = {"Test DLCS Field": "one|~|two|~|three"}
        result = importer.map_field_value(
            input_record,
            "test_ursus_field_tesim",
        )
        assert result == [
            "one",
            "two",
            "three",
        ]

    def test_calls_function(self, importer, monkeypatch):
        """If mapper defines a function map_[SOLR_NAME], calls that function."""
        # pylint: disable=no-member
        monkeypatch.setitem(
            importer.mapper.FIELD_MAPPING,
            "test_ursus_field_tesim",
            lambda x: "lkghsdh",
        )
        result = importer.map_field_value({}, "test_ursus_field_tesim")
        assert result == "lkghsdh"


def test_get_bare_field_name():
    """function get_bare_field_name"""

    assert (
        get_bare_field_name("human_readable_test_field_name_tesim") == "test_field_name"
    )


class TestMapRecord:
    """function map_record"""

    COLLECTION_NAMES = {"noitcelloc-321": "Test Collection KGSL"}

    def test_maps_record(self, importer, monkeypatch):
        """maps the record for Ursus"""
        monkeypatch.setattr(
            importer.mapper,
            "FIELD_MAPPING",
            {
                "id": lambda r: r["Item ARK"],
                "test_ursus_field_tesim": "Test DLCS Field",
            },
        )
        result = importer.map_record(
            {"Item ARK": "ark:/123/abc", "Test DLCS Field": "lasigd|~|asdfg"}
        )

        assert result.pop("ingest_id_ssi")
        assert result == {
            "features_sim": None,
            "genre_sim": None,
            "human_readable_language_sim": None,
            "human_readable_resource_type_sim": None,
            "id": "ark:/123/abc",
            "location_sim": None,
            "member_of_collections_ssim": [],
            "named_subject_sim": None,
            "place_of_origin_sim": None,
            "script_sim": None,
            "subject_sim": None,
            "support_sim": None,
            "test_ursus_field_tesim": ["lasigd", "asdfg"],
            "thumbnail_url_ss": None,
            "writing_system_sim": None,
            "year_isim": [],
            "names_sim": None,
            "architect_sim": None,
            "author_sim": None,
            "calligrapher_sim": None,
            "combined_subject_ssim": [],
            "commentator_sim": None,
            "composer_sim": None,
            "editor_sim": None,
            "engraver_sim": None,
            "illuminator_sim": None,
            "illustrator_sim": None,
            "lyricist_sim": None,
            "printmaker_sim": None,
            "rubricator_sim": None,
            "scribe_sim": None,
            "uniform_title_sim": None,
            "translator_sim": None,
            "associated_name_sim": None,
            "form_sim": None,
            "date_dtsim": [],
            "header_index_tesim": [],
            "name_fields_index_tesim": [],
            "keywords_tesim": [],
            "keywords_sim": [],
            "collection_sim": None,
            "record_origin_ssi": "feed_ursus",
        }

    def test_sets_id(self, importer):
        """sets 'id' to reversed ark"""
        result = importer.map_record(
            {
                "Item ARK": "ark:/123/abc",
                "IIIF Manifest URL": "https://iiif.library.ucla.edu/ark%3A%2F123%2Fabc/manifest",
            }
        )
        assert result["id"] == "cba-321"

    def test_sets_thumbnail(self, importer):
        """sets a thumbnail URL"""
        result = importer.map_record(
            {
                "Item ARK": "ark:/123/abc",
                "IIIF Access URL": "https://test.iiif.server/url",
                "IIIF Manifest URL": "https://iiif.library.ucla.edu/ark%3A%2F123%2Fabc/manifest",
            },
        )
        assert (
            result["thumbnail_url_ss"]
            == "https://test.iiif.server/url/full/!200,200/0/default.jpg"
        )

    def test_sets_access(self, importer):
        """sets permissive values for blacklight-access-control"""
        result = importer.map_record(
            {
                "Item ARK": "ark:/123/abc",
                "Visibility": "open",
                "IIIF Manifest URL": "https://iiif.library.ucla.edu/ark%3A%2F123%2Fabc/manifest",
            },
        )
        assert result["discover_access_group_ssim"] == ["public"]
        assert result["read_access_group_ssim"] == ["public"]
        assert result["download_access_person_ssim"] == ["public"]

    def test_sets_iiif_manifest_url(self, importer):
        """sets a IIIF manifest URL based on the ARK"""
        result = importer.map_record(
            {
                "Item ARK": "ark:/123/abc",
                "IIIF Manifest URL": "https://iiif.library.ucla.edu/ark%3A%2F123%2Fabc/manifest",
            }
        )
        assert (
            result["iiif_manifest_url_ssi"]
            == "https://iiif.library.ucla.edu/ark%3A%2F123%2Fabc/manifest"
        )

    def test_sets_collection(self, importer):
        """sets the collection name by using the collection row"""

        importer.collection_names = self.COLLECTION_NAMES
        result = importer.map_record(
            {
                "Item ARK": "ark:/123/abc",
                "Parent ARK": "ark:/123/collection",
                "IIIF Manifest URL": "https://iiif.library.ucla.edu/ark%3A%2F123%2Fabc/manifest",
            }
        )
        assert result["member_of_collections_ssim"] == ["Test Collection KGSL"]

    @pytest.mark.parametrize(
        ["column_name", "facet_field_name"],
        [
            ("Coverage.geographic", "location_sim"),
            ("Language", "human_readable_language_sim"),
            ("Name.subject", "named_subject_sim"),
            ("Subject", "subject_sim"),
            ("Type.genre", "genre_sim"),
            ("Type.typeOfResource", "human_readable_resource_type_sim"),
        ],
    )
    def test_sets_facet_fields(self, column_name, facet_field_name, importer):
        """Copies *_tesim to *_sim fields for facets"""
        value = "value aksjg"
        result = importer.map_record(
            {
                "Item ARK": "ark:/123/abc",
                "IIIF Manifest URL": "https://iiif.library.ucla.edu/ark%3A%2F123%2Fabc/manifest",
                column_name: value,
            }
        )
        assert result[facet_field_name] == [value]


class TestThumbnailFromChild:
    """Tests for feed_ursus.thumbnail_from_child."""

    def test_uses_title(self, importer):
        """Returns the thumbnail from child row 'f. 001r'"""

        importer.child_works = collate_child_works(
            {
                "ark:/work/1": {
                    "Object Type": "Work",
                    "Item ARK": "ark:/work/1",
                    "Parent ARK": "ark:/collection/1",
                    "Thumbnail URL": None,
                    "Title": None,
                },
                "ark:/child/2": {
                    "Object Type": "ChildWork",
                    "Item ARK": "ark:/child/2",
                    "Parent ARK": "ark:/work/1",
                    "Thumbnail URL": "/thumb2.jpg",
                    "Title": "f. 001v",
                },
                "ark:/child/1": {
                    "Object Type": "ChildWork",
                    "Item ARK": "ark:/child/1",
                    "Parent ARK": "ark:/work/1",
                    "Thumbnail URL": "/thumb1.jpg",
                    "Title": "f. 001r",
                },
            }
        )
        record = {"ark_ssi": "ark:/work/1"}

        result = importer.thumbnail_from_child(record)
        assert result == "/thumb1.jpg"

    def test_uses_mapper(self, importer):
        """Uses the mapper to generate a thumbnail from access_copy, if necessary"""

        importer.child_works = collate_child_works(
            {
                "ark:/work/1": {
                    "Item ARK": "ark:/work/1",
                    "Parent ARK": "ark:/collection/1",
                    "IIIF Access URL": None,
                    "Title": None,
                    "Object Type": "Work",
                },
                "ark:/child/1": {
                    "Item ARK": "ark:/child/1",
                    "Parent ARK": "ark:/work/1",
                    "IIIF Access URL": "http://iiif.url/123",
                    "Title": "f. 001r",
                    "Object Type": "ChildWork",
                },
            }
        )
        record = {"ark_ssi": "ark:/work/1"}

        result = importer.thumbnail_from_child(record)
        assert result == "http://iiif.url/123/full/!200,200/0/default.jpg"

    def test_defaults_to_first(self, importer):
        """Returns the thumbnail from first child row if it can't find 'f. 001r'"""
        importer.child_works = collate_child_works(
            {
                "ark:/work/1": {
                    "Item ARK": "ark:/work/1",
                    "Parent ARK": "ark:/collection/1",
                    "Thumbnail URL": None,
                    "Title": None,
                    "Object Type": "Work",
                },
                "ark:/child/2": {
                    "Item ARK": "ark:/child/2",
                    "Parent ARK": "ark:/work/1",
                    "Thumbnail URL": "/thumb2.jpg",
                    "Title": "f. 001v",
                    "Object Type": "ChildWork",
                },
                "ark:/child/1": {
                    "Item ARK": "ark:/child/1",
                    "Parent ARK": "ark:/work/1",
                    "Thumbnail URL": "/thumb1.jpg",
                    "Title": "f. 002r",
                    "Object Type": "ChildWork",
                },
            }
        )
        record = {"ark_ssi": "ark:/work/1"}

        result = importer.thumbnail_from_child(record)
        assert result == "/thumb2.jpg"

    def test_with_no_children_returns_none(self, importer):
        """If there are no child rows, return None"""
        importer.child_works = collate_child_works(
            {
                "ark:/work/1": {
                    "Item ARK": "ark:/work/1",
                    "Parent ARK": "ark:/collection/1",
                    "Thumbnail URL": None,
                    "Title": None,
                    "Object Type": "Work",
                },
            }
        )
        record = {"ark_ssi": "ark:/work/1"}

        result = importer.thumbnail_from_child(record)
        assert result is None


@pytest.fixture
def record():
    return {"iiif_manifest_url_ssi": "http://test.manifest/url/"}


class TestThumbnailFromManifest:
    """Function thumbnail_from_manifest"""

    def test_picks_folio_1r(self, monkeypatch, importer, record):
        "uses the page titled 'f. 001r', if found"
        monkeypatch.setattr(
            feed_ursus.importer.requests, "get", lambda x: fixtures.GOOD_MANIFEST
        )

        result = importer.thumbnail_from_manifest(record)
        assert (
            result
            == "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fzw07hs0c/full/!200,200/0/default.jpg"  # pylint: disable=line-too-long
        )

    def test_picks_first_page(self, monkeypatch, importer, record):
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

    def test_request_fails(self, monkeypatch, importer, record):
        "returns None if HTTP request fails"

        monkeypatch.setattr(
            feed_ursus.importer.requests,
            "get",
            lambda x: fixtures.MockResponse(None, 404),
        )

        result = importer.thumbnail_from_manifest(record)
        assert result is None

    def test_manifest_without_images(self, monkeypatch, importer, record):
        "returns None if manifest contains no images"

        monkeypatch.setattr(
            feed_ursus.importer.requests,
            "get",
            lambda x: fixtures.MANIFEST_WITHOUT_IMAGES,
        )

        result = importer.thumbnail_from_manifest(record)
        assert result is None

    def test_bad_data(self, monkeypatch, importer, record):
        "returns None if manifest isn't parsable"

        monkeypatch.setattr(
            feed_ursus.importer.requests, "get", lambda x: fixtures.BAD_MANIFEST
        )

        result = importer.thumbnail_from_manifest(record)
        assert result is None

    def test_no_manifest_url(self, importer):
        "returns None if the record doesn't include field 'iiif_manifest_url_ssi'"

        result = importer.thumbnail_from_manifest({})
        assert result is None
