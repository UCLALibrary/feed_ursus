# pyright: standard

import pytest
from pydantic import ValidationError

from feed_ursus.less_strict_solr_record import LessStrictSolrRecord
from feed_ursus.ursus_solr_record import UrsusSolrRecord


def test_bad_term_value(minimal_solr_record):
    record = {
        **minimal_solr_record,
        "visibility_ssi": "sinai",
    }

    with pytest.raises(ValidationError):
        UrsusSolrRecord.model_validate(record)

    result = LessStrictSolrRecord.model_validate(record).model_dump(
        mode="json",
        exclude_none=True,
    )

    for field, value in record.items():
        assert result["visibility_ssi"] == "sinai"


def test_bad_term_in_list(minimal_solr_record):
    record = {
        **minimal_solr_record,
        "human_readable_rights_statement_tesim": ["published", "unknown"],
        "rights_statement_tesim": [
            "published",
            "http://vocabs.library.ucla.edu/rights/unknown",
        ],
    }

    with pytest.raises(ValidationError):
        UrsusSolrRecord.model_validate(record)

    result = LessStrictSolrRecord.model_validate(record).model_dump(
        mode="json",
        exclude_none=True,
    )

    assert result["human_readable_rights_statement_tesim"] == ["published", "unknown"]
    assert result["rights_statement_tesim"] == [
        "published",
        "http://vocabs.library.ucla.edu/rights/unknown",
    ]


def test_latitude_longitude_mismatch(minimal_solr_record):
    record = {
        **minimal_solr_record,
        "longitude_tesim": ["-118.847769"],
    }

    with pytest.raises(ValidationError):
        UrsusSolrRecord.model_validate(record)

    result = LessStrictSolrRecord.model_validate(record).model_dump(
        mode="json",
        exclude_none=True,
    )

    assert result["longitude_tesim"] == ["-118.847769"]
    assert "latitude_tesim" not in result
    assert "geographic_coordinates_ssim" not in result


def test_related_record_mismatch(minimal_solr_record):
    record = {
        **minimal_solr_record,
        "related_record_ssm": ["ARK:/21198/zz002jgs66"],
        "human_readable_related_record_title_ssm": None,
    }

    with pytest.raises(ValidationError):
        UrsusSolrRecord.model_validate(record)

    result = LessStrictSolrRecord.model_validate(record).model_dump(
        mode="json",
        exclude_none=True,
    )

    assert result["related_record_ssm"] == ["ARK:/21198/zz002jgs66"]
    assert "human_readable_related_record_title_ssm" not in result
