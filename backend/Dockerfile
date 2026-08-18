FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y tesseract-ocr tesseract-ocr-tam tesseract-ocr-sin && rm -rf /var/lib/apt/lists/*
COPY backend/pyproject.toml ./
COPY backend/app ./app
RUN pip install --no-cache-dir . --extra-index-url https://download.pytorch.org/whl/cpu
COPY backend/alembic.ini ./
COPY backend/alembic ./alembic
COPY ml ./ml
COPY datasets/english/train_labeled.csv ./datasets/english/train_labeled.csv
RUN adduser --disabled-password --gecos '' swift && mkdir -p /data/attachments && chown -R swift:swift /data
USER swift
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
