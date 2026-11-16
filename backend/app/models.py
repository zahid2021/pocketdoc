from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint

from .database import Base


def now():
    return datetime.now()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    role = Column(String, index=True)  # patient, doctor, receptionist, admin
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, default="")
    password_hash = Column(String, nullable=False)
    password_plain = Column(String, default="")
    active = Column(Boolean, default=True)
    removed = Column(Boolean, default=False)
    city = Column(String, default="Lahore")
    lat = Column(Float, default=31.5204)
    lng = Column(Float, default=74.3587)
    area_district = Column(String, default="")
    area_division = Column(String, default="")
    plan_code = Column(String, default="basic")
    notify_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=now)


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    specialty = Column(String, nullable=False)
    bio = Column(Text, default="")
    experience_years = Column(Integer, default=5)
    fee_note = Column(String, default="Pay at the clinic")
    avg_minutes = Column(Integer, default=6)
    rating_avg = Column(Float, default=0)
    rating_count = Column(Integer, default=0)
    rating_base_avg = Column(Float, default=0)
    rating_base_count = Column(Integer, default=0)
    status = Column(String, default="pending")  # pending, approved, rejected, inactive
    license_no = Column(String, default="")
    hours_text = Column(String, default="Mon – Sat 9:00 AM – 5:00 PM")


class Clinic(Base):
    __tablename__ = "clinics"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    kind = Column(String, default="clinic")  # clinic, hospital
    address = Column(String, default="")
    city = Column(String, default="Lahore")
    district = Column(String, default="")
    division = Column(String, default="")
    lat = Column(Float, default=31.5204)
    lng = Column(Float, default=74.3587)
    phone = Column(String, default="")
    hours_text = Column(String, default="Mon – Sat 9:00 AM – 5:00 PM")


class DoctorClinic(Base):
    __tablename__ = "doctor_clinics"
    id = Column(Integer, primary_key=True)
    doctor_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False)
    __table_args__ = (UniqueConstraint("doctor_user_id", "clinic_id", name="uq_doc_clinic"),)


class ReceptionAssignment(Base):
    __tablename__ = "reception_assignments"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False)
    can_operate_queue = Column(Boolean, default=False)
    __table_args__ = (UniqueConstraint("user_id", "clinic_id", name="uq_recept_clinic"),)


class Token(Base):
    __tablename__ = "tokens"
    id = Column(Integer, primary_key=True)
    number = Column(Integer, nullable=False)
    doctor_user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False)
    patient_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    patient_name = Column(String, nullable=False)
    contact_phone = Column(String, default="")
    status = Column(String, index=True, default="waiting")
    source = Column(String, default="app")  # app, walkin
    day = Column(String, index=True, nullable=False)
    created_at = Column(DateTime, default=now)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    __table_args__ = (UniqueConstraint("doctor_user_id", "day", "number", name="uq_token_num"),)


class QueueState(Base):
    __tablename__ = "queue_states"
    id = Column(Integer, primary_key=True)
    doctor_user_id = Column(Integer, index=True, nullable=False)
    day = Column(String, index=True, nullable=False)
    status = Column(String, default="not_started")  # not_started, running, paused, completed
    pause_reason = Column(String, default="")
    updated_at = Column(DateTime, default=now)
    __table_args__ = (UniqueConstraint("doctor_user_id", "day", name="uq_queue_day"),)


class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True)
    patient_user_id = Column(Integer, index=True, nullable=False)
    doctor_user_id = Column(Integer, index=True, nullable=False)
    __table_args__ = (UniqueConstraint("patient_user_id", "doctor_user_id", name="uq_fav"),)


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    token_id = Column(Integer, unique=True, nullable=False)
    patient_user_id = Column(Integer, nullable=False)
    doctor_user_id = Column(Integer, index=True, nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, default="")
    hidden = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True, nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, default="")
    kind = Column(String, default="info")
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, nullable=True)
    action = Column(String, nullable=False)
    detail = Column(Text, default="")
    created_at = Column(DateTime, default=now)


class Plan(Base):
    __tablename__ = "plans"
    code = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    radius_km = Column(Integer, nullable=False)
    price_pkr = Column(Integer, default=0)
    blurb = Column(String, default="")
    active = Column(Boolean, default=True)
