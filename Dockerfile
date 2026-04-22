# ============================================
# Stage 1: Builder
# ============================================
# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.12-slim as builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Ставим Poetry глобально
RUN pip install --no-cache-dir "poetry>=2.0.0"

WORKDIR /app

# 1. Создаем venv
RUN python -m venv /opt/venv

COPY pyproject.toml poetry.lock* ./


RUN poetry config virtualenvs.create false \
    && . /opt/venv/bin/activate \
    && poetry install --no-interaction --no-ansi --no-root

# 3. ПРОВЕРКА (через прямой путь к venv)
RUN /opt/venv/bin/python -c "import django; print('Django OK')" \
    && /opt/venv/bin/python -c "import celery; print('Celery OK')"


# ============================================
# Stage 2: Development
# ============================================
FROM python:3.12-slim as development

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем виртуальное окружение целиком
COPY --from=builder /opt/venv /opt/venv

# Активируем venv и настраиваем пути для твоей структуры (src/ и apps/)
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app:/app/src:/app/apps"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Копируем код проекта
COPY . .

RUN mkdir -p /app/logs /app/static /app/media /app/staticfiles

EXPOSE 8000

# Стандартная команда запуска (без watchfiles)
CMD ["python", "src/manage.py", "runserver", "0.0.0.0:8000"]

# ============================================
# Stage 3: Production
# ============================================
FROM python:3.12-slim as production

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app:/app/src:/app/apps"

COPY --chown=appuser:appuser . .

RUN mkdir -p /app/logs /app/static /app/media /app/staticfiles \
    && chown -R appuser:appuser /app

USER appuser

# Сборка статики
RUN python src/manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--chdir", "src", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
