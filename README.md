# feed_ursus
Script to process CSVs into an Sinai-ready solr index.

# Using feed_ursus.py

We recommend installing with [poetry](https://python-poetry.org) and [pyenv](https://github.com/pyenv/pyenv).  which can be installed with [homebrew](https://brew.sh):

```
brew install pyenv
curl -sSL https://install.python-poetry.org | python3 -
```

You may need to add `export PATH="/Users/andy/.local/bin:$PATH"` to your shell profile.

If you installed poetry using homebrew (as this document formerly recommended), you might run into some dependency issues. If this happens try `brew uninstall poetry` and the official installer as shown above

To install dependencies in a virtual environment:

```
poetry install
```

Then, to run commands inside the new virtual environment, you can either enter `poetry shell` to enter the virtual environment, or you can prefix your commands with `poetry run`.

You can then use the script to convert a csv into a json document that follows the data model of an Ursus solr index:

```
poetry run feed_ursus.py [path/to/your.csv]
```

This repo includes a docker-compose.yml file that will run local instances of solr and ursus for use in testing this script. To use them (first install [docker](https://docs.docker.com/install/) and [docker compose](https://docs.docker.com/compose/install/)):

```
docker-compose up --detach
docker-compose run web bundle exec rails db:setup
```

Give it a minute or so for solr to get up and running, then point feed_ursus.py directly at the new solr:

```
poetry run ./feed_ursus.py [path/to/your.csv] --solr_url http://localhost:6983/solr/californica
```

When the command finishes running, you can see your new site at http://localhost:6003

# Running the test suite

First, install the dev dependencies and enter the virtualenv:
```
poetry install --dev
poetry shell
```

Then you can simply run:
```
pytest --mypy --pylint
```

This will run:
- [pylint](https://www.pylint.org/), a linter, via [pytest-pylint](https://github.com/carsongee/pytest-pylint)
- [mypy](http://mypy-lang.org/), a static type checker, via [pytest-mypy](https://github.com/dbader/pytest-mypy/)
- the test suite, written using [pytest](https://docs.pytest.org/en/latest/)

# Caveats

## IIIF Manifests

When importing a work, the script will always assume that a IIIF manifest exists at https://iiif.library.ucla.edu/[ark]/manifest, where [ark] is the URL-encoded Archival Resource Key of the work. This link should work, as long as a manifest has been pushed to that location by importing the work into [Fester](https://github.com/UCLALibrary/fester) or [Californica](https://github.com/UCLALibrary/californica). If you haven't done one of those, obviously, the link will fail and the image won't be visible, but metadata will import and be visible. A manifest can then be created and pushed to the expected location without re-running feed_ursus.py.
