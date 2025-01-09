from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.models import Message, Room, User, db
from datetime import datetime

bp = Blueprint('api', __name__)

@bp.route('/timer', methods=['GET'])
@login_required
def get_timer():
    return jsonify({
        'state': current_user.current_focus_state,
        'remaining': 0  # TODO: Calculate remaining time
    })

@bp.route('/timer/start', methods=['POST'])
@login_required
def start_timer():
    data = request.get_json()
    duration = data.get('duration', 25*60)  # Default 25 minutes
    # TODO: Implement timer logic
    return jsonify({'status': 'success'})

@bp.route('/messages', methods=['GET'])
@login_required
def get_messages():
    room_id = request.args.get('room_id', type=int)
    before = request.args.get('before')
    
    if not room_id:
        return jsonify({'error': 'room_id is required'}), 400
    
    query = Message.query.filter_by(room_id=room_id)
    if before:
        query = query.filter(Message.created_at < before)
    
    messages = query.order_by(Message.created_at.desc()).limit(50).all()
    
    return jsonify([{
        'id': msg.id,
        'content': msg.content,
        'author': msg.author.username,
        'type': msg.type,
        'focus_state': msg.focus_state,
        'created_at': msg.created_at.isoformat()
    } for msg in messages])

@bp.route('/messages', methods=['POST'])
@login_required
def post_message():
    data = request.get_json()
    
    if not data.get('content') or not data.get('room_id'):
        return jsonify({'error': 'content and room_id are required'}), 400
    
    message = Message(
        content=data['content'],
        author_id=current_user.id,
        room_id=data['room_id'],
        type=data.get('type', 'message'),
        focus_state=current_user.current_focus_state
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({
        'id': message.id,
        'content': message.content,
        'author': current_user.username,
        'type': message.type,
        'focus_state': message.focus_state,
        'created_at': message.created_at.isoformat()
    })

@bp.route('/users/me', methods=['GET'])
@login_required
def get_current_user():
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'focus_state': current_user.current_focus_state,
        'total_focus_time': current_user.total_focus_time,
        'pomodoros_completed': current_user.pomodoros_completed
    })

@bp.route('/rooms', methods=['GET'])
@login_required
def get_rooms():
    rooms = Room.query.all()
    return jsonify([{
        'id': room.id,
        'name': room.name,
        'member_count': len(room.members)
    } for room in rooms])

@bp.route('/rooms', methods=['POST'])
@login_required
def create_room():
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'error': 'name is required'}), 400
    
    room = Room(name=data['name'])
    room.members.append(current_user)
    
    db.session.add(room)
    db.session.commit()
    
    return jsonify({
        'id': room.id,
        'name': room.name,
        'member_count': 1
    })
