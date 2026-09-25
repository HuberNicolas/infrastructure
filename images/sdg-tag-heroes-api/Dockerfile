# syntax=docker/dockerfile:1
# Production image of the SDG Tag Heroes API. Built with the repository root of sdg-tag-heroes as context.
# Unlike deploy/api.Dockerfile in that repository (development: code mounted, --reload, env/ copied into the image),
# this image contains the code, runs without reload as a non-root user and reads its configuration from the
# environment only.

FROM python:3.14.7-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/ \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/cache/huggingface \
    IN_DOCKER=true

WORKDIR /api

# Same Poetry version and lockfile as during the thesis; installs into the system interpreter
COPY api/pyproject.toml api/poetry.lock ./
# hadolint ignore=DL3042
RUN --mount=type=cache,target=/root/.cache \
    pip install poetry==1.5.0 \
 && poetry config virtualenvs.create false \
 && poetry install --only main --no-interaction --no-ansi --no-root

# The API imports these packages from / (PYTHONPATH=/), exactly as the development setup mounts them
COPY api /api
COPY models /models
COPY db /db
COPY request_models /request_models
COPY schemas /schemas
COPY enums /enums
COPY settings /settings
COPY services /services
COPY utils /utils
COPY prompts /prompts

# /data/api holds the UMAP models (1.5 GB, not in git) and is a volume; /cache the Hugging Face models
RUN useradd --system --uid 10001 --no-create-home app \
 && mkdir -p /logs /data/api /cache \
 && chown -R app:app /logs /data /cache
USER 10001:10001

EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/', timeout=4)"]

# One worker: every worker loads its own PyTorch and sentence-transformers models
CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8001", "--proxy-headers", "--forwarded-allow-ips=*"]
