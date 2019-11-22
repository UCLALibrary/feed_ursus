# feed_ursus
Script to process CSVs into an Ursus-ready solr index.

# Try it out

0. [Install pipenv](https://pipenv.kennethreitz.org/en/latest/#install-pipenv-today)
0. Run the included instance of ursus
```docker-compose up --detach```
0. Load a CSV
```pipenv run feed_ursus.py [path/to/your.csv] --solr_url http://localhost:6983/solr/californica```
0. Take a look at http://localhost:6003
