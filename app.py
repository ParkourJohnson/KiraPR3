from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import os
from flask_login import UserMixin
from datetime import datetime
from flask_mail import Mail, Message
import random
from sqlalchemy import or_, and_

app = Flask(__name__)

secret_key = os.urandom(24)
app.secret_key = secret_key

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hotel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

app.config['MAIL_SERVER'] = 'smtp.mail.ru'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'petrovich-bomzh45@bk.ru'
app.config['MAIL_PASSWORD'] = 'L9BN2zVrzYyCPFCf15gK'
app.config['MAIL_DEFAULT_SENDER'] = 'petrovich-bomzh45@bk.ru'
mail = Mail(app)

def generate_confirmation_code():
    return random.randint(100000, 999999)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(255), nullable=False)
    is_booked = db.Column(db.Boolean, default=False)

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
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)

    user = db.relationship('User', backref='bookings', lazy=True)
    room = db.relationship('Room', backref='bookings', lazy=True)

@app.route('/')
def index():
    is_logged_in = f'{current_user}' in session
    return render_template('index.html', is_logged_in=is_logged_in)

@app.route('/rooms')
@login_required
def rooms():
    rooms = Room.query.all()
    room_data = []
    
    for room in rooms:
        bookings = Booking.query.filter_by(room_id=room.id).all()
        booked_dates = [(booking.start_date, booking.end_date) for booking in bookings]
        room_data.append({
            'room': room,
            'booked_dates': booked_dates
        })
    
    return render_template('rooms.html', rooms=room_data)

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

        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

        if end_date_obj < start_date_obj:
            flash("Дата окончания должна быть позже даты начала.", "error")
            return redirect(url_for('book_room', room_id=room_id))
        
        if (start_date_obj.date() < datetime.today().date()):
            flash("Даты бронирования не могут быть раньше чем сегодня")
            return redirect(url_for('book_room', room_id=room.id))
        
        # Проверка доступности номеров на выбранные даты
        existing_bookings = Booking.query.filter(
            Booking.room_id == room_id,
            or_(
                and_(Booking.start_date <= start_date_obj, Booking.end_date >= start_date_obj),
                and_(Booking.start_date <= end_date_obj, Booking.end_date >= end_date_obj),
                and_(Booking.start_date >= start_date_obj, Booking.end_date <= end_date_obj)
            )
        ).all()

        if existing_bookings:
            flash("Номер недоступен на выбранные даты.", "error")
            return redirect(url_for('index'))
        
        num_days = (end_date_obj - start_date_obj).days
        total_cost = num_days * room.price

        return render_template('booking_confirmation.html', room=room, total_cost=total_cost, start_date=start_date, end_date=end_date)

    return render_template('book_room.html', room=room)

@app.route('/confirm_booking/<int:room_id>', methods=['POST'])
@login_required
def confirm_booking(room_id):
    room = Room.query.get_or_404(room_id)

    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')

    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

    book = Booking(
        user_id = current_user.id,
        room_id=room.id,
        start_date=start_date_obj,
        end_date=end_date_obj,
        total_amount = (end_date_obj - start_date_obj).days * room.price
        )

    db.session.add(book)
    db.session.commit()

    flash(f'Бронирование номера №{room.id} успешно завершено!')
    return redirect(url_for('index'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
        session[f'{current_user}'] = 1
        return redirect(url_for('rooms'))

    return render_template('login.html')

@app.route('/profile')
@login_required
def profile():
    bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', bookings=bookings, user=current_user)

@app.route('/delete_booking/<int:booking_id>', methods = ['POST'])
@login_required
def delete_booking(booking_id):
    if request.method == 'POST':
        booking = Booking.query.get(booking_id)

        if booking:
            db.session.delete(booking)
            db.session.commit()
            flash("Бронирование успешно удалено", 'success')
    
        return redirect(url_for('profile'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из аккаунта.")
    session.pop(f'{current_user}', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

with app.app_context():
    db.create_all()