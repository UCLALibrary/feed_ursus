"""Tests for feed_ursus.py"""

# pylint: disable=no-self-use

import unittest.mock

import click.testing
import pytest  # type: ignore
import requests_mock

import feed_ursus.importer
from . import fixtures  # pylint: disable=wrong-import-order


class TestImporter:
    class TestLoadCsvs:
        """Tests for function load_csv"""

        def test_file_exists(self, monkeypatch):
            """gets the contents of a CSV file"""

            monkeypatch.setattr(feed_ursus.importer, "Solr", unittest.mock.Mock())

            feed_ursus.importer.Importer().load_csvs(["tests/csv/anais_collection.csv"])

        def test_file_does_not_exist(self, monkeypatch):
            """raises an error if file does not exist"""

            monkeypatch.setattr(feed_ursus.importer, "Solr", unittest.mock.Mock())
            runner = click.testing.CliRunner()

            with pytest.raises(FileNotFoundError):
                feed_ursus.importer.Importer().load_csvs(
                    ["tests/fixtures/nonexistent.csv"]
                )

    class TestMapFieldValue:
        """tests for function map_field_value"""

        def test_parses_array(self, monkeypatch):
            """parses value to an array of strings separated by '|~|'"""

            monkeypatch.setitem(
                feed_ursus.importer.mapper.FIELD_MAPPING,
                "test_ursus_field_tesim",
                "Test DLCS Field",
            )
            input_record = {"Test DLCS Field": "one|~|two|~|three"}
            result = feed_ursus.importer.Importer().map_field_value(
                input_record, "test_ursus_field_tesim"
            )
            assert result == [
                "one",
                "two",
                "three",
            ]

        def test_calls_function(self, monkeypatch):
            """If mapper defines a function map_[SOLR_NAME], calls that function."""
            # pylint: disable=no-member
            monkeypatch.setitem(
                feed_ursus.importer.mapper.FIELD_MAPPING,
                "test_ursus_field_tesim",
                lambda x: "lkghsdh",
            )
            result = feed_ursus.importer.Importer().map_field_value(
                {}, "test_ursus_field_tesim"
            )
            assert result == "lkghsdh"


def test_get_bare_field_name():
    """function get_bare_field_name"""

    assert (
        feed_ursus.importer.get_bare_field_name("human_readable_test_field_name_tesim")
        == "test_field_name"
    )


class TestMapRecord:
    """function map_record"""

    def test_maps_record(self, monkeypatch):
        """maps the record for Ursus"""
        monkeypatch.setattr(
            feed_ursus.importer.mapper,
            "FIELD_MAPPING",
            {
                "id": lambda r: r["Item ARK"],
                "test_ursus_field_tesim": "Test DLCS Field",
            },
        )
        result = feed_ursus.importer.Importer().map_record(
            {"Item ARK": "ark:/123/abc", "Test DLCS Field": "lasigd|~|asdfg"}
        )
        
        id = result.pop("ingest_id_ssi")
        assert isinstance(id, str)
        assert len(id) >= 10

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

    def test_sets_id(self):
        """sets 'id' to reversed ark"""
        result = feed_ursus.importer.Importer().map_record(
            {
                "Item ARK": "ark:/123/abc",
                "IIIF Manifest URL": "https://iiif.library.ucla.edu/ark%3A%2F123%2Fabc/manifest",
            }
        )
        assert result["id"] == "cba-321"

    def test_sets_thumbnail(self):
        """sets a thumbnail URL"""
        result = feed_ursus.importer.Importer().map_record(
            {
                "Item ARK": "ark:/123/abc",
                "IIIF Access URL": "https://test.iiif.server/url",
                "IIIF Manifest URL": "https://iiif.library.ucla.edu/ark%3A%2F123%2Fabc/manifest",
            }
        )
        assert (
            result["thumbnail_url_ss"]
            == "https://test.iiif.server/url/full/!200,200/0/default.jpg"
        )

    def test_sets_access(self):
        """sets permissive values for blacklight-access-control"""
        result = feed_ursus.importer.Importer().map_record(
            {
                "Item ARK": "ark:/123/abc",
                "Visibility": "open",
                "IIIF Manifest URL": "https://iiif.library.ucla.edu/ark%3A%2F123%2Fabc/manifest",
            }
        )
        assert result["discover_access_group_ssim"] == ["public"]
        assert result["read_access_group_ssim"] == ["public"]
        assert result["download_access_person_ssim"] == ["public"]

    def test_sets_iiif_manifest_url(self):
        """sets a IIIF manifest URL based on the ARK"""
        result = feed_ursus.importer.Importer().map_record(
            {
                "Item ARK": "ark:/123/abc",
                "IIIF Manifest URL": "https://iiif.library.ucla.edu/ark%3A%2F123%2Fabc/manifest",
            }
        )
        assert (
            result["iiif_manifest_url_ssi"]
            == "https://iiif.library.ucla.edu/ark%3A%2F123%2Fabc/manifest"
        )

    def test_sets_collection(self):
        """sets the collection name by using the collection row"""

        importer = feed_ursus.importer.Importer()
        importer.collection_names = {"noitcelloc-321": "Test Collection KGSL"}

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
    def test_sets_facet_fields(self, column_name, facet_field_name):
        """Copies *_tesim to *_sim fields for facets"""
        value = "value aksjg"
        result = feed_ursus.importer.Importer().map_record(
            {
                "Item ARK": "ark:/123/abc",
                "IIIF Manifest URL": "https://iiif.library.ucla.edu/ark%3A%2F123%2Fabc/manifest",
                column_name: value,
            }
        )
        assert result[facet_field_name] == [value]


class TestThumbnailFromManifest:
    """Function thumbnail_from_manifest"""

    record = {"iiif_manifest_url_ssi": "http://test.manifest/url/"}

    def test_picks_folio_1r(self):
        "uses the page titled 'f. 001r', if found"

        with requests_mock.Mocker() as m:
            m.get("http://test.manifest/url/", json=fixtures.GOOD_MANIFEST.json_data)
            result = feed_ursus.importer.thumbnail_from_manifest(self.record)
        
        assert (
            result
            == "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fzw07hs0c/full/!200,200/0/default.jpg"  # pylint: disable=line-too-long
        )

    def test_picks_first_page(self, monkeypatch):
        "uses the first image if 'f. 001r' is not found"

        with requests_mock.Mocker() as m:
            m.get("http://test.manifest/url/", json=fixtures.MANIFEST_WITHOUT_F001R.json_data
        )
            result = feed_ursus.importer.thumbnail_from_manifest(self.record)
        
        assert (
            result
            == "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fhm957748/full/!200,200/0/default.jpg"  # pylint: disable=line-too-long
        )

    def test_request_fails(self, monkeypatch):
        "returns None if HTTP request fails"

        monkeypatch.setattr(
            feed_ursus.importer.requests, "get", lambda x: fixtures.MockResponse(None, 404)
        )

        result = feed_ursus.importer.thumbnail_from_manifest(self.record)
        assert result is None

    def test_manifest_without_images(self, monkeypatch):
        "returns None if manifest contains no images"

        monkeypatch.setattr(
            feed_ursus.importer.requests, "get", lambda x: fixtures.MANIFEST_WITHOUT_IMAGES
        )

        result = feed_ursus.importer.thumbnail_from_manifest(self.record)
        assert result is None

    def test_bad_data(self, monkeypatch):
        "returns None if manifest isn't parsable"

        monkeypatch.setattr(feed_ursus.importer.requests, "get", lambda x: fixtures.BAD_MANIFEST)

        result = feed_ursus.importer.thumbnail_from_manifest(self.record)
        assert result is None

    def test_no_manifest_url(self):
        "returns None if the record doesn't include field 'iiif_m'"

        result = feed_ursus.importer.thumbnail_from_manifest({})
        assert result is None
