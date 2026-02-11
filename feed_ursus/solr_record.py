from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, computed_field

# NOTE: some aren't parsing, just keep as string for now
SolrDatetime = str  # Annotated[
#     datetime,
#     BeforeValidator(
#         lambda datestr: datetime.fromisoformat(datestr.replace("Z", "+00:00"))
#     ),
# ]


class UrsusSolrRecord(BaseModel):
    access_copy_ssi: str = ""
    alternative_title_tesim: list[str] = []

    @computed_field
    def architect_sim(self) -> list[str] | None:
        return self.architect_tesim or None

    architect_tesim: list[str] = []
    archival_collection_box_ssi: str = ""
    archival_collection_folder_ssi: str = ""
    archival_collection_number_ssi: str = ""
    archival_collection_tesi: str = ""
    archival_collection_title_ssi: str = ""
    ark_ssi: str = ""

    @computed_field
    def artist_sim(self) -> list[str] | None:
        return self.artist_tesim or None

    artist_tesim: list[str] = []

    @computed_field
    def associated_name_sim(self) -> list[str] | None:
        return self.associated_name_tesim or None

    associated_name_tesim: list[str] = []

    @computed_field
    def author_sim(self) -> list[str] | None:
        return self.author_tesim or None

    author_tesim: list[str] = []
    binding_condition_tesim: list[str] = []
    binding_note_ssi: str = ""
    binding_note_tesim: list[str] = []

    @computed_field
    def calligrapher_sim(self) -> list[str] | None:
        return self.calligrapher_tesim or None

    calligrapher_tesim: list[str] = []
    caption_tesim: list[str] = []

    @computed_field
    def cartographer_sim(self) -> list[str] | None:
        return self.cartographer_tesim or None

    cartographer_tesim: list[str] = []
    citation_source_tesim: list[str] = []
    collation_tesim: list[str] = []

    @computed_field
    def collection_sim(self) -> list[str] | None:
        return [self.collection_ssi] if self.collection_ssi else None

    collection_ssi: str = ""
    colophon_tesim: list[str] = []
    combined_subject_ssim: list[str] = []

    @computed_field
    def commentator_sim(self) -> list[str] | None:
        return self.commentator_tesim or None

    commentator_tesim: list[str] = []

    @computed_field
    def composer_sim(self) -> list[str] | None:
        return self.composer_tesim or None

    composer_tesim: list[str] = []
    condition_note_ssi: str = ""
    condition_note_tesim: list[str] = []
    content_disclaimer_ssm: list[str] = []
    contents_note_tesim: list[str] = []
    contents_tesim: list[str] = []
    contributor_tesim: list[str] = []

    @computed_field
    def creator_sim(self) -> list[str] | None:
        return self.creator_tesim or None

    creator_tesim: list[str] = []
    date_created_tesim: list[str] = []
    date_dtsim: list[SolrDatetime] = []
    date_dtsort: SolrDatetime | None = None
    delivery_tesim: list[str] = []
    description_tesim: list[str] = []
    descriptive_title_tesim: list[str] = []

    @computed_field
    def dimensions_sim(self) -> list[str] | None:
        return self.dimensions_tesim or None

    dimensions_tesim: list[str] = []

    @computed_field
    def director_sim(self) -> list[str] | None:
        return self.director_tesim or None

    director_tesim: list[str] = []
    discover_access_group_ssim: list[str] = []
    download_access_person_ssim: list[str] = []
    edition_ssm: list[str] = []

    @computed_field
    def editor_sim(self) -> list[str] | None:
        return self.editor_tesim or None

    editor_tesim: list[str] = []
    electronic_locator_ss: str = ""

    @computed_field
    def engraver_sim(self) -> list[str] | None:
        return self.engraver_tesim or None

    engraver_tesim: list[str] = []
    explicit_tesim: list[str] = []

    @computed_field
    def extent_sim(self) -> list[str] | None:
        return self.extent_tesim or None

    extent_tesim: list[str] = []
    featured_image_ssi: str = ""

    @computed_field
    def features_sim(self) -> list[str] | None:
        return self.features_tesim or None

    features_tesim: list[str] = []
    finding_aid_url_ssm: list[str] = []
    foliation_tesim: list[str] = []
    folio_dimensions_ss: str = ""

    @computed_field
    def form_sim(self) -> list[str] | None:
        return self.form_tesim or None

    form_tesim: list[str] = []
    format_book_tesim: list[str] = []
    format_extent_tesim: list[str] = []
    funding_note_tesim: list[str] = []

    @computed_field
    def genre_sim(self) -> list[str] | None:
        return self.genre_tesim or None

    genre_tesim: list[str] = []
    geographic_coordinates_ssim: list[str] = []
    hand_note_tesim: list[str] = []
    has_model_ssim: list[str] = []
    header_index_tesim: list[str] = []
    history_tesim: list[str] = []

    @computed_field
    def host_sim(self) -> list[str] | None:
        return self.host_tesim or None

    host_tesim: list[str] = []
    human_readable_iiif_text_direction_ssi: str = ""
    human_readable_iiif_viewing_hint_ssi: str = ""

    @computed_field
    def human_readable_language_sim(self) -> list[str] | None:
        return self.human_readable_language_tesim or None

    human_readable_language_tesim: list[str] = []
    human_readable_related_record_title_ssm: list[str] = []

    @computed_field
    def human_readable_resource_type_sim(self) -> list[str] | None:
        return self.human_readable_resource_type_tesim or None

    human_readable_resource_type_tesim: list[str] = []
    human_readable_rights_statement_tesim: list[str] = []
    id: str
    identifier_tesim: list[str] = []
    iiif_manifest_url_ssi: str = ""
    iiif_range_ssi: str = ""
    iiif_text_direction_ssi: str = ""
    iiif_viewing_hint_ssi: str = ""

    @computed_field
    def illuminator_sim(self) -> list[str] | None:
        return self.illuminator_tesim or None

    illuminator_tesim: list[str] = []
    illustrations_note_tesim: list[str] = []

    @computed_field
    def illustrator_sim(self) -> list[str] | None:
        return self.illustrator_tesim or None

    illustrator_tesim: list[str] = []
    image_count_ssi: str = ""
    incipit_tesim: list[str] = []
    ingest_id_ssi: str = ""
    ink_color_tesim: list[str] = []
    inscription_tesim: list[str] = []

    @computed_field
    def interviewee_sim(self) -> list[str] | None:
        return self.interviewee_tesim or None

    interviewee_tesim: list[str] = []

    @computed_field
    def interviewer_sim(self) -> list[str] | None:
        return self.interviewer_tesim or None

    interviewer_tesim: list[str] = []

    @computed_field
    def keywords_sim(self) -> list[str] | None:
        return self.keywords_tesim or None

    keywords_tesim: list[str] = []

    @computed_field
    def language_sim(self) -> list[str] | None:
        return self.language_tesim or None

    language_tesim: list[str] = []
    latitude_tesim: list[str] = []
    license_tesim: list[str] = []

    @computed_field
    def local_identifier_sim(self) -> list[str] | None:
        return self.local_identifier_ssim or None

    local_identifier_ssim: list[str] = []
    local_identifier_ssm: list[str] = []
    local_rights_statement_ssim: list[str] = []
    local_rights_statement_ssm: list[str] = []

    @computed_field
    def location_sim(self) -> list[str] | None:
        return self.location_tesim or None

    location_tesim: list[str] = []
    longitude_tesim: list[str] = []

    @computed_field
    def lyricist_sim(self) -> list[str] | None:
        return self.lyricist_tesim or None

    lyricist_tesim: list[str] = []
    masthead_parameters_ssi: str = ""

    @computed_field
    def medium_sim(self) -> list[str] | None:
        return self.medium_tesim or None

    medium_tesim: list[str] = []
    member_of_collection_ids_ssim: list[str] = []
    member_of_collections_ssim: list[str] = []

    @computed_field
    def musician_sim(self) -> list[str] | None:
        return self.musician_tesim or None

    musician_tesim: list[str] = []
    name_fields_index_tesim: list[str] = []

    @computed_field
    def named_subject_sim(self) -> list[str] | None:
        return self.named_subject_tesim or None

    named_subject_tesim: list[str] = []

    @computed_field
    def names_sim(self) -> list[str] | None:
        """combine fields for the names facet. or None

        In most cases combined fields end up in a store _tesim field, but not for names_sim"""

        combined = (
            self.author_tesim
            + self.scribe_tesim
            + self.associated_name_tesim
            + self.translator_tesim
        )
        return combined if combined else None

    @computed_field
    def normalized_date_sim(self) -> list[str] | None:
        return self.normalized_date_tesim or None

    normalized_date_tesim: list[str] = []
    note_admin_tesim: list[str] = []
    note_tesim: list[str] = []
    oai_set_ssim: list[str] = []
    opac_url_ssi: str = ""
    other_versions_tesim: list[str] = []
    overtext_manuscript_ssm: list[str] = []
    page_layout_ssim: list[str] = []

    @computed_field
    def photographer_sim(self) -> list[str] | None:
        return self.photographer_tesim or None

    photographer_tesim: list[str] = []

    @computed_field
    def place_of_origin_sim(self) -> list[str] | None:
        return self.place_of_origin_tesim or None

    place_of_origin_tesim: list[str] = []
    preservation_copy_ssi: str = ""

    @computed_field
    def printer_sim(self) -> list[str] | None:
        return self.printer_tesim or None

    printer_tesim: list[str] = []

    @computed_field
    def printmaker_sim(self) -> list[str] | None:
        return self.printmaker_tesim or None

    printmaker_tesim: list[str] = []

    @computed_field
    def producer_sim(self) -> list[str] | None:
        return self.producer_tesim or None

    producer_tesim: list[str] = []

    @computed_field
    def program_sim(self) -> list[str] | None:
        return self.program_tesim or None

    program_tesim: list[str] = []
    provenance_tesim: list[str] = []

    @computed_field
    def publisher_sim(self) -> list[str] | None:
        return self.publisher_tesim or None

    publisher_tesim: list[str] = []
    read_access_group_ssim: list[str] = []

    @computed_field
    def recipient_sim(self) -> list[str] | None:
        return self.recipient_tesim or None

    recipient_tesim: list[str] = []
    record_origin_ssi: str = ""
    references_tesim: list[str] = []
    related_record_ssm: list[str] = []
    related_tesim: list[str] = []
    related_to_ssm: list[str] = []

    @computed_field
    def repository_sim(self) -> list[str] | None:
        return self.repository_tesim or None

    repository_tesim: list[str] = []
    representative_image_ssi: str = ""

    @computed_field
    def researcher_sim(self) -> list[str] | None:
        return self.researcher_tesim or None

    researcher_tesim: list[str] = []

    @computed_field
    def resource_type_sim(self) -> list[str] | None:
        return self.resource_type_tesim or None

    resource_type_tesim: list[str] = []
    resp_statement_tesim: list[str] = []
    rights_country_tesim: list[str] = []
    rights_holder_tesim: list[str] = []
    rights_statement_tesim: list[str] = []

    @computed_field
    def rubricator_sim(self) -> list[str] | None:
        return self.rubricator_tesim or None

    rubricator_tesim: list[str] = []

    @computed_field
    def scribe_sim(self) -> list[str] | None:
        return self.scribe_tesim or None

    scribe_tesim: list[str] = []
    script_note_tesim: list[str] = []

    @computed_field
    def script_sim(self) -> list[str] | None:
        return self.script_tesim or None

    script_tesim: list[str] = []
    sequence_isi: int | None = None

    @computed_field
    def series_sim(self) -> list[str] | None:
        return self.series_tesim or None

    series_tesim: list[str] = []
    services_contact_ssm: list[str] = []
    shelfmark_ssi: str = ""
    sort_year_isi: int | None = None

    @computed_field
    def subject_cultural_object_sim(self) -> list[str] | None:
        return self.subject_cultural_object_tesim or None

    subject_cultural_object_tesim: list[str] = []

    @computed_field
    def subject_domain_topic_sim(self) -> list[str] | None:
        return self.subject_domain_topic_tesim or None

    subject_domain_topic_tesim: list[str] = []

    @computed_field
    def subject_geographic_sim(self) -> list[str] | None:
        return self.subject_geographic_tesim or None

    subject_geographic_tesim: list[str] = []

    @computed_field
    def subject_sim(self) -> list[str] | None:
        return self.subject_tesim or None

    @computed_field
    def subject_temporal_sim(self) -> list[str] | None:
        return self.subject_temporal_tesim or None

    subject_temporal_tesim: list[str] = []
    subject_tesim: list[str] = []

    @computed_field
    def subject_topic_sim(self) -> list[str] | None:
        return self.subject_topic_tesim or None

    subject_topic_tesim: list[str] = []
    summary_tesim: list[str] = []

    @computed_field
    def support_sim(self) -> list[str] | None:
        return self.support_tesim or None

    support_tesim: list[str] = []
    tagline_ssi: str = ""
    thumbnail_url_ss: str = ""

    @computed_field
    def title_sim(self) -> list[str] | None:
        return self.title_tesim or None

    title_tesim: list[str] = []
    toc_tesim: list[str] = []

    @computed_field
    def translator_sim(self) -> list[str] | None:
        return self.translator_tesim or None

    translator_tesim: list[str] = []
    undertext_objects_ssim: list[str] = []

    @computed_field
    def uniform_title_sim(self) -> list[str] | None:
        return self.uniform_title_tesim or None

    uniform_title_tesim: list[str] = []
    viscodex_ssi: str = ""
    visibility_ssi: str = ""

    @computed_field
    def writing_system_sim(self) -> list[str] | None:
        return self.writing_system_tesim or None

    writing_system_tesim: list[str] = []
    year_isim: list[int] = []
