import re
from datetime import datetime
from enum import Enum, EnumType
from pathlib import Path
from typing import Annotated, Any, TypeVar, assert_never, overload

from pydantic import (
    BeforeValidator,
    StringConstraints,
    TypeAdapter,
    ValidationError,
)


def parse_empty(value: Any) -> Any | None:
    if isinstance(value, str):
        value = value.strip()

    return value or None


Empty = Annotated[
    None,
    BeforeValidator(parse_empty),
]


# NOTE: some aren't parsing, just keep as string for now
SolrDatetime = str  # Annotated[
#     datetime,
#     BeforeValidator(
#         lambda datestr: datetime.fromisoformat(datestr.replace("Z", "+00:00"))
#     ),
# ]


MARC_SYMBOL = re.compile(r" \$\w ")
MARC_SYMBOL_INITIAL_OR_FINAL = re.compile(r"(^\$\w )|( \$\w$)")


def parse_marc(
    raw_string: str,
    marc_symbol_replacement: str = " ",
) -> str | None:
    parsed = MARC_SYMBOL.sub(marc_symbol_replacement, raw_string)
    parsed = MARC_SYMBOL_INITIAL_OR_FINAL.sub("", parsed)
    parsed.strip()

    return parsed


def parse_marc_subject(raw_string: str) -> str | None:
    return parse_marc(raw_string, marc_symbol_replacement=" | ")


MARCString = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
    BeforeValidator(parse_marc),
]

MARCSubject = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
    BeforeValidator(lambda value: parse_marc(value, marc_symbol_replacement=" | ")),
]

T = TypeVar("T", bound=str | int | Enum | datetime)


@overload
def parse_list(value: str) -> list[str]: ...
@overload
def parse_list(value: list[T]) -> list[T]: ...
@overload
def parse_list(value: None) -> None: ...
def parse_list(value: str | list[T] | None):
    match value:
        case None | [] | "":
            return None
        case list():
            return value
        case str():
            return value.split("|~|")
        case _:
            assert_never(value)


MARCList = Annotated[
    list[T],
    BeforeValidator(parse_list),
]

ARK_REGEX = re.compile(r"^ark:/\d+(/([a-z]|[0-9])+)+$")


def ensure_ark_prefix(value: str) -> str:
    """The item ARK (Archival Resource Key)

    Args:
        row: An input CSV record.

    Returns:
        The item ARK.
    """
    if ARK_REGEX.match("ark:/" + value) and not ARK_REGEX.match(value):
        return "ark:/" + value
    else:
        return value


Ark = Annotated[
    str,
    StringConstraints(pattern=ARK_REGEX),
    BeforeValidator(ensure_ark_prefix),
]


BaseUrsusId = Annotated[str, StringConstraints(pattern=r"^(([a-z]|[0-9])+-)\d+$")]
id_validator: TypeAdapter[BaseUrsusId] = TypeAdapter(BaseUrsusId)
ark_validator: TypeAdapter[Ark] = TypeAdapter(Ark)


def make_ursus_id(value: str) -> "UrsusId":
    """If value passes validation as an ursus id, returns it unchanged. If it does not, but it passes validation as an ark, transforms it into an ursus id."""

    try:
        return id_validator.validate_python(value)
    except ValidationError:
        return (
            ark_validator.validate_python(value)
            .replace("ark:/", "")
            .replace("/", "-")[::-1]
        )


UrsusId = Annotated[BaseUrsusId, BeforeValidator(make_ursus_id)]
