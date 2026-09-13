"""Appointment routes (MVC: Controller)."""
from datetime import datetime

from flask import Blueprint, jsonify, request

from app.models import db
from app.models.appointment import Appointment
from app.seed import default_lookup_value

appointments_bp = Blueprint('appointments', __name__)


@appointments_bp.route('/api/appointments', methods=['GET'])
def get_appointments():
    appointments = Appointment.query.order_by(Appointment.appointment_date.desc()).all()
    return jsonify([a.to_dict() for a in appointments])


@appointments_bp.route('/api/appointments/<int:id>', methods=['GET'])
def get_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    return jsonify(appointment.to_dict())


def _parse_appt_datetime(value):
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return None


@appointments_bp.route('/api/appointments', methods=['POST'])
def create_appointment():
    data = request.get_json() or {}
    missing = [f for f in ('patient_id', 'doctor_id', 'treatment_id', 'appointment_date')
               if not data.get(f)]
    if missing:
        return jsonify({'error': f"Missing required fields: {', '.join(missing)}"}), 400
    appointment_date = _parse_appt_datetime(data['appointment_date'])
    if appointment_date is None:
        return jsonify({'error': 'appointment_date must be ISO datetime'}), 400
    appointment = Appointment(
        patient_id=data.get('patient_id'),
        doctor_id=data.get('doctor_id'),
        treatment_id=data.get('treatment_id'),
        appointment_date=appointment_date,
        status=data.get('status') or default_lookup_value('appointment_status') or 'pending',
        notes=data.get('notes')
    )
    db.session.add(appointment)
    db.session.commit()
    return jsonify(appointment.to_dict()), 201


@appointments_bp.route('/api/appointments/<int:id>', methods=['PUT'])
def update_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    data = request.get_json() or {}
    appointment.patient_id = data.get('patient_id', appointment.patient_id)
    appointment.doctor_id = data.get('doctor_id', appointment.doctor_id)
    appointment.treatment_id = data.get('treatment_id', appointment.treatment_id)
    if data.get('appointment_date'):
        parsed = _parse_appt_datetime(data['appointment_date'])
        if parsed is None:
            return jsonify({'error': 'appointment_date must be ISO datetime'}), 400
        appointment.appointment_date = parsed
    appointment.status = data.get('status', appointment.status)
    appointment.notes = data.get('notes', appointment.notes)
    db.session.commit()
    return jsonify(appointment.to_dict())


@appointments_bp.route('/api/appointments/<int:id>', methods=['DELETE'])
def delete_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    db.session.delete(appointment)
    db.session.commit()
    return '', 204
