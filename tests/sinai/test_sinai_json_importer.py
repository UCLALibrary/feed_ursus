# pylint: disable=no-self-use

import json

import pytest

import feed_sinai.sinai_types as st
from feed_sinai.sinai_json_importer import SinaiJsonImporter
from feed_sinai.solr_record import ManuscriptSolrRecord
from tests.sinai import test_sinai_types

# feed_sinai.mapper = importlib.import_module("feed_sinai.mapper.dlp")

BASE_PATH = "tests/sinai/export_test"


@pytest.fixture
def importer() -> SinaiJsonImporter:
    return SinaiJsonImporter(base_path=BASE_PATH)


def test_get_filename(importer: SinaiJsonImporter) -> None:
    assert importer.get_filename("ark:/21198/z1h13zxq") == "z1h13zxq.json"


def test_get_agent(importer: SinaiJsonImporter) -> None:
    result = importer.get_agent("ark:/21198/s1b59x")
    assert isinstance(result, st.Agent)
    assert result.model_dump() == {
        "ark": "ark:/21198/s1b59x",
        "type": {"id": "person", "label": "Person"},
        "pref_name": "Onuphrius",
        "gender": {"id": "man", "label": "Man"},
        "death": {
            "value": "ca. 400 CE",
            "iso": {"not_before": "0375", "not_after": "0425"},
        },
        "rel_con": (
            {
                "label": "Onuphrius, Saint, -approximately 400",
                "uri": st.AnyUrl("http://viaf.org/viaf/20485021"),
                "source": st.RelatedConceptSource.VIAF,
            },
            {
                "label": "Onuphrius, Saint, -approximately 400",
                "uri": st.AnyUrl("https://id.loc.gov/authorities/names/n92113349"),
                "source": st.RelatedConceptSource.LoC,
            },
            {
                "label": "Onuphrius, Saint, -approximately 400",
                "uri": st.AnyUrl("https://w3id.org/haf/person/232371232899"),
                "source": st.RelatedConceptSource.HAF,
            },
            {
                "label": "Onuphrius anachoreta in Aegypto",
                "uri": st.AnyUrl("https://pinakes.irht.cnrs.fr/notices/saint/691/"),
                "source": st.RelatedConceptSource.Pinakes,
            },
        ),
    }


class TestGetPlace:
    @pytest.mark.parametrize(
        ("ark", "expected"),
        (
            (
                "ark:/21198/pl1234",
                {
                    "ark": "ark:/21198/pl1234",
                    "pref_name": "Nisibis",
                    "alt_name": ("ܢܨܝܒܝܢ", "Nusaybin", "Ṣōbā"),
                },
            ),
            ("ark:/21198/pl5678", {"ark": "ark:/21198/pl5678", "pref_name": "Amid"}),
        ),
    )
    def test_get_good_place(
        self, ark: str, expected: st.Place, importer: SinaiJsonImporter
    ) -> None:
        assert importer.get_place(ark).model_dump() == expected

    def test_loads_all_places(self, importer: SinaiJsonImporter) -> None:
        n_files = 0
        for path in (importer.base_path / "places").glob("*.json"):
            importer.get_place("ark:/21198/" + path.stem)
            n_files += 1

        assert n_files == 2


def test_get_assoc_name_item(importer: SinaiJsonImporter) -> None:
    unmerged = test_sinai_types.TestAssocNameItem.EPHREM.convert(
        st.AssocNameItemUnmerged
    )
    result = importer.get_assoc_name_item(unmerged)
    assert isinstance(result, st.AssocNameItemMerged)
    assert result.agent_record and result.agent_record.alt_name == (
        "Ephrem the Syrian",
        "ܐܦܪܝܡ",
    )


class TestGetWork:
    def test_good_get_work(self, importer: SinaiJsonImporter) -> None:
        stub = st.WorkStub(id="ark:/21198/s1b015")
        result = importer.get_conceptual_work(stub)
        assert isinstance(result, st.ConceptualWorkMerged)
        assert result.pref_title == "2 John"

    def test_loads_all_works(self, importer: SinaiJsonImporter) -> None:
        n_files = 0
        for path in (importer.base_path / "works").glob("*.json"):
            stub = st.WorkStub(id="ark:/21198/" + path.stem)
            importer.get_conceptual_work(stub)
            n_files += 1
        assert n_files == 129


def test_get_work_brief(importer: SinaiJsonImporter) -> None:
    raw = st.WorkBriefUnmerged(desc_title="Abc123", creator=["ark:/21198/s1b59x"])
    result = importer.get_work_brief(raw)
    assert isinstance(result, st.WorkBriefMerged)
    assert result.creator and isinstance(result.creator[0].agent_record, st.Agent)
    assert result.creator[0].agent_record.pref_name == "Onuphrius"


@pytest.mark.parametrize(
    ("raw", "pref_title"),
    (
        (
            st.ContentsUnmerged(
                label="1st Week: Saturday of <the week of> Rest",
                work_id="ark:/21198/s1xs34",
                locus="f. 4r",
            ),
            "Acts",
        ),
        (st.ContentsUnmerged(work_id="ark:/21198/s12g6d", locus="f. 5r, 6r"), "3 John"),
        (
            st.ContentsUnmerged(
                label="3rd Week: Sunday, Saturday",
                locus="f. 7v, 8v",
                note=["Sub-heading: Joseph of Arimathea"],
            ),
            None,
        ),
    ),
)
def test_get_contents_item(
    raw: st.ContentsUnmerged, pref_title: str, importer: SinaiJsonImporter
) -> None:
    result = importer.get_contents_item(raw)
    assert result.pref_title == pref_title
    assert result.work_id == raw.work_id
    assert result.label == raw.label
    assert result.locus == raw.locus
    assert result.note == raw.note


class TestGetWorkWit:
    def test_get_work_wit_with_stub(self, importer: SinaiJsonImporter) -> None:
        raw = st.WorkWitItemUnmerged(
            work=st.WorkStub(id="ark:/21198/s1b015"),
        )
        result = importer.get_work_wit(raw)
        assert isinstance(result, st.WorkWitItemMerged)
        assert isinstance(result.work, st.ConceptualWorkMerged)
        assert result.work.pref_title == "2 John"

    def test_get_work_wit_with_workbrief(self, importer: SinaiJsonImporter) -> None:
        raw = st.WorkWitItemUnmerged(
            work=st.WorkBriefUnmerged(
                desc_title="Test Work", creator=["ark:/21198/s1b59x"]
            )
        )
        result = importer.get_work_wit(raw)
        assert isinstance(result, st.WorkWitItemMerged)
        assert isinstance(result.work, st.WorkBriefMerged)
        assert result.work.creator and isinstance(
            result.work.creator[0].agent_record, st.Agent
        )
        assert result.work.creator[0].agent_record.pref_name == "Onuphrius"

    def test_gets_contents_item(self, importer: SinaiJsonImporter) -> None:
        raw = st.WorkWitItemUnmerged(
            work=st.WorkBriefUnmerged(
                desc_title="Test Work", creator=["ark:/21198/s1b59x"]
            ),
            contents=[
                st.ContentsUnmerged(
                    label="1st Week: Saturday of <the week of> Rest",
                    work_id="ark:/21198/s1xs34",
                    locus="f. 4r",
                )
            ],
        )

        result = importer.get_work_wit(raw)

        assert result.contents[0].model_dump() == {
            "pref_title": "Acts",
            "label": "1st Week: Saturday of <the week of> Rest",
            "work_id": "ark:/21198/s1xs34",
            "locus": "f. 4r",
        }


def test_get_para(importer: SinaiJsonImporter) -> None:
    ct = st.ControlledTerm(id="x", label="X")

    raw = st.ParaItemUnmerged(
        type=ct,
        locus="abc",
        lang=[ct],
        assoc_name=[st.AssocNameItemUnmerged(id="ark:/21198/s1c304", role=ct)],
        assoc_place=[st.AssocPlaceItemUnmerged(id="ark:/21198/pl1234", event=ct)],
    )

    result = importer.get_para(raw)

    assert result.assoc_name[0].agent_record
    assert result.assoc_name[0].agent_record.pref_name == "Mar Saba"

    assert result.assoc_place[0].place_record
    assert result.assoc_place[0].place_record.pref_name == "Nisibis"


class TestGetTextUnit:
    def test_good_text_unit(self, importer: SinaiJsonImporter) -> None:
        stub = st.LayerTextUnitUnmerged.model_validate_json(
            """
            {
                "id": "ark:/21198/s1308n",
                "label": "Item 1"
            }
        """
        )
        result = importer.get_layer_text_unit(stub)
        assert result.model_dump() == {
            "id": "ark:/21198/s1308n",
            "label": "Item 1",
            "text_unit_record": {
                "ark": "ark:/21198/s1308n",
                "label": "Liturgical collection",
                "lang": ({"id": "nucl1302", "label": "Georgian"},),
                "parent": ("ark:/21198/s18d1p",),
                "reconstruction": False,
                "work_wit": (
                    {
                        "work": {
                            "desc_title": "Liturgical collection",
                            "genre": (
                                {
                                    "id": "liturgical-texts",
                                    "label": "Liturgical texts",
                                },
                            ),
                        },
                    },
                ),
            },
        }

    def test_loads_all_text_units(self, importer: SinaiJsonImporter) -> None:
        n_files = 0
        for path in (importer.base_path / "text_units").glob("*.json"):
            stub = st.LayerTextUnitUnmerged(
                id="ark:/21198/" + path.stem, label="whatevs"
            )
            importer.get_layer_text_unit(stub)
            n_files += 1
        assert n_files == 15


class TestGetLayer:
    def test_good_layer(self, importer: SinaiJsonImporter) -> None:
        raw = st.ManuscriptLayerUnmerged.model_validate_json(
            """
            {
                "id": "ark:/21198/ten0p1ol",
                "label": "Overtext layer (late 9th c., Kufic)",
                "type": {
                    "id": "overtext",
                    "label": "Overtext"
                    },
                "locus": "ff. 128-143"
            }
        """
        )
        result = importer.get_layer(raw).model_dump()

        assert result == {
            "id": "ark:/21198/ten0p1ol",
            "label": "Overtext layer (late 9th c., Kufic)",
            "type": {"id": "overtext", "label": "Overtext"},
            "locus": "ff. 128-143",
            "layer_record": {
                "ark": "ark:/21198/ten0p1ol",
                "reconstruction": False,
                "state": {"id": "overtext", "label": "Overtext"},
                "label": "Arabic NF M 28, Part 1, Overtext",
                "locus": "ff. 128-143",
                "summary": "Gospels, late 9th c., Arabic (Kufic)",
                "extent": "16 ff.",
                "writing": (
                    {
                        "script": (
                            {
                                "id": "kufic",
                                "label": "Kufic",
                                "writing_system": "Arabic",
                            },
                        ),
                        "locus": "ff. 128-143",
                    },
                ),
                "ink": (
                    {
                        "locus": "ff. 128-143",
                        "note": ("Titles in red ink",),
                    },
                ),
                "text_unit": (
                    {
                        "id": "ark:/21198/ten0p1olt1",
                        "label": "Primary Text Unit 1",
                        "locus": "ff. 128-143",
                        "text_unit_record": {
                            "ark": "ark:/21198/ten0p1olt1",
                            "reconstruction": False,
                            "label": "Arabic Gospels",
                            "locus": "ff. 128r-143v",
                            "lang": ({"id": "arab1395", "label": "Arabic"},),
                            "work_wit": (
                                {
                                    "work": {
                                        "ark": "ark:/21198/s12c7r",
                                        "pref_title": "Matthew",
                                        "alt_title": ("Bible. Matthew",),
                                        "genre": (
                                            {
                                                "id": "biblical-texts",
                                                "label": "Biblical texts",
                                            },
                                            {
                                                "id": "gospel-books",
                                                "label": "Gospel books",
                                            },
                                        ),
                                        "rel_con": (
                                            {
                                                "label": "Bible. Matthew",
                                                "uri": st.AnyUrl(
                                                    st.AnyUrl(
                                                        "https://viaf.org/viaf/188427863"
                                                    )
                                                ),
                                                "source": st.RelatedConceptSource.VIAF,
                                            },
                                            {
                                                "label": "Bible. Matthew",
                                                "uri": st.AnyUrl(
                                                    st.AnyUrl(
                                                        "http://id.loc.gov/authorities/names/n79056834"
                                                    )
                                                ),
                                                "source": st.RelatedConceptSource.LoC,
                                            },
                                        ),
                                    },
                                    "locus": "ff. 128r-130",
                                },
                                {
                                    "work": {
                                        "ark": "ark:/21198/s1630k",
                                        "pref_title": "Mark",
                                        "alt_title": ("Bible. Mark",),
                                        "genre": (
                                            {
                                                "id": "biblical-texts",
                                                "label": "Biblical texts",
                                            },
                                            {
                                                "id": "gospel-books",
                                                "label": "Gospel books",
                                            },
                                        ),
                                        "rel_con": (
                                            {
                                                "label": "Bible. Mark",
                                                "uri": st.AnyUrl(
                                                    "https://viaf.org/viaf/179823714"
                                                ),
                                                "source": st.RelatedConceptSource.VIAF,
                                            },
                                            {
                                                "label": "Bible. Mark",
                                                "uri": st.AnyUrl(
                                                    "http://id.loc.gov/authorities/names/n78095773"
                                                ),
                                                "source": st.RelatedConceptSource.LoC,
                                            },
                                        ),
                                    },
                                    "locus": "ff. 130v-135r",
                                },
                                {
                                    "work": {
                                        "ark": "ark:/21198/s1k88r",
                                        "pref_title": "Luke",
                                        "alt_title": ("Bible. Luke",),
                                        "genre": (
                                            {
                                                "id": "biblical-texts",
                                                "label": "Biblical texts",
                                            },
                                            {
                                                "id": "gospel-books",
                                                "label": "Gospel books",
                                            },
                                        ),
                                        "rel_con": (
                                            {
                                                "label": "Bible. Luke",
                                                "uri": st.AnyUrl(
                                                    "http://viaf.org/viaf/257061095"
                                                ),
                                                "source": st.RelatedConceptSource.VIAF,
                                            },
                                        ),
                                    },
                                    "locus": "ff. 135r-140r",
                                },
                                {
                                    "work": {
                                        "ark": "ark:/21198/s1388d",
                                        "pref_title": "John",
                                        "alt_title": ("Bible. John",),
                                        "genre": (
                                            {
                                                "id": "biblical-texts",
                                                "label": "Biblical texts",
                                            },
                                            {
                                                "id": "gospel-books",
                                                "label": "Gospel books",
                                            },
                                        ),
                                        "rel_con": (
                                            {
                                                "label": "Bible. John",
                                                "uri": st.AnyUrl(
                                                    "https://viaf.org/viaf/57145910123927021804"
                                                ),
                                                "source": st.RelatedConceptSource.VIAF,
                                            },
                                            {
                                                "label": "Bible. John",
                                                "uri": st.AnyUrl(
                                                    "http://id.loc.gov/authorities/names/n79060414"
                                                ),
                                                "source": st.RelatedConceptSource.LoC,
                                            },
                                        ),
                                    },
                                    "locus": "ff. 140v-143v",
                                },
                            ),
                            "note": (
                                {
                                    "type": {
                                        "id": "contents",
                                        "label": "Contents Note",
                                    },
                                    "value": "The Gospels continue in Arabic NF M 8 and NF M 27",
                                },
                            ),
                            "desc_provenance": {
                                "program": (
                                    {
                                        "label": "Sinai Palimpests Project",
                                        "description": "Described as part of the Sinai Palimpsests Project (2006-2017). The Sinai Palimpsests Project was sponsored by St. Catherine’s Monastery of the Sinai in partnership with the Early Manuscripts Electronic Library and the UCLA Library, and with funding from Arcadia. The Project provides scholarly identification and description of the undertext objects in a subset of palimpsested manuscripts in the Sinai collection, with minimal metadata for the overtexts of the host manuscripts.",
                                    },
                                )
                            },
                            "parent": ("ark:/21198/ten0p1ol",),
                            "internal": (
                                "Test record, delete after development is complete",
                            ),
                        },
                    },
                ),
                "assoc_date": (
                    {
                        "type": {"id": "origin", "label": "Origin Date"},
                        "note": ("Paleographic dating",),
                        "value": "Second half 9th c. CE",
                        "iso": {"not_before": "0851", "not_after": "0900"},
                    },
                ),
                "note": (
                    {
                        "type": {"id": "ornamentation", "label": "Ornamentation"},
                        "value": "Decorative headpieces throughout",
                    },
                    {
                        "type": {"id": "condition", "label": "Condition"},
                        "value": "Several damaged folios were repaired and reinforced more recently",
                    },
                ),
                "bib": (
                    {
                        "id": st.UUID("36ac2d29-349f-496d-b4ea-aff4e605c4ba"),
                        "type": {"id": "ref", "label": "Reference Work"},
                        "range": "p. 48-90",
                    },
                ),
                "parent": ("ark:/21198/ten02zkr",),
                "desc_provenance": {
                    "program": (
                        {
                            "label": "Sinai Palimpests Project",
                            "description": "Described as part of the Sinai Palimpsests Project (2006-2017). The Sinai Palimpsests Project was sponsored by St. Catherine’s Monastery of the Sinai in partnership with the Early Manuscripts Electronic Library and the UCLA Library, and with funding from Arcadia. The Project provides scholarly identification and description of the undertext objects in a subset of palimpsested manuscripts in the Sinai collection, with minimal metadata for the overtexts of the host manuscripts.",
                        },
                    )
                },
                "internal": ("Test record for development purposes; please delete.",),
            },
        }

    def test_loads_assoc_name_agents(self, importer: SinaiJsonImporter) -> None:
        result = importer.get_layer(
            st.ManuscriptLayerUnmerged(
                id="ark:/21198/te5fp1ol",
                label="abc",
                type=st.ControlledTerm(id="a", label="b"),
            )
        )
        assert result.layer_record.assoc_name[0].agent_record.pref_name == "Ephrem"  # type: ignore

    def test_loads_all_layers(self, importer: SinaiJsonImporter) -> None:
        n_files = 0
        for path in (importer.base_path / "layers").glob("*.json"):
            stub = st.ManuscriptLayerUnmerged(
                id="ark:/21198/" + path.stem,
                label="whatevs",
                type={"id": "what", "label": "ever"},
            )
            importer.get_layer(stub)
            n_files += 1
        assert n_files == 15


class TestGetMergedManuscript:
    def test_good_manuscript(self, importer: SinaiJsonImporter) -> None:
        with open(f"{BASE_PATH}/outputs/z1h13zxq.json", encoding="utf-8") as f:
            expected = json.load(f)

        result = importer.get_merged_manuscript(
            importer.base_path / "ms_objs/z1h13zxq.json"
        )

        test_ms_layer = result.part[0].uto[0]

        assert test_ms_layer.id == "ark:/21198/s1gh06"
        assert isinstance(test_ms_layer, st.UndertextManuscriptLayerMerged)
        assert test_ms_layer.model_dump().get("layer_record") is None

        assert json.loads(result.model_dump_json()) == expected

    @pytest.mark.xfail  # No test data yet
    def test_loads_assoc_name_agents(self) -> None:
        raise NotImplementedError

    @pytest.mark.xfail  # Don't seem to have good data here yet
    def test_loads_all_manuscripts(self, importer: SinaiJsonImporter) -> None:
        n_files = 0
        for path in (importer.base_path / "ms_objs").glob("*.json"):
            importer.get_merged_manuscript(path)
            n_files += 1
        assert n_files == 15


def test_iterate_merged_records(importer: SinaiJsonImporter) -> None:
    for ms_obj in importer.iterate_merged_records():
        assert isinstance(ms_obj, st.ManuscriptObjectMerged)
        assert isinstance(ms_obj.model_dump_json(), str)


def test_solr_record_works_on_all(importer: SinaiJsonImporter) -> None:
    for ms_obj in importer.iterate_merged_records():
        solr = ManuscriptSolrRecord(ms_obj=ms_obj)
        for field in ManuscriptSolrRecord.model_computed_fields:
            getattr(solr, field)

        assert isinstance(importer.solr_record(ms_obj=ms_obj), dict)
