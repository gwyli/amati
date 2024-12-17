python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
pip install -e ".[build]"
pip install -e ".[dev]"
pre-commit install