FROM python:3.14.2-slim@sha256:9b81fe9acff79e61affb44aaf3b6ff234392e8ca477cb86c9f7fd11732ce9b6a

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
