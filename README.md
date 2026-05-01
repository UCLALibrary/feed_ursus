# feed_ursus

Command line tools to load CSV content into a Solr index for the UCLA Digital Library's frontend, Ursus (https://digital.library.ucla.edu/) and the [Sinai Manuscripts Digital Library](https://sinaimanuscripts.library.ucla.edu)

## Using feed_ursus

To use feed_ursus (e.g. as a librarian), you can install it as a systemwide command directly from pypi, without having to first clone the repository.

### Installation

#### Installing with UV

We recommend installing with [uv](https://docs.astral.sh/uv). On MacOS, you can install uv with [homebrew](https://brew.sh):

```
brew install uv
```

Then:

```
uv tool install feed_ursus
```

UV will install feed_ursus in its own virtualenv, but make the command accessible from anywhere so you don't need to active the virtualenv yourself.

To upgrade a uv-installed feed ursus to the latest version:

```
uv tool upgrade feed_ursus
```

#### Installing with pipx

If you are already using pipx, you can use it instead of uv:

```
pipx install feed_ursus
pipx upgrade feed_ursus
```

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
feed_ursus [path/to/your.csv]
```

This assumes that a solr core is running at the default location; you can also use:

```
feed_ursus --solr_url=http://localhost:8983/solr/ursus [path/to/your.csv]
```

## Developing feed_ursus

### Installing

For development, use the included devcontainer configuration, or install the project requirements with `uv sync` (not supported).

### Running the tests

Tests are written for [pytest](https://docs.pytest.org/en/latest/):

```
pytest
```

### Running the formatter and linters:

ruff (formatter and linter) will run in check mode in ci, so make sure you run it before committing:

```
ruff format .
ruff check --fix
```

mypy (static type checker, used for `sinai` command):

```
mypy
```

pyright (other type checker, used for `feed_ursus`, handles match-case statements better):

```
pyright
```

### VSCode Debugger Configuration

To debug with VSCode, the python environment has to be created within the project directory.

TODO: update this section for uv. UV seems more predictable overall so it's probablly easier? Just a matter of `rm -rf .venv && uv install`?

If it exists, remove the existing setup and install in the project directory:

- `poetry env list`
- `poetry env remove <name of environment you want to delete>`
- `poetry config virtualenvs.in-project true`
- `poetry install`

Add an appropriate `.vscode/launch.json`, this assumes you have the python debugger extension installed.

```
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Run the feed_ursus module",
            "type": "debugpy",
            "request": "launch",
            "cwd": "${workspaceFolder}",
            "console": "integratedTerminal",
            "module": "feed_ursus.feed_ursus",
            "justMyCode": true,
        }
    ]
}
```

# Caveats

## IIIF Manifests

When importing a work, the script will always assume that a IIIF manifest exists at https://iiif.library.ucla.edu/[ark]/manifest, where [ark] is the URL-encoded Archival Resource Key of the work. This link should work, as long as a manifest has been pushed to that location by importing the work into [Fester](https://github.com/UCLALibrary/fester). If you haven't done one of those, obviously, the link will fail and the image won't be visible, but metadata will import and be visible. A manifest can then be created and pushed to the expected location without re-running feed_ursus.py.
