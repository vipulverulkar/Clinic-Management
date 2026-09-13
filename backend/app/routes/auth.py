"""Auth routes (MVC: Controller)."""
import time
from collections import defaultdict

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from app.audit import log_action
from app.models import db
from app.models.user import User
from app.seed import default_lookup_value

auth_bp = Blueprint('auth', __name__)

# Simple in-memory login rate limit: 5 failed attempts per IP per 5 minutes.
_FAILED_LOGINS = defaultdict(list)
_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 300


def _limited(ip):
    now = time.time()
    attempts = [t for t in _FAILED_LOGINS[ip] if now - t < _WINDOW_SECONDS]
    _FAILED_LOGINS[ip] = attempts
    return len(attempts) >= _MAX_ATTEMPTS


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
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
        _FAILED_LOGINS[ip].append(time.time())
        return jsonify({'error': 'Invalid username or password'}), 401
    _FAILED_LOGINS.pop(ip, None)
    log_action('login', 'user', user.id, f'Login by {user.username}')
    return jsonify(user.to_dict())
