# analytics-api
# Примеры использования API
# Загрузка файла:
curl -X POST -F "file=@data.csv" http://localhost:5000/upload
# Получение статистики:
curl "http://localhost:5000/data/stats?file_id=1"
# Очистка данных:
curl "http://localhost:5000/data/clean?file_id=1&remove_duplicates=true&fill_missing=true"
# Список файлов:
curl http://localhost:5000/files
