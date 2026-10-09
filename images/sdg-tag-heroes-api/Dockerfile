# syntax=docker/dockerfile:1
# Production image of the SDG Tag Heroes API. Built with the repository root of sdg-tag-heroes as context.
# Unlike deploy/api.Dockerfile in that repository (development: code mounted, --reload, env/ copied into the image),
# this image contains the code, runs without reload as a non-root user and reads its configuration from the
# environment only.

FROM python:3.10.14-slim

# NUMBA_CACHE_DIR: umap compiles with numba and caches next to its own files, which the non-root user cannot write
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/ \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HF_HOME=/cache/huggingface \
    NUMBA_CACHE_DIR=/cache/numba \
    IN_DOCKER=true

WORKDIR /api

# The versions of the thesis lockfile, except that PyTorch is the CPU build: the PyPI wheel brings over 2 GB of CUDA
# libraries (nvidia-*, triton) that a server without a GPU never loads. Same torch version, lockfile unchanged;
# torch comes without dependencies, they are pinned in the lockfile like everything else
ARG TORCH_VERSION=2.1.1
COPY api/pyproject.toml api/poetry.lock ./
# Poetry only exports the lockfile, from its own throwaway environment, so none of its packages end up in the image
# hadolint ignore=DL3042
RUN --mount=type=cache,target=/root/.cache \
    python -m venv /tmp/poetry \
 && /tmp/poetry/bin/pip install poetry==1.5.0 \
 && /tmp/poetry/bin/poetry export --only main --without-hashes --output /tmp/requirements.txt \
 && grep -vE '^(torch|triton|nvidia-[a-z0-9-]+)==' /tmp/requirements.txt > /tmp/requirements-cpu.txt \
 && pip install --no-deps "torch==${TORCH_VERSION}" --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-deps -r /tmp/requirements-cpu.txt \
 && pip check \
 && rm -rf /tmp/poetry /tmp/requirements*.txt

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

# /data/api holds the UMAP models (not in git) and is a volume; /cache the Hugging Face models and the numba cache
RUN useradd --system --uid 10001 --no-create-home app \
 && mkdir -p /logs /data/api /cache \
 && chown -R app:app /logs /data /cache
USER 10001:10001

EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/', timeout=4)"]

# One worker: every worker loads its own PyTorch and sentence-transformers models
CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8001", "--proxy-headers", "--forwarded-allow-ips=*"]
