ruff check --fix
ruff format
python scripts/setup_test_specs.py
pytest --cov-report term-missing --cov=amati tests
pytest --doctest-modules amati/
docker build -t amati -f Dockerfile . 
cd tests/
docker run -v "$(pwd):/data" amati -d /data --consistency-check
cd ../