# ==========================================
# STAGE 1: Shared base (dependencies only)
# ==========================================
FROM python:3.12.10-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.13 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1 \
    PATH="/OPENAQ/.venv/bin:$PATH"

WORKDIR /OPENAQ

COPY pyproject.toml .python-version uv.lock ./

# Runtime dependencies only (no dev group). This layer is shared by both stages below.
RUN uv sync --locked --no-dev --no-install-project

# Non-root user; Data/ and log/ are written at runtime
RUN useradd --create-home --uid 1000 app \
    && mkdir -p Data log \
    && chown app:app Data log

# ==========================================
# STAGE 2: ETL batch runner
# ==========================================
FROM base AS etl-runner
COPY --chown=app:app . .
USER app
ENTRYPOINT ["python", "main.py"]

# ==========================================
# STAGE 3: Streamlit dashboard
# ==========================================
FROM base AS dashboard
COPY --chown=app:app . .
USER app
EXPOSE 8501
ENTRYPOINT ["streamlit", "run", "dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]