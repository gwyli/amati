"""
Clones the repositories containing open source API specs for testing
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yaml
from loguru import logger


def guard():
    """
    Prevents executing this script or using clone outside
    of the top-level directory for amati
    """

    if Path("pyproject.toml") not in Path().iterdir():
        raise ValueError("setup_test_specs.py must be run in the top-level directory")


def get_repos() -> dict[str, Any]:
    """
    Gets the list of repositories to clone.
    """

    guard()

    config: Path = Path("tests/data/.amati.tests.yaml")
    with config.open(encoding="utf-8") as f:
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

        clone_directory: Path = Path("/tmp/.amati")
        clone_directory.parent.mkdir(parents=True, exist_ok=True)
        tmp_directory = tempfile.mkdtemp(
            dir=clone_directory.parent, prefix=clone_directory.name
        )

        logger.info(f"Cloning {remote['uri']} into {tmp_directory}")

        subprocess.run(
            [
                "git",
                "clone",
                remote["uri"],
                f"{tmp_directory}",
                "--depth=1",
                f"--revision={remote['revision']}",
            ],
            check=True,
        )

        logger.info(f"Moving {tmp_directory} to {local_directory}")
        local_directory.mkdir()

        subprocess.run(
            [
                "rsync",
                "-a",
                "--remove-source-files",
                f"{tmp_directory}/",
                local_directory,
            ],
            check=True,
        )

        shutil.rmtree(tmp_directory, ignore_errors=True)


if __name__ == "__main__":
    logger.remove()  # Remove the default logger
    # Add a new logger that outputs to stderr with a specific format
    logger.add(sys.stderr, format="{time} | {level} | {message}")

    data = get_repos()
    clone(data)
