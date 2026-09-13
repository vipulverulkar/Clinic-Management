"""Patient model (MVC: Model)."""
from datetime import datetime

from app.models import db


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    dob = db.Column(db.Date)
    gender = db.Column(db.String(10))
    blood_group = db.Column(db.String(5))
    medical_history = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'dob': self.dob.isoformat() if self.dob else None,
            'gender': self.gender,
            'blood_group': self.blood_group,
            'medical_history': self.medical_history,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
