"""
Clones the repositories containing open source API specs for testing
"""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml
from loguru import logger


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

    with open("tests/data/.amati.tests.yaml", encoding="utf-8") as f:
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
        local_directory: Path = directory / local

        if local_directory.exists():
            logger.info(f"{local_directory} already exists. Skipping.")
            continue

        clone_directory: Path = Path("/tmp") / local
        logger.info(f"Cloning {remote['uri']} into {clone_directory}")

        subprocess.run(
            [
                "git",
                "clone",
                remote["uri"],
                f"/tmp/{local}",
                "--depth=1",
                f"--revision={remote['revision']}",
            ],
            check=True,
        )

        logger.info(f"Moving {clone_directory} to {local_directory}")
        local_directory.mkdir()

        subprocess.run(["mv", clone_directory, directory], check=True)

        shutil.rmtree(clone_directory, ignore_errors=True)


if __name__ == "__main__":
    logger.remove()  # Remove the default logger
    # Add a new logger that outputs to stderr with a specific format
    logger.add(sys.stderr, format="{time} | {level} | {message}")

    data = get_repos()
    clone(data)
