"""
Tests amati/validators/oas311.py
"""

import json
import warnings
from pathlib import Path
from typing import Any

import pytest
import yaml

from amati.amati import check, dispatch, load_file
from amati.logging import LogMixin


def get_test_data() -> dict[str, Any]:
    """
    Gathers the set of test data.
    """

    with open("tests/data/.amati.tests.yaml", "r", encoding="utf-8") as f:
        content = yaml.safe_load(f)

    return content


def get_errors(error_file: Path) -> list[dict[str, Any]]:
    """
    Returns the stored, expected, set of errors associated
    with a given test specification.
    """

    with open(error_file, "r", encoding="utf-8") as f:
        expected_errors = json.loads(f.read())

    return expected_errors


@pytest.mark.external
def test_specs():

    content = get_test_data()

    directory = Path(content["directory"])

    for name, repo in content["repos"].items():

        for spec in repo["specs"]:
            file: Path = Path(directory) / name / spec

            data = load_file(file)

            with LogMixin.context():
                result, errors = dispatch(data)

            if errors := repo.get("error_file"):
                error_file = get_errors(Path(errors))

                assert json.dumps(error_file, sort_keys=True) == json.dumps(
                    error_file, sort_keys=True
                )
                assert not result

            else:

                assert not errors
                assert result

                # Pydantic emits a set of warnings with the error
                # PydanticSerializationUnexpectedValue when running this check. The
                # purpose of the check is to validate that amati can output the same
                # file that was provided. If the test passes then there has been no
                # incorrect serialisation.
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        action="ignore",
                        category=UserWarning,
                        message="Pydantic serializer warnings:.*",
                    )
                    assert check(data, result)
