black .
isort .
pylint $(git ls-files '*.py')
python scripts/tests/setup_test_specs.py
pytest --cov-report term-missing --cov=amati tests
pytest --doctest-modules amati/