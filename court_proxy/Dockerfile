FROM nginx:latest

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY static/ /app/static/

RUN chmod -R 644 /app/static/ && find /app/static/ -type d -exec chmod 755 {} \;