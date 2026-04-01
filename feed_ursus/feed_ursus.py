#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mypy: disallow_untyped_defs=False
"""Convert UCLA Library CSV files for Ursus, our Blacklight installation."""

import importlib.metadata
import typing

import click

from feed_ursus.importer import Importer


@click.group()
@click.option(
    "--solr_url",
    default="http://localhost:8983/solr/ursus",
    help="URL of a solr instance, e.g. http://localhost:8983/solr/ursus",
)
@click.option(
    "--show-progress/--no-show-progress",
    default=True,
    help="Show progress bars.",
)
@click.version_option(version=importlib.metadata.version("feed_ursus"))
@click.pass_context
def feed_ursus(ctx: click.Context, solr_url: str, show_progress: bool):
    """CLI for managing a Solr index for Ursus."""

    ctx.ensure_object(dict)
    ctx.obj["importer"] = Importer(solr_url=solr_url, show_progress=show_progress)


@feed_ursus.command("load")
@click.argument("filenames", nargs=-1, type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--batch/--not-batch",
    default=True,
    help="Enable or disable batch mode.",
)
@click.pass_context
def load_csv(ctx: click.Context, filenames: typing.List[str], batch: bool):
    """Load data from a csv.

    Args:
        filenames: A list of CSV filenames.
    """

    ctx.obj["importer"].load_csv(filenames=filenames, batch=batch)


@feed_ursus.command()
@click.argument("items", nargs=-1, type=str)
@click.option(
    "--yes/--no", is_flag=True, default=False, help="Skip confirmation prompts."
)
@click.pass_context
def delete(ctx: click.Context, items: typing.List[str], yes: bool):
    """Delete records from a Solr index.

    Args:
        solr_url: URL of a solr instance.
        items: List of items to delete. Can be ARKs, Solr IDs, or csv filenames.
               If a csv filename is provided, all ARKs in the file will be deleted.
    """
    ctx.obj["importer"].delete(items=items, yes=yes)


@feed_ursus.command()
@click.pass_context
def log(ctx: click.Context):
    """Show a log of csv ingests."""

    ctx.obj["importer"].print_log()


@feed_ursus.command()
@click.pass_context
def dump(ctx: click.Context):
    """Write entire index to stdout.

    Output will be written in jsonl format: json-formatted records separated by newlines. To write to disk, use the `>` redirect operator. The resulting file can then be loaded into a different solr index via the solr post tool (https://solr.apache.org/guide/8_11/post-tool.html), the solr GUI console, or the solr rest API. Solr generally requires the `.jsonl` suffix; if you use `.json` solr will expect a single json object and fail to parse the newline-separated records.

    Example:
        >>> feed_ursus dump > dump.jsonl  # writes output to `dump.jsonl`
    """
    ctx.obj["importer"].dump()


if __name__ == "__main__":
    print("feed_ursus() executing, running from main()")
    feed_ursus()  # pylint: disable=no-value-for-parameter
