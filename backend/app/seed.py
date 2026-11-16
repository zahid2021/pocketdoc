from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .models import (
    Clinic,
    DoctorClinic,
    DoctorProfile,
    Favorite,
    Notification,
    Plan,
    QueueState,
    ReceptionAssignment,
    Token,
    User,
)
from .security import hash_password, verify_password
from .services import today


def seed(db: Session):
    if db.query(User).filter(User.email == "admin@pocketdoc.app").first():
        return

    plans = [
        Plan(code="basic", name="Basic", radius_km=2, price_pkr=0, blurb="Doctors within 2 km of you."),
        Plan(code="plus", name="Plus", radius_km=5, price_pkr=299, blurb="A wider neighbourhood, up to 5 km."),
        Plan(code="family", name="Family", radius_km=10, price_pkr=599, blurb="Most of the city around you, up to 10 km."),
        Plan(code="premium", name="Premium", radius_km=20, price_pkr=999, blurb="City-wide search, up to 20 km."),
    ]
    db.add_all(plans)

    def user(role, name, email, phone, password, city, lat, lng, plan="basic"):
        row = User(
            role=role,
            name=name,
            email=email,
            phone=phone,
            password_hash=hash_password(password),
            password_plain=password,
            city=city,
            lat=lat,
            lng=lng,
            plan_code=plan,
            active=True,
        )
        db.add(row)
        db.flush()
        return row

    admin = user("admin", "PocketDoc Admin", "admin@pocketdoc.app", "03000000000", "admin123", "Lahore", 31.5204, 74.3587)
    patient = user("patient", "Ali Hassan", "patient@pocketdoc.app", "03001111111", "patient123", "Lahore", 31.5215, 74.3520, "family")
    sara = user("patient", "Sara Malik", "sara@pocketdoc.app", "03002222222", "patient123", "Lahore", 31.5300, 74.3400, "plus")
    karachi_patient = user("patient", "Omar Sheikh", "omar@pocketdoc.app", "03003333333", "patient123", "Karachi", 24.8685, 67.0260, "basic")

    ahmed = user("doctor", "Dr. Ahmed Khan", "doctor@pocketdoc.app", "03004444444", "doctor123", "Lahore", 31.5220, 74.3500)
    bilal = user("doctor", "Dr. Bilal Ahmed", "bilal@pocketdoc.app", "03005555555", "doctor123", "Lahore", 31.5220, 74.3500)
    sana = user("doctor", "Dr. Sana Ali", "sana@pocketdoc.app", "03006666666", "doctor123", "Lahore", 31.5750, 74.3230)
    faisal = user("doctor", "Dr. Faisal Mehmood", "faisal@pocketdoc.app", "03007777777", "doctor123", "Lahore", 31.4890, 74.3920)
    ayesha = user("doctor", "Dr. Ayesha Noor", "ayesha@pocketdoc.app", "03008888888", "doctor123", "Lahore", 31.4700, 74.3000)
    hina = user("doctor", "Dr. Hina Qureshi", "hina@pocketdoc.app", "03009999999", "doctor123", "Karachi", 24.8700, 67.0300)
    reception = user("receptionist", "Nadia Iqbal", "reception@pocketdoc.app", "03001234567", "reception123", "Lahore", 31.5220, 74.3500)

    clinics = {
        "city": Clinic(
            name="City Clinic",
            kind="clinic",
            address="Main Road",
            city="Lahore",
            lat=31.5220,
            lng=74.3500,
            phone="042-111-0001",
            hours_text="Mon – Sat 9:00 AM – 5:00 PM",
        ),
        "health": Clinic(
            name="Health Care Clinic",
            kind="clinic",
            address="near Bus Stand",
            city="Lahore",
            lat=31.5750,
            lng=74.3230,
            phone="042-111-0002",
            hours_text="Mon – Sat 10:00 AM – 6:00 PM",
        ),
        "life": Clinic(
            name="Life Care Clinic",
            kind="clinic",
            address="Garden Town",
            city="Lahore",
            lat=31.4890,
            lng=74.3920,
            phone="042-111-0003",
            hours_text="Mon – Fri 9:00 AM – 4:00 PM",
        ),
        "national": Clinic(
            name="National Hospital",
            kind="hospital",
            address="Ferozepur Road",
            city="Lahore",
            lat=31.4700,
            lng=74.3000,
            phone="042-111-0004",
            hours_text="Open daily 8:00 AM – 10:00 PM",
        ),
        "skin": Clinic(
            name="Clifton Skin Studio",
            kind="clinic",
            address="Clifton Block 5",
            city="Karachi",
            lat=24.8700,
            lng=67.0300,
            phone="021-111-0005",
            hours_text="Tue – Sun 11:00 AM – 7:00 PM",
        ),
    }
    db.add_all(clinics.values())
    db.flush()

    profiles = [
        (ahmed, "General Physician", 12, 4.8, 250, 6, "City Clinic, Main Road. A calm general practice with a live token queue.", "approved", "PMC-44120"),
        (bilal, "Cardiologist", 9, 4.7, 140, 12, "Heart checks and follow-ups at City Clinic. Pay the consultation fee at the desk.", "approved", "PMC-22811"),
        (sana, "General Physician", 8, 4.6, 180, 7, "Family clinic near the bus stand. Tokens are called in order.", "approved", "PMC-19002"),
        (faisal, "General Physician", 15, 4.7, 320, 6, "Life Care Clinic. Walk-ins and app tokens share one queue.", "approved", "PMC-10088"),
        (ayesha, "Pediatrician", 11, 4.9, 210, 10, "Children's clinic inside National Hospital.", "approved", "PMC-77310"),
        (hina, "Dermatologist", 7, 4.5, 90, 8, "Skin consultations in Clifton. Waiting for admin approval.", "pending", "PMC-66001"),
    ]
    for person, specialty, years, rating, count, avg, bio, status, lic in profiles:
        db.add(
            DoctorProfile(
                user_id=person.id,
                specialty=specialty,
                bio=bio,
                experience_years=years,
                fee_note="Pay at the clinic. PocketDoc does not collect consultation fees.",
                avg_minutes=avg,
                rating_avg=rating,
                rating_count=count,
                rating_base_avg=rating,
                rating_base_count=count,
                status=status,
                license_no=lic,
                hours_text="Mon – Sat 9:00 AM – 5:00 PM",
            )
        )

    links = [
        (ahmed, clinics["city"]),
        (bilal, clinics["city"]),
        (sana, clinics["health"]),
        (faisal, clinics["life"]),
        (ayesha, clinics["national"]),
        (hina, clinics["skin"]),
    ]
    for person, clinic in links:
        db.add(DoctorClinic(doctor_user_id=person.id, clinic_id=clinic.id))

    db.add(ReceptionAssignment(user_id=reception.id, clinic_id=clinics["city"].id, can_operate_queue=False))
    db.add(Favorite(patient_user_id=patient.id, doctor_user_id=ahmed.id))

    day = today()
    started = datetime.now() - timedelta(minutes=2)

    def add_token(doctor, clinic, number, name, phone, status, source, patient_user=None, started_at=None):
        db.add(
            Token(
                number=number,
                doctor_user_id=doctor.id,
                clinic_id=clinic.id,
                patient_user_id=patient_user.id if patient_user else None,
                patient_name=name,
                contact_phone=phone,
                status=status,
                source=source,
                day=day,
                started_at=started_at,
            )
        )

    others = [
        (11, "Hira S.", "03010000011", "in_consultation", "app"),
        (12, "Usman R.", "03010000012", "waiting", "app"),
        (13, "Maryam K.", "03010000013", "checked_in", "walkin"),
        (14, "Zain A.", "03010000014", "waiting", "app"),
        (15, "Fatima N.", "03010000015", "waiting", "app"),
        (16, "Hamza T.", "03010000016", "waiting", "walkin"),
        (17, "Noor J.", "03010000017", "waiting", "app"),
    ]
    for number, name, phone, status, source in others:
        add_token(
            ahmed,
            clinics["city"],
            number,
            name,
            phone,
            status,
            source,
            started_at=started if status == "in_consultation" else None,
        )
    add_token(ahmed, clinics["city"], 18, patient.name, patient.phone, "waiting", "app", patient)
    add_token(bilal, clinics["city"], 4, "Kamran Ali", "03020000004", "waiting", "walkin")
    add_token(sana, clinics["health"], 3, "Anum Raza", "03030000003", "in_consultation", "app", started_at=datetime.now() - timedelta(minutes=4))
    add_token(sana, clinics["health"], 4, "Bilal Saeed", "03030000004", "waiting", "app")
    add_token(sana, clinics["health"], 5, "Hania Iqbal", "03030000005", "waiting", "app")

    db.add(QueueState(doctor_user_id=ahmed.id, day=day, status="running", pause_reason=""))
    db.add(QueueState(doctor_user_id=sana.id, day=day, status="running", pause_reason=""))
    db.add(QueueState(doctor_user_id=faisal.id, day=day, status="not_started", pause_reason=""))

    db.add(Notification(user_id=patient.id, title="Token confirmed", body="Your token for Dr. Ahmed Khan is #18.", kind="token"))
    db.add(Notification(user_id=patient.id, title="You are in the queue", body="We will alert you when your turn is close.", kind="queue", read=True))
    db.add(Notification(user_id=ahmed.id, title="Queue is running", body="Token #11 is in consultation.", kind="queue"))
    db.add(Notification(user_id=admin.id, title="Doctor waiting for approval", body="Dr. Hina Qureshi submitted a clinic in Karachi.", kind="admin"))

    db.commit()
    _ = (admin, sara, karachi_patient)


def ensure_punjab(db: Session):
    from .punjab import find_place, in_pakistan, nearest_place

    for clinic in db.query(Clinic).all():
        if clinic.district or not in_pakistan(clinic.lat or 0, clinic.lng or 0):
            continue
        place = find_place(clinic.city) or nearest_place(clinic.lat or 0, clinic.lng or 0)
        if place:
            clinic.district = place["district"]
            clinic.division = place["division"]
    for person in db.query(User).all():
        if person.area_district or person.lat is None or not in_pakistan(person.lat, person.lng):
            continue
        place = find_place(person.city) or nearest_place(person.lat, person.lng)
        if place:
            person.area_district = place["district"]
            person.area_division = place["division"]

    clinics_to_add = [
        ("bwp@pocketdoc.app", "Dr. Imran Shahid", "03041111001", "General Physician", 14, 4.8, 190, 7, "Model Town C clinic in Bahawalpur. Pay at the desk.", "PMC-88001", "Model Town Clinic", "clinic", "Street 4, Model Town C", "Bahawalpur", 29.3905, 71.6720),
        ("multan.doc@pocketdoc.app", "Dr. Saima Riaz", "03041111002", "Pediatrician", 10, 4.7, 160, 8, "Children's clinic near Cantt, Multan.", "PMC-88002", "Cantt Children Clinic", "clinic", "Abdali Road", "Multan", 30.1700, 71.4700),
        ("faisal.doc@pocketdoc.app", "Dr. Usman Ghani", "03041111003", "General Physician", 11, 4.6, 140, 6, "Clock tower area practice in Faisalabad.", "PMC-88003", "Clock Tower Clinic", "clinic", "Rail Bazaar", "Faisalabad", 31.4180, 73.0790),
        ("grw.doc@pocketdoc.app", "Dr. Tariq Mehmood", "03041111004", "Cardiologist", 16, 4.8, 210, 12, "Satellite Town, Gujranwala.", "PMC-88004", "Satellite Heart Clinic", "clinic", "Satellite Town", "Gujranwala", 32.1610, 74.1880),
        ("sialkot.doc@pocketdoc.app", "Dr. Waqas Cheema", "03041111005", "General Physician", 9, 4.5, 90, 6, "Cantt clinic in Sialkot.", "PMC-88005", "Cantt Family Clinic", "clinic", "Paris Road", "Sialkot", 32.5080, 74.5430),
        ("rwp.doc@pocketdoc.app", "Dr. Farah Younas", "03041111006", "Gynecologist", 13, 4.9, 240, 10, "Saddar, Rawalpindi.", "PMC-88006", "Saddar Clinic", "clinic", "Adamjee Road", "Rawalpindi", 33.5890, 73.0500),
        ("sgd.doc@pocketdoc.app", "Dr. Naveed Akhtar", "03041111007", "General Physician", 12, 4.6, 120, 6, "Queens Road, Sargodha.", "PMC-88007", "Queens Road Clinic", "clinic", "Queens Road", "Sargodha", 32.0740, 72.6710),
        ("swl.doc@pocketdoc.app", "Dr. Amina Shah", "03041111008", "General Physician", 8, 4.7, 100, 6, "High Street, Sahiwal.", "PMC-88008", "High Street Clinic", "clinic", "High Street", "Sahiwal", 30.6610, 73.1080),
        ("ryk.doc@pocketdoc.app", "Dr. Adeel Hassan", "03041111009", "General Physician", 15, 4.6, 130, 7, "City road clinic in Rahim Yar Khan.", "PMC-88009", "City Road Clinic", "clinic", "Shahi Road", "Rahim Yar Khan", 28.4190, 70.3050),
        ("dgk.doc@pocketdoc.app", "Dr. Kamran Latif", "03041111010", "General Physician", 10, 4.5, 80, 7, "Hospital road, Dera Ghazi Khan.", "PMC-88010", "Hospital Road Clinic", "hospital", "Hospital Road", "Dera Ghazi Khan", 30.0480, 70.6400),
        ("ape.doc@pocketdoc.app", "Dr. Rabia Noor", "03041111011", "General Physician", 7, 4.8, 70, 6, "Small-town clinic in Ahmadpur East.", "PMC-88011", "Ahmadpur Clinic", "clinic", "Railway Road", "Ahmadpur East", 29.1470, 71.2610),
        ("basti.doc@pocketdoc.app", "Dr. Hira Jameel", "03041111012", "General Physician", 6, 4.7, 40, 6, "Clinic in Basti Malook, Multan district.", "PMC-88012", "Basti Malook Clinic", "clinic", "Main Bazaar, Basti Malook", "Basti Malook", 29.8590, 71.5280),
        ("khi.doc@pocketdoc.app", "Dr. Farhan Siddiqui", "03041111013", "General Physician", 12, 4.7, 180, 8, "Clifton clinic in Karachi.", "PMC-88013", "Clifton Clinic", "clinic", "Block 5, Clifton", "Clifton", 24.8620, 67.0310),
        ("hyd.doc@pocketdoc.app", "Dr. Sana Memon", "03041111014", "Gynecologist", 11, 4.8, 150, 10, "Latifabad clinic in Hyderabad.", "PMC-88014", "Latifabad Clinic", "clinic", "Latifabad Unit 7", "Latifabad", 25.3670, 68.3700),
        ("skz.doc@pocketdoc.app", "Dr. Asif Soomro", "03041111015", "General Physician", 9, 4.6, 90, 6, "City clinic in Sukkur.", "PMC-88015", "Sukkur City Clinic", "clinic", "Queens Road", "Sukkur", 27.7052, 68.8574),
        ("pew.doc@pocketdoc.app", "Dr. Haris Afridi", "03041111016", "General Physician", 13, 4.7, 160, 7, "Saddar clinic in Peshawar.", "PMC-88016", "Saddar Clinic Peshawar", "clinic", "Saddar Road", "Peshawar", 34.0151, 71.5249),
        ("qta.doc@pocketdoc.app", "Dr. Zahra Kakar", "03041111017", "Pediatrician", 10, 4.8, 120, 8, "Jinnah Road clinic in Quetta.", "PMC-88017", "Jinnah Road Clinic", "clinic", "Jinnah Road", "Quetta", 30.1798, 66.9750),
        ("isb.doc@pocketdoc.app", "Dr. Maham Javed", "03041111018", "General Physician", 8, 4.6, 110, 6, "Blue Area clinic in Islamabad.", "PMC-88018", "Blue Area Clinic", "clinic", "Blue Area", "Blue Area", 33.7100, 73.0580),
        ("glt.doc@pocketdoc.app", "Dr. Shahid Hunzai", "03041111019", "General Physician", 14, 4.9, 70, 8, "Main bazaar clinic in Gilgit.", "PMC-88019", "Gilgit Clinic", "clinic", "Main Bazaar", "Gilgit", 35.9208, 74.3080),
        ("mzd.doc@pocketdoc.app", "Dr. Noor Abbasi", "03041111020", "General Physician", 9, 4.7, 60, 7, "Clinic in Muzaffarabad.", "PMC-88020", "Muzaffarabad Clinic", "clinic", "Civil Lines", "Muzaffarabad", 34.3700, 73.4710),
        ("gwd.doc@pocketdoc.app", "Dr. Balach Dashti", "03041111021", "General Physician", 7, 4.6, 40, 8, "Marine Drive clinic in Gwadar.", "PMC-88021", "Gwadar Clinic", "clinic", "Marine Drive", "Gwadar", 25.1264, 62.3225),
        ("moro.doc@pocketdoc.app", "Dr. Aijaz Jalbani", "03041111022", "General Physician", 9, 4.6, 70, 6, "Main bazaar clinic in Moro, between Nawabshah and Sukkur.", "PMC-88022", "Moro Clinic", "clinic", "Main Bazaar", "Moro", 26.6630, 68.0000),
        ("mingora.doc@pocketdoc.app", "Dr. Salman Yousafzai", "03041111023", "General Physician", 11, 4.7, 110, 7, "City clinic in Mingora, Swat.", "PMC-88023", "Mingora Clinic", "clinic", "Makan Bagh", "Mingora", 34.7795, 72.3600),
        ("hub.doc@pocketdoc.app", "Dr. Shahzeb Mengal", "03041111024", "General Physician", 8, 4.5, 50, 6, "Hub chowki clinic on the Karachi–Quetta road.", "PMC-88024", "Hub Clinic", "clinic", "Hub Chowki", "Hub", 25.0220, 66.8800),
        ("skd.doc@pocketdoc.app", "Dr. Abbas Ali", "03041111025", "General Physician", 12, 4.8, 60, 8, "Bazaar clinic in Skardu.", "PMC-88025", "Skardu Clinic", "clinic", "Yadgar Chowk", "Skardu", 35.2976, 75.6337),
        ("mpr.doc@pocketdoc.app", "Dr. Saba Chaudhry", "03041111026", "Gynecologist", 10, 4.7, 90, 9, "Allama Iqbal Road clinic in Mirpur.", "PMC-88026", "Mirpur Clinic", "clinic", "Allama Iqbal Road", "Mirpur", 33.1480, 73.7510),
        ("atd.doc@pocketdoc.app", "Dr. Hamza Jadoon", "03041111027", "General Physician", 13, 4.8, 140, 7, "Supply bazaar clinic in Abbottabad.", "PMC-88027", "Abbottabad Clinic", "clinic", "Supply Bazaar", "Abbottabad", 34.1688, 73.2215),
        ("kotri.doc@pocketdoc.app", "Dr. Fiza Shah", "03041111028", "Pediatrician", 8, 4.6, 80, 8, "Station road clinic in Kotri, between Hyderabad and Karachi.", "PMC-88028", "Kotri Clinic", "clinic", "Station Road", "Kotri", 25.3650, 68.3080),
    ]
    for email, name, phone, specialty, years, rating, count, avg, bio, lic, clinic_name, kind, address, place_name, lat, lng in clinics_to_add:
        if db.query(User).filter(User.email == email).first():
            continue
        place = find_place(place_name) or find_place("Lahore")
        doctor = User(
            role="doctor",
            name=name,
            email=email,
            phone=phone,
            password_hash=hash_password("doctor123"),
            password_plain="doctor123",
            city=place_name,
            lat=lat,
            lng=lng,
            area_district=place["district"],
            area_division=place["division"],
            active=True,
        )
        db.add(doctor)
        db.flush()
        clinic = Clinic(
            name=clinic_name,
            kind=kind,
            address=address,
            city=place_name,
            district=place["district"],
            division=place["division"],
            lat=lat,
            lng=lng,
            hours_text="Mon – Sat 9:00 AM – 5:00 PM",
        )
        db.add(clinic)
        db.flush()
        db.add(
            DoctorProfile(
                user_id=doctor.id,
                specialty=specialty,
                bio=bio,
                experience_years=years,
                fee_note="Pay at the clinic. PocketDoc does not collect consultation fees.",
                avg_minutes=avg,
                rating_avg=rating,
                rating_count=count,
                rating_base_avg=rating,
                rating_base_count=count,
                status="approved",
                license_no=lic,
            )
        )
        db.add(DoctorClinic(doctor_user_id=doctor.id, clinic_id=clinic.id))

    if not db.query(User).filter(User.email == "bahawalpur@pocketdoc.app").first():
        db.add(
            User(
                role="patient",
                name="Hassan Raza",
                email="bahawalpur@pocketdoc.app",
                phone="03042222000",
                password_hash=hash_password("patient123"),
                password_plain="patient123",
                city="Bahawalpur",
                lat=29.3956,
                lng=71.6836,
                area_district="Bahawalpur",
                area_division="Bahawalpur",
                plan_code="family",
                active=True,
            )
        )
    db.commit()


def remember_known_passwords(db: Session):
    guesses = {
        "admin": ("admin123",),
        "patient": ("patient123",),
        "doctor": ("doctor123",),
        "receptionist": ("reception123",),
    }
    changed = False
    for person in db.query(User).all():
        if person.password_plain:
            continue
        for guess in guesses.get(person.role, ()):
            if verify_password(guess, person.password_hash):
                person.password_plain = guess
                changed = True
                break
    if changed:
        db.commit()
