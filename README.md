# feed_ursus
Script to process CSVs into an Ursus-ready solr index.

# Try it out

- [Install pipenv](https://pipenv.kennethreitz.org/en/latest/#install-pipenv-today)

- Install dependencies

```pipenv install```

- Run the included instance of ursus

```docker-compose up --detach```

- Load a CSV

```pipenv run feed_ursus.py [path/to/your.csv] --solr_url http://localhost:6983/solr/californica```

- Take a look at http://localhost:6003
