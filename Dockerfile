FROM python:3.13-slim@sha256:5f55cdf0c5d9dc1a415637a5ccc4a9e18663ad203673173b8cda8f8dcacef689

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
