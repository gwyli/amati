black .
isort .
pylint $(git ls-files '*.py')
pytest --cov-report term-missing --cov=amati tests
pytest --doctest-modules amati/