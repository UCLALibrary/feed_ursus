# pyright: reportInvalidTypeForm=false
# pylint: disable=too-many-lines
"""Pydantic classes for the data model."""

import logging
from itertools import chain
from typing import Callable, Iterator, List, Literal, TypeVar

from pydantic import Field, computed_field
from typing_extensions import ParamSpec

import feed_sinai.sinai_types as st

LAYER_FIELDS = Literal["ot_layer", "guest_layer", "uto"]

P = ParamSpec("P")
T = TypeVar("T")


def filter_none(
    generator_function: Callable[P, Iterator[T | None]],
) -> Callable[P, Iterator[T]]:
    def wrapper(*args: P.args, **kwds: P.kwargs) -> Iterator[T]:
        for item in generator_function(*args, **kwds):
            if item is not None:
                yield item

    return wrapper


Ta = TypeVar("Ta", bound=str | int)


def generator_field(
    generator_function: Callable[P, Iterator[Ta]],
) -> Callable[P, list[Ta]]:
    @computed_field
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> list[Ta]:
        return sorted(set(generator_function(*args, **kwargs)))

    return wrapper


class ManuscriptSolrRecord(st.BaseModel):
    ms_obj: st.ManuscriptObjectMerged = Field(..., exclude=True)
    iiif_manifests: tuple[dict, ...] = tuple()

    def __repr__(self) -> str:
        return f'<ManuscriptSolrRecord ark="{self.ark_ssi}">'

    @computed_field
    def ark_ssi(self) -> str:
        return self.ms_obj.ark

    #
    #   Facets (Main / any)
    #

    @computed_field
    def ms_type_ssi(self) -> str:
        return self.ms_obj.type.label

    @computed_field
    def state_ssi(self) -> str:
        return self.ms_obj.state.label

    @computed_field
    def features_ssim(self) -> list[str]:
        return sorted(
            {
                feature.label
                for feature in self.ms_obj.deep_get("features", cls=st.ControlledTerm)
            }
        )

    @computed_field()
    def support_ssim(self) -> list[str]:
        return sorted(
            {support.label for part in self.ms_obj.part for support in part.support}
        )

    @computed_field
    def repository_ssim(self) -> list[str]:
        return sorted({location.repository for location in self.ms_obj.location})

    @computed_field
    def collection_ssim(self) -> list[str]:
        return sorted(
            {
                location.collection
                for location in self.ms_obj.location
                if location.collection
            }
        )

    @computed_field
    def names_ssim(self) -> list[str]:
        return sorted(
            {
                agent_record.pref_name
                for agent_record in self.ms_obj.deep_get(cls=st.Agent)
            }
        )

    @computed_field
    def places_ssim(self) -> list[str]:
        return sorted({place.pref_name for place in self.ms_obj.deep_get(cls=st.Place)})

    @computed_field
    def date_types_ssim(self) -> list[str]:
        return sorted(
            {
                date.type.label
                for date in self.ms_obj.deep_get(cls=st.AssocDateItem)
                if date.type.id != "origin"
            }
        )

    @computed_field
    def program_ssim(self) -> list[str]:
        return sorted(
            {
                program.label
                for program in (
                    self.ms_obj.desc_provenance.program
                    if self.ms_obj.desc_provenance
                    else []
                )
            }
            | {
                program.label
                for program in (
                    self.ms_obj.image_provenance.program
                    if self.ms_obj.image_provenance
                    else []
                )
                if program.label
            }
        )

    @computed_field
    def reconstructed_from_ssim(self) -> list[str]:
        return [ms.id for ms in self.ms_obj.reconstructed_from]

    @computed_field
    def reconstructed_from_shelfmark(self) -> list[str]:
        return [ms.shelfmark for ms in self.ms_obj.reconstructed_from]

    @computed_field
    def ot_script_ssim(self) -> list[str]:
        return sorted(
            {
                script_item.label
                for ot_layer in self.ot_layers()
                for writing_item in ot_layer.layer_record.writing
                for script_item in writing_item.script
            }
        )

    @computed_field
    def ot_writing_system_ssim(self) -> list[str]:
        return sorted(
            {
                script_item.writing_system
                for ot_layer in self.ot_layers()
                for writing_item in ot_layer.layer_record.writing
                for script_item in writing_item.script
            }
        )

    @computed_field
    def ot_genre_ssim(self) -> list[str]:
        return sorted(
            {
                genre.label
                for layer in self.ot_layers()
                for genre in layer.deep_get("genre", cls=st.ControlledTerm)
            }
        )

    @computed_field
    def ot_years_isim(self) -> list[int]:
        return sorted(
            {
                year
                for layer in self.ot_layers()
                for date in layer.layer_record.assoc_date
                if date.type.id == "origin" and date.iso
                for year in date.iso.years()
            }
        )

    @computed_field
    def ot_language_ssim(self) -> list[str]:
        return sorted(
            {
                language.label
                for layer in self.ot_layers()
                for text_unit in layer.layer_record.text_unit
                for language in text_unit.text_unit_record.lang
            }
        )

    @computed_field
    def ot_works_ssim(self) -> list[str]:
        return sorted(set(self.get_work_titles(layer_type="ot_layer", pref_only=True)))

    #
    #   Facets (Guest/Para Only)
    #

    @computed_field
    def para_script_ssim(self) -> list[str]:
        return sorted(
            {
                script.label
                for layer in self.guest_layers()
                for writing_item in layer.layer_record.writing
                for script in writing_item.script
            }
            | {
                script.label
                for para in self.get_para()
                if para.type.id != "framing"
                for script in para.script
            }
        )

    @computed_field
    def para_writing_system_ssim(self) -> list[str]:
        return sorted(
            {
                script.writing_system
                for layer in self.guest_layers()
                for writing_item in layer.layer_record.writing
                for script in writing_item.script
            }
            | {
                script.writing_system
                for para in self.get_para()
                if para.type.id != "framing"
                for script in para.script
            }
        )

    @computed_field
    def para_years_isim(self) -> list[int]:
        return sorted(
            {
                year
                for layer in self.guest_layers()
                for date in layer.layer_record.assoc_date
                if date.type.id == "origin" and date.iso
                for year in date.iso.years()
            }
        )

    @computed_field
    def para_language_ssim(self) -> list[str]:
        return sorted(
            {
                language.label
                for layer in self.guest_layers()
                for text_unit in layer.layer_record.text_unit
                for language in text_unit.text_unit_record.lang
            }
            | {
                language.label
                for para in self.get_para()
                if para.type.id != "framing"
                for language in para.lang
            }
        )

    @computed_field
    def para_works_ssim(self) -> list[str]:
        return sorted(
            set(self.get_work_titles(layer_type="guest_layer", pref_only=True))
        )

    @computed_field
    def para_genre_ssim(self) -> list[str]:
        return sorted(
            {
                genre.label
                for layer in self.guest_layers()
                for genre in layer.deep_get("genre", cls=st.ControlledTerm)
            }
        )

    @computed_field
    def para_names_ssim(self) -> list[str]:
        return sorted(
            {
                agent_record.pref_name
                for layer in self.guest_layers()
                for agent_record in layer.deep_get(cls=st.Agent)
            }
            | {
                assoc_name.agent_record.pref_name
                for para in self.get_para()
                for assoc_name in para.assoc_name
                if assoc_name.agent_record
            }
        )

    @computed_field
    def para_type_ssim(self) -> list[str]:
        return sorted(
            {subtype.label for para in self.get_para() for subtype in para.subtype}
        )

    #
    #   UTO facets
    #

    @computed_field
    def uto_script_ssim(self) -> list[str]:
        return sorted(
            {script for layer in self.uto_layers() for script in layer.script}
        )

    @computed_field
    def uto_language_ssim(self) -> list[str]:
        return sorted(
            {language for layer in self.uto_layers() for language in layer.lang}
        )

    @computed_field
    def uto_years_isim(self) -> list[int]:
        return sorted(
            {
                year
                for layer in self.uto_layers()
                for date in layer.orig_date
                if date.iso
                for year in date.iso.years()
            }
        )

    #
    #   Scoped / keyword search
    #

    @computed_field
    def shelfmark_ssi(self) -> str:
        return self.ms_obj.shelfmark

    @generator_field
    @filter_none
    def titles_tesim(self) -> Iterator[str | None]:
        yield from self.ms_obj.deep_get(
            "pref_title", "desc_title", "alt_title", cls=str
        )

        for work_wit in self.get_work_wits():
            yield work_wit.as_written
            for contents_item in work_wit.contents:
                yield contents_item.label

    @generator_field
    @filter_none
    def names_tesim(self) -> Iterator[str | None]:
        for agent in self.ms_obj.deep_get(cls=st.Agent):
            yield agent.pref_name
            yield from agent.alt_name

        for assoc_name in self.ms_obj.deep_get(cls=st.AssocNameItemMerged):
            yield assoc_name.value
            yield assoc_name.as_written
            yield from assoc_name.note

    @generator_field
    @filter_none
    def exerpts_tesim(self) -> Iterator[str | None]:
        for exceprt in self.deep_get(cls=st.ExcerptItem):
            yield exceprt.as_written
            yield from exceprt.translation

    @generator_field
    @filter_none
    def places_tesim(self) -> Iterator[str | None]:
        # Note: assumes all Place records are found in the `place_record` field of an AssociatedPlace, which is the case as of commit 7f2a5 on 7/29/2025

        for assoc_place_item in self.ms_obj.deep_get(cls=st.AssocPlaceItemMerged):
            if assoc_place_item.place_record:
                yield assoc_place_item.place_record.pref_name
                yield from assoc_place_item.place_record.alt_name

            yield assoc_place_item.value
            yield assoc_place_item.as_written
            yield from assoc_place_item.note

    @generator_field
    @filter_none
    def contents_tesim(self) -> Iterator[str | None]:
        yield from self.ms_obj.deep_get(
            "summary", "pref_title", "desc_title", "alt_title", cls=str
        )

        for work_wit in self.get_work_wits():
            yield work_wit.as_written
            yield from work_wit.note
            for contents_item in work_wit.contents:
                yield contents_item.label
                yield from contents_item.note

        for layer in self.get_layers():
            if isinstance(layer, st.ManuscriptLayerMerged):
                for text_unit in layer.layer_record.text_unit:
                    yield text_unit.text_unit_record.label

        for exerpt in self.ms_obj.deep_get(cls=st.ExcerptItem):
            yield exerpt.as_written
            yield from exerpt.translation
            yield from exerpt.note

    @generator_field
    @filter_none
    def paracontent_tesim(self) -> Iterator[str | None]:
        for item in chain(
            (
                ms_layer.layer_record
                for ms_layer in self.get_layers(layer_type="guest_layer")
                if ms_layer.layer_record
            ),
            self.ms_obj.deep_get(cls=st.ParaItemMerged),
        ):
            if isinstance(item, st.InscribedLayerMerged):
                yield from item.deep_get("summary", cls=str)

            elif isinstance(item, st.ParaItemMerged):
                yield item.label
                yield item.as_written
                yield from item.translation
                yield from item.note
                for script in item.script:
                    yield script.label
                    yield script.writing_system

            yield from item.deep_get("pref_name", cls=str)

            for assoc_name in item.deep_get(cls=st.AssocNameItemMerged):
                yield assoc_name.value
                yield assoc_name.as_written
                yield from assoc_name.note

            for assoc_place in item.deep_get(cls=st.AssocPlaceItemMerged):
                yield assoc_place.value
                yield assoc_place.as_written
                yield from assoc_place.note

            for assoc_date in item.deep_get(cls=st.AssocDateItem):
                yield from assoc_date.note

    @generator_field
    @filter_none
    def full_text_tesim(self) -> Iterator[str | None]:
        yield self.ms_obj.ark

        for support in self.ms_obj.deep_get("support", cls=st.ControlledTerm):
            yield support.label

        for script in self.ms_obj.deep_get(cls=st.ScriptItem):
            yield script.label
            yield script.writing_system

        yield self.ms_obj.shelfmark

        for note in self.ms_obj.deep_get(cls=st.NoteItem):
            yield note.value
        yield from self.ms_obj.deep_get("note", cls=str)

        yield from self.ms_obj.deep_get("color", cls=str)

        for lang in self.ms_obj.deep_get("lang", cls=st.ControlledTerm):
            yield lang.label

        yield from self.ms_obj.deep_get(
            "pref_title",
            cls=str,
        )

        for text_unit in self.ms_obj.deep_get(cls=st.TextUnit):
            yield text_unit.label

        yield from self.ms_obj.deep_get(
            "desc_title",
            "alt_title",
            "as_written",
            "translation",
            "summary",
            cls=str,
        )

        for contents_item in self.ms_obj.deep_get(cls=st.Contents):
            yield contents_item.label

        for para in self.ms_obj.deep_get(cls=st.ParaItem):
            yield para.label

        yield from self.ms_obj.deep_get(
            "pref_name",
            "alt_name",
            cls=str,
        )

        for name in self.ms_obj.deep_get(cls=st.AssocNameItem):
            yield name.value

        for place in self.ms_obj.deep_get(cls=st.AssocPlaceItem):
            yield place.value

        for related_ms in self.ms_obj.deep_get(cls=st.RelatedMs):
            yield related_ms.type.label
            yield related_ms.label
            for ms in related_ms.mss:
                yield ms.label

        if self.ms_obj.image_provenance:
            for program in self.ms_obj.image_provenance.program:
                yield program.delivery

    @computed_field
    def manuscript_json_ss(self) -> str:
        return self.ms_obj.model_dump_json()

    #
    #   Blacklight Stuff
    #

    @computed_field
    def id(self) -> str:
        return self.ms_obj.ark

    @computed_field
    def has_model_ssim(self) -> List[str]:
        return ["Work"]

    @computed_field
    def visibility_ssi(self) -> str:
        return "open"

    @computed_field
    def discover_access_group_ssim(self) -> List[str]:
        return ["public"]

    @computed_field
    def read_access_group_ssim(self) -> List[str]:
        return ["public"]

    @computed_field
    def download_access_person_ssim(self) -> List[str]:
        return ["public"]

    @computed_field
    def thumbnail_url_ss(self) -> st.AnyUrl | None:
        for iiif in self.ms_obj.iiif:
            if iiif.thumbnail:
                return iiif.thumbnail

        logging.warning(f"no thumbnail for {self.ms_obj.ark}")
        return None

    @computed_field
    def iiif_manifest_url_ssi(self) -> st.AnyUrl | None:
        if len(self.ms_obj.iiif) == 0:
            return None

        return self.ms_obj.iiif[0].manifest

    #
    #   Sinaimanuscripts stuff
    #

    @computed_field
    def header_index_tesim(self) -> list[str]:
        result = [self.ms_obj.shelfmark]
        if self.ms_obj.extent:
            result.append(self.ms_obj.extent)

        return result

    @computed_field
    def ot_date_tesim(self) -> list[str]:
        return sorted(
            {
                date.value
                for layer in self.ot_layers()
                for date in layer.layer_record.assoc_date
                if date.type.id == "origin"
            }
        )

    @computed_field
    def para_date_tesim(self) -> list[str]:
        return sorted(
            {
                date.value
                for layer in self.guest_layers()
                for date in layer.layer_record.assoc_date
                if date.type.id == "origin"
            }
        )

    @computed_field
    def uto_date_tesim(self) -> list[str]:
        return sorted(
            {
                date.value
                for layer in self.ot_layers()
                for date in layer.layer_record.assoc_date
                if date.type.id == "origin"
            }
        )

    #
    #   Helper methods
    #

    def ot_layers(self) -> Iterator[st.ManuscriptLayerMerged]:
        for part in self.ms_obj.part:
            yield from part.ot_layer
        yield from self.ms_obj.ot_layer

    def guest_layers(self) -> Iterator[st.ManuscriptLayerMerged]:
        for part in self.ms_obj.part:
            yield from part.guest_layer
        yield from self.ms_obj.guest_layer

    def uto_layers(self) -> Iterator[st.UndertextManuscriptLayerMerged]:
        for part in self.ms_obj.part:
            yield from part.uto
        yield from self.ms_obj.uto

    def get_layers(
        self, layer_type: LAYER_FIELDS | None = None
    ) -> Iterator[st.ManuscriptLayerMerged | st.UndertextManuscriptLayerMerged]:
        if layer_type in ("ot_layer", None):
            yield from self.ms_obj.ot_layer
            for part in self.ms_obj.part:
                yield from part.ot_layer

        if layer_type in ("guest_layer", None):
            yield from self.ms_obj.guest_layer
            for part in self.ms_obj.part:
                yield from part.guest_layer

        if layer_type in ("uto", None):
            yield from self.ms_obj.uto
            for part in self.ms_obj.part:
                yield from part.uto

    def get_text_units(self) -> Iterator[st.TextUnitMerged]:
        for layer in self.get_layers():
            if layer.layer_record:
                for text_unit in layer.layer_record.text_unit:
                    yield text_unit.text_unit_record

    def get_work_wits(
        self, layer_type: LAYER_FIELDS | None = None
    ) -> Iterator[st.WorkWitItemMerged]:
        for layer in self.get_layers(layer_type=layer_type):
            if isinstance(layer, st.ManuscriptLayerMerged):
                for text_unit in layer.layer_record.text_unit:
                    yield from text_unit.text_unit_record.work_wit

    @filter_none
    def get_work_titles(
        self, layer_type: LAYER_FIELDS | None = None, pref_only: bool = True
    ) -> Iterator[str | None]:
        for work_wit in self.get_work_wits(layer_type=layer_type):
            if isinstance(work_wit.work, st.ConceptualWork):
                yield work_wit.work.pref_title
                if not pref_only:
                    yield work_wit.work.orig_lang_title
                    yield from work_wit.work.alt_title

            elif isinstance(work_wit.work, st.WorkBrief) and not pref_only:
                yield work_wit.work.desc_title

            for contents_item in work_wit.contents:
                yield contents_item.pref_title
                if not pref_only:
                    yield contents_item.label
                    yield contents_item.pref_title

            if not pref_only:
                yield work_wit.alt_title
                yield work_wit.as_written

    def get_exerpts(self, exclude: list[LAYER_FIELDS] = []) -> set[str]:
        return (
            {
                text
                for layer in self.ms_obj.deep_get(
                    cls=st.ManuscriptLayer, exclude=exclude
                )
                for exerpt in layer.deep_get(cls=st.Incipit)
                for text in [
                    exerpt.value,
                    *exerpt.translation,
                ]
            }
            | {
                text
                for layer in self.ms_obj.deep_get(
                    cls=st.ManuscriptLayer, exclude=exclude
                )
                for exerpt in layer.deep_get(cls=st.Explicit)
                for text in [
                    exerpt.value,
                    *exerpt.translation,
                ]
            }
            | {
                text
                for layer in self.ms_obj.deep_get(
                    cls=st.ManuscriptLayer, exclude=exclude
                )
                for exerpt in layer.deep_get(cls=st.ExcerptItem)
                for text in [
                    exerpt.as_written,
                    *exerpt.translation,
                ]
                if text
            }
        )

    def get_para(self) -> Iterator[st.ParaItemMerged]:
        """Get all para items from the manuscript."""
        yield from self.ms_obj.para

        for part in self.ms_obj.part:
            yield from part.para

        for layer in self.get_layers():
            if isinstance(layer, st.ManuscriptLayerMerged):
                yield from layer.layer_record.para

                for text_unit in layer.layer_record.text_unit:
                    yield from text_unit.text_unit_record.para
