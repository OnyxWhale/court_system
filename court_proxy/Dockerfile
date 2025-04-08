FROM openresty/openresty:latest

COPY nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
COPY static/ /app/static/

RUN chmod -R 644 /app/static/ && find /app/static/ -type d -exec chmod 755 {} \;