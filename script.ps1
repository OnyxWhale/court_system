New-Item -Path "court_parser" -ItemType Directory -Force
Set-Location -Path "court_parser"

# Инициализация Django-проекта
django-admin startproject court_parser .
python manage.py startapp parser

# Создание директорий
New-Item -Path "templates/parser" -ItemType Directory -Force
New-Item -Path "logs" -ItemType Directory -Force
New-Item -Path "staticfiles" -ItemType Directory -Force

# Создание файлов
New-Item -Path "parser/parser.py" -ItemType File -Force
New-Item -Path "parser/tasks.py" -ItemType File -Force
New-Item -Path "court_parser/celery.py" -ItemType File -Force
New-Item -Path "templates/parser/base.html" -ItemType File -Force
New-Item -Path "templates/parser/home.html" -ItemType File -Force
New-Item -Path "templates/parser/threads.html" -ItemType File -Force
New-Item -Path "Dockerfile" -ItemType File -Force
New-Item -Path "docker-compose.yml" -ItemType File -Force
New-Item -Path "requirements.txt" -ItemType File -Force
New-Item -Path "wait-for-it.sh" -ItemType File -Force

Write-Host "Структура для court_parser создана успешно."