"""User management routes (MVC: Controller)."""
from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash

from app.models import db
from app.models.user import User

users_bp = Blueprint('users', __name__)


@users_bp.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict() for u in users])


@users_bp.route('/api/users/<int:id>', methods=['GET'])
def get_user(id):
    return jsonify(User.query.get_or_404(id).to_dict())


@users_bp.route('/api/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json() or {}
    if data.get('username'):
        new_username = data['username'].strip()
        existing = User.query.filter_by(username=new_username).first()
        if existing and existing.id != user.id:
            return jsonify({'error': 'Username already exists'}), 409
        user.username = new_username
    if data.get('role'):
        if user.role == 'admin' and data['role'] != 'admin':
            admin_count = User.query.filter_by(role='admin').count()
            if admin_count <= 1:
                return jsonify({'error': 'Cannot demote the last admin user'}), 400
        user.role = data['role']
    if data.get('password'):
        user.password_hash = generate_password_hash(data['password'])
    db.session.commit()
    return jsonify(user.to_dict())


@users_bp.route('/api/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.role == 'admin' and User.query.filter_by(role='admin').count() <= 1:
        return jsonify({'error': 'Cannot delete the last admin user'}), 400
    db.session.delete(user)
    db.session.commit()
    return '', 204
