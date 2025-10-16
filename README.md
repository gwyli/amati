# amati

amati is designed to validate that a file conforms to the [OpenAPI Specification v3.x](https://spec.openapis.org/) (OAS).

## Name

"amati" means to observe in Malay, especially with attention to detail. It's also one of the plurals of beloved or favourite in Italian.

## Usage

```sh
python amati/amati.py validate --help
usage: amati validate [-h] -s SPEC [--consistency-check] [--local] [--html-report]

options:
  -h, --help            show this help message and exit
  -s, --spec SPEC       The specification to be validated
  --consistency-check   Runs a consistency check between the input specification and the parsed specification
  --local               Store errors local to the caller in .amati/<file-name>.errors.json
  --html-report         Creates an HTML report of the errors, called <file-name>.errors.html, alongside <filename>.errors.json
```

### Docker

A Dockerfile is available on [DockerHub](https://hub.docker.com/r/benale/amati/tags) or `docker pull benale/amati:alpha`.

Whilst an alpha build, only the image tagged `alpha` will be maintained. If there are breaking API changes these will be detailed in releases. Releases can be separately watched using the custom option when watching this repository.

To run against a specific specification the location of the specification needs to be mounted in the container.

```sh
docker run -v "<path-to-specification>:/<mount-name> benale/amati:alpha validate --spec <path-to-spec> <options>
```

e.g. where you have a specification located in `/Users/myuser/myrepo/myspec.yaml` and create a mount `/data`:

```sh
docker run -v /Users/myuser/myrepo:/data benale/amati:alpha validate --spec /data/myspec.yaml --html-report
```

### PyPI

amati is [available on PyPI](https://pypi.org/project/amati/), to run everything:

```py
>>> from amati import amati
>>> amati.run('tests/data/openapi.yaml', consistency_check=True, local=True, html_report=True)
True
```

## Architecture

amati uses [Pydantic](https://docs.pydantic.dev/latest/), especially the validation, and [typing](https://docs.python.org/3/library/typing.html) to construct the entire OAS as a single data type. Passing a dictionary to the top-level data type runs all the validation in the Pydantic models constructing a single set of inherited classes and datatypes that validate that the API specification is accurate. To the extent that Pydantic is functional, amati has a [functional core and an imperative shell](https://www.destroyallsoftware.com/screencasts/catalog/functional-core-imperative-shell).

Where the specification conforms, but relies on implementation-defined behavior (e.g. [data type formats](https://spec.openapis.org/oas/v3.1.1.html#data-type-format)), a warning will be raised.

## Contributing

### Prerequisites

* The latest version of [uv](https://docs.astral.sh/uv/)
* [git 2.49+](https://git-scm.com/downloads/linux)
* [Docker](https://docs.docker.com/engine/install/)

### Starting

The project uses a [`pyproject.toml` file](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/#writing-pyproject-toml) to determine what to build.

To get started run:

```sh
sh bin/startup.sh
```

### Testing and formatting

This project uses:

* [Pytest](https://docs.pytest.org/en/stable/) as a testing framework
* [Pyright](https://microsoft.github.io/pyright/#/) on strict mode for type checking
* [Ruff](https://docs.astral.sh/ruff/) as a linter and formatter
* [Hypothesis](https://hypothesis.readthedocs.io/en/latest/index.html) for test data generation
* [Coverage](https://coverage.readthedocs.io/en/7.6.8/) on both the tests and code for test coverage
* [Shellcheck](https://github.com/koalaman/shellcheck/wiki) for as SAST for shell scripts

It's expected that there are no errors and 100% of the code is reached and executed. The strategy for test coverage is based on parsing test specifications and not unit tests.
amati runs tests on the external specifications, detailed in `tests/data/.amati.tests.yaml`. To be able to run these tests the GitHub repos containing the specifications need to be available locally. Specific revisions of the repos can be downloaded by running the following, which will clone the repos into `.amati/amati-tests-specs/<repo-name>`.

```sh
python scripts/setup_test_specs.py
```

If there are some issues with the specification a JSON file detailing those should be placed into `tests/data/` and the name of that file noted in `tests/data/.amati.tests.yaml` for the test suite to pick it up and check that the errors are expected. Any specifications that close the coverage gap are gratefully received.

To run everything, from linting, type checking to downloading test specs and building and testing the Docker image run:

```sh
sh bin/checks.sh
```

### Docker

A `Dockerfile` is provided, to build:

```sh
docker build -t amati -f Dockerfile .
```

to run against a specific specification the location of the specification needs to be mounted in the container.

```sh
docker run -v "<path-to-specification>:/<mount-name> amati validate -s <path-to-spec> <options>
```

This can be tested against a provided specification, from the root directory

```sh
docker run --detach -v "$(pwd):/data" amati validate  -s <path-to-spec> <options>
```


### Data

There are some scripts to create the data needed by the project, for example, all the registered TLDs. To refresh the data, run:

```py
python amati/amati.py refresh
```

[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/gwyli/amati/badge)](https://scorecard.dev/viewer/?uri=github.com/gwyli/amati)