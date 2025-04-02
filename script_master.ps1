# Создание сети
docker network create court_network --driver bridge

# Переход в court_proxy и запуск
Set-Location -Path "court_proxy"
docker-compose up --build -d

Set-Location -Path "../court_parser"
docker-compose up --build -d

Set-Location -Path "../court_judges"
docker-compose up --build -d

Write-Host "court_proxy запущен на http://localhost:1408"