# mypy: disable-error-code="prop-decorator"

import re
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal, Self, Type, assert_never
from urllib.parse import urlparse

# from urllib.parse import urlparse
from pydantic import (
    AliasChoices,
    AnyUrl,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    ModelWrapValidatorHandler,
    computed_field,
    create_model,
    field_validator,
    model_validator,
)
from pysolr import Solr  # type: ignore

from feed_ursus import date_parser, year_parser
from feed_ursus.controlled_fields import (
    Language,
    ObjectType,
    ResourceType,
    RightsStatement,
    TextDirection,
    ViewingHint,
    Visibility,
)
from feed_ursus.util import (
    Ark,
    Empty,
    MARCList,
    MARCString,
    MARCSubject,
    SolrDatetime,
    UrsusId,
    make_ursus_id,
    serialize_term,
)

solr_date_from_python = Solr("http://nowhere")._from_python


class ReindexRecord(BaseModel):
    solr_id: Literal["ongoing_reingest"] = Field("ongoing_reingest", alias="id")
    cutoff_timestamp: datetime


class IngestSolrRecord(BaseModel):
    model_config = ConfigDict(
        serialize_by_alias=True,
        validate_by_name=True,
        validate_by_alias=True,
    )

    solr_id: str = Field(..., min_length=1, alias="id")
    is_ingest_bsi: Literal[True] = True
    ingest_filenames_ssim: list[str] = Field(..., min_length=1)
    feed_ursus_version_ssi: str = Field(..., min_length=1)
    ingest_user_ssi: str = Field(..., min_length=1)
    csv_files_tsm: list[str] = Field(..., min_length=1)


# Experimental, not actually used, likely to confuse type checker
def copy_field(field_name: str) -> Any:
    def inner(self: UrsusSolrRecord) -> Any:
        return getattr(self, field_name)

    return computed_field(property(inner))


# Experimental, not actually used, likely to confuse type checker
def controlled_term_id(
    field_name: str,
) -> Any:
    def inner(self: UrsusSolrRecord) -> str | list[str] | None:
        match getattr(self, field_name, AttributeError):
            case None | []:
                return None
            case Enum() as value:
                return value.name
            case [*values]:
                return [
                    value.name if isinstance(value, Enum) else str(value)
                    for value in values
                ]
            case _:
                raise AttributeError(
                    f"{field_name} must be a single or multi-valued enum field"
                )

    return computed_field(property(inner))


class UrsusSolrRecord(BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        serialize_by_alias=True,
        str_min_length=1,
        str_strip_whitespace=True,
        validate_by_name=True,
        validate_by_alias=True,
    )

    _strict = True

    #
    #   Required Fields
    #

    ark_ssi: Ark = Field(default=..., validation_alias="Item ARK")

    title_tesim: MARCList[MARCString] = Field(
        ..., validation_alias="Title", min_length=1
    )

    @computed_field(alias="id")
    @property
    def solr_id(self) -> str:
        return make_ursus_id(self.ark_ssi)

    #
    #   Controlled Fields
    #

    #   Text direction

    human_readable_iiif_text_direction_ssi: TextDirection | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Text direction"),
    )

    @computed_field
    @property
    def iiif_text_direction_ssi(self) -> str | None:
        return serialize_term(self.human_readable_iiif_text_direction_ssi, by="id")

    #   IIIF Viewing Hint

    human_readable_iiif_viewing_hint_ssi: ViewingHint | Empty = Field(
        default=None,
        validation_alias=AliasChoices("viewingHint"),
    )

    @computed_field
    @property
    def iiif_viewing_hint_ssi(self) -> str | None:
        return serialize_term(self.human_readable_iiif_viewing_hint_ssi, by="id")

    #    Language

    @staticmethod
    def validate_language(value: str | Language) -> Language:
        match value:
            case Language():
                return value
            case str() if value in Language.__members__:
                return Language[value]
            case _:
                return Language(value)

    human_readable_language_tesim: (
        MARCList[
            Annotated[
                Language,
                BeforeValidator(validate_language),
            ]
        ]
        | Empty
    ) = Field(
        default=None,
        validation_alias=AliasChoices("Language"),
    )

    @computed_field
    @property
    def human_readable_language_sim(self) -> list[str] | None:
        return serialize_term(self.human_readable_language_tesim, by="label")

    @computed_field
    @property
    def language_sim(self) -> list[str] | None:
        return serialize_term(self.human_readable_language_tesim, by="id")

    @computed_field
    @property
    def language_tesim(self) -> list[str] | None:
        # Resource Type

        return serialize_term(self.human_readable_language_tesim, by="id")

    human_readable_resource_type_tesim: MARCList[ResourceType] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Type.typeOfResource"),
    )

    @computed_field
    @property
    def human_readable_resource_type_sim(self) -> list[str] | None:
        return serialize_term(self.human_readable_resource_type_tesim, by="label")

    @computed_field
    @property
    def resource_type_sim(self) -> list[str] | None:
        return serialize_term(self.human_readable_resource_type_tesim, by="id")

    @computed_field
    @property
    def resource_type_ssim(self) -> list[str] | None:
        return serialize_term(self.human_readable_resource_type_tesim, by="id")

    # rights statement

    human_readable_rights_statement_tesim: (
        MARCList[
            Annotated[
                RightsStatement,
                BeforeValidator(
                    lambda value: "public domain" if value == "pd" else value
                ),
            ]
        ]
        | Empty
    ) = Field(
        default=None,
        validation_alias=AliasChoices("Rights.copyrightStatus"),
    )

    @computed_field
    @property
    def rights_statement_tesim(self) -> list[str] | None:
        return serialize_term(self.human_readable_rights_statement_tesim, by="id")

    #
    #   Other Fields
    #

    access_copy_ssi: AnyUrl | Empty = Field(
        default=None,
        validation_alias=AliasChoices(
            "access_copy",
            "IIIF Access URL",
        ),
    )

    alternative_title_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices(
            "AltTitle.other",
            "AltTitle.parallel",
            "AltTitle.translated",
            "Alternate Title.creator",
            "Alternate Title.descriptive",
            "Alternate Title.inscribed",
            "AltTitle.descriptive",
            "Alternate Title.other",
        ),
    )

    @computed_field
    @property
    def architect_sim(self) -> list[str] | None:
        return self.architect_tesim or None

    architect_tesim: MARCList[MARCString] | Empty = Field(
        default=None, validation_alias="Name.architect"
    )

    archival_collection_box_ssi: MARCString | Empty = Field(
        default=None, validation_alias="Box"
    )

    archival_collection_folder_ssi: MARCString | Empty = Field(
        default=None,
        validation_alias="Folder",
    )

    archival_collection_number_ssi: MARCString | Empty = Field(
        default=None,
        validation_alias="Archival Collection Number",
    )

    archival_collection_title_ssi: MARCString | Empty = Field(
        default=None,
        validation_alias="Archival Collection Title",
    )

    @computed_field
    @property
    def archival_collection_tesi(self) -> str | None:
        result: str = ""
        match self.archival_collection_title_ssi, self.archival_collection_number_ssi:
            case str() as title, str() as number:
                result = f"{title} ({number})"
            case str() as title, None:
                result = title
            case None, str() as number:
                result = f"Archival Collection {number}"
            case _:
                # No collection title or number; don't bother with box and folder
                return None

        box = re.sub(
            r"^\s*box\s*",
            "",
            self.archival_collection_box_ssi or "",
            flags=re.IGNORECASE,
        )

        if box:
            result += f", Box {box}"

        folder = re.sub(
            r"^\s*folder\s*",
            "",
            self.archival_collection_folder_ssi or "",
            flags=re.IGNORECASE,
        )

        if folder:
            result += f", Folder {folder}"

        return result

    @computed_field
    @property
    def artist_sim(self) -> list[str] | None:
        return self.artist_tesim or None

    artist_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Artist", "Name.artist"),
    )

    @computed_field
    @property
    def associated_name_sim(self) -> list[str] | None:
        return self.associated_name_tesim or None

    associated_name_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Associated Name"),
    )

    @computed_field
    @property
    def author_sim(self) -> list[str] | None:
        return self.author_tesim or None

    author_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Author"),
    )

    binding_condition_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Binding condition"),
    )

    @computed_field
    @property
    def binding_note_ssi(self) -> str | None:
        if self.binding_note_tesim and len(self.binding_note_tesim):
            return self.binding_note_tesim[0]
        else:
            return None

    binding_note_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Binding note", "Description.binding"),
    )

    @computed_field
    @property
    def calligrapher_sim(self) -> list[str] | None:
        return self.calligrapher_tesim

    calligrapher_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Calligrapher", "Name.calligrapher"),
    )

    caption_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Description.caption"),
    )

    @computed_field
    @property
    def cartographer_sim(self) -> list[str] | None:
        return self.cartographer_tesim or None

    cartographer_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Cartographer", "Name.cartographer"),
    )

    citation_source_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("References"),
    )
    collation_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Collation"),
    )

    colophon_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Colophon", "Description.colophon"),
    )

    @computed_field
    @property
    def combined_subject_ssim(self) -> list[str] | None:
        return (
            (self.named_subject_tesim or [])
            + (self.subject_tesim or [])
            + (self.subject_topic_tesim or [])
            + (self.subject_geographic_tesim or [])
            + (self.subject_temporal_tesim or [])
        ) or None

    @computed_field
    @property
    def commentator_sim(self) -> list[str] | None:
        return self.commentator_tesim or None

    commentator_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Commentator", "Name.commentator"),
    )

    @computed_field
    @property
    def composer_sim(self) -> list[str] | None:
        return self.composer_tesim or None

    composer_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Name.composer"),
    )

    @computed_field
    @property
    def condition_note_ssi(self) -> str | None:
        if self.condition_note_tesim and len(self.condition_note_tesim):
            return self.condition_note_tesim[0]
        else:
            return None

    condition_note_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Condition note", "Description.condition"),
    )

    content_disclaimer_ssm: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Content disclaimer"),
    )

    contents_note_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Contents note"),
    )

    contents_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Contents"),
    )

    contributor_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Contributors"),
    )

    @computed_field
    @property
    def creator_sim(self) -> list[str] | None:
        return self.creator_tesim or None

    creator_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Creator", "Name.creator"),
    )

    date_created_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Date.created", "Date.creation"),
    )

    @computed_field
    @property
    def date_dtsim(self) -> list[SolrDatetime] | None:
        match self.normalized_date_tesim:
            case list(dates):
                return [
                    solr_date_from_python(date)
                    for date in date_parser.get_dates(dates, strict=self._strict)
                ]  # pyright: ignore[reportPrivateUsage, reportUnknownMemberType]
            case None:
                return None

    @computed_field
    @property
    def date_dtsort(self) -> SolrDatetime | None:
        match self.date_dtsim:
            case [] | None:
                return None
            case [first, *_]:
                return first
            case _:
                return None

    delivery_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("delivery"),
    )

    description_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Description.note"),
    )

    descriptive_title_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Descriptive title"),
    )

    @computed_field
    @property
    def dimensions_sim(self) -> list[str] | None:
        return self.dimensions_tesim or None

    dimensions_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Format.dimensions"),
    )

    @computed_field
    @property
    def director_sim(self) -> list[str] | None:
        return self.director_tesim or None

    director_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Director", "Name.director"),
    )

    @computed_field
    @property
    def dlcs_collection_name_tesim(self) -> list[str] | None:
        return self.member_of_collections_ssim

    edition_ssm: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Edition"),
    )

    @computed_field
    @property
    def editor_sim(self) -> list[str] | None:
        return self.editor_tesim

    editor_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Editor", "Name.editor"),
    )

    electronic_locator_ss: MARCString | Empty = Field(
        default=None,
        validation_alias=AliasChoices("External item record", "View Record"),
    )

    @computed_field
    @property
    def engraver_sim(self) -> list[str] | None:
        return self.engraver_tesim or None

    engraver_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Engraver", "Name.engraver"),
    )

    explicit_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Explicit"),
    )

    @computed_field
    @property
    def extent_sim(self) -> list[str] | None:
        return self.extent_tesim or None

    extent_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Format.extent"),
    )

    featured_image_ssi: MARCString | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Featured image"),
    )

    @computed_field
    @property
    def features_sim(self) -> list[str] | None:
        return self.features_tesim or None

    features_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Features"),
    )

    finding_aid_url_ssm: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Finding Aid URL", "Alt ID.url"),
    )

    foliation_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Foliation", "Foliation note"),
    )

    folio_dimensions_ss: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Folio dimensions", "Folio Dimensions"),
    )

    @computed_field
    @property
    def form_sim(self) -> list[str] | None:
        return self.form_tesim or None

    form_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Form"),
    )

    format_book_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Format"),
    )

    funding_note_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Description.fundingNote"),
    )

    @computed_field
    @property
    def genre_sim(self) -> list[str] | None:
        return self.genre_tesim or None

    genre_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Type.genre", "Genre"),
    )

    @computed_field
    @property
    def geographic_coordinates_ssim(self) -> list[str] | None:
        return [
            ", ".join([lat, long])
            for lat, long in zip(
                self.latitude_tesim or [],
                self.longitude_tesim or [],
            )
        ] or None

    @model_validator(mode="after")
    def longitudes_match_latitudes(self) -> Self:
        if len(self.latitude_tesim or []) != len(self.longitude_tesim or []):
            raise ValueError(
                "\n".join(
                    [
                        "Mismatched lengths:",
                        f"Latitude {self.latitude_tesim}",
                        f"Longitude {self.longitude_tesim}",
                    ]
                )
            )
        return self

    hand_note_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Hand note"),
    )

    has_model_ssim: ObjectType = Field(
        default=ObjectType.WORK,
        validation_alias=AliasChoices("Object Type"),
    )

    @field_validator("has_model_ssim", mode="before")
    @classmethod
    def map_object_type(
        cls, value: ObjectType | list[str] | str | None
    ) -> ObjectType | str:
        match value:
            case "" | [] | None:
                # Default
                return "Work"
            case str(item) | [str(item)]:
                #  Object Type should be single-valued, but was accidentally indexed as a multivalued field, so if it's a list it should only contain a single item to unpack.
                return {
                    "Manuscript": "Work",
                    "Page": "ChildWork",
                }.get(item, item)
            case ObjectType() as item:
                return item
            case _:
                raise ValueError(
                    "Object Type should be a string or a list containing just one item"
                )

    history_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("History"),
    )

    @computed_field
    @property
    def host_sim(self) -> list[str] | None:
        return self.host_tesim

    host_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Host", "Name.host"),
    )

    identifier_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Identifier"),
    )

    iiif_manifest_url_ssi: MARCString | Empty = Field(
        default=None,
        validation_alias=AliasChoices("IIIF Manifest URL"),
    )

    iiif_range_ssi: MARCString | Empty = Field(
        default=None,
        validation_alias=AliasChoices("IIIF Range"),
    )

    illuminator_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Illuminator", "Name.illuminator"),
    )

    @computed_field
    @property
    def illuminator_sim(self) -> list[str] | None:
        return self.illuminator_tesim

    illustrations_note_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices(
            "Illustrations note", "Description.illustrations"
        ),
    )

    illustrator_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Illustrator", "Name.illustrator"),
    )

    @computed_field
    @property
    def illustrator_sim(self) -> list[str] | None:
        return self.illustrator_tesim or None

    image_count_ssi: MARCString | Empty = Field(
        default=None,
        validation_alias=AliasChoices("image count"),
    )

    incipit_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Incipit"),
    )

    ingest_id_ssi: str | Empty = None

    inscription_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Inscription"),
    )

    interviewee_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Interviewee", "Name.interviewee"),
    )

    @computed_field
    @property
    def interviewee_sim(self) -> list[str] | None:
        return self.interviewee_tesim or None

    interviewer_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Name.interviewer", "Interviewer"),
    )

    @computed_field
    @property
    def interviewer_sim(self) -> list[str] | None:
        return self.interviewer_tesim or None

    latitude_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Description.latitude"),
    )

    license_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("License"),
    )

    local_identifier_ssim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices(
            "Alt ID.local",
            "Alternate Identifier.local",
            "AltIdentifier.callNo",
            "AltIdentifier.local",
        ),
    )

    local_rights_statement_ssm: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Rights.statementLocal"),
    )

    location_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Coverage.geographic"),
    )

    @computed_field
    @property
    def location_sim(self) -> list[str] | None:
        return self.location_tesim

    longitude_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Description.longitude"),
    )

    lyricist_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Name.lyricist"),
    )

    @computed_field
    @property
    def lyricist_sim(self) -> list[str] | None:
        return self.lyricist_tesim or None

    masthead_parameters_ssi: MARCString | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Masthead"),
    )

    @computed_field
    @property
    def medium_sim(self) -> list[str] | None:
        return self.medium_tesim or None

    medium_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Format.medium"),
    )

    member_of_collection_ids_ssim: MARCList[UrsusId] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Parent ARK"),
    )

    # must be populated by importer
    member_of_collections_ssim: list[str] | Empty = None

    # @model_validator(mode="after")
    def validate_member_of_collections(self) -> Self:
        """Should have the same number of collection ids and collection names"""

        ids, names = self.member_of_collection_ids_ssim, self.member_of_collections_ssim
        if len(ids or []) != len(names or []):
            raise ValueError(
                f"Mismatched lengths: member_of_collection_ids_ssim and member_of_collections_ssim"
            )
        return self

    musician_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Musician", "Name.musician"),
    )

    @computed_field
    @property
    def musician_sim(self) -> list[str] | None:
        return self.musician_tesim

    named_subject_tesim: MARCList[MARCSubject] | Empty = Field(
        default=None,
        validation_alias=AliasChoices(
            "Name.subject",
            "Personal or Corporate Name.subject",
            "Subject.corporateName",
            "Subject.personalName",
        ),
    )

    @computed_field
    @property
    def named_subject_sim(self) -> list[str] | None:
        return self.named_subject_tesim

    normalized_date_tesim: MARCList[str] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Date.normalized"),
    )

    @computed_field
    @property
    def normalized_date_sim(self) -> list[str] | None:
        return self.normalized_date_tesim or None

    note_admin_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices(
            "AdminNote",
            "Description.adminnote",
            "Note.admin",
        ),
    )

    note_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Note"),
    )

    oai_set_ssim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("oai_set"),
    )

    opac_url_ssi: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Opac url", "Description.opac"),
    )

    other_versions_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Other version(s)"),
    )

    page_layout_ssim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Page layout"),
    )

    photographer_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices(
            "Name.photographer",
            "Personal or Corporate Name.photographer",
        ),
    )

    @computed_field
    @property
    def photographer_sim(self) -> list[str] | None:
        return self.photographer_tesim or None

    place_of_origin_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Place of origin", "Publisher.placeOfOrigin"),
    )

    @computed_field
    @property
    def place_of_origin_sim(self) -> list[str] | None:
        return self.place_of_origin_tesim or None

    preservation_copy_ssi: MARCString | Empty = Field(
        default=None,
        validation_alias=AliasChoices("File Name"),
    )

    @field_validator("preservation_copy_ssi", mode="after")
    @classmethod
    def fix_file_path(cls, value: str | Empty) -> str | None:
        """makes sure the path in preservation_copy starts with "Masters/" """

        if isinstance(value, str) and not value.startswith("Masters/"):
            value = f"Masters/{value}"
        return value

    printer_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Printer", "Name.printer"),
    )

    @computed_field
    @property
    def printer_sim(self) -> list[str] | None:
        return self.printer_tesim or None

    printmaker_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Printmaker", "Name.printmaker"),
    )

    @computed_field
    @property
    def printmaker_sim(self) -> list[str] | None:
        return self.printmaker_tesim or None

    producer_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Producer", "Name.producer"),
    )

    @computed_field
    @property
    def producer_sim(self) -> list[str] | None:
        return self.producer_tesim or None

    program_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Program"),
    )

    @computed_field
    @property
    def program_sim(self) -> list[str] | None:
        return self.program_tesim or None

    provenance_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Provenance", "Description.history"),
    )

    publisher_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Publisher.publisherName"),
    )

    @computed_field
    @property
    def publisher_sim(self) -> list[str] | None:
        return self.publisher_tesim or None

    recipient_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Recipient", "Name.recipient"),
    )

    @computed_field
    @property
    def recipient_sim(self) -> list[str] | None:
        return self.recipient_tesim or None

    related_record_ssm: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Related Records"),
    )

    # this one is NOT a controlled field based on an Enum, it has to be populated by the importer looking up titles form arks
    human_readable_related_record_title_ssm: list[str] | Empty = None

    @model_validator(mode="after")
    def validate_related_record_titles(self) -> Self:
        match self.related_record_ssm, self.human_readable_related_record_title_ssm:
            case None, None:
                pass
            case list(ids), list(titles) if len(ids) == len(titles):
                pass
            case (
                (list(ids), list(titles))
                | (list(ids), None as titles)
                | (None as ids, list(titles))
            ):
                raise ValueError(
                    "\n".join(
                        [
                            "related_record_ssm and human_readable_related_record_title_ssm must be of equal length",
                            f"related_record_title_ssm == {ids}",
                            f"human_readable_related_record_title_ssm == {titles}",
                            "",
                        ]
                    )
                )
            case _ as ids, _ as titles:
                assert_never(ids or titles)

        return self

    related_to_ssm: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Related Items"),
    )

    @computed_field
    @property
    def repository_sim(self) -> list[str] | None:
        return self.repository_tesim or None

    repository_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices(
            "repository",
            "Repository",
            "Name.repository",
            "Personal or Corporate Name.repository",
        ),
    )

    representative_image_ssi: MARCString | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Representative image"),
    )

    researcher_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Researcher", "Name.researcher"),
    )

    @computed_field
    @property
    def researcher_sim(self) -> list[str] | None:
        return self.researcher_tesim or None

    resp_statement_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Statement of Responsibility"),
    )

    rights_country_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Rights.countryCreation"),
    )

    rights_holder_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices(
            "Personal or Corporate Name.copyrightHolder",
            "Rights.rightsHolderName",
        ),
    )

    @computed_field
    @property
    def rubricator_sim(self) -> list[str] | None:
        return self.rubricator_tesim or None

    rubricator_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Rubricator", "Name.rubricator"),
    )

    @computed_field
    @property
    def scribe_sim(self) -> list[str] | None:
        return self.scribe_tesim or None

    scribe_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Scribe"),
    )

    script_note_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Script note", "Script Note"),
    )

    @computed_field
    @property
    def script_sim(self) -> list[str] | None:
        return self.script_tesim or None

    script_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Script"),
    )

    @computed_field
    @property
    def series_sim(self) -> list[str] | None:
        return self.series_tesim or None

    series_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Series"),
    )

    services_contact_ssm: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices(
            "Rights.servicesContact",
            "Rights.rightsHolderContact",
        ),
    )

    shelfmark_ssi: MARCString | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Shelfmark"),
    )

    # shelfmark_aplha_numeric_ssort - don't create, we're using a solr copy field

    @computed_field
    @property
    def sort_title_ssort(self) -> str | None:
        match self.title_tesim:
            case [str(first), *_]:
                return first
            case _:
                return None

    @computed_field
    @property
    def subject_cultural_object_sim(self) -> list[str] | None:
        return self.subject_cultural_object_tesim or None

    subject_cultural_object_tesim: MARCList[MARCSubject] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Subject.culturalObject"),
    )

    @computed_field
    @property
    def subject_domain_topic_sim(self) -> list[str] | None:
        return self.subject_domain_topic_tesim or None

    subject_domain_topic_tesim: MARCList[MARCSubject] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Subject.domainTopic"),
    )

    @computed_field
    @property
    def subject_geographic_sim(self) -> list[str] | None:
        return self.subject_geographic_tesim or None

    subject_geographic_tesim: MARCList[MARCSubject] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Subject geographic", "Subject place"),
    )

    subject_tesim: MARCList[MARCSubject] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Subject"),
    )

    @computed_field
    @property
    def subject_sim(self) -> list[str] | None:
        return self.subject_tesim or None

    @computed_field
    @property
    def subject_temporal_sim(self) -> list[str] | None:
        return self.subject_temporal_tesim or None

    subject_temporal_tesim: MARCList[MARCSubject] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Subject temporal"),
    )

    @computed_field
    @property
    def subject_topic_sim(self) -> list[str] | None:
        return self.subject_topic_tesim or None

    subject_topic_tesim: MARCList[MARCSubject] | Empty = Field(
        default=None,
        validation_alias=AliasChoices(
            "Subject topic",
            "Subject.conceptTopic",
            "Subject.descriptiveTopic",
        ),
    )

    summary_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Summary", "Description.abstract"),
    )

    @computed_field
    @property
    def support_sim(self) -> list[str] | None:
        return self.support_tesim or None

    support_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Support"),
    )

    tagline_ssi: MARCString | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Tagline"),
    )

    thumbnail_url_ss: str | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Thumbnail URL", "Thumbnail"),
    )

    @field_validator("thumbnail_url_ss", mode="after")
    @classmethod
    def ensure_thumbnail_iiif_suffix(cls, thumb: Any) -> str:
        if isinstance(thumb, str) and re.match(
            r"^/iiif/2/[^/]+$", urlparse(thumb).path
        ):
            return thumb + "/full/!200,200/0/default.jpg"

        return thumb

    @computed_field
    @property
    def title_sim(self) -> list[str]:
        return self.title_tesim

    toc_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices(
            "Table of Contents",
            "Description.tableOfContents",
        ),
    )

    @computed_field
    @property
    def translator_sim(self) -> list[str] | None:
        return self.translator_tesim or None

    translator_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Translator"),
    )

    @computed_field
    @property
    def uniform_title_sim(self) -> list[str] | None:
        return self.uniform_title_tesim or None

    uniform_title_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("AltTitle.uniform"),
    )

    visibility_ssi: Visibility = Field(
        default=Visibility.OPEN,
        validation_alias=AliasChoices("Visibility"),
    )

    @model_validator(mode="before")
    @classmethod
    def map_visibility(cls, data: Self | dict[str, Any]) -> Any:
        """Handle mapping of deprecated values plus special cases where "Visibility" is not provided. Note that there is different logic depending on whether the "Visibility" column was omitted entirely from the csv, or included but Empty for a row."""

        if not isinstance(data, dict):
            return data

        if not ("Visibility" in data or "Item Status" in data):
            return data

        # we want to consume "Item Status", it's only used here and not stored
        match data.get("Visibility"), data.pop("Item Status", None):
            # Include a bunch of deprecated values that need to be mapped
            case (
                "authenticated"
                | "private"
                | "registered"
                | "restricted"
                | "discovery"
                | "sinai",
                _,
            ):
                data["Visibility"] = "authenticated"

            case "open" | "public", _:
                data["Visibility"] = "open"

            # "Visibility" column was in csv but Empty for row
            case "", _:
                data["Visibility"] = "open"

            # "Visibility" was not in the csv, use "Item Status"
            case (
                None,
                "Completed" | "Completed with minimal metadata",
            ):
                data["Visibility"] = "open"

            # "Visibility" was not in the csv, "Item Status" column exists but isn't "Completed"
            case None, str():
                data["Visibility"] = "authenticated"

            # "Visibility" and "Item Status" both absent)
            case None, None:
                data["Visibility"] = "open"

            # Probably bad data, pass it on to builtin pydantic validation
            case _ as value, _:
                data["Visibility"] = value

        return data

    @computed_field
    @property
    def writing_system_sim(self) -> list[str] | None:
        return self.writing_system_tesim or None

    writing_system_tesim: MARCList[MARCString] | Empty = Field(
        default=None,
        validation_alias=AliasChoices("Writing system"),
    )

    @computed_field
    @property
    def year_isim(self) -> list[int] | None:
        return year_parser.integer_years(self.normalized_date_tesim) or None

    # groups for blacklight_access_control permissions

    @computed_field
    @property
    def discover_access_group_ssim(self) -> list[Literal["public"]]:
        match self.visibility_ssi:
            case Visibility.UCLA | Visibility.OPEN:
                return ["public"]
            case _:
                return []

    @computed_field
    @property
    def read_access_group_ssim(self) -> list[Literal["public"]]:
        return self.discover_access_group_ssim

    @computed_field
    @property
    def download_access_person_ssim(self) -> list[Literal["public"]]:
        return self.discover_access_group_ssim

    #
    #   General Validators
    #

    @model_validator(mode="wrap")
    @classmethod
    def validate_computed_fields(
        cls,
        data: Self | dict[str, Any],
        handler: ModelWrapValidatorHandler[Self],
    ) -> Self:
        if isinstance(data, dict):
            # remove computed fields from the dict, save them to check
            input_data = {
                field_name: data.pop(field_name)
                for field_name in cls.model_computed_fields.keys()
                if field_name in data
            }

            # validate / ingest / map as normal
            validated = handler(data)
            modeldump = validated.model_dump(mode="json")

            # check that computed fields match the saved inputs
            errors: list[str] = []
            for field_name, value in input_data.items():
                validated_value = modeldump.get(field_name)
                if value != validated_value:
                    errors.append(f"{field_name} ({value} != {validated_value})")

            if errors:
                raise ValueError(
                    "\n".join(
                        [
                            "Inputs do not match computed:",
                            *errors,
                            "",  # for a final newline
                        ]
                    )
                )

            return validated

        else:
            return handler(data)

    @classmethod
    def less_strict(cls) -> Type[BaseModel]:
        new_fields = {}

        for f_name, f_info in cls.model_fields.items():
            f_dct = f_info.asdict()
            new_fields[f_name] = (
                Annotated[
                    (
                        f_dct["annotation"] | Any,
                        *f_dct["metadata"],
                        Field(**f_dct["attributes"]),
                    )
                ],
                None,
            )

        # Create intermediate base class that overrides some validation functions
        class _LessStrictBase(cls):
            _strict = False

            @model_validator(mode="after")
            def longitudes_match_latitudes(self) -> Self:
                return self

            @model_validator(mode="after")
            def validate_related_record_titles(self) -> Self:
                return self

            @model_validator(mode="wrap")
            @classmethod
            def validate_computed_fields(
                cls,
                data: Self | dict[str, Any],
                handler: ModelWrapValidatorHandler[Self],
            ) -> Self:
                return handler(data)

        return create_model(
            f"{cls.__name__}LessStrict",
            __base__=_LessStrictBase,
            **new_fields,
        )
