# Dockerfile для RAG Backend
FROM python:3.11-slim

# Метаданные
LABEL maintainer="your-email@example.com"
LABEL description="Agentic RAG System Backend"
LABEL version="1.0.0"

# Установить системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Создать рабочую директорию
WORKDIR /app

# Скопировать requirements
COPY requirements.txt .

# Установить Python зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Скопировать код приложения
COPY backend ./backend
COPY frontend ./frontend

# Создать директории для данных
RUN mkdir -p data/documents logs && \
    chmod 755 data logs

# Создать non-root пользователя
RUN useradd -m -u 1000 raguser && \
    chown -R raguser:raguser /app

# Переключиться на non-root пользователя
USER raguser

# Открыть порт
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Запустить приложение
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
