import sqlite3

query = '''
UPDATE Room
SET is_booked = false;
'''

# Создание или подключение к базе данных
conn = sqlite3.connect('instance/hotel.db')  # Путь к файлу базы данных. Если файла не существует, он будет создан

# Создание курсора для выполнения SQL-запросов
cursor = conn.cursor()

cursor.execute(query)

conn.commit()

# Пример выборки данных
cursor.execute("SELECT * FROM Room")
rows = cursor.fetchall()
for row in rows:
    print(row)

# Закрытие подключения
conn.close()