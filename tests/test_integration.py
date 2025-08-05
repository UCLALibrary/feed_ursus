# mypy: disallow_untyped_defs=False
"""Tests for feed_ursus.py"""

# pylint: disable=no-self-use

import os

from click.testing import CliRunner
from pysolr import Solr  # type: ignore

from feed_ursus import feed_ursus

SOLR_URL = os.getenv("SOLR_URL", "http://localhost:8983/solr/californica")


def test_feed_ursus():
    """Integration test for feed_ursus."""
    solr = Solr(SOLR_URL)

    # these should have been deleted already, but let's be sure
    solr.delete(id="xp6xn100zz-89112", commit=True)
    solr.delete(id="82765200zz-89112", commit=True)

    runner = CliRunner()
    result = runner.invoke(
        feed_ursus.feed_ursus,
        [
            "--solr_url",
            SOLR_URL,
            "load",
            "tests/csv/anais_collection.csv",
            "tests/csv/anais_work_simple.csv",
        ],
    )
    assert result.exit_code == 0

    collection_record = solr.search("id:xp6xn100zz-89112", defType="lucene")
    # Doesn't run against a fresh solr index, so there's no guarantee the result comes from this run of the feed_ursus command.
    # But at least we can see that pysolr works and talks to solr in this environment.
    assert collection_record.docs[0]["title_tesim"] == [
        "Nin (Anais) Papers, circa 1910-1977"
    ]

    work_record = solr.search("id:82765200zz-89112", defType="lucene").docs[0]
    assert work_record["title_tesim"] == ["Nin, Joaquin. 1914 [photograph]"]
    assert work_record["member_of_collections_ssim"] == [
        "Nin (Anais) Papers, circa 1910-1977"
    ]
    assert work_record["member_of_collection_ids_ssim"] == ["xp6xn100zz-89112"]

    # Delete and confirm
    result = runner.invoke(
        feed_ursus.feed_ursus,
        [
            "--solr_url",
            SOLR_URL,
            "delete",
            "--yes",
            "tests/csv/anais_collection.csv",
            "tests/csv/anais_work_simple.csv",
        ],
    )
    assert result.exit_code == 0
    assert (
        len(solr.search("id:xp6xn100zz-89112", defType="lucene").docs) == 0
    )  # collection record
    assert (
        len(solr.search("id:82765200zz-89112", defType="lucene").docs) == 0
    )  # work record


def test_feed_ursus_async():
    """Integration test for feed_ursus."""
    solr = Solr(SOLR_URL)

    # these should have been deleted already, but let's be sure
    solr.delete(id="xp6xn100zz-89112", commit=True)
    solr.delete(id="82765200zz-89112", commit=True)

    runner = CliRunner()
    result = runner.invoke(
        feed_ursus.feed_ursus,
        [
            "--solr_url",
            SOLR_URL,
            "load",
            "--async",
            "tests/csv/anais_collection.csv",
            "tests/csv/anais_work_simple.csv",
        ],
    )
    assert result.exit_code == 0

    collection_record = solr.search("id:xp6xn100zz-89112", defType="lucene")
    # Doesn't run against a fresh solr index, so there's no guarantee the result comes from this run of the feed_ursus command.
    # But at least we can see that pysolr works and talks to solr in this environment.
    assert collection_record.docs[0]["title_tesim"] == [
        "Nin (Anais) Papers, circa 1910-1977"
    ]

    work_record = solr.search("id:82765200zz-89112", defType="lucene").docs[0]
    assert work_record["title_tesim"] == ["Nin, Joaquin. 1914 [photograph]"]
    assert work_record["member_of_collections_ssim"] == [
        "Nin (Anais) Papers, circa 1910-1977"
    ]
    assert work_record["member_of_collection_ids_ssim"] == ["xp6xn100zz-89112"]

    # Delete and confirm
    result = runner.invoke(
        feed_ursus.feed_ursus,
        [
            "--solr_url",
            SOLR_URL,
            "delete",
            "--yes",
            "tests/csv/anais_collection.csv",
            "tests/csv/anais_work_simple.csv",
        ],
    )
    assert result.exit_code == 0
    assert (
        len(solr.search("id:xp6xn100zz-89112", defType="lucene").docs) == 0
    )  # collection record
    assert (
        len(solr.search("id:82765200zz-89112", defType="lucene").docs) == 0
    )  # work record
