#!/usr/bin/env python
# -*- coding: utf-8 -*-
# mypy: disallow_untyped_defs=False
"""Convert UCLA Library CSV files for Ursus, our Blacklight installation."""

import importlib.metadata
import typing
from math import inf

import click
import requests
from packaging.version import Version
from pydantic import BaseModel, ConfigDict

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
@click.option(
    "--check-outdated/--ignore-outdated",
    default=True,
    help="Check pypi for a newer version, and exit if one exists.",
)
@click.version_option(version=importlib.metadata.version("feed_ursus"))
@click.pass_context
def feed_ursus(
    ctx: click.Context,
    solr_url: str,
    show_progress: bool,
    check_outdated: bool,
):
    """CLI for managing a Solr index for Ursus."""

    if check_outdated and (new_version := is_outdated()):
        raise click.ClickException(
            f"feed_ursus is outdated: please upgrade to version {new_version}"
            "(e.g. `uv tool upgrade feed_ursus`)"
        )

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
@click.option(
    "--start",
    type=click.IntRange(0, None),
    default=0,
    help="Starting index (zero-based).",
)
@click.option(
    "--max-errors",
    type=click.IntRange(1, None),
    default=None,
    help="Stop after this many errors.",
)
def validate(ctx: click.Context, start: int = 0, max_errors: int | None = None):
    """Validate solr index.

    All records will be validated as Ursus records, and any errors printed to stdout.

    Example:
        >>> feed_ursus validate
    """
    ctx.obj["importer"].validate(start=start, max_errors=(max_errors or inf))


@feed_ursus.command()
@click.pass_context
@click.option(
    "--start",
    type=click.IntRange(0, None),
    default=0,
    help="Starting index (zero-based).",
)
@click.option(
    "--max-errors",
    type=click.IntRange(1, None),
    default=None,
    help="Stop after this many errors.",
)
@click.option(
    "--dry-run/--no-dry-run",
    is_flag=True,
    default=False,
    help="Check data processing but do not resubmit to solr.",
)
def reindex(
    ctx: click.Context,
    start: int = 0,
    max_errors: int | None = None,
    dry_run: bool = False,
):
    """Reindex solr index.

    All records will be loaded and parsed as Ursus records, and computed fields will be
    regenerated, before being fed back to solr. Records will be validated but validation
    rules will be somewhat looser than when importing from csv.

    Example:
        >>> feed_ursus reindex
    """
    ctx.obj["importer"].reindex(
        start=start,
        max_errors=(max_errors or inf),
        dry_run=dry_run,
    )


@feed_ursus.command()
@click.option(
    "--filename-prefix",
    type=click.STRING,
    default="data",
    help="Prefix for filenames.",
)
@click.option(
    "--batch-size",
    type=click.IntRange(1, None),
    default=1000,
    help="Number of records to save per file.",
)
@click.pass_context
def dump(ctx: click.Context, filename_prefix: str, batch_size: int):
    """Write entire index to disk.

    Example:
        >>> feed_ursus dump --filename-prefix data
        # writes output to `data01.jsonl`, `data02.jsonl`, etc.
    """
    ctx.obj["importer"].dump(filename_prefix=filename_prefix, batch_size=batch_size)


@feed_ursus.command()
@click.pass_context
@click.argument("filenames", nargs=-1, type=click.Path(exists=True, dir_okay=False))
def loaddump(ctx: click.Context, filenames: tuple[str, ...]):
    """
    Reload data saved with 'feed_ursus dump'.

    Example:
        >>> feed_ursus load_dump data*.jsonl
    """
    ctx.obj["importer"].load_dump(filenames)


class PyPIInfo(BaseModel):
    """Very limited model of a PyPI json response – intended only for retrieving version
    numbers, everything else is ignored."""

    model_config = ConfigDict(extra="ignore")
    version: str


class PyPIResponse(BaseModel):
    """Very limited model of a PyPI json response – intended only for retrieving version
    numbers, everything else is ignored."""

    model_config = ConfigDict(extra="ignore")
    info: PyPIInfo


def is_outdated() -> typing.Literal[False] | Version:
    local_version = Version(importlib.metadata.version("feed_ursus"))
    response = PyPIResponse.model_validate(
        requests.get("https://pypi.python.org/pypi/feed_ursus/json").json()
    )
    latest_version = Version(response.info.version)

    if local_version < latest_version and not local_version.is_devrelease:
        return latest_version
    else:
        return False


if __name__ == "__main__":
    print("feed_ursus() executing, running from main()")
    feed_ursus()  # pylint: disable=no-value-for-parameter
