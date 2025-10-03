FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./

COPY alembic.ini /app/alembic.ini
COPY alembic/ /app/alembic/

COPY src/app ./app

RUN pip install --upgrade pip
RUN pip install uv
RUN uv pip install -r pyproject.toml --all-extras --system

EXPOSE 8000
ENV PYTHONPATH=/app
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
