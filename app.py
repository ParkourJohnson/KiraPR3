from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from flask_login import UserMixin
from datetime import datetime
from flask_mail import Mail, Message
import random

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

app.config['MAIL_SERVER'] = 'smtp.mail.ru'  # SMTP-сервер для bk.ru
app.config['MAIL_PORT'] = 465  # Порт для защищенного соединения SSL
app.config['MAIL_USE_SSL'] = True  # Использование SSL
app.config['MAIL_USERNAME'] = 'petrovich-bomzh45@bk.ru'  # Ваша почта
app.config['MAIL_PASSWORD'] = 'L9BN2zVrzYyCPFCf15gK'  # Пароль от почты
app.config['MAIL_DEFAULT_SENDER'] = 'petrovich-bomzh45@bk.ru'  # От кого отправляются письма
mail = Mail(app)

# Функция для генерации случайного кода
def generate_confirmation_code():
    return random.randint(100000, 999999)

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
    email = db.Column(db.String(255), nullable = False)
    confirmation_code = db.Column(db.Integer, nullable = True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)  # Используй правильное имя таблицы
    start_date = db.Column(db.DateTime, nullable=False)  # Дата начала бронирования
    end_date = db.Column(db.DateTime, nullable=False)    # Дата конца бронирования

    user = db.relationship('User', backref='bookings', lazy=True)
    room = db.relationship('Room', backref='bookings', lazy=True)

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

@app.route('/book_room/<int:room_id>', methods=['GET', 'POST'])
@login_required
def book_room(room_id):
    room = Room.query.get_or_404(room_id)
    
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        if not start_date or not end_date:
            flash("Пожалуйста, выберите даты.", "error")
            return redirect(url_for('book_room', room_id=room_id))

        # Здесь можно добавить проверку на доступность номеров в выбранные даты

        # Считаем стоимость
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        num_days = (end_date_obj - start_date_obj).days

        if num_days <= 0:
            flash("Дата окончания должна быть позже даты начала.", "error")
            return redirect(url_for('book_room', room_id=room_id))
        
        total_cost = num_days * room.price

        # Рендерим страницу с итогами
        return render_template('booking_confirmation.html', room=room, total_cost=total_cost, start_date=start_date, end_date=end_date)

    return render_template('book_room.html', room=room)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Маршрут для регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        if User.query.filter_by(username=username).first():
            flash('Такой пользователь уже существует!')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Электронная почта занята')
            return redirect(url_for('register'))

        confirmation_code = generate_confirmation_code()

        new_user = User(username=username)
        new_user.set_password(password)
        new_user.email = email
        new_user.confirmation_code = confirmation_code

        db.session.add(new_user)
        db.session.commit()

        msg = Message('Подтверждение регистрации', recipients=[email])
        msg.body = f'Ваш код подтверждения: {confirmation_code}'
        mail.send(msg)

        flash('Регистрация успешна! Проверьте почту для подтверждения регистрации')
        return redirect(url_for('confirm_registration'))

    return render_template('register.html')

@app.route('/confirm_registration', methods=['GET', 'POST'])
def confirm_registration():
    if request.method == 'POST':
        email = request.form['email']
        confirmation_code = request.form['confirmation_code']

        user = User.query.filter_by(email=email).first()
        if user and user.confirmation_code == int(confirmation_code):
            flash('Регистрация подтверждена! Теперь вы можете войти.')
            # Очистить код подтверждения после успешной проверки
            user.confirmation_code = None
            db.session.commit()
            return redirect(url_for('login'))
        else:
            flash('Неверный код подтверждения. Попробуйте еще раз.')

    return render_template('confirm_registration.html')


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
        
        if user.confirmation_code is not None:
            flash('Вам необходимо подвердить регистрацию')
            return redirect(url_for('confirm_registration'))

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

with app.app_context():
    db.create_all()