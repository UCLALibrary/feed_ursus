# pyright: standard

from typing import Annotated, Any, Self

from pydantic import (
    ConfigDict,
    Field,
    ModelWrapValidatorHandler,
    create_model,
    model_validator,
)
from pydantic.fields import computed_field

from feed_ursus.ursus_solr_record import UrsusSolrRecord, field_validator
from feed_ursus.util import SolrDatetime


# Create intermediate base class that overrides some validation functions
class _LessStrictBase(UrsusSolrRecord):
    model_config = ConfigDict(
        extra="allow",
        serialize_by_alias=True,
        validate_by_name=True,
        validate_by_alias=True,
    )

    @computed_field
    @property
    def date_dtsim(self) -> list[SolrDatetime] | None:
        try:
            return super().date_dtsim
        except Exception:
            return None

    @model_validator(mode="after")
    def longitudes_match_latitudes(self) -> Self:
        return self

    @field_validator("thumbnail_url_ss", mode="after")
    @classmethod
    def ensure_thumbnail_iiif_suffix(cls, thumb: Any) -> str:
        return thumb

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

    @model_validator(mode="before")
    @classmethod
    def remove_solr_internal_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for field in ["hashed_id_ssi", "score"]:
                data.pop(field, None)

        return data


new_fields = {}

for f_name, f_info in UrsusSolrRecord.model_fields.items():
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


LessStrictSolrRecord = create_model(
    f"{UrsusSolrRecord.__name__}LessStrict",
    __base__=_LessStrictBase,
    **new_fields,
)
