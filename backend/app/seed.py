"""Seed data and lookup helpers (MVC: service layer for startup data)."""
from werkzeug.security import generate_password_hash

from app.config import Config
from app.models import db
from app.models.doctor import Doctor
from app.models.lookup import Lookup, LookupType
from app.models.setting import Setting
from app.models.treatment import Treatment
from app.models.user import User

# Master data moved out of hardcoded UI lists into the database.
# New values can be added via the /api/lookups endpoints (Masters page).
DEFAULT_LOOKUPS = {
    'specialization': ['Cardiology', 'Neurology', 'Orthopedics', 'Pediatrics',
                       'Dermatology', 'Gynecology', 'General Medicine',
                       'Psychiatry', 'ENT', 'Ophthalmology'],
    'treatment_category': ['Consultation', 'Diagnostic', 'Surgical',
                           'Therapy', 'Medication', 'Follow-up'],
    'appointment_status': ['pending', 'confirmed', 'completed', 'cancelled'],
    'gender': ['Male', 'Female', 'Other'],
    'blood_group': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
    'user_role': ['admin', 'staff'],
    'payment_method': ['Cash', 'Card', 'UPI'],
}

DEFAULT_LOOKUP_TYPES = [
    # type, label, icon, description, placeholder, has_form
    ('specialization', 'Specializations', 'bi-person-badge',
     'Medical specialities offered at the clinic', 'e.g. Cardiology', True),
    ('treatment_category', 'Treatment Categories', 'bi-capsule',
     'Categories for the treatment catalog', 'e.g. Physiotherapy', True),
    ('appointment_status', 'Appointment Statuses', 'bi-calendar-check',
     'Workflow statuses for appointments', 'e.g. no-show', True),
    ('gender', 'Genders', 'bi-people', 'Patient gender options', '', False),
    ('blood_group', 'Blood Groups', 'bi-droplet', 'Blood group options', '', False),
    ('user_role', 'User Roles', 'bi-person-gear', 'Application user roles', '', False),
    ('payment_method', 'Payment Methods', 'bi-cash-coin', 'Accepted payment methods', '', False),
]

DEFAULT_SETTINGS = {
    'clinic_name': 'Multi-Speciality Clinic',
    'clinic_address': '123 Main Street',
    'clinic_phone': '+91-9876543210',
    'clinic_email': 'care@clinic.example',
    'tax_percent': '0',
    'invoice_prefix': 'INV',
}

# Sample Indian doctors (fictional names) with INR consultation fees.
DEFAULT_DOCTORS = [
    {'name': 'Dr. Ananya Sharma', 'specialization': 'Cardiology',
     'phone': '+91-9820012345', 'email': 'ananya.sharma@clinic.example',
     'experience_years': 12, 'consultation_fee': 1200,
     'qualification': 'MD Cardiology, AIIMS New Delhi',
     'bio': 'Interventional cardiologist with 12 years of experience.'},
    {'name': 'Dr. Rajesh Iyer', 'specialization': 'Neurology',
     'phone': '+91-9820012346', 'email': 'rajesh.iyer@clinic.example',
     'experience_years': 15, 'consultation_fee': 1500,
     'qualification': 'MD Neurology, NIMHANS Bengaluru',
     'bio': 'Specialist in epilepsy and movement disorders.'},
    {'name': 'Dr. Vikram Mehta', 'specialization': 'Orthopedics',
     'phone': '+91-9820012347', 'email': 'vikram.mehta@clinic.example',
     'experience_years': 10, 'consultation_fee': 1000,
     'qualification': 'MS Orthopedics, CMC Vellore',
     'bio': 'Joint replacement and sports injury surgeon.'},
    {'name': 'Dr. Priya Nair', 'specialization': 'Pediatrics',
     'phone': '+91-9820012348', 'email': 'priya.nair@clinic.example',
     'experience_years': 8, 'consultation_fee': 800,
     'qualification': 'MD Pediatrics, JIPMER Puducherry',
     'bio': 'Child care and immunization specialist.'},
    {'name': 'Dr. Kavitha Reddy', 'specialization': 'Dermatology',
     'phone': '+91-9820012349', 'email': 'kavitha.reddy@clinic.example',
     'experience_years': 9, 'consultation_fee': 900,
     'qualification': 'MD Dermatology, Osmania Medical College',
     'bio': 'Cosmetic and clinical dermatologist.'},
    {'name': 'Dr. Sneha Kulkarni', 'specialization': 'Gynecology',
     'phone': '+91-9820012350', 'email': 'sneha.kulkarni@clinic.example',
     'experience_years': 11, 'consultation_fee': 1100,
     'qualification': 'MS OBGY, KEM Hospital Mumbai',
     'bio': 'High-risk pregnancy and laparoscopic surgeon.'},
    {'name': 'Dr. Amit Patel', 'specialization': 'General Medicine',
     'phone': '+91-9820012351', 'email': 'amit.patel@clinic.example',
     'experience_years': 14, 'consultation_fee': 700,
     'qualification': 'MD General Medicine, BJ Medical College Ahmedabad',
     'bio': 'Diabetes, thyroid and lifestyle medicine.'},
    {'name': 'Dr. Arjun Malhotra', 'specialization': 'Psychiatry',
     'phone': '+91-9820012352', 'email': 'arjun.malhotra@clinic.example',
     'experience_years': 7, 'consultation_fee': 1000,
     'qualification': 'MD Psychiatry, PGIMER Chandigarh',
     'bio': 'Adult and adolescent mental health.'},
    {'name': 'Dr. Divya Menon', 'specialization': 'ENT',
     'phone': '+91-9820012353', 'email': 'divya.menon@clinic.example',
     'experience_years': 9, 'consultation_fee': 900,
     'qualification': 'MS ENT, Amrita School of Medicine Kochi',
     'bio': 'Endoscopic sinus and ear surgery.'},
    {'name': 'Dr. Sanjay Gupta', 'specialization': 'Ophthalmology',
     'phone': '+91-9820012354', 'email': 'sanjay.gupta@clinic.example',
     'experience_years': 13, 'consultation_fee': 1100,
     'qualification': 'MS Ophthalmology, AIIMS New Delhi',
     'bio': 'Cataract and LASIK surgeon.'},
    {'name': 'Dr. Rahul Verma', 'specialization': 'Orthopedics',
     'phone': '+91-9820012355', 'email': 'rahul.verma@clinic.example',
     'experience_years': 6, 'consultation_fee': 800,
     'qualification': 'DNB Orthopedics, Sir Ganga Ram Hospital New Delhi',
     'bio': 'Trauma and fracture care specialist.'},
    {'name': 'Dr. Lakshmi Venkatesh', 'specialization': 'Pediatrics',
     'phone': '+91-9820012356', 'email': 'lakshmi.venkatesh@clinic.example',
     'experience_years': 10, 'consultation_fee': 850,
     'qualification': 'DCH, Madras Medical College Chennai',
     'bio': 'Newborn care and growth monitoring.'},
]

# Sample treatment catalog with INR pricing.
DEFAULT_TREATMENTS = [
    {'name': 'General Health Checkup', 'category': 'Consultation',
     'description': 'Comprehensive physical examination with vitals.',
     'duration_minutes': 30, 'cost': 500},
    {'name': 'Specialist Consultation', 'category': 'Consultation',
     'description': 'In-depth consultation with a specialist doctor.',
     'duration_minutes': 30, 'cost': 800},
    {'name': 'Blood Test Panel', 'category': 'Diagnostic',
     'description': 'CBC, sugar, cholesterol and liver function tests.',
     'duration_minutes': 20, 'cost': 600},
    {'name': 'X-Ray Chest', 'category': 'Diagnostic',
     'description': 'Digital chest radiography with report.',
     'duration_minutes': 15, 'cost': 800},
    {'name': 'Ultrasound Abdomen', 'category': 'Diagnostic',
     'description': 'Whole abdomen ultrasound scanning.',
     'duration_minutes': 30, 'cost': 1200},
    {'name': 'Wound Suturing', 'category': 'Surgical',
     'description': 'Cleaning, suturing and dressing of minor wounds.',
     'duration_minutes': 30, 'cost': 1500},
    {'name': 'Cataract Surgery', 'category': 'Surgical',
     'description': 'Phacoemulsification with intraocular lens implant.',
     'duration_minutes': 60, 'cost': 25000},
    {'name': 'Physiotherapy Session', 'category': 'Therapy',
     'description': 'One-on-one rehabilitation and exercise therapy.',
     'duration_minutes': 45, 'cost': 600},
    {'name': 'Counseling Session', 'category': 'Therapy',
     'description': 'Confidential psychological counseling.',
     'duration_minutes': 60, 'cost': 1000},
    {'name': 'Flu Vaccination', 'category': 'Medication',
     'description': 'Seasonal influenza vaccine administration.',
     'duration_minutes': 15, 'cost': 1200},
    {'name': 'IV Drip Therapy', 'category': 'Medication',
     'description': 'Supervised intravenous fluid and vitamin therapy.',
     'duration_minutes': 60, 'cost': 2000},
    {'name': 'Post-Surgery Review', 'category': 'Follow-up',
     'description': 'Suture removal and recovery assessment.',
     'duration_minutes': 20, 'cost': 400},
    {'name': 'Chronic Care Review', 'category': 'Follow-up',
     'description': 'Ongoing review for diabetes, BP and thyroid care.',
     'duration_minutes': 20, 'cost': 500},
]


def default_lookup_value(lookup_type):
    """First active value of a lookup type, used for DB column defaults."""
    row = (Lookup.query
           .filter_by(type=lookup_type, is_active=True)
           .order_by(Lookup.sort_order, Lookup.id)
           .first())
    return row.value if row else None


def seed_all():
    """Idempotent startup seed. Must be called inside an app context."""
    for i, (lookup_type, label, icon, description, placeholder, has_form) in enumerate(DEFAULT_LOOKUP_TYPES):
        if db.session.get(LookupType, lookup_type) is None:
            db.session.add(LookupType(type=lookup_type, label=label, icon=icon,
                                      description=description, placeholder=placeholder,
                                      has_form=has_form, sort_order=i))
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
