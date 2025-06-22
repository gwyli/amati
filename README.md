# amati

A programme designed to validate that a file conforms to [OpenAPI Specification](https://spec.openapis.org/oas/v3.1.1.html) (OAS).

Currently a proof of concept.

## Name

amati means to observe in Malay, especially with attention to detail. It's also one of the plurals of beloved or favourite in Italian.

## Architecture

This uses Pydantic, especially the validation, and Typing to construct the entire OAS as a single data type. Passing a dictionary to the top-level data type runs all the validation in the Pydantic models constructing a single set of inherited classes and datatypes that validate that the API specification is accurate.

Where the specification conforms, but relies on implementation-defined behavior (e.g. [data type formats](https://spec.openapis.org/oas/v3.1.1.html#data-type-format)), a warning will be raised.

## Requirements

* The latest version of [uv](https://docs.astral.sh/uv/)
* [git 2.49+](https://git-scm.com/downloads/linux)

## Testing and formatting

This project uses:

* [Pytest](https://docs.pytest.org/en/stable/) as a testing framework
* [PyLance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) on strict mode for type checking
* [Pylint](https://www.pylint.org/) as a linter, using a modified version from [Google's style guide](https://google.github.io/styleguide/pyguide.html)
* [Hypothesis](https://hypothesis.readthedocs.io/en/latest/index.html) for test data generation
* [Coverage](https://coverage.readthedocs.io/en/7.6.8/) on both the tests and code for test coverage
* [Black](https://black.readthedocs.io/en/stable/index.html) for automated formatting
* [isort](https://pycqa.github.io/isort/) for import sorting

It's expected that there are no errors, no surviving mutants and 100% of the code is reached and executed.

amati runs tests on external specifications, detailed in `tests/data/.amati.tests.yaml`. To be able to run these tests the appropriate GitHub repos need to be local. Specific revisions of the repos can be downloaded by running

```sh
python scripts/tests/setup_test_specs.py
```

To run everything, from linting, type checking to downloading test specs run:

```sh
sh bin/checks.sh
```

## Building

The project uses a [`pyproject.toml` file](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#writing-pyproject-toml) to determine what to build.

To install, assuming that [uv](https://docs.astral.sh/uv/) is already installed and initialised

```sh
uv python install
uv venv
uv sync
```

### Data

There are some scripts to create the data needed by the project, for example, all the possible licences. If the data needs to be refreshed this can be done by running the contents of `/scripts/data`.




