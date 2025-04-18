# Укажите путь к вашему проекту и папке, которую нужно исключить
$projectPath = "D:\Development\court_system\court_parser"
$excludePath = "D:\Development\court_system\venv"
$outputFile = "D:\Development\court_system\all_code2.txt"

# Очистка или создание выходного файла
Remove-Item -Path $outputFile -Force -ErrorAction SilentlyContinue
New-Item -Path $outputFile -ItemType File -Force | Out-Null

# Рекурсивный поиск всех файлов в проекте, исключая определенную папку
Get-ChildItem -Path $projectPath -Recurse -File | Where-Object {
    $_.FullName -notlike "$excludePath*"
} | ForEach-Object {
    # Чтение содержимого файлов и добавление в выходной файл
    $content = Get-Content -Path $_.FullName -ErrorAction SilentlyContinue
    Add-Content -Path $outputFile -Value "----- File: $($_.FullName) -----"
    Add-Content -Path $outputFile -Value $content
}