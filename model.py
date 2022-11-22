from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
from datetime import datetime

db = SQLAlchemy()


# room table
class Room(db.Model):
    """ table name : room
        table info 
    - room_idx : index id 
    - room_name:  
    - room_capacity: room_capacity
    - room_password: room_password for enter 
    - room_create_at: room_create at datetime 
    - room_enter_user: room_enter_user """

    __tablename__ = 'room'

    room_idx = sa.Column(sa.Integer, primary_key=True, nullable=False, autoincrement=True)
    room_name = sa.Column(sa.String(20, 'utf8mb4_unicode_ci'), nullable=False, unique=True)
    room_capacity = sa.Column(sa.Integer, nullable=False)
    room_password = sa.Column(sa.String(10, 'utf8mb4_unicode_ci'), nullable=False)
    room_create_at = sa.Column(sa.DateTime, default=datetime.utcnow())
    room_enter_user = sa.Column(sa.Integer, nullable=False)

    def __init__(self, room_idx, room_name, room_capacity, room_password, room_create_at, room_enter_user):
        self.room_idx = room_idx
        self.room_name = room_name
        self.room_capacity = room_capacity
        self.room_password = room_password
        self.room_create_at = room_create_at
        self.room_enter_user = room_enter_user

    def __repr__(self):
        return f"<Room('{self.room_idx}', '{self.room_name}')>"


# user table
class User(db.Model):
    """ table name : room
        table info 
    - user_idx : index id 
    - user_nickname: user nickname
    - room_idx : room unique idx
    - user_create_at: when the user create """

    __tablename__ = 'user'

    user_idx = sa.Column(sa.Integer, primary_key=True, nullable=False, autoincrement=True)
    user_nickname = sa.Column(sa.String(20, 'utf8mb4_unicode_ci'), unique=True, nullable=False)
    room_idx = sa.Column(sa.Integer, sa.ForeignKey('room.room_idx'), nullable=False)
    user_create_at = sa.Column(sa.DateTime, default=datetime.utcnow())

    def __init__(self, user_idx, user_nickname, room_idx, user_create_at):
        self.user_idx = user_idx
        self.user_nickname = user_nickname
        self.room_idx = room_idx
        self.user_create_at = user_create_at
