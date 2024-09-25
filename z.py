from app import Room, db, app

with app.app_context():
    rooms = Room.query.all()
    for room in rooms:
        print(f"{room.id}: {room.room_name} - {room.price} руб.")
