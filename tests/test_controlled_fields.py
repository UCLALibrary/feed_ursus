import pytest
from pydantic import BaseModel

import feed_ursus.controlled_fields as cf


@pytest.mark.parametrize(
    ("name", "value"),
    [
        (
            "http://creativecommons.org/licenses/by-nd/3.0/us/",
            "Attribution-NoDerivs 3.0 United States",
        ),
        (
            "https://creativecommons.org/licenses/by-nd/4.0/",
            "Creative Commons BY-ND Attribution-NoDerivatives 4.0 International",
        ),
        (
            "http://creativecommons.org/publicdomain/mark/1.0/",
            "Creative Commons Public Domain Mark 1.0",
        ),
    ],
)
def test_license(name: str, value: str):
    by_name = cf.License[name]
    by_value = cf.License(value)
    assert by_name is by_value
    assert by_name.value == value


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("http://iiif.io/api/presentation/2#leftToRightDirection", "left-to-right"),
        ("http://iiif.io/api/presentation/2#rightToLeftDirection", "right-to-left"),
        ("http://iiif.io/api/presentation/2#topToBottomDirection", "top-to-bottom"),
        ("http://iiif.io/api/presentation/2#bottomToTopDirection", "bottom-to-top"),
    ],
)
def test_text_direction(name: str, value: str):
    by_name = cf.TextDirection[name]
    by_value = cf.TextDirection(value)
    assert by_name is by_value
    assert by_name.value == value


def test_resource_type() -> None:
    """IDs are big URLs that are not valid python keywords, it should work anyway."""
    assert ("http://id.loc.gov/vocabulary/resourceTypes/not", "notated music") in [
        (x.name, x.value) for x in cf.ResourceType
    ]


def test_resource_type_in_pydantic_model() -> None:
    """ResourceType enum should work in Pydantic models."""

    class Record(BaseModel):
        resource_type: cf.ResourceType

    record = Record.model_validate({"resource_type": "notated music"})
    expected = cf.ResourceType["http://id.loc.gov/vocabulary/resourceTypes/not"]
    assert record.resource_type == expected
