FROM python:3.14.6-slim@sha256:b877e50bd90de10af8d82c57a022fc2e0dc731c5320d762a27986facfc3355c1

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
