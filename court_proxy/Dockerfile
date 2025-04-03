FROM nginx:latest

# Установка OpenSSL для генерации сертификатов
RUN apt-get update && apt-get install -y openssl

# Генерация самоподписанного сертификата
RUN mkdir -p /etc/nginx/ssl && \
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/selfsigned.key \
    -out /etc/nginx/ssl/selfsigned.crt \
    -subj "/C=RU/ST=State/L=City/O=Organization/CN=localhost"

# Копирование конфигурации и статики
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY static/ /app/static/

# Установка прав
RUN chmod -R 755 /app/static