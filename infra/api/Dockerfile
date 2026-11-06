FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv UV_COMPILE_BYTECODE=0 UV_LINK_MODE=copy PATH=/opt/venv/bin:$PATH PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
COPY apps/auth-api/pyproject.toml apps/auth-api/
COPY apps/butterfly/pyproject.toml apps/butterfly/
COPY apps/synapse-api/pyproject.toml apps/synapse-api/
COPY apps/intent-api/pyproject.toml apps/intent-api/
COPY apps/workspace-api/pyproject.toml apps/workspace-api/
COPY packages/structured-logging/pyproject.toml packages/structured-logging/
COPY packages/token-verification/pyproject.toml packages/token-verification/
RUN uv sync --frozen --no-dev --all-packages --no-install-workspace
COPY apps/auth-api apps/auth-api
COPY apps/butterfly apps/butterfly
COPY apps/synapse-api apps/synapse-api
COPY apps/intent-api apps/intent-api
COPY apps/workspace-api apps/workspace-api
COPY packages/structured-logging packages/structured-logging
COPY packages/token-verification packages/token-verification
COPY docs/sap docs/sap
RUN uv sync --frozen --no-dev --all-packages \
    && useradd --uid 1000 --create-home app \
    && mkdir /data && chown app:app /data
USER app
