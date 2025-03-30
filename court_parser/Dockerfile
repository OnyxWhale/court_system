FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
# Устанавливаем зависимости (включая исполняемые файлы в /usr/local/bin)
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
RUN apt-get update && apt-get install -y curl
WORKDIR /app
# Копируем библиотеки
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
# Копируем исполняемые файлы (включая gunicorn) <--- ДОБАВЛЕНО
COPY --from=builder /usr/local/bin /usr/local/bin
# Копируем код приложения
COPY . .
ENV PYTHONUNBUFFERED=1
# CMD теперь не так важен, так как переопределяется в docker-compose, но оставим для консистентности
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "court_parser.wsgi:application"]