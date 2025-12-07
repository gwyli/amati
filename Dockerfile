FROM python:3.14.1-slim@sha256:b823ded4377ebb5ff1af5926702df2284e53cecbc6e3549e93a19d8632a1897e

ENV PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY amati/ amati/

RUN uv lock \
&& uv sync --locked --no-dev \
&& adduser --disabled-password --gecos '' appuser \
&& chown -R appuser /app

USER appuser

ENTRYPOINT ["uv", "run", "python", "amati/amati.py"]
