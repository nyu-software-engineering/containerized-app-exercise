FROM python:3.10-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

FROM base AS test

ENV PIPENV_VENV_IN_PROJECT=1 \
    PATH="/app/.venv/bin:${PATH}"

COPY Pipfile Pipfile.lock ./
RUN python -m pip install --no-cache-dir pipenv==2024.4.1 \
    && pipenv verify \
    && pipenv sync --dev

COPY pyproject.toml ./
COPY receipts/ ./receipts/
COPY tests/ ./tests/

CMD ["python", "-m", "pytest"]

FROM base AS runtime

# The current OCR client uses only the standard library and the Tesseract binary.
# Keep test tools and Pipenv out of the runtime image.
COPY receipts/ ./receipts/
COPY tests/fixtures/corner-deli.png ./samples/corner-deli.png

USER 10001:10001

ENTRYPOINT ["python", "-m", "receipts.ocr"]
CMD ["--help"]
