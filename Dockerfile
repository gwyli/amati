FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml .
COPY uv.lock .
COPY README.md .
COPY amati/ amati/
RUN uv sync --locked --no-dev

ENTRYPOINT ["uv", "run", "python", "amati/amati.py"]