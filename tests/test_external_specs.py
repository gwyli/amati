"""
Tests amati/validators/oas311.py
"""

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from amati.amati import run


def get_test_data() -> dict[str, Any]:
    """
    Gathers the set of test data.
    """
    config: Path = Path("tests/data/.amati.tests.yaml")
    with config.open(encoding="utf-8") as f:
        content = yaml.safe_load(f)

    return content


def get_errors(error_file: Path) -> list[dict[str, Any]]:
    """
    Returns the stored, expected, set of errors associated
    with a given test specification.
    """

    with error_file.open(encoding="utf-8") as f:
        expected_errors = json.loads(f.read())

    return expected_errors


def determine_file_names(file: Path) -> dict[str, Path]:
    """
    Make sorting out all the file names easier.
    """

    file_names: dict[str, Path] = {}

    file_name = Path(file.parts[-1])
    error_base = file_name.with_suffix(file_name.suffix + ".errors")
    directory = Path(".amati")

    file_names["error_json"] = directory / error_base.with_suffix(
        error_base.suffix + ".json"
    )
    file_names["error_html"] = directory / error_base.with_suffix(
        error_base.suffix + ".html"
    )

    return file_names


@pytest.mark.external
def test_specs():
    content = get_test_data()

    directory = Path(content["directory"])

    for name, repo in content["repos"].items():
        file: Path = Path(directory) / name / repo["spec"]
        files = determine_file_names(file)

        consistency_check = run(
            file_path=file, consistency_check=True, local=True, html_report=True
        )

        if errors := repo.get("error_file"):
            error_file = get_errors(Path(errors))

            with Path(files["error_json"]).open(encoding="utf-8") as f:
                json_encoded = json.loads(f.read())

            assert json.dumps(json_encoded, sort_keys=True) == json.dumps(
                error_file, sort_keys=True
            )

            assert files["error_html"].exists()

            # Cleanup
            files["error_json"].unlink()
            files["error_html"].unlink()
        else:
            assert consistency_check
