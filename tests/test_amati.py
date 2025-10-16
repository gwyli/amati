"""
Tests amati/amati.py, especially the args.
"""

import subprocess
from pathlib import Path


def test_specifc_spec():
    subprocess.run(
        [
            "python",
            "amati/amati.py",
            "validate",
            "-s",
            "tests/data/openapi.yaml",
            "--consistency-check",
        ],
        check=True,
    )


def test_gzip():
    subprocess.run(
        [
            "python",
            "amati/amati.py",
            "validate",
            "-s",
            "tests/data/openapi.yaml.gz",
            "--consistency-check",
        ],
        check=True,
    )


def test_errors_created_local():
    error_file: Path = Path(".amati/invalid-openapi.yaml.errors.json")
    html_file: Path = Path(".amati/invalid-openapi.yaml.errors.html")

    if error_file.exists():
        error_file.unlink()
    if html_file.exists():
        html_file.unlink()

    subprocess.run(
        [
            "python",
            "amati/amati.py",
            "validate",
            "-s",
            "tests/data/invalid-openapi.yaml",
            "--local",
            "--html-report",
        ],
        check=True,
    )
    assert error_file.exists()
    assert html_file.exists()
    error_file.unlink()
    html_file.unlink()


def test_errors_created():
    error_file: Path = Path("tests/data/invalid-openapi.yaml.errors.json")
    html_file: Path = Path("tests/data/invalid-openapi.yaml.errors.html")

    if error_file.exists():
        error_file.unlink()
    if html_file.exists():
        html_file.unlink()

    subprocess.run(
        [
            "python",
            "amati/amati.py",
            "validate",
            "-s",
            "tests/data/invalid-openapi.yaml",
            "--html-report",
        ],
        check=True,
    )
    assert error_file.exists()
    assert html_file.exists()
    error_file.unlink()
    html_file.unlink()
