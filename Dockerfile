# The builder image, used to build the virtual environment
FROM python:3.12-bookworm as builder

RUN pip install poetry==1.8.0

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN touch README.md

RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

# The runtime image, used to just run the code provided its virtual environment
FROM python:3.12-slim-bookworm as mitm

RUN DEBIAN_FRONTEND=noninteractive \
    apt update && \
    apt install -y curl

WORKDIR /app

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY extra ./extra
COPY kasa_webhook ./kasa_webhook
COPY logging_conf.yaml .

CMD [ \
    "uvicorn", "--log-config", "logging_conf.yaml", \
    "--host", "0.0.0.0", "--port", "80", \
    "kasa_webhook.api:app" \
    ]

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=2 CMD [ "/app/extra/healthcheck.sh" ]

