FROM python:3.14-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.9.26 /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv UV_COMPILE_BYTECODE=0 UV_LINK_MODE=copy UV_NO_CACHE=1
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src src
RUN uv sync --frozen --no-dev

FROM python:3.14-slim
ENV PATH=/opt/venv/bin:$PATH PYTHONUNBUFFERED=1 MODEL_DIR=/models/serve PORT=8012
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/src /app/src
RUN useradd --uid 1000 --create-home app
USER app
EXPOSE 8012
CMD ["onnx-classifier"]
