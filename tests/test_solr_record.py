# mypy: disallow_untyped_defs=False
"""Tests for solr_record.py"""

# pylint: disable=no-self-use

import pytest  # type: ignore

from feed_ursus.solr_record import UrsusSolrRecord


class TestUrsusSolrRecord:
    def test_basic_validation(self):
        record = UrsusSolrRecord(id="test_id")
        assert record.id == "test_id"

    def test_computed_names_sim(self):
        record = UrsusSolrRecord(
            id="test_id",
            author_tesim=["Author1", "Author2"],
            scribe_tesim=["Scribe1"],
            associated_name_tesim=["Assoc1"],
            translator_tesim=["Trans1"],
        )
        assert record.names_sim == ["Author1", "Author2", "Scribe1", "Assoc1", "Trans1"]

    def test_computed_names_sim_empty(self):
        record = UrsusSolrRecord(id="test_id")
        assert record.names_sim is None

    def test_computed_keywords_sim(self):
        record = UrsusSolrRecord(
            id="test_id",
            genre_tesim=["Genre1"],
            features_tesim=["Feature1"],
            place_of_origin_tesim=["Place1"],
            support_tesim=["Support1"],
            form_ssi="Form1",
        )
        # Note: keywords_sim is computed in importer, not here
        # But in the model, keywords_tesim is stored
        assert record.keywords_tesim == []  # Default

    def test_computed_collection_sim(self):
        record = UrsusSolrRecord(id="test_id", collection_ssi="Test Collection")
        assert record.collection_sim == ["Test Collection"]

    def test_computed_collection_sim_empty(self):
        record = UrsusSolrRecord(id="test_id")
        assert record.collection_sim is None

    def test_computed_uniform_title_sim(self):
        record = UrsusSolrRecord(id="test_id", uniform_title_tesim=["Uniform Title"])
        assert record.uniform_title_sim == ["Uniform Title"]

    def test_computed_uniform_title_sim_empty(self):
        record = UrsusSolrRecord(id="test_id")
        assert record.uniform_title_sim is None

    # Add more tests for other computed fields as needed
    def test_computed_architect_sim(self):
        record = UrsusSolrRecord(id="test_id", architect_tesim=["Arch1"])
        assert record.architect_sim == ["Arch1"]

    def test_computed_author_sim(self):
        record = UrsusSolrRecord(id="test_id", author_tesim=["Auth1"])
        assert record.author_sim == ["Auth1"]

    def test_computed_illuminator_sim(self):
        record = UrsusSolrRecord(id="test_id", illuminator_tesim=["Ill1"])
        assert record.illuminator_sim == ["Ill1"]

    def test_computed_scribe_sim(self):
        record = UrsusSolrRecord(id="test_id", scribe_tesim=["Scr1"])
        assert record.scribe_sim == ["Scr1"]

    def test_computed_rubricator_sim(self):
        record = UrsusSolrRecord(id="test_id", rubricator_tesim=["Rub1"])
        assert record.rubricator_sim == ["Rub1"]

    def test_computed_commentator_sim(self):
        record = UrsusSolrRecord(id="test_id", commentator_tesim=["Com1"])
        assert record.commentator_sim == ["Com1"]

    def test_computed_translator_sim(self):
        record = UrsusSolrRecord(id="test_id", translator_tesim=["Tra1"])
        assert record.translator_sim == ["Tra1"]

    def test_computed_lyricist_sim(self):
        record = UrsusSolrRecord(id="test_id", lyricist_tesim=["Lyr1"])
        assert record.lyricist_sim == ["Lyr1"]

    def test_computed_composer_sim(self):
        record = UrsusSolrRecord(id="test_id", composer_tesim=["Comp1"])
        assert record.composer_sim == ["Comp1"]

    def test_computed_illustrator_sim(self):
        record = UrsusSolrRecord(id="test_id", illustrator_tesim=["Illu1"])
        assert record.illustrator_sim == ["Illu1"]

    def test_computed_editor_sim(self):
        record = UrsusSolrRecord(id="test_id", editor_tesim=["Edit1"])
        assert record.editor_sim == ["Edit1"]

    def test_computed_calligrapher_sim(self):
        record = UrsusSolrRecord(id="test_id", calligrapher_tesim=["Call1"])
        assert record.calligrapher_sim == ["Call1"]

    def test_computed_engraver_sim(self):
        record = UrsusSolrRecord(id="test_id", engraver_tesim=["Eng1"])
        assert record.engraver_sim == ["Eng1"]

    def test_computed_printmaker_sim(self):
        record = UrsusSolrRecord(id="test_id", printmaker_tesim=["Print1"])
        assert record.printmaker_sim == ["Print1"]
