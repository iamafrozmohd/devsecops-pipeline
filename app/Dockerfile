# Hardened container for the hash-lookup API.
# - small Alpine base, pinned to a specific Python minor version (never "latest")
# - dependencies installed without cache, OS packages upgraded at build time
# - pip and setuptools removed after install: no package manager at runtime, and their
#   bundled libraries (urllib3, msgpack) were flagged HIGH by the Trivy image scan
# - runs as an unprivileged user, read-only friendly, with a health check
FROM python:3.13-alpine

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /srv

RUN apk upgrade --no-cache \
    && addgroup -S app \
    && adduser -S -G app -H -s /sbin/nologin app

COPY requirements.txt .
RUN pip install -r requirements.txt \
    && pip uninstall -y pip setuptools wheel

COPY --chown=root:root __init__.py app.py ./app/

USER app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:8080/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--access-logfile", "-", "app.app:app"]
