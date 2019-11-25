# feed_ursus
Script to process CSVs into an Ursus-ready solr index.

# Using feed_ursus.py

First, make sure you have Python 3 available and [install pipenv](https://pipenv.kennethreitz.org/en/latest/#install-pipenv-today). Then you can use pipenv to install the project's dependencies in a new virtual environment: 

```pipenv install```

Then, to run commands inside the new virtual environment, you can either enter `pipenv shell` to enter the virtual environment, or you can prefix your commands with `pipenv run`.

You can then use the script to convert a csv into a json document that follows the data model of an Ursus solr index:

```pipenv run feed_ursus.py [path/to/your.csv]```

This repo includes a docker-compose.yml file that will run local instances of solr and ursus for use in testing this script. To use them (assuming you have installed docker and docker compose):

```docker-compose up --detach```

Give it a minute or so for solr to get up and running, then point feed_ursus.py directly at the new solr

```pipenv run feed_ursus.py [path/to/your.csv] --solr_url http://localhost:6983/solr/californica```

When the command finishes running, you can see your new site at http://localhost:6003

# Caveats

## IIIF Manifests

When importing a work, the script will always assume that a IIIF manifest exists at https://iiif.library.ucla.edu/[ark]/manifest, where [ark] is the URL-encoded Archival Resource Key of the work. This link should work, as long as a manifest has been pushed to that location by importing the work into [Fester](https://github.com/UCLALibrary/fester) or [Californica](https://github.com/UCLALibrary/californica). If you haven't done one of those, obviously, the link will fail and the image won't be visible, but metadata will import and be visible. A manifest can then be created and pushed to the expected location without re-running feed_ursus.py.
