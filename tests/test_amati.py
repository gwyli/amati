"""
Tests amati/amati.py, especially the args.
"""

import os
import subprocess

import pytest


def test_specifc_spec():
    subprocess.run(
        [
            "python",
            "amati/amati.py",
            "-s",
            "tests/data/openapi.yaml",
            "--consistency-check",
        ],
        check=True,
    )


def test_discover_without_directory_failure():
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run(["python", "amati/amati.py", "--consistency-check"], check=True)


def test_discover_without_directory_success():
    os.chdir("tests/data")
    subprocess.run(
        ["python", "../../amati/amati.py", "--consistency-check"], check=True
    )
    os.chdir("../../")


def test_discover_with_directory():
    subprocess.run(["python", "amati/amati.py", "-d", "tests/data/"], check=True)
