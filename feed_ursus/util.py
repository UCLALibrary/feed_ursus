import re
from collections import abc
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal, TypeVar, assert_never, overload

from pydantic import (
    BeforeValidator,
    StringConstraints,
    TypeAdapter,
    ValidationError,
    ValidatorFunctionWrapHandler,
    WrapValidator,
)


class UnknownItemError(ValueError):
    pass


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


# used in parse_marc
MARC_SYMBOL = re.compile(r" \$[a-z] ")
MARC_SYMBOL_INITIAL_OR_FINAL = re.compile(r"(^\$[a-z] )|( \$[a-z]$)")


def parse_marc(
    raw_string: str,
    marc_symbol_replacement: str = " ",
) -> str | None:
    """
    Remove sequences of the form `$z`, which UCLA library uses to denote MARC subfields.

    Args:
        raw_string (str): The input string containing MARC subfield symbols.
        marc_symbol_replacement (str, optional): The character to replace MARC symbols with.
            Defaults to a space " ".
    Returns:
        str | None: The parsed string with MARC symbols removed/replaced, or None if the
            input is None.
    Example:
        >>> parse_marc("Title $a Subtitle $z Internal")
        'Title Subtitle Internal'
        >>> parse_marc("$a Title $b Author", marc_symbol_replacement=" | ")
        'Title | Author'
    """

    parsed = MARC_SYMBOL.sub(marc_symbol_replacement, raw_string)
    parsed = MARC_SYMBOL_INITIAL_OR_FINAL.sub("", parsed)
    parsed.strip()

    return parsed


def parse_marc_subject(parse_marc):
    return lambda value: parse_marc(value, marc_symbol_replacement=" | ")


# Via pydantic magic, add the parse_marc function, a minimimum length, and whitspace-stripping to the str type
MARCString = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
    BeforeValidator(parse_marc),
]

# Same as MARCString, but use ' | ' as the delimeter for MARC subfields
MARCSubject = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
    BeforeValidator(parse_marc_subject(parse_marc)),
]

T = TypeVar("T", bound=str | int | Enum | datetime)


@overload
def parse_list(value: str) -> list[str]: ...
@overload
def parse_list(value: list[T]) -> list[T]: ...
@overload
def parse_list(value: None) -> None: ...


def parse_list(value: str | list[T] | None) -> None | list[T] | list[str]:
    """
    Split strings along the delimiter `|~|`, as used by the dlexport app (https://github.com/UCLALibrary/dlexport) to export multivalued fields.

    Args:
        value: A string, list, or None to be parsed. Strings are split by the `|~|` delimiter.

    Returns:
        A list of strings if the input is a non-empty string or list, or None if the input
        is None, an empty list, or an empty string.

    Raises:
        AssertionError: If value is an unexpected type (via assert_never).

    Examples:
        >>> parse_list("item1|~|item2|~|item3")
        ['item1', 'item2', 'item3']
        >>> parse_list(["item1", "item2"])
        ["item1", "item2"]
        >>> parse_list("")
        None
        >>> parse_list(None)
        None
        >>> parse_list([])
        None
    """

    match value:
        case None | [] | "":
            return None
        case list():
            return value
        case str():
            return value.split("|~|")
        case _:
            assert_never(value)


# List type that will validate a string using the |~| separator
MARCList = Annotated[
    list[T],
    BeforeValidator(parse_list),
]


# Used to valide Ark objects
# see test/test_util.py:TestArk for examples of valid and invalid Arks
ARK_REGEX = re.compile(r"^ark:/\d+(/([a-z]|[0-9])+)+$")


def ensure_ark_prefix(value: str | None) -> str | None:
    """Add the prefix 'ark:/' to an archival resource key, if it is not there already and doing so results in a valid ark.

    Args:
        value: string representing an Archival Resource Key.

    Returns:
        The item ARK.

    Examples:
        >>> ensure_ark_prefix("ark:/21198/z1234567")
        'ark:/21198/z1234567'
        >>> ensure_ark_prefix("21198/z1234567")
        'ark:/21198/z1234567'

    See also:
        https://arks.org/about/
        https://datatracker.ietf.org/doc/draft-kunze-ark/
    """
    if (
        isinstance(value, str)
        and ARK_REGEX.match("ark:/" + value)
        and not ARK_REGEX.match(value)
    ):
        return "ark:/" + value
    else:
        return value


Ark = Annotated[
    str,
    StringConstraints(pattern=ARK_REGEX),
    BeforeValidator(ensure_ark_prefix),
]

# See examples of valid/invalid IDs in tests/test_util.py:TestUrsusId
BaseUrsusId = Annotated[str, StringConstraints(pattern=r"^(([a-z]|[0-9])+-)\d+$")]
base_id_validator: TypeAdapter[BaseUrsusId] = TypeAdapter(BaseUrsusId)
ark_validator: TypeAdapter[Ark] = TypeAdapter(Ark)


def make_ursus_id(value: str) -> "UrsusId":
    """If value passes validation as an ursus id, returns it unchanged. If it does not, but it passes validation as an ark, transforms it into an ursus id.

    If transformation does not result in a valid ursus id, the value is returned unchanged. Pydantic will reject these values based on the regex pattern in BaseUrsusId.

    Ursus IDs are formed from arks by removing the 'ark:/' prefix, replacing '/' with '-', and reversing the resulting string. The reversal was so that the initial characters would be unique rather than the UCLA Name Assigning Authority Number – an important consideration for Fedora ids back when we used californica."""

    try:
        return base_id_validator.validate_python(value)
    except ValidationError:
        return (
            ark_validator.validate_python(value)
            .replace("ark:/", "")
            .replace("/", "-")[::-1]
        )


UrsusId = Annotated[BaseUrsusId, BeforeValidator(make_ursus_id)]


@overload
def serialize_term(item: Enum | str, by) -> str: ...


@overload
def serialize_term(item: abc.Collection[Enum | str], by) -> list[str]: ...


@overload
def serialize_term(item: None, by) -> None: ...


def serialize_term(
    item: Enum | str | abc.Collection[Enum | str] | None,
    by: Literal["id", "label"] = "id",
):
    """Serialize a controlled field.

    Controlled fields are defined as Python Enums, with the `name` parameter referring to a term id and the `value` parameter referring to the term label.

    Argument can be:
    - an Enum subtype, in which case the `name` or `value parameter will be returned, depending on the `by` argument.
    - a string, which we use in the UrsusSolrRecord.less_strict variant of the model to capture bad legacy values, which will be returned as is.
    - an iterable containing either of the two types above, in which case a list will be returned, with each item having been processed as above.
    - None, for empty fields, which will be returned unchanged.
    """

    match item, by:
        case Enum(), "id":
            return item.name
        case Enum(), "label":
            return item.value
        case str(), _:
            return item
        case abc.Collection(), _:
            return [serialize_term(member, by=by) for member in item]
        case None, _:
            return None
        case _, _:
            assert_never(item)


def ignore_failed_validator_wrapper(
    value: Any,
    handler: ValidatorFunctionWrapHandler,
) -> str:
    try:
        return handler(value)
    except ValidationError as err:
        return value


ignore_failed_validator = WrapValidator(ignore_failed_validator_wrapper)
