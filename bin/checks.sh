black .
isort .
pylint $(git ls-files '*.py')
python scripts/tests/setup_test_specs.py
pytest --cov-report term-missing --cov=amati tests
pytest --doctest-modules amati/
docker build -t amati -f Dockerfile . 
cd test
docker run --detach -v "$(pwd):/data" amati -d /data
cd ../