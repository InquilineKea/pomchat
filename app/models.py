from . import db
from datetime import datetime
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    total_focus_time = db.Column(db.Integer, default=0)  # in seconds
    pomodoros_completed = db.Column(db.Integer, default=0)
    current_focus_state = db.Column(db.String(20), default='IDLE')
    
    messages = db.relationship('Message', backref='author', lazy=True)
    rooms = db.relationship('Room', secondary='room_members', backref='members')

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False, default='message')
    focus_state = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Room(db.Model):
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship('Message', backref='room', lazy=True)

class RoomMember(db.Model):
    __tablename__ = 'room_members'
    
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

class Timer:
    FOCUS = 'FOCUSING'
    BREAK = 'BREAK'
    LONG_BREAK = 'LONG_BREAK'
    IDLE = 'IDLE'
    
    def __init__(self):
        self.state = self.IDLE
        self.remaining = 0
        self.start_time = None
        
    def start_focus(self, duration=25*60):
        self.state = self.FOCUS
        self.remaining = duration
        self.start_time = datetime.utcnow()
    
    def start_break(self, duration=5*60, is_long=False):
        self.state = self.LONG_BREAK if is_long else self.BREAK
        self.remaining = duration
        self.start_time = datetime.utcnow()
    
    def stop(self):
        self.state = self.IDLE
        self.remaining = 0
        self.start_time = None
    
    @property
    def is_active(self):
        return self.state != self.IDLE
