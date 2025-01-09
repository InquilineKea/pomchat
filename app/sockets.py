from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from . import socketio

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        emit('user_status', {
            'username': current_user.username,
            'status': 'online'
        }, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        emit('user_status', {
            'username': current_user.username,
            'status': 'offline'
        }, broadcast=True)

@socketio.on('join_room')
def handle_join_room(data):
    room_id = data.get('room_id')
    if room_id:
        join_room(room_id)
        emit('user_status', {
            'username': current_user.username,
            'status': 'joined',
            'room_id': room_id
        }, room=room_id)

@socketio.on('leave_room')
def handle_leave_room(data):
    room_id = data.get('room_id')
    if room_id:
        leave_room(room_id)
        emit('user_status', {
            'username': current_user.username,
            'status': 'left',
            'room_id': room_id
        }, room=room_id)

@socketio.on('message')
def handle_message(data):
    room_id = data.get('room_id')
    content = data.get('content')
    if room_id and content:
        emit('message', {
            'content': content,
            'author': current_user.username,
            'room_id': room_id,
            'focus_state': current_user.current_focus_state
        }, room=room_id)

@socketio.on('timer_sync')
def handle_timer_sync(data):
    state = data.get('state')
    remaining = data.get('remaining')
    if state:
        current_user.current_focus_state = state
        emit('timer_update', {
            'state': state,
            'remaining': remaining
        }, broadcast=True)

@socketio.on('focus_change')
def handle_focus_change(data):
    state = data.get('state')
    if state:
        current_user.current_focus_state = state
        emit('focus_change', {
            'username': current_user.username,
            'focus_state': state
        }, broadcast=True)
