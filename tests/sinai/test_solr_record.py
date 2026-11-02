# mypy: disable-error-code=truthy-function
from pathlib import Path
from typing import Iterator
from unittest.mock import patch

import pytest

import feed_sinai.sinai_types as st
from feed_sinai.sinai_json_importer import SinaiJsonImporter
from feed_sinai.solr_record import ManuscriptSolrRecord, filter_none

BASE_PATH = "tests/sinai/export_test"
IMPORTER = SinaiJsonImporter(base_path=BASE_PATH)
SOLR_RECORD = ManuscriptSolrRecord(
    ms_obj=IMPORTER.get_merged_manuscript(
        Path("tests/sinai/export_test/ms_objs/te5f0f9b.json")
    )
)


@pytest.fixture
def result() -> ManuscriptSolrRecord:
    return SOLR_RECORD


def test_filter_none() -> None:
    @filter_none
    def f() -> Iterator[int | None]:
        yield from (1, 2, 3, None, 4, None)

    result = tuple(f())
    assert result == (1, 2, 3, 4)


def test_id(result: ManuscriptSolrRecord) -> None:
    assert result.id == "ark:/21198/te5f0f9b"


def test_ark_ssi(result: ManuscriptSolrRecord) -> None:
    assert result.ark_ssi == "ark:/21198/te5f0f9b"


def test_has_model_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.has_model_ssim == ["Work"]


def test_visibility_ssi(result: ManuscriptSolrRecord) -> None:
    assert result.visibility_ssi == "open"


def test_manuscript_json_ts(result: ManuscriptSolrRecord) -> None:
    assert result.manuscript_json_ts


def test_ms_type_ssi(result: ManuscriptSolrRecord) -> None:
    assert result.ms_type_ssi


def test_state_ssi(result: ManuscriptSolrRecord) -> None:
    assert result.state_ssi


def test_features_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.features_ssim


def test_support_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.support_ssim


def test_repository_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.repository_ssim


def test_collection_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.collection_ssim


def test_names_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.names_ssim


def test_places_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.places_ssim


def test_date_types_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.date_types_ssim


def test_program_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.program_ssim


def test_ot_script_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.ot_script_ssim


def test_ot_writing_system_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.ot_writing_system_ssim


def test_ot_genre_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.ot_genre_ssim


def test_ot_year_isim(result: ManuscriptSolrRecord) -> None:
    assert result.ot_year_isim == [
        *range(601, 700),
        700,  # range is INCLUSIVE of 700
        1290,
    ]


def test_ot_language_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.ot_language_ssim


def test_ot_works_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.ot_works_ssim


def test_para_script_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.para_script_ssim


def test_para_writing_system_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.para_writing_system_ssim


def test_para_genre_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.para_genre_ssim


def test_para_year_isim(result: ManuscriptSolrRecord) -> None:
    assert result.para_year_isim == []


def test_para_language_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.para_language_ssim


def test_para_works_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.para_works_ssim == []


def test_para_names_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.para_names_ssim == [
        "Andrew of Crete",
        "Ephrem",
        "Maximus the Confessor",
        "Paul the Deacon",
    ]


def test_para_type_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.para_type_ssim == [
        "Colophon",
        "Prayer Request",
        "Reader's Note",
        "Rubric",
        "Table of Contents",
        "Transfer of Ownership",
    ]


def test_uto_script_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.uto_script_ssim == []


def test_uto_year_isim(result: ManuscriptSolrRecord) -> None:
    assert result.uto_year_isim == []


def test_uto_language_ssim(result: ManuscriptSolrRecord) -> None:
    assert result.uto_language_ssim == []


def test_shelfmark_ssi(result: ManuscriptSolrRecord) -> None:
    assert result.shelfmark_ssi


def test_titles_tesim(result: ManuscriptSolrRecord) -> None:
    assert result.titles_tesim


def test_names_tesim(result: ManuscriptSolrRecord) -> None:
    assert result.names_tesim


def test_exerpts_tesim(result: ManuscriptSolrRecord) -> None:
    assert result.exerpts_tesim


def test_places_tesim(result: ManuscriptSolrRecord) -> None:
    assert result.places_tesim


def test_contents_tesim(result: ManuscriptSolrRecord) -> None:
    assert result.contents_tesim


def test_paracontent_tesim(result: ManuscriptSolrRecord) -> None:
    assert result.paracontent_tesim


def test_full_text_tesim(result: ManuscriptSolrRecord) -> None:
    assert result.full_text_tesim


def test_extent_tesi(result: ManuscriptSolrRecord) -> None:
    assert result.extent_tesi == "146 ff."


def test_text_unit_labels_tesim(result: ManuscriptSolrRecord) -> None:
    assert result.text_unit_labels_tesim == [
        "Synaxarion",
        "Gospel of Luke",
    ]


def test_origin_date_values_tesim(result: ManuscriptSolrRecord) -> None:
    assert result.origin_date_values_tesim == {
        "AM 6,104 = 1292 CE",
        "7th c. CE",
    }


def test_works_facet_includes_every_id_and_no_desc_titles() -> None:
    work_wit = IMPORTER.get_work_wit(
        st.WorkWitItemUnmerged(
            work=st.WorkBriefUnmerged(
                id=["ark:/21198/s1b015", "ark:/21198/s12g6d"],
                desc_title="Letters of John",
            )
        )
    )
    with patch.object(ManuscriptSolrRecord, "get_work_wits", return_value=[work_wit]):
        assert SOLR_RECORD.ot_works_ssim == ["2 John", "3 John"]


def test_works_ssim_combines_overtext_and_guest_layers() -> None:
    def work_wit(ark: str, desc_title: str) -> st.WorkWitItemMerged:
        return IMPORTER.get_work_wit(
            st.WorkWitItemUnmerged(
                work=st.WorkBriefUnmerged(id=[ark], desc_title=desc_title)
            )
        )

    def by_layer(_: ManuscriptSolrRecord, layer_type: str | None = None) -> list:
        ot = [work_wit("ark:/21198/s1b015", "Overtext")]
        guest = [work_wit("ark:/21198/s12g6d", "Guest")]
        return {"ot_layer": ot, "guest_layer": guest}.get(layer_type, ot + guest)

    with patch.object(ManuscriptSolrRecord, "get_work_wits", by_layer):
        assert SOLR_RECORD.works_ssim == ["2 John", "3 John"]
        assert SOLR_RECORD.ot_works_ssim == ["2 John"]
        assert SOLR_RECORD.para_works_ssim == ["3 John"]
