FROM python:3.14.3-slim@sha256:486b8092bfb12997e10d4920897213a06563449c951c5506c2a2cfaf591c599f

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
