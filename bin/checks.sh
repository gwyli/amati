#!/bin/sh
ruff check --fix
ruff format
python scripts/setup_test_specs.py
pytest --cov-report term-missing --cov=amati tests
pytest --doctest-modules amati/
pyright --verifytypes amati --ignoreexternal
docker build -t amati -f Dockerfile . 
cd .amati/test-specs/swagger/src/main/resources/ || exit
docker run -v "$(pwd):/data" amati validate -s /data/openapi.yaml --consistency-check
cd - || exit