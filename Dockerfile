# ---- build: resolve wheels once, so the runtime layer stays toolchain-free ----
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /wheels
RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt


# ---- runtime ----
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=Eshop.settings

RUN apt-get update \
    && apt-get install --no-install-recommends -y libjpeg62-turbo zlib1g curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 eshop

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt && rm -rf /wheels

COPY --chown=eshop:eshop . .

# Collecting static needs a settings module that imports cleanly; a throwaway
# key is fine because nothing is served during the build.
RUN DJANGO_DEBUG=false DJANGO_SECRET_KEY=build-only-not-a-runtime-secret \
    python manage.py collectstatic --noinput \
    && mkdir -p /app/data /app/pictures \
    && chown -R eshop:eshop /app/data /app/pictures /app/staticfiles

USER eshop
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://localhost:8000/healthz/ || exit 1

CMD ["gunicorn", "Eshop.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
