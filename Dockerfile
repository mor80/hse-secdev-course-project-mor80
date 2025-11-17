# syntax=docker/dockerfile:1.6

ARG PYTHON_VERSION=3.11.9
ARG PYTHON_DIST=slim-bookworm

FROM python:${PYTHON_VERSION}-${PYTHON_DIST} AS builder
WORKDIR /app
ENV \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}"

RUN apt-get update \
    && apt-get install --yes --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m venv /opt/venv \
    && pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt


FROM python:${PYTHON_VERSION}-${PYTHON_DIST} AS runtime
WORKDIR /app

ENV \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:${PATH}"

RUN apt-get update \
    && apt-get install --yes --no-install-recommends curl postgresql-client tini \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

COPY --chmod=500 docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
COPY app ./app
COPY alembic.ini .
COPY migrations ./migrations
COPY requirements.txt requirements.txt

RUN groupadd --gid 1001 app && useradd --uid 1001 --gid 1001 --create-home app \
    && mkdir -p /app/logs \
    && chown -R app:app /app /usr/local/bin/docker-entrypoint.sh

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8000/health || exit 1

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/docker-entrypoint.sh"]
