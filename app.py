from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

# Создаем экземпляр Flask-приложения
app = Flask(__name__)

# Указываем путь к базе данных (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Создаем объект базы данных SQLAlchemy
db = SQLAlchemy(app)

# Определение модели для номеров (Room)
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Идентификатор номера
    room_name = db.Column(db.String(100), nullable=False)  # Название номера
    description = db.Column(db.Text, nullable=False)  # Описание номера
    price = db.Column(db.Float, nullable=False)  # Цена за ночь
    image = db.Column(db.String(255), nullable=False)  # Путь к изображению номера

# Маршрут для главной страницы
@app.route('/')
def index():
    return render_template('index.html')

# Маршрут для страницы с номерами
@app.route('/templates/rooms.html')
def rooms():
    rooms_list = Room.query.all()  # Получаем все номера из базы данных
    return render_template('rooms.html', rooms=rooms_list)

# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True)
