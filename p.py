from app import db, Room, app

# Создаем номера
rooms = [
    Room(room_name="Стандартный номер", description="Уютный стандартный номер с одной кроватью.", price=3500.00, image="images/room1.jpg"),
    Room(room_name="Двухместный номер", description="Просторный номер с двумя кроватями.", price=4500.00, image="images/room2.jpg"),
    Room(room_name="Люкс", description="Просторный номер люкс с шикарным видом на город.", price=7500.00, image="images/room3.jpg"),
]

# Добавление номеров в базу данных
with app.app_context():
    db.session.add_all(rooms)  # Добавляем все номера
    db.session.commit()         # Сохраняем изменения
    print("Номера успешно добавлены в базу данных!")
