FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY services/processing-worker/pyproject.toml .
RUN pip install --upgrade pip && pip install -e ".[dev]"

COPY services/processing-worker/app/ ./app/
COPY ai/ ./ai/

CMD ["python", "-m", "app.main"]