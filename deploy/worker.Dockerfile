FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src/app ./app

RUN pip install --upgrade pip
RUN pip install uv
RUN uv pip install -r pyproject.toml --all-extras --system

ENV PYTHONPATH=/app
CMD ["uv", "run", "arq", "app.worker.tasks.WorkerSettings"]