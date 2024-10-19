from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from flask_login import UserMixin

# Создаем экземпляр Flask-приложения
app = Flask(__name__)

secret_key = os.urandom(24)
app.secret_key = secret_key

# Указываем путь к базе данных (SQLite)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Создаем объект базы данных SQLAlchemy
db = SQLAlchemy(app)

# Настройка менеджера пользователей
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Определение модели для номеров (Room)
class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Идентификатор номера
    room_name = db.Column(db.String(100), nullable=False)  # Название номера
    description = db.Column(db.Text, nullable=False)  # Описание номера
    price = db.Column(db.Float, nullable=False)  # Цена за ночь
    image = db.Column(db.String(255), nullable=False)  # Путь к изображению номера
    is_booked = db.Column(db.Boolean, default=False) # Статус бронирования номера

# Наследуем класс User от UserMixin, который содержит нужные методы
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Маршрут для главной страницы
@app.route('/')
def index():
    return render_template('index.html')

# Маршрут для страницы с номерами
@app.route('/rooms')
@login_required
def rooms():
    rooms_list = Room.query.all()
    return render_template('rooms.html', rooms=rooms_list)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Маршрут для регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Такой пользователь уже существует!')
            return redirect(url_for('register'))

        new_user = User(username=username)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash('Регистрация успешна! Теперь вы можете войти.')
        return redirect(url_for('login'))

    return render_template('register.html')

# Маршрут для входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash('Неправильный логин или пароль')
            return redirect(url_for('login'))

        login_user(user)
        flash("Авторизация прошла успешно!")
        return redirect(url_for('rooms'))

    return render_template('login.html')

# Маршрут для выхода
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта.")
    return redirect(url_for('index'))

# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True)