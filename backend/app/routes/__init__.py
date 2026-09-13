"""Route registration (MVC: wires Controllers to the app)."""
from app.routes.appointments import appointments_bp
from app.routes.auditlog import audit_bp
from app.routes.auth import auth_bp
from app.routes.bills import bills_bp
from app.routes.doctors import doctors_bp
from app.routes.lookups import lookups_bp
from app.routes.patients import patients_bp
from app.routes.reports import reports_bp
from app.routes.settings import settings_bp
from app.routes.system import system_bp
from app.routes.treatments import treatments_bp
from app.routes.users import users_bp


def register_blueprints(app):
    for bp in (appointments_bp, audit_bp, auth_bp, bills_bp, doctors_bp,
               lookups_bp, patients_bp, reports_bp, settings_bp, system_bp,
               treatments_bp, users_bp):
        app.register_blueprint(bp)
