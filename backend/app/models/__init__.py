"""Models package (MVC: Model layer). Defines the shared SQLAlchemy instance."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from app.models import appointment, bill, doctor, lookup, patient, setting, treatment, user  # noqa: E402,F401
