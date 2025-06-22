"""
Clones the repositories containing open source API specs for testing
"""

import subprocess
from pathlib import Path
from typing import Any

import yaml


def guard():
    """
    Prevents executing this script or using clone outside
    of the top-level directory for amati
    """

    if Path("pyproject.toml") not in Path(".").iterdir():
        raise ValueError("setup_test_specs.py must be run in the top-level directory")


def get_repos() -> dict[str, Any]:
    """
    Gets the list of repositories to clone.
    """

    guard()

    with open("tests/data/.amati.tests.yaml", "r", encoding="utf-8") as f:
        content = yaml.safe_load(f)

    return content


def clone(content: dict[str, Any]):
    """
    Clones the test repos specified in .amati.tests.yaml
    into the specified directory
    """

    guard()

    directory = Path(content["directory"])

    if not directory.exists():
        directory.mkdir()

    for local, remote in content["repos"].items():

        clone_directory: Path = directory / local

        if clone_directory.exists():
            print(f"{clone_directory} already exists. Skipping.")
            continue

        clone_directory.mkdir()

        subprocess.run(
            [
                "git",
                "clone",
                remote["uri"],
                str(clone_directory),
                "--depth=1",
                f"--revision={remote["revision"]}",
            ],
            check=True,
        )


if __name__ == "__main__":

    data = get_repos()
    clone(data)
