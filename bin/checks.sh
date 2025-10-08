#!/bin/sh
ruff check --fix
ruff format
python scripts/setup_test_specs.py
pytest --cov-report term-missing --cov=amati tests
pytest --doctest-modules amati/
pyright --verifytypes amati --ignoreexternal
docker build -t amati -f Dockerfile . 
cd tests/ || exit
docker run -v "$(pwd):/data" amati -d /data --consistency-check
cd ..
