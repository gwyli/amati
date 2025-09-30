FROM python:3.13-slim@sha256:6cbc4355e9cff50d6ae679b08435b355d388b62d32aa701d08ac9f77bd7c287c

ENV PYTHONUNBUFFERED=1

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY amati/ amati/

RUN uv lock
RUN uv sync --locked --no-dev

RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

ENTRYPOINT ["uv", "run", "python", "amati/amati.py"]
