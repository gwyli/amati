"""
Tests amati/validators/oas311.py
"""

import json
import warnings
from pathlib import Path
from typing import Any, Literal, cast

from amati.amati import check, dispatch, load_file
from amati.logging import LogMixin

TEST_DATA_PATH = Path("tests/data")

type TestOptions = Literal["good"] | Literal["bad"]
type TestData = dict[TestOptions, list[Path]]


def get_test_data() -> TestData:
    """
    Gathers the set of test data.
    """

    files: TestData = {"good": [], "bad": []}

    for file in TEST_DATA_PATH.glob("**/*.*"):

        if file.suffix in (".yaml", ".yml", ".json", ".gz"):
            test_style: TestOptions = cast(TestOptions, file.parts[-2])
            files[test_style].append(file)

    return files


def test_good_files():

    files = get_test_data()

    for file in files["good"]:

        data = load_file(file)

        with LogMixin.context():
            result, errors = dispatch(data)

        assert not errors
        assert result

        # Pydantic emits a set of warnings with the error
        # PydanticSerializationUnexpectedValue when running this check. The purpose
        # of the check is to validate that amati can output the same file that was
        # provided. If the test passes then there has been no incorrect serialisation.
        with warnings.catch_warnings():
            warnings.filterwarnings(
                action="ignore",
                category=UserWarning,
                message="Pydantic serializer warnings:.*",
            )
            assert check(data, result)


def get_errors(file: Path) -> list[dict[str, Any]]:
    """
    Returns the stored, expected, set of errors associated
    with a given test specification.
    """

    expected_error_file = Path(str(file).replace("yaml", "errors"))
    print(expected_error_file)

    with open(expected_error_file, "r", encoding="utf-8") as f:
        expected_errors = json.loads(f.read())

    return expected_errors


def test_bad_files():

    files = get_test_data()

    for file in files["bad"]:

        expected_errors = get_errors(file)
        print(file)

        data = load_file(file)

        with LogMixin.context():
            result, errors = dispatch(data)

        print(json.dumps(errors, sort_keys=True))
        print(json.dumps(expected_errors, sort_keys=True))

        assert json.dumps(errors, sort_keys=True) == json.dumps(
            expected_errors, sort_keys=True
        )
        assert not result
