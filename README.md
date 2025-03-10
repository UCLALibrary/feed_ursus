# feed_ursus
Command line tool to load CSV content into a Solr index for the UCLA Digital Library's frontend, Ursus (https://digital.library.ucla.edu/)

## Using feed_ursus

For basic use, you can install feed_ursus as a systemwide command directly from pypi, without having to first clone the repository.

### Installation

We recommend installing with [pipx](https://pipx.pypa.io/). On MacOS, you can install pipx (and python!) with [homebrew](https://brew.sh):

```
brew install pipx pyenv
pipx ensurepath
```

Then:

```
pipx install feed_ursus
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

It might take a minute or so for solr to get up and running, at which point you should be able to see your new site at http://localhost:3000. Ursus will be empty, because you haven't loaded any data yet.

To load data from a csv:

```
feed_ursus --solr_url=http://localhost:8983/solr/californica --mapping=dlp load [path/to/your.csv] 
```

### Mappers

Different metadata mappings are included for general Digital Library use (`--mapping=dlp`) and for the Sinai Manuscripts Digital Library (`--mapping=sinai`). The default is "dlp" – "sinai" is not guaranteed to be up to date as the sinai project is using a forked version at https://github.com/uclalibrary/feed_sinai.

## Developing feed_ursus

### Installing

For development, clone the repository and use poetry to set up the virtualenv:

```
git clone git@github.com:UCLALibrary/feed_ursus.git
cd feed_ursus
pipx install poetry
poetry self add poetry-git-version-plugin
poetry install
```

Then, to activate the virtualenv:

```
poetry shell
```

The following will assume the virtualenv is active. You could also run e.g. `poetry run feed_ursus [path/to/your.csv]`

### Using the development version

```
feed_ursus --solr_url http://localhost:8983/solr/californica load [path/to/your.csv]
```

### Running the tests

Tests are written for [pytest](https://docs.pytest.org/en/latest/):

```
pytest
```

### Running the formatter and linters:

black (formatter) will run in check mode in ci, so make sure you run it before committing:
```
black .
```

flake8 (linter) isn't currently running in ci, but should be put back in soon:
```
flake8
```

pylint (linter) isn't currently running in ci, but should be put back in soon:
```
pylint
```

mypy (static type checker) isn't currently running in ci, but should be put back in soon:
```
mypy
```

# Caveats

## IIIF Manifests

When importing a work, the script will always assume that a IIIF manifest exists at https://iiif.library.ucla.edu/[ark]/manifest, where [ark] is the URL-encoded Archival Resource Key of the work. This link should work, as long as a manifest has been pushed to that location by importing the work into [Fester](https://github.com/UCLALibrary/fester) or [Californica](https://github.com/UCLALibrary/californica). If you haven't done one of those, obviously, the link will fail and the image won't be visible, but metadata will import and be visible. A manifest can then be created and pushed to the expected location without re-running feed_ursus.py.
