"""Seed data and lookup helpers (MVC: service layer for startup data).

All default content lives in seed_data/*.json — no hardcoded master data
in code. Everything is idempotent: existing rows are never duplicated.
"""
import json
import os

from werkzeug.security import generate_password_hash

from app.config import Config
from app.models import db
from app.models.doctor import Doctor
from app.models.lookup import Lookup, LookupType
from app.models.setting import Setting
from app.models.treatment import Treatment
from app.models.user import User

SEED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seed_data')


def _load(filename):
    with open(os.path.join(SEED_DIR, filename), encoding='utf-8') as f:
        return json.load(f)


DEFAULT_LOOKUPS = _load('lookups.json')
DEFAULT_LOOKUP_TYPES = _load('lookup_types.json')
DEFAULT_SETTINGS = _load('settings.json')
DEFAULT_DOCTORS = _load('doctors.json')
DEFAULT_TREATMENTS = _load('treatments.json')


def default_lookup_value(lookup_type):
    """First active value of a lookup type, used for DB column defaults."""
    row = (Lookup.query
           .filter_by(type=lookup_type, is_active=True)
           .order_by(Lookup.sort_order, Lookup.id)
           .first())
    return row.value if row else None


def seed_all():
    """Idempotent startup seed. Must be called inside an app context."""
    for i, item in enumerate(DEFAULT_LOOKUP_TYPES):
        if db.session.get(LookupType, item['type']) is None:
            db.session.add(LookupType(sort_order=i, **item))
    db.session.commit()
    for lookup_type, values in DEFAULT_LOOKUPS.items():
        existing = {r.value for r in Lookup.query.filter_by(type=lookup_type).all()}
        for i, value in enumerate(values):
            if value not in existing:
                db.session.add(Lookup(type=lookup_type, value=value, sort_order=i))
        db.session.commit()
    if User.query.first() is None:
        admin = User(username=Config.ADMIN_USERNAME,
                     password_hash=generate_password_hash(Config.ADMIN_PASSWORD),
                     role='admin')
        db.session.add(admin)
        db.session.commit()
        print(f'Seeded default admin user: {Config.ADMIN_USERNAME}')
    for key, value in DEFAULT_SETTINGS.items():
        if db.session.get(Setting, key) is None:
            db.session.add(Setting(key=key, value=value))
    db.session.commit()
    for doc in DEFAULT_DOCTORS:
        if Doctor.query.filter_by(name=doc['name']).first() is None:
            db.session.add(Doctor(**doc))
    db.session.commit()
    for trt in DEFAULT_TREATMENTS:
        if Treatment.query.filter_by(name=trt['name']).first() is None:
            db.session.add(Treatment(**trt))
    db.session.commit()


def get_setting(key, default=''):
    row = db.session.get(Setting, key)
    return row.value if row else default


def get_int_setting(key, default):
    try:
        return int(float(get_setting(key, str(default))))
    except (TypeError, ValueError):
        return default
