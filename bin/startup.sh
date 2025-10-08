#!/bin/sh
uv python install
. .venv/bin/activate
uv sync
pre-commit install