"""Tests for feed_ursus.py"""
# pylint: disable=no-self-use


import pytest  # type: ignore
from pandas import DataFrame  # type: ignore
from pysolr import Solr  # type: ignore
import feed_ursus
import test.fixtures as fixtures  # pylint: disable=wrong-import-order


@pytest.mark.xfail()
def test_load_csv():
    """test for function load_csv"""
    raise NotImplementedError


class TestMapFieldValue:
    """tests for function map_field_value"""

    def test_parses_array(self, monkeypatch):
        """parses value to an array of strings separated by '|~|'"""

        monkeypatch.setitem(
            feed_ursus.mapper.FIELD_MAPPING, "test_ursus_field_tesim", "Test DLCS Field"
        )
        input_record = {"Test DLCS Field": "one|~|two|~|three"}
        result = feed_ursus.map_field_value(
            input_record, "test_ursus_field_tesim", config={}
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
            feed_ursus.mapper.FIELD_MAPPING,
            "test_ursus_field_tesim",
            lambda x: "lkghsdh",
        )
        result = feed_ursus.map_field_value({}, "test_ursus_field_tesim", config={})
        assert result == "lkghsdh"


def test_get_bare_field_name():
    """function get_bare_field_name"""

    assert (
        feed_ursus.get_bare_field_name("human_readable_test_field_name_tesim")
        == "test_field_name"
    )


class TestMapRecord:
    """function map_record"""

    CONFIG = {"collection_names": {"ark:/123/collection": "Test Collection KGSL"}}
    solr_client = Solr("http://localhost:6983/solr/californica", always_commit=True)
    def test_maps_record(self, monkeypatch):
        """maps the record for Ursus"""
        monkeypatch.setattr(
            feed_ursus.mapper,
            "FIELD_MAPPING",
            {
                "id": lambda r: r["Item ARK"],
                "test_ursus_field_tesim": "Test DLCS Field",
            },
        )
        result = feed_ursus.map_record(
            {"Item ARK": "ark:/123/abc", "Test DLCS Field": "lasigd|~|asdfg"},
            self.solr_client, config=self.CONFIG,
        )

        assert result == {
            "features_sim": None,
            "genre_sim": None,
            "human_readable_language_sim": None,
            "human_readable_resource_type_sim": None,
            "id": "ark:/123/abc",
            "location_sim": None,
            "member_of_collections_ssim": None,
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
            "keywords_sim": []
            }

    def test_sets_id(self):
        """sets 'id' equal to 'Item ARK'/'ark_ssi'"""
        result = feed_ursus.map_record(
            {"Item ARK": "ark:/123/abc"}, self.solr_client, config=self.CONFIG,
        )
        assert result["id"] == "ark:/123/abc"

    def test_sets_thumbnail(self):
        """sets a thumbnail URL"""
        result = feed_ursus.map_record(
            {
                "Item ARK": "ark:/123/abc",
                "IIIF Access URL": "https://test.iiif.server/url",
            },
            self.solr_client,
            config=self.CONFIG,
        )
        assert (
            result["thumbnail_url_ss"]
            == "https://test.iiif.server/url/full/!200,200/0/default.jpg"
        )

    def test_sets_access(self):
        """sets permissive values for blacklight-access-control"""
        result = feed_ursus.map_record(
            {"Item ARK": "ark:/123/abc"}, self.solr_client, config=self.CONFIG,
        )
        assert result["discover_access_group_ssim"] == ["public"]
        assert result["read_access_group_ssim"] == ["public"]
        assert result["download_access_person_ssim"] == ["public"]

    def test_sets_iiif_manifest_url(self):
        """sets a IIIF manifest URL based on the ARK"""
        result = feed_ursus.map_record(
            {"Item ARK": "ark:/123/abc"}, self.solr_client, config=self.CONFIG,
        )
        assert (
            result["iiif_manifest_url_ssi"]
            == "https://iiif.library.ucla.edu/ark%3A%2F123%2Fabc/manifest"
        )

    def test_sets_collection(self):
        """sets the collection name by using the collection row"""

        result = feed_ursus.map_record(
            {"Item ARK": "ark:/123/abc", "Parent ARK": "ark:/123/collection"},
            self.solr_client,
            config=self.CONFIG,
        )
        assert result["dlcs_collection_name_tesim"] == ["Test Collection KGSL"]
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
        result = feed_ursus.map_record(
            {"Item ARK": "ark:/123/abc", column_name: value},
            self.solr_client,
            config=self.CONFIG,
        )
        assert result[facet_field_name] == [value]


class TestThumbnailFromChild:
    """Tests for feed_ursus.thumbnail_from_child."""

    def test_uses_title(self):
        """Returns the thumbnail from child row 'f. 001r'"""

        data = DataFrame(
            data={
                "Item ARK": ["ark:/work/1", "ark:/child/2", "ark:/child/1"],
                "Parent ARK": ["ark:/collection/1", "ark:/work/1", "ark:/work/1"],
                "Thumbnail URL": [None, "/thumb2.jpg", "/thumb1.jpg"],
                "Title": [None, "f. 001v", "f. 001r"],
            }
        )
        record = {"ark_ssi": "ark:/work/1"}
        result = feed_ursus.thumbnail_from_child(record, config={"data_frame": data})
        assert result == "/thumb1.jpg"

    def test_uses_mapper(self):
        """Uses the mapper to generate a thumbnail from access_copy, if necessary"""

        data = DataFrame(
            data={
                "Item ARK": ["ark:/work/1", "ark:/child/1"],
                "Parent ARK": ["ark:/collection/1", "ark:/work/1"],
                "IIIF Access URL": [None, "http://iiif.url/123"],
                "Title": [None, "f. 001r"],
            }
        )
        record = {"ark_ssi": "ark:/work/1"}
        result = feed_ursus.thumbnail_from_child(record, config={"data_frame": data})
        assert result == "http://iiif.url/123/full/!200,200/0/default.jpg"

    def test_defaults_to_first(self):
        """Returns the thumbnail from first child row if it can't find 'f. 001r'"""
        data = DataFrame(
            data={
                "Item ARK": ["ark:/work/1", "ark:/child/2", "ark:/child/1"],
                "Parent ARK": ["ark:/collection/1", "ark:/work/1", "ark:/work/1"],
                "Thumbnail URL": [None, "/thumb2.jpg", "/thumb1.jpg"],
                "Title": [None, "f. 001v", "f. 002r"],
            }
        )
        record = {"ark_ssi": "ark:/work/1"}
        result = feed_ursus.thumbnail_from_child(record, config={"data_frame": data})
        assert result == "/thumb2.jpg"

    def test_with_no_children_returns_none(self):
        """If there are no child rows, return None"""
        data = DataFrame(
            data={
                "Item ARK": ["ark:/work/1"],
                "Parent ARK": ["ark:/collection/1"],
                "Thumbnail URL": [None],
                "Title": [None],
            }
        )
        record = {"ark_ssi": "ark:/work/1"}
        result = feed_ursus.thumbnail_from_child(record, config={"data_frame": data})
        assert result is None


class TestThumbnailFromManifest:
    """Function thumbnail_from_manifest"""

    record = {"iiif_manifest_url_ssi": "http://test.manifest/url/"}

    def test_picks_folio_1r(self, monkeypatch):
        "uses the page titled 'f. 001r', if found"
        monkeypatch.setattr(
            feed_ursus.requests, "get", lambda x: fixtures.GOOD_MANIFEST
        )

        result = feed_ursus.thumbnail_from_manifest(self.record)
        assert (
            result
            == "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fzw07hs0c/full/!200,200/0/default.jpg"  # pylint: disable=line-too-long
        )

    def test_picks_first_page(self, monkeypatch):
        "uses the first image if 'f. 001r' is not found"
        monkeypatch.setattr(
            feed_ursus.requests, "get", lambda x: fixtures.MANIFEST_WITHOUT_F001R
        )

        result = feed_ursus.thumbnail_from_manifest(self.record)
        assert (
            result
            == "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz14b44n8%2Fhm957748/full/!200,200/0/default.jpg"  # pylint: disable=line-too-long
        )

    def test_request_fails(self, monkeypatch):
        "returns None if HTTP request fails"

        monkeypatch.setattr(
            feed_ursus.requests, "get", lambda x: fixtures.MockResponse(None, 404)
        )

        result = feed_ursus.thumbnail_from_manifest(self.record)
        assert result is None

    def test_manifest_without_images(self, monkeypatch):
        "returns None if manifest contains no images"

        monkeypatch.setattr(
            feed_ursus.requests, "get", lambda x: fixtures.MANIFEST_WITHOUT_IMAGES
        )

        result = feed_ursus.thumbnail_from_manifest(self.record)
        assert result is None

    def test_bad_data(self, monkeypatch):
        "returns None if manifest isn't parsable"

        monkeypatch.setattr(feed_ursus.requests, "get", lambda x: fixtures.BAD_MANIFEST)

        result = feed_ursus.thumbnail_from_manifest(self.record)
        assert result is None

    def test_no_manifest_url(self):
        "returns None if the record doesn't include field 'iiif_m'"

        result = feed_ursus.thumbnail_from_manifest({})
        assert result is None
