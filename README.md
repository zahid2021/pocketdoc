# PocketDoc

Live waiting time and token queue for clinics. One backend serves the patient phone app, the patient website, the doctor desk, the reception desk, and the super admin.

## Run

```bash
cd pocketdoc
chmod +x run.sh
./run.sh
```

Open http://localhost:5173

The phone layout appears automatically on a narrow screen. On a laptop, use **Open mobile app view** in the footer. Add the site to the home screen on Android or iPhone to use it as an app.

## Demo logins

| Role | Email | Password |
| --- | --- | --- |
| Patient (Ali, token #18, 10 km) | patient@pocketdoc.app | patient123 |
| Patient (Sara, 5 km) | sara@pocketdoc.app | patient123 |
| Patient (Omar, Karachi, 2 km) | omar@pocketdoc.app | patient123 |
| Patient (Hassan, Bahawalpur) | bahawalpur@pocketdoc.app | patient123 |
| Doctor (Dr. Ahmed Khan) | doctor@pocketdoc.app | doctor123 |
| Reception (City Clinic) | reception@pocketdoc.app | reception123 |
| Admin | admin@pocketdoc.app | admin123 |

Dr. Hina Qureshi is waiting for admin approval. Reception cannot run Start / Pause / Next until an admin turns that permission on.

## What is shared

Patient search, tokens, favourites, ratings, and radius plans use the same API as the doctor queue and the reception desk. When the doctor taps Next, the patient token screen updates within a few seconds.

Waiting time is an estimate from a demo average per doctor. It is labelled as an estimate until a clinic sets a real average.

Consultation fees are not collected in the app.

Postgres: set `DATABASE_URL` before starting. The default database is SQLite in `backend/data/`.
