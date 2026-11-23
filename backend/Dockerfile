FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

COPY pyproject.toml ./
COPY uv.lock* ./
COPY src/ ./src/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

EXPOSE 8000

CMD ["sh", "-c", "alembic -c src/infra/migrations/alembic.ini upgrade head && python -m infra.seed && python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]