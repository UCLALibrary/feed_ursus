"""Tests for feed_ursus.py"""
# pylint: disable=no-self-use

import importlib
import os
import time

from click.testing import CliRunner
from pysolr import Solr  # type: ignore

from feed_ursus import feed_ursus

feed_ursus.mapper = importlib.import_module("feed_ursus.mapper.sinai")


SOLR_URL = os.getenv("SOLR_URL", "http://localhost:8983/solr/californica")

def test_feed_ursus():
    """Integration test for feed_ursus."""
    solr = Solr(SOLR_URL)
    solr.delete(id='xp6xn100zz-89112', commit=True)

    runner = CliRunner()
    result = runner.invoke(
        feed_ursus.load_csv, 
        ['--solr_url', SOLR_URL, "tests/csv/anais_collection.csv"]
    )
    assert result.exit_code == 0

    doc_in_solr = solr.search('id:xp6xn100zz-89112', defType="lucene")
    # Doesn't run against a fresh solr index, so there's no guarantee the result comes from this run of the feed_ursus command.
    # But at least we can see that pysolr works and talks to solr in this environment.
    assert doc_in_solr.docs[0]["title_tesim"] == ['Nin (Anais) Papers, circa 1910-1977']
