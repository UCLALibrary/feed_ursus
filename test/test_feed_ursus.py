"""Tests for feed_ursus.py"""
# pylint: disable=no-self-use

import pytest  # type: ignore

import feed_ursus


@pytest.mark.xfail()
def test_load_csv():
    """test for function load_csv"""
    raise NotImplementedError


def test_map_field_name(monkeypatch):
    """maps a CSV column header to a Solr field name"""
    monkeypatch.setitem(
        feed_ursus.mapper.FIELDS, "Test DLCS Field", "test_ursus_field_tesim"
    )
    assert feed_ursus.map_field_name("Test DLCS Field") == "test_ursus_field_tesim"


class TestMapFieldValue:
    """function map_field_value"""

    def test_parses_array(self, monkeypatch):
        """parses value to an array of strings separated by '|~|'"""

        monkeypatch.setitem(
            feed_ursus.mapper.FIELDS, "Test DLCS Field", "test_ursus_field_tesim"
        )
        assert feed_ursus.map_field_value("Test DLCS Field", "one|~|two|~|three") == [
            "one",
            "two",
            "three",
        ]

    def test_calls_function(self, monkeypatch):
        """If mapper defines a function map_[SOLR_NAME], calls that function."""
        # pylint: disable=no-member
        monkeypatch.setitem(
            feed_ursus.mapper.FIELDS, "Test DLCS Field", "test_ursus_field_tesim"
        )
        monkeypatch.setattr(
            feed_ursus.mapper,
            "map_test_ursus_field_tesim",
            lambda x: "lkghsdh",
            raising=False,
        )
        feed_ursus.map_field_value("Test DLCS Field", "one|~|two|~|three")
        assert feed_ursus.mapper.map_test_ursus_field_tesim("abc") == "lkghsdh"


class TestMapRecord:
    """function map_record"""

    def test_maps_record(self, monkeypatch):
        """maps the record for Ursus"""
        monkeypatch.setitem(
            feed_ursus.mapper.FIELDS, "Test DLCS Field", "test_ursus_field_tesim"
        )
        result = feed_ursus.map_record(
            {"Item ARK": "ark:/123/abc", "Test DLCS Field": "lasigd|~|asdfg"}
        )
        assert result["id"] == "ark:/123/abc"
        assert result["ark_ssi"] == "ark:/123/abc"
        assert result["test_ursus_field_tesim"] == ["lasigd", "asdfg"]

    def test_sets_id(self):
        """sets 'id' equal to 'Item ARK'/'ark_ssi'"""
        assert (
            feed_ursus.map_record({"Item ARK": "ark:/123/abc"})["id"] == "ark:/123/abc"
        )

    def test_sets_thumbnail(self):
        """sets a thumbnail URL"""
        result = feed_ursus.map_record(
            {
                "Item ARK": "ark:/123/abc",
                "IIIF Access URL": "https://test.iiif.server/url",
            }
        )
        assert (
            result["thumbnail_url_ss"]
            == "https://test.iiif.server/url/full/!200,200/0/default.jpg"
        )

    def test_sets_access(self):
        """sets permissive values for blacklight-access-control"""
        result = feed_ursus.map_record({"Item ARK": "ark:/123/abc"})
        assert result["discover_access_group_ssim"] == ["public"]
        assert result["read_access_group_ssim"] == ["public"]
        assert result["download_access_person_ssim"] == ["public"]

    def test_sets_iiif_manifest_url(self):
        """sets a IIIF manifest URL based on the ARK"""
        result = feed_ursus.map_record({"Item ARK": "ark:/123/abc"})
        assert (
            result["iiif_manifest_url_ssi"]
            == "https://iiif.library.ucla.edu/ark%3A%2F123%2Fabc/manifest"
        )

    @pytest.mark.parametrize(
        ["column_name", "facet_field_name"],
        [
            ("Type.genre", "genre_sim"),
            ("Language", "human_readable_language_sim"),
            ("Type.typeOfResource", "human_readable_resource_type_sim"),
            ("Coverage.geographic", "location_sim"),
            ("Relation.isPartOf", "member_of_collections_ssim"),
            ("Name.subject", "named_subject_sim"),
            ("Subject", "subject_sim"),
        ],
    )
    def test_sets_facet_fields(self, column_name, facet_field_name):
        """Copies *_tesim to *_sim fields for facets"""
        value = "value aksjg"
        result = feed_ursus.map_record({"Item ARK": "ark:/123/abc", column_name: value})
        assert result[facet_field_name] == [value]
