"""Patient routes (MVC: Controller)."""
from datetime import datetime

from flask import Blueprint, jsonify, request

from app.models import db
from app.models.patient import Patient

patients_bp = Blueprint('patients', __name__)


@patients_bp.route('/api/patients', methods=['GET'])
def get_patients():
    patients = Patient.query.order_by(Patient.created_at.desc()).all()
    return jsonify([p.to_dict() for p in patients])


@patients_bp.route('/api/patients/<int:id>', methods=['GET'])
def get_patient(id):
    patient = Patient.query.get_or_404(id)
    return jsonify(patient.to_dict())


@patients_bp.route('/api/patients', methods=['POST'])
def create_patient():
    data = request.get_json()
    patient = Patient(
        name=data.get('name'),
        phone=data.get('phone'),
        email=data.get('email'),
        address=data.get('address'),
        dob=datetime.strptime(data['dob'], '%Y-%m-%d').date() if data.get('dob') else None,
        gender=data.get('gender'),
        blood_group=data.get('blood_group'),
        medical_history=data.get('medical_history')
    )
    db.session.add(patient)
    db.session.commit()
    return jsonify(patient.to_dict()), 201


@patients_bp.route('/api/patients/<int:id>', methods=['PUT'])
def update_patient(id):
    patient = Patient.query.get_or_404(id)
    data = request.get_json()
    patient.name = data.get('name', patient.name)
    patient.phone = data.get('phone', patient.phone)
    patient.email = data.get('email', patient.email)
    patient.address = data.get('address', patient.address)
    if data.get('dob'):
        patient.dob = datetime.strptime(data['dob'], '%Y-%m-%d').date()
    patient.gender = data.get('gender', patient.gender)
    patient.blood_group = data.get('blood_group', patient.blood_group)
    patient.medical_history = data.get('medical_history', patient.medical_history)
    db.session.commit()
    return jsonify(patient.to_dict())


@patients_bp.route('/api/patients/<int:id>', methods=['DELETE'])
def delete_patient(id):
    patient = Patient.query.get_or_404(id)
    db.session.delete(patient)
    db.session.commit()
    return '', 204
