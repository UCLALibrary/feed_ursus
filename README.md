# feed_ursus
Script to process CSVs into an Sinai-ready solr index.

## Using feed_ursus

For basic use, you can install feed_ursus as a systemwide command directly from github, without having to first clone the repository.

### Installation

We recommend installing with [pipx](https://pipx.pypa.io/), and [pyenv](https://github.com/pyenv/pyenv) for alternative python versions:

```
brew install pipx pyenv
pipx ensurepath
```

Then:

```
pipx install git+https://github.com/uclalibrary/feed_ursus.git
```

Pipx will install feed_ursus in its own virtualenv, but make the command accessible from anywhere so you don't need to active the virtualenv yourself.

### Use

Convert a csv into a json document that follows the data model of an Ursus solr index:

```
feed_ursus [path/to/your.csv]
```

This repo includes a docker-compose.yml file that will run local instances of solr and ursus for use in testing this script. To use them, first install [docker](https://docs.docker.com/install/) and [docker compose](https://docs.docker.com/compose/install/). Then run:

```
docker-compose up --detach
docker-compose run web bundle exec rails db:setup
```

It might take a minute or so for solr to get up and running, at which point you should be able to see your new site at http://localhost:3003. Ursus will be empty, because you haven't loaded any data yet.

To load data from a csv:

```
feed_ursus [path/to/your.csv] --solr_url=http://localhost:8983/solr/californica --mapping=dlp
```

### Mappers

Different metadata mappings are included for general Digital Library use (`--mapping=dlp`) and for the Sinai Manuscripts Digital Library (`--mapping=sinai`). Because this script was originally used for the Sinai Manuscripts project, the default value is `sinai` for backwards compatibility.

## Developing feed_ursus

For development, skip pipx and use [poetry](https://python-poetry.org) along with [pyenv](https://github.com/pyenv/pyenv).

### Installing

Get poetry and pyenv, if you don't have them already:

```
brew install pyenv
curl -sSL https://install.python-poetry.org | python3 -
```

Then:

```
poetry install
```

### Using the development version

```
poetry run feed_ursus [path/to/your.csv] --solr_url http://localhost:8983/solr/californica
```

or

```
poetry shell
feed_ursus [path/to/your.csv] --solr_url http://localhost:8983/solr/californica
```

### Running the tests

```
poetry run pytest --mypy --pylint
```

or

```
poetry shell
pytest --mypy --pylint
```

This will run:
- [pylint](https://www.pylint.org/), a linter, via [pytest-pylint](https://github.com/carsongee/pytest-pylint)
- [mypy](http://mypy-lang.org/), a static type checker, via [pytest-mypy](https://github.com/dbader/pytest-mypy/)
- the test suite, written using [pytest](https://docs.pytest.org/en/latest/)

# Caveats

## IIIF Manifests

When importing a work, the script will always assume that a IIIF manifest exists at https://iiif.library.ucla.edu/[ark]/manifest, where [ark] is the URL-encoded Archival Resource Key of the work. This link should work, as long as a manifest has been pushed to that location by importing the work into [Fester](https://github.com/UCLALibrary/fester) or [Californica](https://github.com/UCLALibrary/californica). If you haven't done one of those, obviously, the link will fail and the image won't be visible, but metadata will import and be visible. A manifest can then be created and pushed to the expected location without re-running feed_ursus.py.
