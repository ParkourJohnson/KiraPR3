import sqlite3

delquery = '''
ALTER TABLE Booking ADD COLUMN total_amount FLOAT NOT NULL;
'''

query = '''

'''

conn = sqlite3.connect('instance/hotel.db')

cursor = conn.cursor()

cursor.execute("SELECT * FROM User")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()