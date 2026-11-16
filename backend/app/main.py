from datetime import datetime
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from .database import Base, engine, ensure_columns, get_db
from .models import (
    AuditLog,
    Clinic,
    DoctorClinic,
    DoctorProfile,
    Favorite,
    Notification,
    Plan,
    ReceptionAssignment,
    Review,
    Token,
    User,
)
from .security import get_current, hash_password, make_token, optional_user, require, verify_password
from .punjab import find_place, in_pakistan, nearest_place, province_center, province_for_division, search_local, search_streets
from .seed import ensure_punjab, remember_known_passwords, seed
from .services import (
    CITIES,
    PAUSE_REASONS,
    assert_reception_doctor,
    audit,
    book_token,
    day_tokens,
    distance_km,
    doctor_card,
    doctor_ids_for_clinics,
    ensure_patient_can_see,
    get_queue_state,
    next_patient,
    notify,
    pause_queue,
    plan_radius,
    primary_clinic,
    same_district,
    public_queue,
    reception_can_operate,
    reception_clinic_ids,
    recompute_rating,
    resume_queue,
    staff_token_row,
    start_queue,
    today,
    token_patient_view,
    walk_in,
    within_radius,
)

app = FastAPI(title="PocketDoc API", docs_url="/api/docs", openapi_url="/api/openapi.json")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    ensure_columns()
    db = next(get_db())
    try:
        seed(db)
        ensure_punjab(db)
        remember_known_passwords(db)
    finally:
        db.close()


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str
    phone: str = ""
    password: str = Field(min_length=6, max_length=80)
    city: str = "Lahore"
    lat: float | None = None
    lng: float | None = None
    district: str = ""
    division: str = ""


class PlaceIn(BaseModel):
    name: str
    lat: float
    lng: float
    district: str = ""
    division: str = ""


class LoginIn(BaseModel):
    email: str
    password: str


class ProfileIn(BaseModel):
    name: str | None = None
    phone: str | None = None
    city: str | None = None
    notify_enabled: bool | None = None


class LocationIn(BaseModel):
    lat: float
    lng: float


class PlanIn(BaseModel):
    plan_code: str


class BookIn(BaseModel):
    doctor_id: int
    clinic_id: int | None = None


class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = ""


class PauseIn(BaseModel):
    reason: str


class OperateIn(BaseModel):
    reason: str | None = None


class DoctorSettingsIn(BaseModel):
    avg_minutes: int | None = Field(default=None, ge=3, le=60)
    bio: str | None = None
    fee_note: str | None = None
    hours_text: str | None = None


class WalkIn(BaseModel):
    doctor_id: int
    name: str = Field(min_length=2, max_length=80)
    phone: str = ""


class StatusIn(BaseModel):
    status: str


class DoctorRegisterIn(BaseModel):
    name: str
    email: str
    phone: str = ""
    password: str = Field(min_length=6)
    specialty: str
    license_no: str = ""
    clinic_name: str
    clinic_kind: str = "clinic"
    address: str
    city: str = "Lahore"
    lat: float | None = None
    lng: float | None = None
    district: str = ""
    division: str = ""


class ClinicIn(BaseModel):
    name: str
    kind: str = "clinic"
    address: str = ""
    city: str = "Lahore"
    lat: float | None = None
    lng: float | None = None
    district: str = ""
    division: str = ""
    phone: str = ""
    hours_text: str = "Mon – Sat 9:00 AM – 5:00 PM"


class ReceptionIn(BaseModel):
    name: str
    email: str
    phone: str = ""
    password: str = Field(min_length=6)
    clinic_id: int
    can_operate_queue: bool = False


class PermissionIn(BaseModel):
    can_operate_queue: bool


class AdminPlanIn(BaseModel):
    name: str | None = None
    radius_km: int | None = None
    price_pkr: int | None = None
    blurb: str | None = None
    active: bool | None = None


def user_out(db: Session, user: User):
    plan = db.get(Plan, user.plan_code) if user.plan_code else None
    profile = None
    if user.role == "doctor":
        doc = db.query(DoctorProfile).filter(DoctorProfile.user_id == user.id).first()
        clinic = primary_clinic(db, user.id)
        profile = {
            "specialty": doc.specialty if doc else "",
            "status": doc.status if doc else "",
            "avg_minutes": doc.avg_minutes if doc else 6,
            "bio": doc.bio if doc else "",
            "fee_note": doc.fee_note if doc else "",
            "hours_text": doc.hours_text if doc else "",
            "license_no": doc.license_no if doc else "",
            "clinic_id": clinic.id if clinic else None,
        }
    clinics = []
    if user.role == "receptionist":
        ids = reception_clinic_ids(db, user.id)
        for cid in ids:
            clinic = db.get(Clinic, cid)
            assignment = (
                db.query(ReceptionAssignment)
                .filter(ReceptionAssignment.user_id == user.id, ReceptionAssignment.clinic_id == cid)
                .first()
            )
            if clinic:
                clinics.append(
                    {
                        "id": clinic.id,
                        "name": clinic.name,
                        "kind": clinic.kind,
                        "city": clinic.city,
                        "can_operate_queue": bool(assignment and assignment.can_operate_queue),
                    }
                )
    return {
        "id": user.id,
        "role": user.role,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "city": user.city,
        "lat": user.lat,
        "lng": user.lng,
        "area_district": user.area_district or "",
        "area_division": user.area_division or "",
        "plan_code": user.plan_code,
        "plan": None
        if not plan
        else {"code": plan.code, "name": plan.name, "radius_km": plan.radius_km, "price_pkr": plan.price_pkr},
        "notify_enabled": user.notify_enabled,
        "doctor": profile,
        "clinics": clinics,
    }


def auth_response(db: Session, user: User):
    return {"token": make_token(user), "user": user_out(db, user)}


def resolved_place(name: str, lat: float | None = None, lng: float | None = None, district: str = "", division: str = ""):
    if lat is not None and lng is not None:
        near = nearest_place(lat, lng)
        return {
            "name": (name or "").strip() or (near["name"] if near else "Pakistan"),
            "lat": lat,
            "lng": lng,
            "district": district or (near["district"] if near else ""),
            "division": division or (near["division"] if near else ""),
        }
    found = find_place(name)
    if not found:
        raise HTTPException(400, "Choose a place in Pakistan — city, town, basti or street")
    return found


def apply_place(user: User, place: dict):
    user.city = place["name"]
    user.lat = place["lat"]
    user.lng = place["lng"]
    user.area_district = place.get("district") or ""
    user.area_division = place.get("division") or ""


@app.get("/api/places")
def places(q: str = ""):
    local = search_local(q, 8)
    streets = search_streets(q) if len(q.strip()) >= 3 else []
    seen = set()
    results = []
    for place in local + streets:
        key = (round(place["lat"], 3), round(place["lng"], 3), place["name"].lower())
        if key in seen:
            continue
        seen.add(key)
        results.append(place)
    return results[:10]


@app.post("/api/me/place")
def set_place(body: PlaceIn, user: User = Depends(require("patient")), db: Session = Depends(get_db)):
    if not (-90 <= body.lat <= 90 and -180 <= body.lng <= 180):
        raise HTTPException(400, "Location is not valid")
    apply_place(user, resolved_place(body.name, body.lat, body.lng, body.district, body.division))
    audit(db, user.id, "patient.place", user.city)
    db.commit()
    return user_out(db, user)


@app.get("/api/map")
def clinic_map(
    lat: float | None = None,
    lng: float | None = None,
    district: str = "",
    division: str = "",
    province: str = "",
    viewer: User | None = Depends(optional_user),
    db: Session = Depends(get_db),
):
    if province:
        district = ""
        division = ""
    origin_lat = lat if lat is not None else (viewer.lat if viewer else 30.0)
    origin_lng = lng if lng is not None else (viewer.lng if viewer else 69.0)
    if province and lat is None:
        center = province_center(province)
        if center:
            origin_lat, origin_lng = center["lat"], center["lng"]
    district = district or ("" if province else (viewer.area_district if viewer and viewer.role == "patient" else ""))
    division = division or ""
    now = datetime.now()
    rows = (
        db.query(User, DoctorProfile)
        .join(DoctorProfile, DoctorProfile.user_id == User.id)
        .filter(User.role == "doctor", User.active == True, DoctorProfile.status == "approved")  # noqa: E712
        .all()
    )
    results = []
    for doctor, profile in rows:
        clinic = primary_clinic(db, doctor.id)
        if not clinic:
            continue
        dist = distance_km(origin_lat, origin_lng, clinic.lat, clinic.lng)
        same_div = division and (clinic.division or "") == division
        same_dis = district and (clinic.district or "") == district
        if province:
            if province_for_division(clinic.division) != province:
                continue
        elif division:
            if not same_div:
                continue
        elif district:
            if not (same_dis or dist <= 35):
                continue
        elif lat is None and lng is None:
            if not in_pakistan(clinic.lat, clinic.lng):
                continue
        elif dist > 80:
            continue
        card = doctor_card(db, doctor, profile, viewer if viewer and viewer.role == "patient" else None, now)
        card["distance_km"] = round(dist, 1)
        results.append(card)
    results.sort(key=lambda card: card["distance_km"])
    zoom = 6 if province else 8 if division else 12 if district else 5
    return {
        "center": {"lat": origin_lat, "lng": origin_lng},
        "district": district,
        "division": division,
        "province": province,
        "zoom": zoom,
        "results": results,
    }


@app.get("/api/health")
def health():
    return {"ok": True, "service": "pocketdoc"}


@app.get("/api/meta")
def meta(db: Session = Depends(get_db)):
    plans = db.query(Plan).filter(Plan.active == True).order_by(Plan.radius_km).all()  # noqa: E712
    return {
        "cities": [place["name"] for place in search_local("")],
        "pause_reasons": list(PAUSE_REASONS),
        "plans": [
            {"code": p.code, "name": p.name, "radius_km": p.radius_km, "price_pkr": p.price_pkr, "blurb": p.blurb}
            for p in plans
        ],
        "brand": {
            "name": "PocketDoc",
            "tagline": "Your Turn. Our Priority.",
            "line": "Ab wait nahi, sirf update.",
        },
    }


@app.post("/api/auth/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "An account with this email already exists")
    place = resolved_place(body.city, body.lat, body.lng, body.district, body.division)
    user = User(
        role="patient",
        name=body.name.strip(),
        email=email,
        phone=body.phone.strip(),
        password_hash=hash_password(body.password),
        password_plain=body.password,
        city=place["name"],
        lat=place["lat"],
        lng=place["lng"],
        area_district=place.get("district") or "",
        area_division=place.get("division") or "",
        plan_code="basic",
    )
    db.add(user)
    audit(db, None, "patient.register", email)
    db.commit()
    db.refresh(user)
    return auth_response(db, user)


@app.post("/api/auth/register-doctor")
def register_doctor(body: DoctorRegisterIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "An account with this email already exists")
    if body.clinic_kind not in ("clinic", "hospital"):
        raise HTTPException(400, "Clinic type must be clinic or hospital")
    place = resolved_place(body.city, body.lat, body.lng, body.district, body.division)
    city, lat, lng = place["name"], place["lat"], place["lng"]
    user = User(
        role="doctor",
        name=body.name.strip(),
        email=email,
        phone=body.phone.strip(),
        password_hash=hash_password(body.password),
        password_plain=body.password,
        city=city,
        lat=lat,
        lng=lng,
        area_district=place.get("district") or "",
        area_division=place.get("division") or "",
    )
    db.add(user)
    db.flush()
    clinic = Clinic(
        name=body.clinic_name.strip(),
        kind=body.clinic_kind,
        address=body.address.strip(),
        city=city,
        district=place.get("district") or "",
        division=place.get("division") or "",
        lat=lat,
        lng=lng,
        phone=body.phone.strip(),
    )
    db.add(clinic)
    db.flush()
    db.add(
        DoctorProfile(
            user_id=user.id,
            specialty=body.specialty.strip(),
            license_no=body.license_no.strip(),
            status="pending",
            bio="Pending admin approval.",
            fee_note="Pay at the clinic.",
        )
    )
    db.add(DoctorClinic(doctor_user_id=user.id, clinic_id=clinic.id))
    audit(db, user.id, "doctor.register", f"{email} clinic={clinic.name}")
    db.commit()
    return {"ok": True, "message": "Request sent. You can sign in after an admin approves the clinic."}


@app.post("/api/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Email or password is incorrect")
    if user.removed:
        raise HTTPException(403, "This account has been removed")
    if not user.active:
        raise HTTPException(403, "This account is deactivated")
    if user.role == "doctor":
        profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == user.id).first()
        if profile and profile.status == "pending":
            raise HTTPException(403, "Your clinic is waiting for admin approval")
        if profile and profile.status in ("rejected", "inactive"):
            raise HTTPException(403, "This doctor account is not active")
    return auth_response(db, user)


@app.get("/api/me")
def me(user: User = Depends(get_current), db: Session = Depends(get_db)):
    return user_out(db, user)


@app.patch("/api/me")
def update_me(body: ProfileIn, user: User = Depends(get_current), db: Session = Depends(get_db)):
    if body.name:
        user.name = body.name.strip()
    if body.phone is not None:
        user.phone = body.phone.strip()
    if body.city:
        apply_place(user, resolved_place(body.city))
    if body.notify_enabled is not None:
        user.notify_enabled = body.notify_enabled
    db.commit()
    return user_out(db, user)


@app.post("/api/me/location")
def update_location(body: LocationIn, user: User = Depends(require("patient")), db: Session = Depends(get_db)):
    if not (-90 <= body.lat <= 90 and -180 <= body.lng <= 180):
        raise HTTPException(400, "Location is not valid")
    near = nearest_place(body.lat, body.lng)
    user.lat = body.lat
    user.lng = body.lng
    if near:
        user.area_district = near["district"]
        user.area_division = near["division"]
        user.city = near["name"]
    audit(db, user.id, "patient.location", f"{body.lat:.4f},{body.lng:.4f}")
    db.commit()
    return user_out(db, user)


@app.post("/api/me/plan")
def choose_plan(body: PlanIn, user: User = Depends(require("patient")), db: Session = Depends(get_db)):
    plan = db.get(Plan, body.plan_code)
    if not plan or not plan.active:
        raise HTTPException(404, "Plan not found")
    user.plan_code = plan.code
    audit(db, user.id, "patient.plan", plan.code)
    notify(db, user.id, "Search radius updated", f"Your plan is now {plan.name} ({plan.radius_km} km).", "plan")
    db.commit()
    return user_out(db, user)


def _visible_doctors(db: Session, viewer: User | None):
    rows = (
        db.query(User, DoctorProfile)
        .join(DoctorProfile, DoctorProfile.user_id == User.id)
        .filter(User.role == "doctor", User.active == True, DoctorProfile.status == "approved")  # noqa: E712
        .all()
    )
    now = datetime.now()
    cards = []
    for doctor, profile in rows:
        clinic = primary_clinic(db, doctor.id)
        if viewer and viewer.role == "patient":
            if not clinic or not (within_radius(db, viewer, clinic) or same_district(viewer, clinic)):
                continue
        card = doctor_card(db, doctor, profile, viewer, now)
        if viewer and viewer.role == "patient" and clinic:
            card["distance_km"] = round(distance_km(viewer.lat, viewer.lng, clinic.lat, clinic.lng), 1)
        cards.append(card)
    cards.sort(key=lambda c: (c["distance_km"] is None, c["distance_km"] or 0, -c["rating"]))
    return cards


@app.get("/api/doctors/featured")
def featured(viewer: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    rows = (
        db.query(User, DoctorProfile)
        .join(DoctorProfile, DoctorProfile.user_id == User.id)
        .filter(User.role == "doctor", DoctorProfile.status == "approved")
        .all()
    )
    now = datetime.now()
    cards = []
    for doctor, profile in rows:
        clinic = primary_clinic(db, doctor.id)
        if not clinic:
            continue
        if viewer and viewer.role == "patient" and not (within_radius(db, viewer, clinic) or same_district(viewer, clinic)):
            continue
        card = doctor_card(db, doctor, profile, viewer if viewer and viewer.role == "patient" else None, now)
        cards.append(card)
    cards.sort(key=lambda c: -c["rating"])
    if viewer and viewer.role == "patient":
        return cards[:4]
    picked = []
    seen = set()
    for card in cards:
        city = (card.get("clinic") or {}).get("city") or ""
        if city in seen:
            continue
        seen.add(city)
        picked.append(card)
        if len(picked) == 4:
            break
    return picked


@app.get("/api/doctors")
def search_doctors(
    q: str = "",
    kind: str = "all",
    user: User = Depends(require("patient")),
    db: Session = Depends(get_db),
):
    needle = q.strip().lower()
    cards = []
    for card in _visible_doctors(db, user):
        if kind in ("clinic", "hospital") and (not card["clinic"] or card["clinic"]["kind"] != kind):
            continue
        blob = " ".join(
            [
                card["name"],
                card["specialty"],
                card["clinic"]["name"] if card["clinic"] else "",
                card["clinic"]["address"] if card["clinic"] else "",
                card["clinic"]["city"] if card["clinic"] else "",
            ]
        ).lower()
        if needle and needle not in blob:
            continue
        cards.append(card)
    return {
        "radius_km": plan_radius(db, user),
        "city": user.city,
        "results": cards,
    }


@app.get("/api/doctors/{doctor_id}")
def doctor_detail(doctor_id: int, viewer: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    doctor = db.get(User, doctor_id)
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_id).first()
    if not doctor or not profile or doctor.role != "doctor":
        raise HTTPException(404, "Doctor not found")
    if profile.status != "approved" and not (viewer and viewer.role in ("admin", "doctor") and (viewer.role == "admin" or viewer.id == doctor.id)):
        raise HTTPException(404, "Doctor not found")
    now = datetime.now()
    card = doctor_card(db, doctor, profile, viewer, now)
    state = get_queue_state(db, doctor.id)
    tokens = day_tokens(db, doctor.id)
    card["queue"] = public_queue(tokens, profile, state, viewer.id if viewer else None, now)
    card["current_number"] = next((t.number for t in tokens if t.status == "in_consultation"), None)
    reviews = (
        db.query(Review)
        .filter(Review.doctor_user_id == doctor.id, Review.hidden == False)  # noqa: E712
        .order_by(Review.created_at.desc())
        .limit(8)
        .all()
    )
    card["reviews"] = []
    for review in reviews:
        author = db.get(User, review.patient_user_id)
        card["reviews"].append(
            {
                "rating": review.rating,
                "comment": review.comment,
                "author": (author.name.split()[0] if author else "Patient"),
                "created_at": review.created_at.isoformat() if review.created_at else None,
            }
        )
    return card


@app.post("/api/doctors/{doctor_id}/favorite")
def toggle_favorite(doctor_id: int, user: User = Depends(require("patient")), db: Session = Depends(get_db)):
    if not primary_clinic(db, doctor_id):
        raise HTTPException(404, "Clinic not found")
    row = (
        db.query(Favorite)
        .filter(Favorite.patient_user_id == user.id, Favorite.doctor_user_id == doctor_id)
        .first()
    )
    if row:
        db.delete(row)
        saved = False
    else:
        db.add(Favorite(patient_user_id=user.id, doctor_user_id=doctor_id))
        saved = True
    db.commit()
    return {"is_favorite": saved}


@app.get("/api/favorites")
def favorites(user: User = Depends(require("patient")), db: Session = Depends(get_db)):
    ids = [r.doctor_user_id for r in db.query(Favorite).filter(Favorite.patient_user_id == user.id).all()]
    return [card for card in _visible_doctors(db, user) if card["id"] in ids]


@app.post("/api/tokens")
def create_token(body: BookIn, user: User = Depends(require("patient")), db: Session = Depends(get_db)):
    token = book_token(db, user, body.doctor_id, body.clinic_id)
    db.commit()
    db.refresh(token)
    return token_patient_view(db, token, user)


@app.get("/api/tokens/mine")
def my_tokens(user: User = Depends(require("patient")), db: Session = Depends(get_db)):
    rows = (
        db.query(Token)
        .filter(Token.patient_user_id == user.id)
        .order_by(Token.created_at.desc())
        .all()
    )
    return [token_patient_view(db, token, user) for token in rows]


@app.post("/api/tokens/{token_id}/cancel")
def cancel_token(token_id: int, user: User = Depends(require("patient")), db: Session = Depends(get_db)):
    token = db.get(Token, token_id)
    if not token or token.patient_user_id != user.id:
        raise HTTPException(404, "Token not found")
    if token.status not in ("waiting", "checked_in"):
        raise HTTPException(400, "This token can no longer be cancelled")
    token.status = "cancelled"
    audit(db, user.id, "token.cancel", f"token={token.id}")
    notify(db, token.doctor_user_id, "Token cancelled", f"Token #{token.number} was cancelled.", "queue")
    db.commit()
    return token_patient_view(db, token, user)


@app.post("/api/tokens/{token_id}/review")
def review_token(token_id: int, body: ReviewIn, user: User = Depends(require("patient")), db: Session = Depends(get_db)):
    token = db.get(Token, token_id)
    if not token or token.patient_user_id != user.id:
        raise HTTPException(404, "Token not found")
    if token.status != "completed":
        raise HTTPException(400, "You can rate a visit only after it is completed")
    if db.query(Review).filter(Review.token_id == token.id).first():
        raise HTTPException(409, "This visit already has a review")
    db.add(
        Review(
            token_id=token.id,
            patient_user_id=user.id,
            doctor_user_id=token.doctor_user_id,
            rating=body.rating,
            comment=body.comment.strip()[:500],
        )
    )
    recompute_rating(db, token.doctor_user_id)
    audit(db, user.id, "review.create", f"token={token.id} rating={body.rating}")
    db.commit()
    return token_patient_view(db, token, user)


@app.get("/api/notifications")
def notifications(user: User = Depends(get_current), db: Session = Depends(get_db)):
    rows = (
        db.query(Notification)
        .filter(Notification.user_id == user.id)
        .order_by(Notification.created_at.desc())
        .limit(40)
        .all()
    )
    return [
        {
            "id": n.id,
            "title": n.title,
            "body": n.body,
            "kind": n.kind,
            "read": n.read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in rows
    ]


@app.post("/api/notifications/read")
def read_notifications(user: User = Depends(get_current), db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.user_id == user.id, Notification.read == False).update(  # noqa: E712
        {"read": True}
    )
    db.commit()
    return {"ok": True}


def _doctor_dashboard(db: Session, doctor_user_id: int, full_names: bool):
    doctor = db.get(User, doctor_user_id)
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_user_id).first()
    if not doctor or not profile:
        raise HTTPException(404, "Doctor not found")
    state = get_queue_state(db, doctor_user_id)
    now = datetime.now()
    tokens = db.query(Token).filter(Token.doctor_user_id == doctor_user_id, Token.day == today()).order_by(Token.number).all()
    active = [t for t in tokens if t.status != "cancelled"]
    return {
        "doctor": {"id": doctor.id, "name": doctor.name, "specialty": profile.specialty, "avg_minutes": profile.avg_minutes},
        "clinic": doctor_card(db, doctor, profile, None, now)["clinic"],
        "queue_status": state.status,
        "pause_reason": state.pause_reason or "",
        "can_operate": True,
        "counts": {
            "total": len(tokens),
            "waiting": sum(1 for t in tokens if t.status == "waiting"),
            "checked_in": sum(1 for t in tokens if t.status == "checked_in"),
            "in_consultation": sum(1 for t in tokens if t.status == "in_consultation"),
            "completed": sum(1 for t in tokens if t.status == "completed"),
            "cancelled": sum(1 for t in tokens if t.status == "cancelled"),
            "no_show": sum(1 for t in tokens if t.status == "no_show"),
        },
        "tokens": [staff_token_row(t, active, profile, state, now, full_names) for t in tokens],
    }


@app.get("/api/doctor/queue")
def doctor_queue(user: User = Depends(require("doctor")), db: Session = Depends(get_db)):
    data = _doctor_dashboard(db, user.id, full_names=False)
    data["can_operate"] = True
    return data


@app.post("/api/doctor/queue/start")
def doctor_start(user: User = Depends(require("doctor")), db: Session = Depends(get_db)):
    start_queue(db, user, user.id)
    db.commit()
    return _doctor_dashboard(db, user.id, False)


@app.post("/api/doctor/queue/pause")
def doctor_pause(body: PauseIn, user: User = Depends(require("doctor")), db: Session = Depends(get_db)):
    pause_queue(db, user, user.id, body.reason)
    db.commit()
    return _doctor_dashboard(db, user.id, False)


@app.post("/api/doctor/queue/resume")
def doctor_resume(user: User = Depends(require("doctor")), db: Session = Depends(get_db)):
    resume_queue(db, user, user.id)
    db.commit()
    return _doctor_dashboard(db, user.id, False)


@app.post("/api/doctor/queue/next")
def doctor_next(user: User = Depends(require("doctor")), db: Session = Depends(get_db)):
    next_patient(db, user, user.id)
    db.commit()
    return _doctor_dashboard(db, user.id, False)


@app.patch("/api/doctor/settings")
def doctor_settings(body: DoctorSettingsIn, user: User = Depends(require("doctor")), db: Session = Depends(get_db)):
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(404, "Profile not found")
    if body.avg_minutes is not None:
        profile.avg_minutes = body.avg_minutes
    if body.bio is not None:
        profile.bio = body.bio.strip()[:800]
    if body.fee_note is not None:
        profile.fee_note = body.fee_note.strip()[:180]
    if body.hours_text is not None:
        profile.hours_text = body.hours_text.strip()[:180]
    audit(db, user.id, "doctor.settings", f"avg={profile.avg_minutes}")
    db.commit()
    return {"ok": True, "avg_minutes": profile.avg_minutes}


@app.get("/api/reception/overview")
def reception_overview(user: User = Depends(require("receptionist")), db: Session = Depends(get_db)):
    clinic_ids = reception_clinic_ids(db, user.id)
    doctor_ids = doctor_ids_for_clinics(db, clinic_ids)
    boards = []
    for doctor_id in doctor_ids:
        board = _doctor_dashboard(db, doctor_id, full_names=True)
        clinic = board["clinic"]
        board["can_operate"] = bool(clinic and reception_can_operate(db, user, clinic["id"]))
        boards.append(board)
    flat = [t for b in boards for t in b["tokens"]]
    return {
        "clinics": [
            {
                "id": c.id,
                "name": c.name,
                "kind": c.kind,
                "city": c.city,
                "can_operate_queue": reception_can_operate(db, user, c.id),
            }
            for cid in clinic_ids
            if (c := db.get(Clinic, cid))
        ],
        "counts": {
            "total": len(flat),
            "waiting": sum(1 for t in flat if t["status"] == "waiting"),
            "checked_in": sum(1 for t in flat if t["status"] == "checked_in"),
            "in_consultation": sum(1 for t in flat if t["status"] == "in_consultation"),
            "completed": sum(1 for t in flat if t["status"] == "completed"),
            "cancelled": sum(1 for t in flat if t["status"] == "cancelled"),
            "no_show": sum(1 for t in flat if t["status"] == "no_show"),
        },
        "boards": boards,
    }


def _reception_token(db: Session, user: User, token_id: int) -> Token:
    token = db.get(Token, token_id)
    if not token:
        raise HTTPException(404, "Token not found")
    clinic_ids = reception_clinic_ids(db, user.id)
    if token.clinic_id not in clinic_ids:
        raise HTTPException(403, "This token is not at your clinic")
    return token


@app.post("/api/reception/walkin")
def reception_walkin(body: WalkIn, user: User = Depends(require("receptionist")), db: Session = Depends(get_db)):
    clinic = assert_reception_doctor(db, user, body.doctor_id)
    token = walk_in(db, user, body.doctor_id, clinic, body.name, body.phone.strip())
    db.commit()
    db.refresh(token)
    return {"id": token.id, "number": token.number, "patient_name": token.patient_name, "status": token.status}


@app.post("/api/reception/tokens/{token_id}/checkin")
def reception_checkin(token_id: int, user: User = Depends(require("receptionist")), db: Session = Depends(get_db)):
    token = _reception_token(db, user, token_id)
    if token.status != "waiting":
        raise HTTPException(400, "Only a waiting token can be checked in")
    token.status = "checked_in"
    audit(db, user.id, "token.checkin", f"token={token.id}")
    notify(db, token.patient_user_id, "Checked in", f"Reception confirmed your arrival for token #{token.number}.", "token")
    db.commit()
    return {"ok": True}


@app.post("/api/reception/tokens/{token_id}/noshow")
def reception_noshow(token_id: int, user: User = Depends(require("receptionist")), db: Session = Depends(get_db)):
    token = _reception_token(db, user, token_id)
    if token.status not in ("waiting", "checked_in"):
        raise HTTPException(400, "This token cannot be marked absent")
    token.status = "no_show"
    audit(db, user.id, "token.noshow", f"token={token.id}")
    notify(db, token.patient_user_id, "Marked absent", f"Token #{token.number} was marked as a no-show.", "queue")
    db.commit()
    return {"ok": True}


@app.post("/api/reception/tokens/{token_id}/cancel")
def reception_cancel(token_id: int, user: User = Depends(require("receptionist")), db: Session = Depends(get_db)):
    token = _reception_token(db, user, token_id)
    if token.status not in ("waiting", "checked_in"):
        raise HTTPException(400, "This token cannot be cancelled")
    token.status = "cancelled"
    audit(db, user.id, "token.cancel.reception", f"token={token.id}")
    notify(db, token.patient_user_id, "Token cancelled", f"Reception cancelled token #{token.number}.", "queue")
    db.commit()
    return {"ok": True}


@app.post("/api/reception/queue/{doctor_id}/{action}")
def reception_operate(doctor_id: int, action: str, body: OperateIn, user: User = Depends(require("receptionist")), db: Session = Depends(get_db)):
    clinic = assert_reception_doctor(db, user, doctor_id)
    if not reception_can_operate(db, user, clinic.id):
        raise HTTPException(403, "You can view this queue, but queue controls are not enabled for your account")
    if action == "start":
        start_queue(db, user, doctor_id)
    elif action == "resume":
        resume_queue(db, user, doctor_id)
    elif action == "next":
        next_patient(db, user, doctor_id)
    elif action == "pause":
        if not body.reason:
            raise HTTPException(400, "Choose a pause reason")
        pause_queue(db, user, doctor_id, body.reason)
    else:
        raise HTTPException(404, "Unknown action")
    db.commit()
    return {"ok": True}


@app.get("/api/reception/lookup")
def reception_lookup(phone: str, user: User = Depends(require("receptionist")), db: Session = Depends(get_db)):
    phone = phone.strip()
    if len(phone) < 6:
        return {"found": False}
    patient = db.query(User).filter(User.role == "patient", User.phone == phone, User.active == True).first()  # noqa: E712
    if not patient:
        return {"found": False}
    return {"found": True, "name": patient.name}


@app.get("/api/admin/overview")
def admin_overview(user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    day = today()
    tokens = db.query(Token).filter(Token.day == day).all()
    return {
        "patients": db.query(User).filter(User.role == "patient").count(),
        "doctors": db.query(DoctorProfile).filter(DoctorProfile.status == "approved").count(),
        "pending_doctors": db.query(DoctorProfile).filter(DoctorProfile.status == "pending").count(),
        "clinics": db.query(Clinic).count(),
        "receptionists": db.query(User).filter(User.role == "receptionist", User.active == True).count(),  # noqa: E712
        "tokens_today": len(tokens),
        "waiting_today": sum(1 for t in tokens if t.status in ("waiting", "checked_in")),
        "reviews": db.query(Review).count(),
    }


@app.get("/api/admin/doctors")
def admin_doctors(user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    rows = (
        db.query(User, DoctorProfile)
        .join(DoctorProfile, DoctorProfile.user_id == User.id)
        .filter(User.removed == False)  # noqa: E712
        .all()
    )
    out = []
    for doctor, profile in rows:
        clinic = primary_clinic(db, doctor.id)
        out.append(
            {
                "id": doctor.id,
                "name": doctor.name,
                "email": doctor.email,
                "password": doctor.password_plain or "",
                "phone": doctor.phone,
                "specialty": profile.specialty,
                "status": profile.status,
                "license_no": profile.license_no,
                "active": doctor.active,
                "clinic": clinic.name if clinic else "",
                "city": clinic.city if clinic else doctor.city,
                "rating": profile.rating_avg,
            }
        )
    return out


def _set_doctor_status(db: Session, actor: User, doctor_id: int, status: str):
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_id).first()
    doctor = db.get(User, doctor_id)
    if not profile or not doctor:
        raise HTTPException(404, "Doctor not found")
    profile.status = status
    if status == "inactive":
        doctor.active = False
    if status == "approved":
        doctor.active = True
    audit(db, actor.id, "doctor.status", f"{doctor.email} -> {status}")
    notify(db, doctor.id, "Account update", f"Your PocketDoc doctor account is now {status}.", "admin")
    db.commit()
    return {"ok": True}


@app.post("/api/admin/doctors/{doctor_id}/approve")
def approve_doctor(doctor_id: int, user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    return _set_doctor_status(db, user, doctor_id, "approved")


@app.post("/api/admin/doctors/{doctor_id}/reject")
def reject_doctor(doctor_id: int, user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    return _set_doctor_status(db, user, doctor_id, "rejected")


@app.post("/api/admin/doctors/{doctor_id}/deactivate")
def deactivate_doctor(doctor_id: int, user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    return _set_doctor_status(db, user, doctor_id, "inactive")


@app.get("/api/admin/clinics")
def admin_clinics(user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    out = []
    for clinic in db.query(Clinic).order_by(Clinic.city, Clinic.name).all():
        docs = db.query(DoctorClinic).filter(DoctorClinic.clinic_id == clinic.id).count()
        out.append(
            {
                "id": clinic.id,
                "name": clinic.name,
                "kind": clinic.kind,
                "address": clinic.address,
                "city": clinic.city,
                "lat": clinic.lat,
                "lng": clinic.lng,
                "phone": clinic.phone,
                "hours_text": clinic.hours_text,
                "doctors": docs,
            }
        )
    return out


@app.post("/api/admin/clinics")
def create_clinic(body: ClinicIn, user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    place = resolved_place(body.city, body.lat, body.lng, body.district, body.division)
    clinic = Clinic(
        name=body.name.strip(),
        kind=body.kind if body.kind in ("clinic", "hospital") else "clinic",
        address=body.address.strip(),
        city=place["name"],
        district=place.get("district") or "",
        division=place.get("division") or "",
        lat=place["lat"],
        lng=place["lng"],
        phone=body.phone.strip(),
        hours_text=body.hours_text.strip(),
    )
    db.add(clinic)
    audit(db, user.id, "clinic.create", clinic.name)
    db.commit()
    db.refresh(clinic)
    return {"id": clinic.id}


@app.get("/api/admin/patients")
def admin_patients(user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    rows = db.query(User).filter(User.role == "patient", User.removed == False).order_by(User.created_at.desc()).all()  # noqa: E712
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "password": u.password_plain or "",
            "phone": u.phone,
            "city": u.city,
            "plan_code": u.plan_code,
            "active": u.active,
        }
        for u in rows
    ]


@app.post("/api/admin/patients/{patient_id}/active")
def admin_patient_active(patient_id: int, body: StatusIn, user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    patient = db.get(User, patient_id)
    if not patient or patient.role != "patient":
        raise HTTPException(404, "Patient not found")
    patient.active = body.status == "active"
    audit(db, user.id, "patient.active", f"{patient.email} {body.status}")
    db.commit()
    return {"ok": True}


@app.post("/api/admin/patients/{patient_id}/plan")
def admin_patient_plan(patient_id: int, body: PlanIn, user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    patient = db.get(User, patient_id)
    plan = db.get(Plan, body.plan_code)
    if not patient or patient.role != "patient" or not plan:
        raise HTTPException(404, "Patient or plan not found")
    patient.plan_code = plan.code
    audit(db, user.id, "patient.plan.admin", f"{patient.email} {plan.code}")
    db.commit()
    return {"ok": True}


@app.get("/api/admin/receptionists")
def admin_receptionists(user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    rows = db.query(User).filter(User.role == "receptionist").all()
    out = []
    for person in rows:
        links = db.query(ReceptionAssignment).filter(ReceptionAssignment.user_id == person.id).all()
        out.append(
            {
                "id": person.id,
                "name": person.name,
                "email": person.email,
                "phone": person.phone,
                "active": person.active,
                "assignments": [
                    {
                        "clinic_id": link.clinic_id,
                        "clinic": db.get(Clinic, link.clinic_id).name if db.get(Clinic, link.clinic_id) else "",
                        "can_operate_queue": link.can_operate_queue,
                    }
                    for link in links
                ],
            }
        )
    return out


@app.post("/api/admin/receptionists")
def create_receptionist(body: ReceptionIn, user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(409, "Email already exists")
    clinic = db.get(Clinic, body.clinic_id)
    if not clinic:
        raise HTTPException(404, "Clinic not found")
    person = User(
        role="receptionist",
        name=body.name.strip(),
        email=email,
        phone=body.phone.strip(),
        password_hash=hash_password(body.password),
        password_plain=body.password,
        city=clinic.city,
        lat=clinic.lat,
        lng=clinic.lng,
        area_district=clinic.district or "",
        area_division=clinic.division or "",
    )
    db.add(person)
    db.flush()
    db.add(ReceptionAssignment(user_id=person.id, clinic_id=clinic.id, can_operate_queue=body.can_operate_queue))
    audit(db, user.id, "reception.create", email)
    db.commit()
    return {"id": person.id}


@app.patch("/api/admin/receptionists/{reception_id}")
def patch_receptionist(reception_id: int, body: PermissionIn, user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    links = db.query(ReceptionAssignment).filter(ReceptionAssignment.user_id == reception_id).all()
    if not links:
        raise HTTPException(404, "Receptionist not found")
    for link in links:
        link.can_operate_queue = body.can_operate_queue
    audit(db, user.id, "reception.permission", f"{reception_id} operate={body.can_operate_queue}")
    db.commit()
    return {"ok": True}


@app.get("/api/admin/queues")
def admin_queues(user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    doctors = db.query(User, DoctorProfile).join(DoctorProfile, DoctorProfile.user_id == User.id).filter(DoctorProfile.status == "approved").all()
    out = []
    for doctor, profile in doctors:
        state = get_queue_state(db, doctor.id)
        tokens = day_tokens(db, doctor.id)
        clinic = primary_clinic(db, doctor.id)
        if not tokens and state.status == "not_started":
            continue
        out.append(
            {
                "doctor_id": doctor.id,
                "doctor": doctor.name,
                "specialty": profile.specialty,
                "clinic": clinic.name if clinic else "",
                "city": clinic.city if clinic else "",
                "queue_status": state.status,
                "pause_reason": state.pause_reason or "",
                "waiting": sum(1 for t in tokens if t.status in ("waiting", "checked_in")),
                "current": next((t.number for t in tokens if t.status == "in_consultation"), None),
            }
        )
    return out


@app.get("/api/admin/reviews")
def admin_reviews(user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    rows = db.query(Review).order_by(Review.created_at.desc()).limit(50).all()
    out = []
    for review in rows:
        doctor = db.get(User, review.doctor_user_id)
        patient = db.get(User, review.patient_user_id)
        out.append(
            {
                "id": review.id,
                "rating": review.rating,
                "comment": review.comment,
                "hidden": review.hidden,
                "doctor": doctor.name if doctor else "",
                "patient": patient.name if patient else "",
                "created_at": review.created_at.isoformat() if review.created_at else None,
            }
        )
    return out


@app.post("/api/admin/reviews/{review_id}/hide")
def hide_review(review_id: int, user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(404, "Review not found")
    review.hidden = not review.hidden
    recompute_rating(db, review.doctor_user_id)
    audit(db, user.id, "review.hide", f"{review.id} hidden={review.hidden}")
    db.commit()
    return {"hidden": review.hidden}


@app.get("/api/admin/audit")
def admin_audit(user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(80).all()
    out = []
    for row in rows:
        actor = db.get(User, row.actor_id) if row.actor_id else None
        out.append(
            {
                "id": row.id,
                "action": row.action,
                "detail": row.detail,
                "actor": actor.name if actor else "System",
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        )
    return out


@app.get("/api/admin/accounts")
def admin_accounts(user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    rows = db.query(User).filter(User.removed == False).order_by(User.role, User.name).all()  # noqa: E712
    out = []
    for person in rows:
        profile = ""
        if person.role == "doctor":
            doc = db.query(DoctorProfile).filter(DoctorProfile.user_id == person.id).first()
            clinic = primary_clinic(db, person.id)
            profile = " · ".join(
                part
                for part in (
                    doc.specialty if doc else "",
                    doc.status if doc else "",
                    clinic.name if clinic else "",
                    person.city,
                )
                if part
            )
        elif person.role == "patient":
            profile = f"{person.city} · plan {person.plan_code} · {person.phone}"
        elif person.role == "receptionist":
            links = db.query(ReceptionAssignment).filter(ReceptionAssignment.user_id == person.id).all()
            names = []
            for link in links:
                clinic = db.get(Clinic, link.clinic_id)
                if clinic:
                    names.append(clinic.name)
            profile = ", ".join(names) or person.city
        else:
            profile = "Super admin"
        out.append(
            {
                "id": person.id,
                "role": person.role,
                "name": person.name,
                "email": person.email,
                "password": person.password_plain or "",
                "phone": person.phone or "",
                "city": person.city,
                "active": person.active,
                "plan_code": person.plan_code,
                "profile": profile,
            }
        )
    return out


@app.post("/api/admin/accounts/{account_id}/remove")
def admin_remove_account(account_id: int, user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    target = db.get(User, account_id)
    if not target or target.removed:
        raise HTTPException(404, "Account not found")
    if target.id == user.id or target.role == "admin":
        raise HTTPException(400, "The admin account stays in place")
    target.removed = True
    target.active = False
    if target.role == "doctor":
        profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == target.id).first()
        if profile:
            profile.status = "inactive"
    audit(db, user.id, "account.remove", f"{target.role} {target.email}")
    db.commit()
    return {"ok": True}


@app.get("/api/admin/plans")
def admin_plans(user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    return [
        {"code": p.code, "name": p.name, "radius_km": p.radius_km, "price_pkr": p.price_pkr, "blurb": p.blurb, "active": p.active}
        for p in db.query(Plan).order_by(Plan.radius_km).all()
    ]


@app.patch("/api/admin/plans/{code}")
def patch_plan(code: str, body: AdminPlanIn, user: User = Depends(require("admin")), db: Session = Depends(get_db)):
    plan = db.get(Plan, code)
    if not plan:
        raise HTTPException(404, "Plan not found")
    if body.name is not None:
        plan.name = body.name.strip()
    if body.radius_km is not None:
        plan.radius_km = body.radius_km
    if body.price_pkr is not None:
        plan.price_pkr = body.price_pkr
    if body.blurb is not None:
        plan.blurb = body.blurb.strip()
    if body.active is not None:
        plan.active = body.active
    audit(db, user.id, "plan.update", f"{code} radius={plan.radius_km}")
    db.commit()
    return {"ok": True}


DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


def _mount_site():
    if not (DIST / "index.html").is_file():
        return

    @app.get("/", include_in_schema=False)
    def site_root():
        return FileResponse(DIST / "index.html")

    @app.get("/{full_path:path}", include_in_schema=False)
    def site_files(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(404, "Not found")
        candidate = (DIST / full_path).resolve()
        if candidate.is_file() and str(candidate).startswith(str(DIST.resolve())):
            return FileResponse(candidate)
        return FileResponse(DIST / "index.html")


_mount_site()
