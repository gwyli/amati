# amati

amati is designed to validate that a file conforms to the [OpenAPI Specification v3.x](https://spec.openapis.org/) (OAS).

## Name

amati means to observe in Malay, especially with attention to detail. It's also one of the plurals of beloved or favourite in Italian.

## Usage

```sh
python amati/amati.py --help
usage: amati [-h] [-s SPEC] [-cc] [-d DISCOVER] [-l] [-hr]

Tests whether a OpenAPI specification is valid. Will look an openapi.json or openapi.yaml file in the directory that
amati is called from. If --discover is set will search the directory tree. If the specification does not follow the
naming recommendation the --spec switch should be used. Creates a file <filename>.errors.json alongside the original
specification containing a JSON representation of all the errors.

options:
  -h, --help            show this help message and exit
  -s, --spec SPEC       The specification to be parsed
  -cc, --consistency-check
                        Runs a consistency check between the input specification and the parsed specification
  -d, --discover DISCOVER
                        Searches the specified directory tree for openapi.yaml or openapi.json.
  -l, --local           Store errors local to the caller in a file called <file-name>.errors.json; a .amati/ directory
                        will be created.
  -hr, --html-report    Creates an HTML report of the errors, called <file-name>.errors.html, alongside the original
                        file or in a .amati/ directory if the --local switch is used
```

A Dockerfile is available on [DockerHub](https://hub.docker.com/r/benale/amati/tags)

To run against a specific specification the location of the specification needs to be mounted in the container.

```sh
docker run -v "<path-to-mount>:/<mount-name> amati <options>
```

e.g. 

```sh
docker run -v /Users/myuser/myrepo:/data amati --spec data/myspec.yaml --hr
```

## Architecture

This uses Pydantic, especially the validation, and Typing to construct the entire OAS as a single data type. Passing a dictionary to the top-level data type runs all the validation in the Pydantic models constructing a single set of inherited classes and datatypes that validate that the API specification is accurate.

Where the specification conforms, but relies on implementation-defined behavior (e.g. [data type formats](https://spec.openapis.org/oas/v3.1.1.html#data-type-format)), a warning will be raised.

## Contributing

### Requirements

* The latest version of [uv](https://docs.astral.sh/uv/)
* [git 2.49+](https://git-scm.com/downloads/linux)

### Testing and formatting

This project uses:

* [Pytest](https://docs.pytest.org/en/stable/) as a testing framework
* [PyLance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) on strict mode for type checking
* [Pylint](https://www.pylint.org/) as a linter, using a modified version from [Google's style guide](https://google.github.io/styleguide/pyguide.html)
* [Hypothesis](https://hypothesis.readthedocs.io/en/latest/index.html) for test data generation
* [Coverage](https://coverage.readthedocs.io/en/7.6.8/) on both the tests and code for test coverage
* [Black](https://black.readthedocs.io/en/stable/index.html) for automated formatting
* [isort](https://pycqa.github.io/isort/) for import sorting

It's expected that there are no errors and 100% of the code is reached and executed. The strategy for test coverage is based on parsing test specifications and not unit tests.

amati runs tests on external specifications, detailed in `tests/data/.amati.tests.yaml`. To be able to run these tests the appropriate GitHub repos need to be local. Specific revisions of the repos can be downloaded by running

```sh
python scripts/tests/setup_test_specs.py
```

To run everything, from linting, type checking to downloading test specs and building and testing the Docker image run:

```sh
sh bin/checks.sh
```

You will need to have Docker installed.

### Building

The project uses a [`pyproject.toml` file](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#writing-pyproject-toml) to determine what to build.

To install, assuming that [uv](https://docs.astral.sh/uv/) is already installed and initialised

```sh
uv python install
uv venv
uv sync
```

### Docker

A development Docker image is provided, `Dockerfile.dev`, to build:

```sh
docker build -t amati -f Dockerfile .
```

and to run against a specific specification the location of the specification needs to be mounted in the container.

```sh
docker run -v "<path-to-mount>:/<mount-name> amati <options>
```

This can be tested against a provided specification, from the root directory

```sh
docker run --detach -v "$(pwd):/data" amati
```


### Data

There are some scripts to create the data needed by the project, for example, all the possible licences. If the data needs to be refreshed this can be done by running the contents of `/scripts/data`.




