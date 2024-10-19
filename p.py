import sqlite3

# Создание или подключение к базе данных
conn = sqlite3.connect('instance/hotel.db')  # Путь к файлу базы данных. Если файла не существует, он будет создан

# Создание курсора для выполнения SQL-запросов
cursor = conn.cursor()

# Пример выборки данных
cursor.execute("SELECT * FROM Booking")
rows = cursor.fetchall()
for row in rows:
    print(row)

# Закрытие подключения
conn.close()