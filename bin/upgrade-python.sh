#!/bin/sh

# Upgrades the Python version
# Steps:
# 1. Run this script
# 2. Upgraed the Dockerfile to match the new version
# 3. Run sh bin/checks.sh to ensure everything is working
# 4. Commit the changes and push

deactivate || true
uv self update
uv python upgrade "$1"
uv python pin "$1"
uv venv
. .venv/bin/activate
uv sync --all-groups