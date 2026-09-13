"""Auth routes (MVC: Controller)."""
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from app.audit import log_action
from app.models import db
from app.models.setting import LoginAttempt
from app.models.user import User
from app.seed import default_lookup_value

auth_bp = Blueprint('auth', __name__)

# DB-backed login rate limit: 5 failed attempts per IP per 5 minutes.
_MAX_ATTEMPTS = 5
_WINDOW = timedelta(minutes=5)


def _limited(ip):
    cutoff = datetime.utcnow() - _WINDOW
    LoginAttempt.query.filter(LoginAttempt.attempted_at < cutoff).delete()
    db.session.commit()
    return LoginAttempt.query.filter_by(ip=ip).filter(
        LoginAttempt.attempted_at >= cutoff).count() >= _MAX_ATTEMPTS


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409
    user = User(username=username,
                password_hash=generate_password_hash(password),
                role=data.get('role') or default_lookup_value('user_role') or 'staff')
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    ip = request.remote_addr or 'unknown'
    if _limited(ip):
        return jsonify({'error': 'Too many failed attempts. Try again later.'}), 429
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, data.get('password') or ''):
        db.session.add(LoginAttempt(ip=ip))
        db.session.commit()
        return jsonify({'error': 'Invalid username or password'}), 401
    LoginAttempt.query.filter_by(ip=ip).delete()
    db.session.commit()
    log_action('login', 'user', user.id, f'Login by {user.username}')
    return jsonify(user.to_dict())
