from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required
from app.models import User, db

bp = Blueprint('auth', __name__)

@bp.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data.get('username'):
        return jsonify({'error': 'username is required'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'username already exists'}), 400
    
    user = User(username=data['username'])
    db.session.add(user)
    db.session.commit()
    
    login_user(user)
    return jsonify({
        'id': user.id,
        'username': user.username
    })

@bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data.get('username'):
        return jsonify({'error': 'username is required'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user:
        return jsonify({'error': 'user not found'}), 404
    
    login_user(user)
    return jsonify({
        'id': user.id,
        'username': user.username
    })

@bp.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'status': 'success'})
