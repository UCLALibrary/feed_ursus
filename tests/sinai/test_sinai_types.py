from pathlib import Path
from typing import Hashable, Optional
from unittest.mock import Mock

import pytest
from pydantic import AnyUrl, ValidationError

import feed_sinai.sinai_types as st
from feed_sinai.sinai_json_importer import SinaiJsonImporter

IMPORTER = SinaiJsonImporter(base_path="tests/sinai/export_test")


class ExampleModel(st.BaseModel):
    children: "tuple[ExampleModel, ...]" = tuple()
    a: Optional[int] = None
    b: Optional[int] = None
    c: Optional[str] = None


class TestBaseModel:
    def test_convert(self) -> None:
        class A(st.BaseModel):
            a: int

        class B(A):
            b: int

        first = A(a=1)
        second = first.convert(B, b=2)
        assert second == B(a=1, b=2)

    class TestDeepGet:
        @pytest.fixture
        def obj(self) -> st.Date:
            return st.Date(
                value="sometime", iso=st.Iso(not_before="1980", not_after="2025")
            )

        def test_gets_by_type(self, obj: st.Date) -> None:
            assert "sometime" in obj.deep_get(cls=str)

        def test_gets_by_type_from_children(self, obj: st.Date) -> None:
            assert {"1980", "2025"} <= set(
                obj.deep_get("not_before", "not_after", cls=str)
            )

        def test_gets_by_name(self, obj: st.Date) -> None:
            assert set(obj.deep_get("not_after", cls=str)) == {"2025"}

        def test_ignores_by_name(self, obj: st.Date) -> None:
            assert "1980" not in obj.deep_get(cls=str, exclude=["not_before"])

        def test_gets_submodels(self, obj: st.Date) -> None:
            assert set(obj.deep_get(cls=st.Iso)) == {obj.iso}

        def test_gets_assoc_name_item(self) -> None:
            name = TestAssocNameItem.EPHREM.convert(st.AssocNameItemUnmerged)
            para = st.ParaItemUnmerged(
                type=st.ControlledTerm(id="t", label="T"),
                locus="locus",
                lang=[st.ControlledTerm(id="l", label="L")],
                assoc_name=[name],
            )
            assert set(para.deep_get(cls=st.AssocNameItemUnmerged)) == {name}

        def test_fib(self) -> None:
            test_obj = ExampleModel.model_validate(
                {
                    "a": 1,
                    "b": 1,
                    "children": [
                        {"a": 2, "b": 3, "children": [{"a": 5, "b": 8}]},
                        {"a": 13, "b": 21},
                        {"children": [{"b": 55, "c": "no"}], "b": 34, "c": "nope"},
                    ],
                }
            )

            assert set(test_obj.deep_get("a", "b", cls=int)) == {
                1,
                2,
                3,
                5,
                8,
                13,
                21,
                34,
                55,
            }


class TestControlledTerm:
    CONTROLLED_TERM = st.ControlledTerm(id="abc", label="123")
    MAN = st.ControlledTerm(id="man", label="Man")

    def test_happy_path(self) -> None:
        result = st.ControlledTerm.model_validate_json('{"id": "abc", "label": "123"}')
        assert result == self.CONTROLLED_TERM

    def test_hashable(self) -> None:
        result = st.ControlledTerm.model_validate_json('{"id": "abc", "label": "123"}')
        assert isinstance(result, Hashable)

    def test_extra_field(self) -> None:
        with pytest.raises(ValidationError):
            st.ControlledTerm.model_validate_json(
                '{"id": "abc", "label": "123"}, "other": "xyz"'
            )

    def test_missing_id(self) -> None:
        with pytest.raises(ValidationError):
            st.ControlledTerm.model_validate_json('{"label": "123"}')

    def test_missing_value(self) -> None:
        with pytest.raises(ValidationError):
            st.ControlledTerm.model_validate_json('{"id": "abc"}')

    def test_empty_id(self) -> None:
        with pytest.raises(ValidationError):
            st.ControlledTerm.model_validate_json('{"id": ", "label": "123"}')

    def test_empty_value(self) -> None:
        with pytest.raises(ValidationError):
            st.ControlledTerm.model_validate_json('{"id": "abc", "label": "}')


# class TestGender:
#     def test_man(self) -> None:
#         result = st.Gender({"id": "man", "label": "Man"})
#         assert result == st.Gender.man

#     def test_woman(self) -> None:
#         result = st.Gender({"id": "woman", "label": "Woman"})
#         assert result == st.Gender.woman

#     def test_other(self) -> None:
#         result = st.Gender({"id": "other", "label": "Other"})
#         assert result == st.Gender.other

#     def test_invalid_gender(self) -> None:
#         """With appologies, we are only tracking 'man', 'woman', and 'other"""
#         with pytest.raises(ValueError):
#             st.Gender({"id": "something", "label": "else"})

#     def test_as_value(self) -> None:
#         class TestModel(BaseModel):
#             gender: st.Gender
#         result = TestModel.model_validate_json('{"id": "other", "label": "Other"}')
#         assert result.gender == st.Gender.other


class TestIso:
    ISO = st.Iso(not_before="0010", not_after="0100")

    def test_good_iso(self) -> None:
        assert (
            st.Iso.model_validate_json('{"not_before": "0010", "not_after": "0100"}')
            == self.ISO
        )

    def test_hashable(self) -> None:
        assert hash(self.ISO)

    def test_no_notafter(self) -> None:
        result = st.Iso.model_validate_json('{"not_before": "0010"}')
        assert result.not_before == "0010"
        assert result.not_after is None

    def test_no_notbefore(self) -> None:
        with pytest.raises(ValidationError):
            st.Iso.model_validate_json('{"not_after": "0010"}')

    def test_optional_month_and_year(self) -> None:
        result = st.Iso.model_validate_json(
            '{"not_before": "2017-07", "not_after": "2025-07-23"}'
        )
        assert result.not_before == "2017-07"
        assert result.not_after == "2025-07-23"
        assert tuple(result.years()) == (
            2017,
            2018,
            2019,
            2020,
            2021,
            2022,
            2023,
            2024,
            2025,
        )

    def test_negative_year(self) -> None:
        assert (
            st.Iso.model_validate_json('{"not_before": "-0003"}').not_before == "-0003"
        )

    class TestYears:
        def test_returns_range(self) -> None:
            range_obj = TestIso.ISO.years()
            assert isinstance(range_obj, range)
            result = [*range_obj]
            assert result[:3] == [10, 11, 12] and result[-3:] == [98, 99, 100]

        def test_no_notafter(self) -> None:
            result = [*st.Iso.model_validate_json('{"not_before": "0010"}').years()]
            assert result == [10]

        def test_negative_and_zero_years(self) -> None:
            result = st.Iso.model_validate_json(
                '{"not_before": "-0003-04-05", "not_after": "0002"}'
            )
            assert [*result.years()] == [-3, -2, -1, 0, 1, 2]


class TestDate:
    DATE = st.Date(value="4th c. CE", iso=TestIso.ISO)

    def test_good_date(self) -> None:
        st.Date.model_validate_json(
            """
            {
                "value": "4th c. CE",
                "iso": {
                    "not_before": "0010",
                    "not_after": "0100"
                }
            }
        """
        )


class TestRelConItem:
    def test_good_json(self) -> None:
        result = st.RelConItem.model_validate_json(
            """
            {
                "label": "Onuphrius, Saint, -approximately 400",
                "uri": "https://w3id.org/haf/person/232371232899",
                "source": "HAF"
            }
        """
        )
        assert result.label == "Onuphrius, Saint, -approximately 400"
        assert result.source == st.RelatedConceptSource.HAF

    def test_invalid_source(self) -> None:
        with pytest.raises(ValidationError):
            st.RelConItem.model_validate_json(
                """
                {
                    "label": "Onuphrius, Saint, -approximately 400",
                    "uri": "https://w3id.org/haf/person/232371232899",
                    "source": "UCLA"
                }
            """
            )


class TestRefnoItem:
    def test_good_json(self) -> None:
        result = st.RefnoItem.model_validate_json(
            """
            {
                "label": "Homiliae super psalmos",
                "idno": "2836.001",
                "source": "CPG"
            }
        """
        )
        assert result.idno == "2836.001"


class TestBibItem:
    @pytest.fixture
    def json(self) -> str:
        return """
            {
                "id": "deb668b6-feec-4828-8749-a97441881226",
                "type": {
                    "id": "ref",
                    "label": "Reference"
                },
                "shortcode": "test shortcode",
                "citation": "test citation",
                "range": "[141], p. 156"
            }
        """

    def test_good_json(self, json: str) -> None:
        result = st.BibItem.model_validate_json(json)
        assert result.type.id == "ref"

    def test_hashable(self, json: str) -> None:
        result = st.BibItem.model_validate_json(json)
        assert hash(result)


# @pytest.mark.xfail
# class TestRelItem:
#     """Not currently used in the data"""
#     raise NotImplementedError


# @pytest.mark.xfail
# class TestRelAgentItem:
#     """Not currently used in the data"""
#     raise NotImplementedError


# @pytest.mark.xfail
# class TestRelPlaceItem:
#     """Not currently used in the data"""
#     raise NotImplementedError


# @pytest.mark.xfail
# class TestCataloguerItem:
#     """Not currently used in the data"""
#     raise NotImplementedError


class TestAgent:
    EPHREM = st.Agent(
        ark="ark:/21198/s1v887",
        type=st.ControlledTerm(id="person", label="Person"),
        pref_name="Ephrem",
        alt_name=["Ephrem the Syrian", "ܐܦܪܝܡ"],
        gender=TestControlledTerm.MAN,
        floruit=st.Date(
            value="303 CE-373 CE",
            iso=st.Iso(not_before="0303", not_after="0373"),
        ),
        rel_con=[
            st.RelConItem.model_validate(
                {
                    "label": "Ephraem, Syrus, Saint, 303-373",
                    "uri": "http://viaf.org/viaf/100177778",
                    "source": "VIAF",
                }
            ),
            st.RelConItem.model_validate(
                {
                    "label": "Ephraem, Syrus, Saint, 303-373",
                    "uri": "http://id.loc.gov/authorities/names/n50082928",
                    "source": "LoC",
                }
            ),
            st.RelConItem.model_validate(
                {
                    "label": "Ephrem, of Nisibis, 303-373",
                    "uri": "https://w3id.org/haf/person/818572788967",
                    "source": "HAF",
                }
            ),
            st.RelConItem.model_validate(
                {
                    "label": "Ephrem",
                    "uri": "http://syriaca.org/person/13",
                    "source": "Syriaca",
                }
            ),
            st.RelConItem.model_validate(
                {
                    "label": "Ephraem Graecus",
                    "uri": "https://pinakes.irht.cnrs.fr/notices/auteur/995/",
                    "source": "Pinakes",
                }
            ),
        ],
    )
    THEODORE = st.Agent(
        ark="ark:/21198/s1d01s",
        type=st.ControlledTerm(id="person", label="Person"),
        pref_name="Theodore the Studite",
        alt_name=["Theodore Studites"],
        gender=TestControlledTerm.MAN,
        floruit=st.Date.model_validate(
            {
                "value": "759 CE-826 CE",
                "iso": {"not_before": "0759", "not_after": "0826"},
            }
        ),
        rel_con=[
            st.RelConItem.model_validate(rc)
            for rc in [
                {
                    "label": "Theodore, Studites, Saint, 759-826",
                    "uri": "http://viaf.org/viaf/62875165",
                    "source": "VIAF",
                },
                {
                    "label": "Theodore, Studites, Saint, 759-826",
                    "uri": "https://id.loc.gov/authorities/names/n81118597",
                    "source": "LoC",
                },
                {
                    "label": "Theodore, Studites, 759-826",
                    "uri": "https://w3id.org/haf/person/636228715607",
                    "source": "HAF",
                },
                {
                    "label": "Theodorus Studita",
                    "uri": "https://pinakes.irht.cnrs.fr/notices/auteur/2685/",
                    "source": "Pinakes",
                },
            ]
        ],
    )

    def test_good_json(self) -> None:
        assert (
            st.Agent.model_validate_json(
                """
        {
            "ark": "ark:/21198/s1d01s",
            "type": {"id": "person", "label": "Person"},
            "pref_name": "Theodore the Studite",
            "alt_name": [
                "Theodore Studites"
            ],
            "gender": {"id": "man", "label": "Man"},
            "floruit": {
                "value": "759 CE-826 CE",
                "iso": {
                    "not_before": "0759",
                    "not_after": "0826"
                }
            },
            "rel_con": [
                {
                    "label": "Theodore, Studites, Saint, 759-826",
                    "uri": "http://viaf.org/viaf/62875165",
                    "source": "VIAF"
                },
                {
                    "label": "Theodore, Studites, Saint, 759-826",
                    "uri": "https://id.loc.gov/authorities/names/n81118597",
                    "source": "LoC"
                },
                {
                    "label": "Theodore, Studites, 759-826",
                    "uri": "https://w3id.org/haf/person/636228715607",
                    "source": "HAF"
                },
                {
                    "label": "Theodorus Studita",
                    "uri": "https://pinakes.irht.cnrs.fr/notices/auteur/2685/",
                    "source": "Pinakes"
                }
            ]
        }
        """
            )
            == self.THEODORE
        )

    def test_bad_ark(self) -> None:
        with pytest.raises(ValidationError, match="String should match pattern"):
            st.Agent.model_validate_json(
                """
            {
                "ark": "21198/s1d01s",
                "type": {"id": "person", "label": "Person"},
                "pref_name": "Theodore the Studite"
            }
            """
            )


class TestWritingItem:
    def test_good_writing_item(self) -> None:
        st.WritingItem.model_validate_json(
            """
            {
                "script": [
                    {
                        "id": "nuskhurimt",
                        "label": "Nuskhurimt",
                        "writing_system": "Georgian"
                    }
                ],
                "note": [
                    "Relatively thick and clumsy"
                ]
            }
        """
        )


class TestInkItem:
    def test_good_ink_item(self) -> None:
        st.InkItem.model_validate_json(
            """
            { 
                "locus": "ff. 55v-144v", 
                "color": [ 
                    "dark brown" 
                ], 
                "note": [ 
                    "Rubrication of titles in red ink" 
                ] 
            } 
        """
        )


class TestLayoutItem:
    def test_good_layout_item(self) -> None:
        st.LayoutItem.model_validate_json(
            """
            {
                "locus": "ff. 3r-54v",
                "columns": "1",
                "lines": "15",
                "dim": "Writing area: 215 x 140 mm",
                "note": [
                    "Possible pricking still visible in outer margins throughout",
                    "Text written inside bordered margins"
                ]
            }
        """
        )


class TestUnitItem:
    def test_good_text_unit_item(self) -> None:
        st.LayerTextUnit.model_validate_json(
            """
            {
                "id": "ark:/21198/s1w103",
                "label": "Item 1"
            }
        """
        )


class TestAssocNameItem:
    EPHREM = st.AssocNameItem(
        id="ark:/21198/s1v887",
        as_written="ܝܘܚܢܢ ܒܪܝ ܬܐܘܕܘܪܘܣ",
        role=st.ControlledTerm(id="scribe", label="Scribe"),
        note=["The ARK is for Ephrem, to demo functionality"],
    )

    def test_good_TestAssocNameItem(self) -> None:
        assert (
            st.AssocNameItem.model_validate_json(
                """
            { 
                "id": "ark:/21198/s1v887",
                "as_written": "ܝܘܚܢܢ ܒܪܝ ܬܐܘܕܘܪܘܣ", 
                "role": { 
                    "id": "scribe", 
                    "label": "Scribe" 
                }, 
                "note": [ 
                    "The ARK is for Ephrem, to demo functionality" 
                ] 
            }
        """
            )
            == self.EPHREM
        )

    def test_hashable(self) -> None:
        assert isinstance(self.EPHREM, Hashable)
        hash(self.EPHREM)

    def test_good_TestAssocNameItemMerged(self) -> None:
        result = self.EPHREM.convert(
            st.AssocNameItemMerged, agent_record=TestAgent.EPHREM
        )
        assert result.agent_record == TestAgent.EPHREM


class TestAssocPlaceItem:
    def test_good_assoc_place_item(self) -> None:
        st.AssocPlaceItem.model_validate_json(
            """
            {
                "value": "Possibly Jerusalem",
                "event": {
                    "id": "origin",
                    "label": "Place of Origin"
                }
            }
        """
        )


class TestAssocDateItem:
    def test_good_assoc_date_item(self) -> None:
        st.AssocDateItem.model_validate_json(
            """
            { 
                "type": { 
                    "id": "origin", 
                    "label": "Origin Date" 
                }, 
                "note": [ 
                    "Paleographic dating" 
                ], 
                "value": "Second half 9th c. CE", 
                "iso": { 
                    "not_before": "0851", 
                    "not_after": "0900" 
                } 
            }
        """
        )


class TestParaItem:
    def test_good_para_item(self) -> None:
        st.ParaItem.model_validate_json(
            """
            {
                "type": {
                    "id": "colophon",
                    "label": "Colophon"
                },
                "locus": "99r",
                "lang": [
                    {
                        "id": "class1252",
                        "label": "Syriac"
                    }
                ],
                "as_written": "ܐܫܠܡ ܒܥܘܕܪܢ ܐܠܗܐ ܡܢܘ ܕܬܝܒ̄ܘ ܥܠ ܐܦܝ ܬܫܥ ܫ̈ܥܝܢ ܝܘܡ ܕܬܪܝܐ ܒ̄ܛ ܒܐܕܐܪ ܫܢܬ ܐܠܦ ܘܚܡܫ̄ ܡ̄ܘ ܡ̣ܢ ܕܐܠܣܟܢ̄ܕܪ ܟܬܒܗ̣ ܕܝܢ ܐܢܫ ܡܚܲܝܠܐ ܘܚܛܝܐ ܘܒܨ̇ܝܪܐ ܕܟܠܗܘܢ ܒܢ̈ܝܗܫܐ ܦܝܡ ܣ ܠܡܬ ܥܡ ܨܐܕܝܬ̤ ܒܪ ܨ̇ܗܘܝ ܡ̣ܢ ܩܪܝܬ̤ ܡܒܪܟܬܐ ܘܪܚܡܬ̤ ܠܡܫܝ̣ܚܐ ܨܕܐܢܝ ܡܢܝܚ ܡܪܝܐ ܢܦܫܗ̣ ܥܡ ܟܠܗܘܢ ܩܕܝܫܘ̈ܗܝ ܐܡܝܢ"
            }
        """
        )


class TestRelatedMs:
    def test_good_related_ms(self) -> None:
        st.RelatedMs.model_validate_json(
            """
            { 
                "type": { 
                    "id": "filiation", 
                    "label": "Filiation" 
                }, 
                "label": "Copied from Syriac 10", 
                "mss": [
                    { 
                        "label": "Sinai Syriac 10", 
                        "id": "ark:/21198/z1p57n0b" 
                    } 
                ], 
                "note": [ 
                    "This is a dummy note for dev purposes" ,
                    "Otherwise largely lost"
                ] 
            } 
        """
        )

    def test_no_ms_id(self) -> None:
        st.RelatedMs.model_validate_json(
            """
            { 
                "type": { 
                    "id": "disjecta", 
                    "label": "Disjecta Membra" 
                }, 
                "label": "Disjecta Membra from the final quire", 
                "note": [ 
                    "The last 4 folios are today Biblioteca Ambrosiana, A 296 inf., ff. 70–73 = Chabot 20 (4 ff.) + Mingana Syr. 632 (1 f.)" ,
                    "Identification of disjecta membra by Rossetto"
                ], 
                "mss": [
                    { 
                        "label": "Biblioteca Ambrosiana, A 296 inf., ff. 70–73 = Chabot 20 (4 ff.)", 
                        "url": "https://archive.org/details/ChabotInventaireDesFragmentsDeMssSyriaquesConservesALaBibliothequeAmbrosienneAMilan/page/n3/mode/2up" 
                    }, 
                    { 
                        "label": "Mingana Syr. 632 (1 f.)", 
                        "url": "http://epapers.bham.ac.uk/160" 
                    } 
                ] 
            }
        """
        )


class TestNoteItem:
    def test_good_note_item(self) -> None:
        """ "Example from https://github.com/UCLALibrary/sinaiportal_data/blob/626274aac4d5f9004db44615827ebc167da00036/export_test/layers/s18d1p.json"""

        st.NoteItem.model_validate_json(
            """
            {
                "type": {
                    "id": "general",
                    "label": "Other Notes"
                },
                "value": "Many additions and erasures in overtext"
            }
        """
        )


class TestInscribedLayer:
    def test_good_inscribed_layer(self) -> None:
        """ "Example from https://github.com/UCLALibrary/sinaiportal_data/blob/626274aac4d5f9004db44615827ebc167da00036/export_test/layers/s18d1p.json"""

        st.InscribedLayer.model_validate_json(
            """
            {
                "ark": "ark:/21198/s18d1p",
                "reconstruction": false,
                "label": "Sinai Georgian 34, Overtext (Undetermined (Georgian))",
                "state": {
                    "id": "overtext",
                    "label": "Overtext"
                },
                "writing": [
                    {
                        "script": [
                            {
                                "id": "georgian-undetermined",
                                "label": "Undetermined (Georgian)",
                                "writing_system": "Georgian"
                            }
                        ]
                    }
                ],
                "ink": [
                    {
                        "color": [
                            "black",
                            "red"
                        ],
                        "note": [
                            "Red used for rubrics"
                        ]
                    }
                ],
                "text_unit": [
                    {
                        "id": "ark:/21198/s1308n",
                        "label": "Item 1"
                    }
                ],
                "features": [
                    {
                        "id": "dated",
                        "label": "Dated"
                    }
                ],
                "assoc_date": [
                    {
                        "type": {
                            "id": "origin",
                            "label": "Date of Origin"
                        },
                        "value": "932  CE",
                        "iso": {
                            "not_before": "0932"
                        }
                    }
                ],
                "note": [
                    {
                        "type": {
                            "id": "general",
                            "label": "Other Notes"
                        },
                        "value": "Many additions and erasures in overtext"
                    }
                ],
                "parent": [
                    "ark:/21198/z1h13zxq"
                ]
            }
        """
        )


class TestManuscriptLayer:
    def test_good_ManuscriptLayerUnmerged(self) -> None:
        """Example from https://github.com/UCLALibrary/sinaiportal_data/blob/626274aac4d5f9004db44615827ebc167da00036/export_test/ms_objs/te5f0f9b.json"""

        st.ManuscriptLayerUnmerged.model_validate_json(
            """
            { 
                "id": "ark:/21198/te5fp1ol", 
                "label": "Overtext layer (13th c., Melkite)", 
                "type": { 
                    "id": "overtext", 
                    "label": "Overtext" 
                }, 
                "locus": "ff. 3r-54v" 
            } 
        """
        )

    def test_ManuscriptLayerMerged(self) -> None:
        st.ManuscriptLayerMerged(
            id="ark:/21198/123",
            label="Test Layer",
            type=st.ControlledTerm(id="guest", label="Guest Content"),
            layer_record=Mock(st.InscribedLayerMerged),
        )

    def test_good_UndertextManuscriptLayerMerged(self) -> None:
        result = st.UndertextManuscriptLayerMerged(
            id="ark:/21198/123",
            label="Test Layer",
            script=["Tengwar"],
            lang=["Sindarin"],
            type=st.ControlledTerm(id="undertext", label="Undertext"),
        ).model_dump()
        assert result == {
            "uto_layer_ark": "ark:/21198/123",
            "label": "Test Layer",
            "script": ("Tengwar",),
            "lang": ("Sindarin",),
            "type": {"id": "undertext", "label": "Undertext"},
        }

    def test_UndertextManuscriptLayerMerged_with_layer_record(self) -> None:
        with pytest.raises(
            ValidationError, match=r"layer_record\s+Input should be None"
        ):
            st.UndertextManuscriptLayerMerged(
                id="ark:/21198/123",
                label="Test Layer",
                layer_record=Mock(st.InscribedLayerMerged),
                type=st.ControlledTerm(id="undertext", label="Undertext"),
            )

    def test_UndertextManuscriptLayerMerged_wrong_type(self) -> None:
        with pytest.raises(
            ValidationError,
            match='UndertextManuscriptLayerMerged records must have type="undertext"',
        ):
            st.UndertextManuscriptLayerMerged(
                id="ark:/21198/123",
                label="Test Layer",
                type=st.ControlledTerm(id="guest", label="Guest Content"),
            )


class TestPart:
    def test_good_Part(self) -> None:
        """Example from https://github.com/UCLALibrary/sinaiportal_data/blob/626274aac4d5f9004db44615827ebc167da00036/export_test/ms_objs/te5f0f9b.json"""

        st.Part.model_validate_json(
            """
            { 
                "label": "Part 1", 
                "summary": "Synaxarion (Gospel Lectionary for the movable feast days according to the Byzantine rite)", 
                "locus": "ff. 3-54", 
                "support": [
                    { 
                        "id": "paper", 
                        "label": "Paper" 
                    } 
                ], 
                "extent": "51 ff.", 
                "dim": "235 x 154 mm (average folio)", 
                "layer": [
                    { 
                        "id": "ark:/21198/te5fp1ol", 
                        "label": "Overtext layer (13th c., Melkite)", 
                        "type": { 
                            "id": "overtext", 
                            "label": "Overtext" 
                        }, 
                        "locus": "ff. 3r-54v" 
                    } 
                ], 
                "note": [
                    { 
                        "type": 
                        { 
                            "id": "support", 
                            "label": "Support" 
                        }, 
                        "value": "Oriental paper" 
                    }, 
                    { 
                        "type": 
                        { 
                            "id": "collation", 
                            "label": "Collation" 
                        }, 
                        "value": "Quire signatures in the first part are marked in the bottom margin on the recto side of the first folio of a quire; quires of 8 ff. with the exception of quire II (6 ff.)" 
                    }, 
                    { 
                        "type": 
                        { 
                            "id": "collation", 
                            "label": "Collation" 
                        }, 
                        "value": "F. 11 may be a replacement" 
                    }, 
                    { 
                        "type": 
                        { 
                            "id": "collation", 
                            "label": "Collation" 
                        }, 
                        "value": "One f. missing after f. 17" 
                    } 
                ] 
            }
        """
        )


class TestLocationItem:
    def test_good_LocationItem(self) -> None:
        """Example from https://github.com/UCLALibrary/sinaiportal_data/blob/626274aac4d5f9004db44615827ebc167da00036/export_test/ms_objs/te5f0f9b.json"""

        st.LocationItem.model_validate_json(
            """
            { 
                "id": "sinai-oc", 
                "collection": "Old Collection" ,
                "repository": "St. Catherine's Monastery of the Sinai"
            }
        """
        )


class TestViscodexItem:
    def test_good_ViscodexItem(self) -> None:
        """Example from https://github.com/UCLALibrary/sinaiportal_data/blob/626274aac4d5f9004db44615827ebc167da00036/export_test/ms_objs/te5f0f9b.json"""

        st.ViscodexItem.model_validate_json(
            """
            { 
                "type": { 
                    "id": "manuscript", 
                    "label": "Manuscript" 
                }, 
                "label": "Viscodex for Syriac 12", 
                "url": "https://vceditor.library.upenn.edu/project/668da6f75d69680001457684/viewOnly" 
            }
        """
        )


class TestIiifItem:
    def test_good_IiifItem(self) -> None:
        """Example from https://github.com/UCLALibrary/sinaiportal_data/blob/626274aac4d5f9004db44615827ebc167da00036/export_test/ms_objs/te5f0f9b.json"""

        st.IiifItem.model_validate_json(
            """
            { 
                "type": { 
                    "id": "main", 
                    "label": "Main" 
                }, 
                "manifest": "https://iiif.library.ucla.edu/ark%3A%2F21198%2Fz15f0f9b/manifest", 
                "text_direction": "right-to-left", 
                "behavior": "paged", 
                "thumbnail": "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz15f0f9b%2Fp161m45m/full/!200,200/0/default.jpg" 
            }
        """
        )

    def test_ingest_in_url(self) -> None:
        """Example from https://github.com/UCLALibrary/sinaiportal_data/blob/626274aac4d5f9004db44615827ebc167da00036/export_test/ms_objs/te5f0f9b.json"""

        result = st.IiifItem.model_validate_json(
            """
            { 
                "type": { 
                    "id": "main", 
                    "label": "Main" 
                }, 
                "manifest": "https://ingest.iiif.library.ucla.edu/ark%3A%2F21198%2Fz15f0f9b/manifest", 
                "text_direction": "right-to-left", 
                "behavior": "paged", 
                "thumbnail": "https://iiif.sinaimanuscripts.library.ucla.edu/iiif/2/ark%3A%2F21198%2Fz15f0f9b%2Fp161m45m/full/!200,200/0/default.jpg" 
            }
        """
        )
        assert result.manifest == AnyUrl(
            "https://iiif.library.ucla.edu/ark%3A%2F21198%2Fz15f0f9b/manifest"
        )


class TestManuscriptObject:
    def test_good_ManuscriptObject(self) -> None:
        """Example from https://github.com/UCLALibrary/sinaiportal_data/blob/626274aac4d5f9004db44615827ebc167da00036/export_test/ms_objs/te5f0f9b.json"""

        result = st.ManuscriptObject.model_validate_json(
            Path("tests/sinai/export_test/ms_objs/te5f0f9b.json").read_text()
        )
        assert (
            result.image_provenance.program[0].camera_operator[0]  # type: ignore
            == "Damianos Kasotakis"
        )

    def test_unmerged_reconstructed_from_is_ark(self) -> None:
        result = st.ManuscriptObjectUnmerged(
            ark="ark:/21198/test",
            reconstruction=True,
            type=Mock(st.ControlledTerm),
            shelfmark="abc",
            state=Mock(st.ControlledTerm),
            part=(Mock(st.PartUnmerged),),
            location=(Mock(st.LocationItem),),
            reconstructed_from=("ark:/21198/456", "ark:/21198/789"),
        )
        assert result.reconstructed_from == ("ark:/21198/456", "ark:/21198/789")

    def test_unmerged_reconstructed_from_not_object(self) -> None:
        with pytest.raises(ValidationError):
            st.ManuscriptObjectUnmerged(
                ark="ark:/21198/test",
                reconstruction=True,
                type=Mock(st.ControlledTerm),
                shelfmark="abc",
                state=Mock(st.ControlledTerm),
                part=(Mock(st.PartUnmerged),),
                location=(Mock(st.LocationItem),),
                reconstructed_from=(
                    Mock(st.ReconstructedFrom),
                    Mock(st.ReconstructedFrom),
                ),
            )

    def test_merged_reconstructed_from_is_object(self) -> None:
        result = st.ManuscriptObjectMerged(
            ark="ark:/21198/test",
            reconstruction=True,
            type=Mock(st.ControlledTerm),
            shelfmark="abc",
            state=Mock(st.ControlledTerm),
            part=(Mock(st.PartMerged),),
            location=(Mock(st.LocationItem),),
            reconstructed_from=(Mock(st.ReconstructedFrom), Mock(st.ReconstructedFrom)),
        )
        assert isinstance(result.reconstructed_from[0], st.ReconstructedFrom)

    def test_merged_reconstructed_from_not_ark(self) -> None:
        with pytest.raises(ValidationError):
            st.ManuscriptObjectMerged(
                ark="ark:/21198/test",
                reconstruction=True,
                type=Mock(st.ControlledTerm),
                shelfmark="abc",
                state=Mock(st.ControlledTerm),
                part=(Mock(st.PartMerged),),
                location=(Mock(st.LocationItem),),
                reconstructed_from=("ark:/21198/456", "ark:/21198/789"),
            )


class TestWorkStub:
    def test_good_WorkStub(self) -> None:
        """example from https://github.com/UCLALibrary/sinaiportal_data/blob/d58a6555cf08448fa0b0b95e0ff91717992d67f2/text_units/s1cd6h.json"""
        st.WorkStub.model_validate_json(
            """
            {
                "id": "ark:/21198/s12c7r"
            }
        """
        )


class TestWorkBrief:
    def test_good_WorkBrief(self) -> None:
        """example from https://github.com/UCLALibrary/sinaiportal_data/blob/626274aac4d5f9004db44615827ebc167da00036/export_test/text_units/s1mh4z.json"""
        st.WorkBrief.model_validate_json(
            """
            {
                "desc_title": "Unidentified text"
            }
        """
        )


class TestExcerptItem:
    def test_good_ExcerptItem(self) -> None:
        """example from https://github.com/UCLALibrary/sinaiportal_data/blob/46584bb30e5f351e73010a4914a71a52e3ea389d/text_units/s1b35q.json"""
        st.ExcerptItem.model_validate_json(
            """
            {
                "type": {
                    "id": "incipit",
                    "label": "Incipit"
                },
                "locus": "f. 8v",
                "as_written": "هذا مبتداء"
            }
        """
        )


class TestContents:
    def test_good_Contents(self) -> None:
        """example from https://github.com/UCLALibrary/sinaiportal_data/blob/46584bb30e5f351e73010a4914a71a52e3ea389d/text_units/s1c37s.json"""
        st.Contents.model_validate_json(
            """
            {
                "label": "Gospel of Matthew (ff. 3v–39v)"
            }
        """
        )


class TestWorkWitItem:
    def test_good_WorkWitItem_with_WorkStub(self) -> None:
        """example from https://github.com/UCLALibrary/sinaiportal_data/blob/d58a6555cf08448fa0b0b95e0ff91717992d67f2/text_units/s1cd6h.json"""
        result = st.WorkWitItem.model_validate_json(
            """
            {
                "work": {
                    "id": "ark:/21198/s12c7r"
                }
            }
        """
        )
        assert isinstance(result.work, st.WorkStub)

    def test_good_WorkWitItem_with_WorkBrief(self) -> None:
        """example from https://github.com/UCLALibrary/sinaiportal_data/blob/d58a6555cf08448fa0b0b95e0ff91717992d67f2/text_units/s1cd6h.json"""
        result = st.WorkWitItem.model_validate_json(
            """
            {
                "work": {
                    "desc_title": "Gospel of Matthew (ff. 3v–39v)"
                }
            }
        """
        )
        assert isinstance(result.work, st.WorkBrief)

    def test_bad_mixed_work_type(self) -> None:
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            st.WorkWitItem.model_validate_json(
                """
                {
                    "work": {
                        "id": "ark:/21198/s12c7r",
                        "label": "Gospel of Matthew (ff. 3v–39v)"
                    }
                }
            """
            )


class TestTextUnit:
    def test_good_TextUnit(self) -> None:
        """example from https://github.com/UCLALibrary/sinaiportal_data/blob/d58a6555cf08448fa0b0b95e0ff91717992d67f2/text_units/s1cd6h.json"""
        st.TextUnit.model_validate_json(
            """
            {
                "ark": "ark:/21198/s1cd6h",
                "reconstruction": false,
                "label": "Gospel of Matthew, chs. 15-27",
                "lang": [
                    {
                        "id": "class1252",
                        "label": "Syriac"
                    }
                ],
                "work_wit": [
                    {
                        "work": {
                            "id": "ark:/21198/s12c7r"
                        }
                    }
                ],
                "note": [
                    {
                        "type": {
                            "id": "contents",
                            "label": "Contents Note"
                        },
                        "value": "Chs. 15-27"
                    },
                    {
                        "type": {
                            "id": "general",
                            "label": "Other Notes"
                        },
                        "value": "Description by Grigory Kessel"
                    }
                ],
                "parent": [
                    "ark:/21198/s1qd1q"
                ]
            }    
        """
        )


class TestCreation:
    def test_good_Creation(self) -> None:
        """Example from https://github.com/UCLALibrary/sinaiportal_data/blob/32278a93089ee067da48dac6adee5bb1ef888986/export_test/works/s1cc8x.json"""
        st.Creation.model_validate_json(
            """
            {
                "value": "600 CE",
                "iso": {
                    "not_before": "0600"
                }
            }
        """
        )


# # TODO not attested
# class TestIncipit:
#     def test_good_Incipit(self) -> None:
#         st.Incipit.model_validate_json("""

#         """)


# # TODO not attested
# class TestExplicit:
#     def test_good_Explicit(self) -> None:
#         st.Explicit.model_validate_json("""

#         """)


# # TODO not attested
# class TestRelWorkItem:
#     def test_good_RelWorkItem(self) -> None:
#         st.RelWorkItem.model_validate_json("""

#         """)


class TestConceptualWorkUnmerged:
    def test_good_ConceptualWorkUnmerged(self) -> None:
        """Example from https://github.com/UCLALibrary/sinaiportal_data/blob/32278a93089ee067da48dac6adee5bb1ef888986/export_test/works/s1cs35.json"""
        st.ConceptualWork.model_validate_json(
            """
            {
                "ark": "ark:/21198/s1cs35",
                "pref_title": "Ezekiel",
                "alt_title": [
                    "Bible. Ezekiel"
                ],
                "genre": [
                    {
                        "id": "biblical-texts",
                        "label": "Biblical texts"
                    }
                ],
                "rel_con": [
                    {
                        "label": "Bible. Ezekiel",
                        "uri": "https://viaf.org/viaf/176193843",
                        "source": "VIAF"
                    },
                    {
                        "label": "Bible. Ezekiel",
                        "uri": "http://id.loc.gov/authorities/names/n79117856",
                        "source": "LoC"
                    }
                ],
                "refno": [],
                "bib": []
            }
        """
        )
