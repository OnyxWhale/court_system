# Базовый образ Nginx
FROM nginx:latest

# Копируем конфигурацию
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Копируем статические файлы
COPY static/ /app/static/

# Устанавливаем права
RUN chmod -R 755 /app/static