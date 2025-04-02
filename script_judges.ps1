New-Item -Path "court_judges" -ItemType Directory -Force
Set-Location -Path "court_judges"

# Инициализация Django-проекта
django-admin startproject court_judges .
python manage.py startapp judges

# Создание директорий
New-Item -Path "templates/judges" -ItemType Directory -Force
New-Item -Path "logs" -ItemType Directory -Force
New-Item -Path "staticfiles" -ItemType Directory -Force

# Создание файлов
New-Item -Path "court_judges/celery.py" -ItemType File -Force
New-Item -Path "templates/judges/base.html" -ItemType File -Force
New-Item -Path "templates/judges/home.html" -ItemType File -Force
New-Item -Path "templates/judges/judge_detail.html" -ItemType File -Force
New-Item -Path "Dockerfile" -ItemType File -Force
New-Item -Path "docker-compose.yml" -ItemType File -Force
New-Item -Path "requirements.txt" -ItemType File -Force

Write-Host "Структура для court_judges создана успешно."