import math
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from .models import (
    AuditLog,
    Clinic,
    DoctorClinic,
    DoctorProfile,
    Favorite,
    Notification,
    Plan,
    QueueState,
    ReceptionAssignment,
    Review,
    Token,
    User,
)

CITIES = {
    "Lahore": (31.5204, 74.3587),
    "Karachi": (24.8607, 67.0011),
    "Islamabad": (33.6844, 73.0479),
    "Rawalpindi": (33.5651, 73.0169),
    "Faisalabad": (31.4504, 73.1350),
    "Multan": (30.1575, 71.5249),
}

ACTIVE = ("waiting", "checked_in", "in_consultation")
PAUSE_REASONS = ("Lunch Break", "Prayer Time", "Short Delay", "Other")


def today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def distance_km(lat1, lng1, lat2, lng2) -> float:
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def audit(db: Session, actor_id, action: str, detail: str = ""):
    db.add(AuditLog(actor_id=actor_id, action=action, detail=detail))


def notify(db: Session, user_id: int | None, title: str, body: str, kind: str = "info"):
    if not user_id:
        return
    user = db.get(User, user_id)
    if not user or not user.notify_enabled:
        return
    db.add(Notification(user_id=user_id, title=title, body=body, kind=kind))


def plan_radius(db: Session, user: User) -> float:
    plan = db.get(Plan, user.plan_code) if user.plan_code else None
    if not plan or not plan.active:
        plan = db.get(Plan, "basic")
    return float(plan.radius_km if plan else 2)


def primary_clinic(db: Session, doctor_user_id: int) -> Clinic | None:
    link = (
        db.query(DoctorClinic)
        .filter(DoctorClinic.doctor_user_id == doctor_user_id)
        .order_by(DoctorClinic.id)
        .first()
    )
    return db.get(Clinic, link.clinic_id) if link else None


def doctor_ids_for_clinics(db: Session, clinic_ids: list[int]) -> list[int]:
    if not clinic_ids:
        return []
    rows = db.query(DoctorClinic.doctor_user_id).filter(DoctorClinic.clinic_id.in_(clinic_ids)).all()
    return [r[0] for r in rows]


def reception_clinic_ids(db: Session, user_id: int) -> list[int]:
    rows = db.query(ReceptionAssignment.clinic_id).filter(ReceptionAssignment.user_id == user_id).all()
    return [r[0] for r in rows]


def get_queue_state(db: Session, doctor_user_id: int, day: str | None = None, create: bool = False) -> QueueState:
    day = day or today()
    state = (
        db.query(QueueState)
        .filter(QueueState.doctor_user_id == doctor_user_id, QueueState.day == day)
        .first()
    )
    if state:
        return state
    state = QueueState(doctor_user_id=doctor_user_id, day=day, status="not_started", pause_reason="")
    if create:
        db.add(state)
        db.flush()
    return state


def day_tokens(db: Session, doctor_user_id: int, day: str | None = None) -> list[Token]:
    day = day or today()
    return (
        db.query(Token)
        .filter(Token.doctor_user_id == doctor_user_id, Token.day == day, Token.status != "cancelled")
        .order_by(Token.number)
        .all()
    )


def estimate_seconds(tokens: list[Token], my_number: int, avg_minutes: int, state: QueueState, now: datetime) -> int:
    if any(t.number == my_number and t.status == "in_consultation" for t in tokens):
        return 0
    seconds = 0
    avg = max(int(avg_minutes or 6), 1) * 60
    running = state.status == "running"
    for token in tokens:
        if token.number >= my_number:
            continue
        if token.status == "in_consultation":
            if running and token.started_at:
                elapsed = (now - token.started_at).total_seconds()
                seconds += max(avg - elapsed, 0)
            else:
                seconds += avg
        elif token.status in ("waiting", "checked_in"):
            seconds += avg
    return int(seconds)


def public_initials(name: str) -> str:
    parts = [p for p in name.split() if p]
    if not parts:
        return "P"
    if len(parts) == 1:
        return parts[0][:1].upper()
    return (parts[0][:1] + parts[-1][:1]).upper()


def staff_name(name: str) -> str:
    parts = [p for p in (name or "").split() if p]
    if not parts:
        return "Patient"
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} {parts[-1][:1]}."


def recompute_rating(db: Session, doctor_user_id: int):
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_user_id).first()
    if not profile:
        return
    reviews = (
        db.query(Review)
        .filter(Review.doctor_user_id == doctor_user_id, Review.hidden == False)  # noqa: E712
        .all()
    )
    base_n = profile.rating_base_count or 0
    base_avg = profile.rating_base_avg or 0
    total_n = base_n + len(reviews)
    if total_n <= 0:
        profile.rating_avg = 0
        profile.rating_count = 0
        return
    total = base_avg * base_n + sum(r.rating for r in reviews)
    profile.rating_avg = round(total / total_n, 2)
    profile.rating_count = total_n


def doctor_card(db: Session, doctor: User, profile: DoctorProfile, viewer: User | None, now: datetime | None = None):
    now = now or datetime.now()
    clinic = primary_clinic(db, doctor.id)
    state = get_queue_state(db, doctor.id)
    tokens = day_tokens(db, doctor.id)
    waiting = [t for t in tokens if t.status in ("waiting", "checked_in")]
    join_seconds = estimate_seconds(tokens, 10_000, profile.avg_minutes, state, now)
    distance = None
    if viewer and viewer.lat and clinic:
        distance = round(distance_km(viewer.lat, viewer.lng, clinic.lat, clinic.lng), 1)
    elif clinic and viewer is None:
        distance = None
    is_fav = False
    if viewer and viewer.role == "patient":
        is_fav = (
            db.query(Favorite)
            .filter(Favorite.patient_user_id == viewer.id, Favorite.doctor_user_id == doctor.id)
            .first()
            is not None
        )
    return {
        "id": doctor.id,
        "name": doctor.name,
        "specialty": profile.specialty,
        "experience_years": profile.experience_years,
        "bio": profile.bio,
        "fee_note": profile.fee_note,
        "avg_minutes": profile.avg_minutes,
        "hours_text": profile.hours_text or (clinic.hours_text if clinic else ""),
        "rating": profile.rating_avg,
        "rating_count": profile.rating_count,
        "status": profile.status,
        "clinic": None
        if not clinic
        else {
            "id": clinic.id,
            "name": clinic.name,
            "kind": clinic.kind,
            "address": clinic.address,
            "city": clinic.city,
            "district": clinic.district or "",
            "division": clinic.division or "",
            "lat": clinic.lat,
            "lng": clinic.lng,
            "phone": clinic.phone,
            "hours_text": clinic.hours_text,
        },
        "queue_status": state.status,
        "pause_reason": state.pause_reason or "",
        "waiting_count": len(waiting),
        "est_seconds": join_seconds,
        "distance_km": distance,
        "can_book": (not viewer or viewer.role != "patient" or not clinic or within_radius(db, viewer, clinic)),
        "outside_plan": bool(viewer and viewer.role == "patient" and clinic and not within_radius(db, viewer, clinic)),
        "is_favorite": is_fav,
        "initials": public_initials(doctor.name),
    }


def within_radius(db: Session, patient: User, clinic: Clinic) -> bool:
    radius = plan_radius(db, patient)
    dist = distance_km(patient.lat, patient.lng, clinic.lat, clinic.lng)
    return dist <= radius + 0.05


def same_district(patient: User, clinic: Clinic) -> bool:
    district = (patient.area_district or "").strip().lower()
    clinic_district = (clinic.district or "").strip().lower()
    return bool(district and clinic_district and district == clinic_district)


def ensure_patient_can_see(db: Session, patient: User, doctor_user_id: int):
    clinic = primary_clinic(db, doctor_user_id)
    if not clinic:
        raise HTTPException(404, "Clinic not found")
    if not within_radius(db, patient, clinic):
        radius = plan_radius(db, patient)
        raise HTTPException(403, f"This clinic is outside your {int(radius)} km plan")
    return clinic


def public_queue(tokens: list[Token], profile: DoctorProfile, state: QueueState, viewer_id: int | None, now: datetime):
    rows = []
    for token in tokens:
        if token.status in ("cancelled",):
            continue
        if token.status in ("completed", "no_show") and token.number:
            # keep a short recent tail out of the live list
            continue
        if token.status not in ACTIVE:
            continue
        rows.append(
            {
                "number": token.number,
                "status": token.status,
                "est_seconds": estimate_seconds(tokens, token.number, profile.avg_minutes, state, now),
                "is_you": bool(viewer_id and token.patient_user_id == viewer_id),
                "started_at": token.started_at.isoformat() if token.started_at else None,
            }
        )
    return rows


def book_token(db: Session, patient: User, doctor_user_id: int, clinic_id: int | None = None) -> Token:
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_user_id).first()
    doctor = db.get(User, doctor_user_id)
    if not doctor or not profile or profile.status != "approved" or not doctor.active:
        raise HTTPException(404, "Doctor is not available")
    clinic = db.get(Clinic, clinic_id) if clinic_id else primary_clinic(db, doctor_user_id)
    if not clinic:
        raise HTTPException(404, "Clinic not found")
    link = (
        db.query(DoctorClinic)
        .filter(DoctorClinic.doctor_user_id == doctor_user_id, DoctorClinic.clinic_id == clinic.id)
        .first()
    )
    if not link:
        raise HTTPException(400, "Doctor is not at this clinic")
    if not within_radius(db, patient, clinic):
        radius = plan_radius(db, patient)
        raise HTTPException(403, f"This clinic is outside your {int(radius)} km plan")
    day = today()
    existing = (
        db.query(Token)
        .filter(
            Token.patient_user_id == patient.id,
            Token.doctor_user_id == doctor_user_id,
            Token.day == day,
            Token.status.in_(ACTIVE),
        )
        .first()
    )
    if existing:
        raise HTTPException(409, f"You already have token #{existing.number} for this doctor today")
    last = (
        db.query(Token)
        .filter(Token.doctor_user_id == doctor_user_id, Token.day == day)
        .order_by(Token.number.desc())
        .first()
    )
    number = (last.number if last else 10) + 1
    token = Token(
        number=number,
        doctor_user_id=doctor_user_id,
        clinic_id=clinic.id,
        patient_user_id=patient.id,
        patient_name=patient.name,
        contact_phone=patient.phone or "",
        status="waiting",
        source="app",
        day=day,
    )
    db.add(token)
    state = get_queue_state(db, doctor_user_id, day, create=True)
    if state.status == "completed":
        state.status = "running"
        state.updated_at = datetime.now()
    notify(
        db,
        patient.id,
        "Token confirmed",
        f"Your token for {doctor.name} is #{number}. We will update you as the queue moves.",
        "token",
    )
    notify(
        db,
        doctor.id,
        "New token",
        f"Token #{number} joined your queue.",
        "queue",
    )
    for assignment in db.query(ReceptionAssignment).filter(ReceptionAssignment.clinic_id == clinic.id).all():
        notify(db, assignment.user_id, "New token", f"Token #{number} booked with {doctor.name}.", "queue")
    audit(db, patient.id, "token.book", f"doctor={doctor_user_id} token=#{number}")
    db.flush()
    return token


def walk_in(db: Session, actor: User, doctor_user_id: int, clinic: Clinic, name: str, phone: str) -> Token:
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_user_id).first()
    doctor = db.get(User, doctor_user_id)
    if not doctor or not profile or profile.status != "approved":
        raise HTTPException(404, "Doctor is not available")
    link = (
        db.query(DoctorClinic)
        .filter(DoctorClinic.doctor_user_id == doctor_user_id, DoctorClinic.clinic_id == clinic.id)
        .first()
    )
    if not link:
        raise HTTPException(400, "That doctor does not work at your clinic")
    day = today()
    patient = None
    if phone:
        patient = db.query(User).filter(User.phone == phone, User.role == "patient", User.active == True).first()  # noqa: E712
        if patient:
            existing = (
                db.query(Token)
                .filter(
                    Token.patient_user_id == patient.id,
                    Token.doctor_user_id == doctor_user_id,
                    Token.day == day,
                    Token.status.in_(ACTIVE),
                )
                .first()
            )
            if existing:
                raise HTTPException(409, f"This patient already has token #{existing.number}")
    last = (
        db.query(Token)
        .filter(Token.doctor_user_id == doctor_user_id, Token.day == day)
        .order_by(Token.number.desc())
        .first()
    )
    number = (last.number if last else 10) + 1
    token = Token(
        number=number,
        doctor_user_id=doctor_user_id,
        clinic_id=clinic.id,
        patient_user_id=patient.id if patient else None,
        patient_name=patient.name if patient else name.strip(),
        contact_phone=phone or (patient.phone if patient else ""),
        status="checked_in",
        source="walkin",
        day=day,
    )
    db.add(token)
    state = get_queue_state(db, doctor_user_id, day, create=True)
    if state.status == "completed":
        state.status = "running"
    if patient:
        notify(db, patient.id, "Token issued at reception", f"Your token for {doctor.name} is #{number}.", "token")
    notify(db, doctor.id, "Walk-in added", f"Token #{number} was added at reception.", "queue")
    audit(db, actor.id, "token.walkin", f"doctor={doctor_user_id} token=#{number} name={token.patient_name}")
    db.flush()
    return token


def _guard_queue_control(state: QueueState, action: str):
    if action == "next" and state.status == "paused":
        raise HTTPException(400, "Resume the queue before calling the next patient")
    if action == "next" and state.status == "not_started":
        raise HTTPException(400, "Start the queue first")


def start_queue(db: Session, actor: User, doctor_user_id: int):
    state = get_queue_state(db, doctor_user_id, create=True)
    now = datetime.now()
    state.status = "running"
    state.pause_reason = ""
    state.updated_at = now
    tokens = day_tokens(db, doctor_user_id)
    if not any(t.status == "in_consultation" for t in tokens):
        nxt = next((t for t in tokens if t.status in ("checked_in", "waiting")), None)
        if nxt:
            nxt.status = "in_consultation"
            nxt.started_at = now
            notify(db, nxt.patient_user_id, "It's your turn", f"Token #{nxt.number}, please come in.", "turn")
    audit(db, actor.id, "queue.start", f"doctor={doctor_user_id}")
    _notify_waiting_estimates(db, doctor_user_id)
    return state


def pause_queue(db: Session, actor: User, doctor_user_id: int, reason: str):
    if reason not in PAUSE_REASONS:
        raise HTTPException(400, "Choose a pause reason")
    state = get_queue_state(db, doctor_user_id, create=True)
    if state.status == "not_started":
        raise HTTPException(400, "Start the queue before pausing it")
    state.status = "paused"
    state.pause_reason = reason
    state.updated_at = datetime.now()
    doctor = db.get(User, doctor_user_id)
    for token in day_tokens(db, doctor_user_id):
        if token.status in ACTIVE:
            notify(
                db,
                token.patient_user_id,
                "Queue paused",
                f"{doctor.name if doctor else 'The doctor'} paused the queue ({reason}). Your estimated wait is on hold.",
                "pause",
            )
    audit(db, actor.id, "queue.pause", f"doctor={doctor_user_id} reason={reason}")
    return state


def resume_queue(db: Session, actor: User, doctor_user_id: int):
    state = get_queue_state(db, doctor_user_id, create=True)
    if state.status != "paused":
        raise HTTPException(400, "The queue is not paused")
    state.status = "running"
    state.pause_reason = ""
    state.updated_at = datetime.now()
    doctor = db.get(User, doctor_user_id)
    for token in day_tokens(db, doctor_user_id):
        if token.status in ACTIVE:
            notify(
                db,
                token.patient_user_id,
                "Queue resumed",
                f"{doctor.name if doctor else 'The doctor'} is seeing patients again.",
                "resume",
            )
    audit(db, actor.id, "queue.resume", f"doctor={doctor_user_id}")
    _notify_waiting_estimates(db, doctor_user_id)
    return state


def next_patient(db: Session, actor: User, doctor_user_id: int):
    state = get_queue_state(db, doctor_user_id, create=True)
    _guard_queue_control(state, "next")
    now = datetime.now()
    tokens = day_tokens(db, doctor_user_id)
    current = next((t for t in tokens if t.status == "in_consultation"), None)
    if current:
        current.status = "completed"
        current.completed_at = now
        notify(
            db,
            current.patient_user_id,
            "Visit completed",
            "Your visit is marked complete. Please rate the visit.",
            "done",
        )
    nxt = next((t for t in tokens if t.status in ("checked_in", "waiting") and (not current or t.number != current.number)), None)
    if nxt:
        nxt.status = "in_consultation"
        nxt.started_at = now
        notify(db, nxt.patient_user_id, "It's your turn", f"Token #{nxt.number}, please come in.", "turn")
        follower = next((t for t in tokens if t.number > nxt.number and t.status in ("waiting", "checked_in")), None)
        if follower:
            notify(
                db,
                follower.patient_user_id,
                "You are next",
                f"Token #{follower.number}. One patient is ahead of you.",
                "soon",
            )
        state.status = "running"
    else:
        state.status = "completed"
    state.updated_at = now
    audit(db, actor.id, "queue.next", f"doctor={doctor_user_id}")
    return state


def _notify_waiting_estimates(db: Session, doctor_user_id: int):
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_user_id).first()
    doctor = db.get(User, doctor_user_id)
    state = get_queue_state(db, doctor_user_id)
    now = datetime.now()
    tokens = day_tokens(db, doctor_user_id)
    if not profile:
        return
    for token in tokens:
        if token.status not in ("waiting", "checked_in"):
            continue
        seconds = estimate_seconds(tokens, token.number, profile.avg_minutes, state, now)
        minutes = max(1, round(seconds / 60)) if seconds else 0
        ahead = sum(1 for t in tokens if t.number < token.number and t.status in ACTIVE)
        if ahead <= 2:
            notify(
                db,
                token.patient_user_id,
                "Queue update",
                f"{doctor.name if doctor else 'Your doctor'}: {ahead} ahead, about {minutes} min.",
                "queue",
            )


def assert_doctor_self(user: User, doctor_user_id: int):
    if user.role == "admin":
        return
    if user.role == "doctor" and user.id == doctor_user_id:
        return
    raise HTTPException(403, "You can only manage your own queue")


def assert_reception_doctor(db: Session, user: User, doctor_user_id: int) -> Clinic:
    clinic_ids = reception_clinic_ids(db, user.id)
    link = (
        db.query(DoctorClinic)
        .filter(DoctorClinic.doctor_user_id == doctor_user_id, DoctorClinic.clinic_id.in_(clinic_ids or [-1]))
        .first()
    )
    if not link:
        raise HTTPException(403, "This doctor is not assigned to your clinic")
    clinic = db.get(Clinic, link.clinic_id)
    return clinic


def reception_can_operate(db: Session, user: User, clinic_id: int) -> bool:
    row = (
        db.query(ReceptionAssignment)
        .filter(ReceptionAssignment.user_id == user.id, ReceptionAssignment.clinic_id == clinic_id)
        .first()
    )
    return bool(row and row.can_operate_queue)


def token_patient_view(db: Session, token: Token, viewer: User):
    doctor = db.get(User, token.doctor_user_id)
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == token.doctor_user_id).first()
    clinic = db.get(Clinic, token.clinic_id)
    state = get_queue_state(db, token.doctor_user_id, token.day)
    now = datetime.now()
    tokens = day_tokens(db, token.doctor_user_id, token.day) if token.day == today() else []
    ahead = sum(1 for t in tokens if t.number < token.number and t.status in ACTIVE)
    est = estimate_seconds(tokens, token.number, profile.avg_minutes if profile else 6, state, now) if tokens else 0
    review = db.query(Review).filter(Review.token_id == token.id).first()
    return {
        "id": token.id,
        "number": token.number,
        "status": token.status,
        "source": token.source,
        "day": token.day,
        "ahead": ahead,
        "est_seconds": est,
        "ticking": state.status == "running" and token.status in ("waiting", "checked_in"),
        "queue_status": state.status,
        "pause_reason": state.pause_reason or "",
        "needs_review": token.status == "completed" and review is None and token.patient_user_id == viewer.id,
        "review": None
        if not review
        else {"rating": review.rating, "comment": review.comment, "hidden": review.hidden},
        "doctor": {
            "id": doctor.id,
            "name": doctor.name,
            "specialty": profile.specialty if profile else "",
            "avg_minutes": profile.avg_minutes if profile else 6,
            "initials": public_initials(doctor.name),
        },
        "clinic": None
        if not clinic
        else {"id": clinic.id, "name": clinic.name, "address": clinic.address, "city": clinic.city},
        "created_at": token.created_at.isoformat() if token.created_at else None,
    }


def staff_token_row(token: Token, tokens: list[Token], profile: DoctorProfile, state: QueueState, now: datetime, full: bool):
    row = {
        "id": token.id,
        "number": token.number,
        "status": token.status,
        "source": token.source,
        "est_seconds": estimate_seconds(tokens, token.number, profile.avg_minutes if profile else 6, state, now)
        if token.status in ACTIVE
        else 0,
        "started_at": token.started_at.isoformat() if token.started_at else None,
        "patient_name": token.patient_name if full else staff_name(token.patient_name),
    }
    if full:
        row["phone"] = token.contact_phone or ""
        row["patient_user_id"] = token.patient_user_id
    return row
