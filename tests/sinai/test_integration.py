# """Tests for feed_sinai.py"""

# # pylint: disable=no-self-use

# import importlib
# import os
# import pytest

# from click.testing import CliRunner

# from feed_sinai import feed_sinai


# SOLR_URL = os.getenv("SOLR_URL", "http://localhost:8983/solr/californica")

# @pytest.mark.xfail
# def test_feed_sinai():
#     """Integration test for feed_sinai."""
#     solr = None
#     solr.delete(id="xp6xn100zz-89112", commit=True)
#     solr.delete(id="82765200zz-89112", commit=True)

#     runner = CliRunner()
#     result = runner.invoke(
#         feed_sinai.sinai,
#         [
#             "--solr_url",
#             SOLR_URL,
#             "load",
#             "tests/csv/anais_collection.csv",
#             "tests/csv/anais_work_simple.csv",
#         ],
#     )
#     assert result.exit_code == 0

#     collection_record = solr.search("id:xp6xn100zz-89112", defType="lucene")
#     # Doesn't run against a fresh solr index, so there's no guarantee the result comes from this run of the feed_sinai command.
#     # But at least we can see that pysolr works and talks to solr in this environment.
#     assert collection_record.docs[0]["title_tesim"] == [
#         "Nin (Anais) Papers, circa 1910-1977"
#     ]

#     work_record = solr.search("id:82765200zz-89112", defType="lucene").docs[0]
#     assert work_record["title_tesim"] == ["Nin, Joaquin. 1914 [photograph]"]
#     assert work_record["member_of_collections_ssim"] == [
#         "Nin (Anais) Papers, circa 1910-1977"
#     ]
#     assert work_record["member_of_collection_ids_ssim"] == ["xp6xn100zz-89112"]
