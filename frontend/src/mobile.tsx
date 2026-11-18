import { FormEvent, useEffect, useState } from "react";
import { Link, NavLink, Route, Routes, useLocation, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, statusLabel } from "./api";
import { useAuth, useLayout } from "./auth";
import { Avatar, Bell, Credit, DemoAccounts, ErrorText, LiveBadge, Logo, Stars, Wait, Wordmark } from "./bits";
import { AreaMap, ClinicMap, directionsUrl, PlacePicker } from "./mapui";

function Icon({ d }: { d: string }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d={d} />
    </svg>
  );
}

function TabBar() {
  return (
    <nav className="tabbar">
      <NavLink to="/" end>
        <Icon d="M4 11.5 12 4l8 7.5V20a1 1 0 0 1-1 1h-5v-6H10v6H5a1 1 0 0 1-1-1v-8.5z" />
        Home
      </NavLink>
      <NavLink to="/search">
        <Icon d="M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16zm10 2-5.2-5.2" />
        Search
      </NavLink>
      <NavLink to="/appointments">
        <Icon d="M7 3v3M17 3v3M4 8h16M6 5h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z" />
        Appointments
      </NavLink>
      <NavLink to="/profile">
        <Icon d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4zm-7 8a7 7 0 0 1 14 0" />
        Profile
      </NavLink>
    </nav>
  );
}

export function PatientMobile() {
  const { width, mode } = useLayout();
  const loc = useLocation();
  const staged = mode === "mobile" && width > 880;
  const showTabs = ["/", "/appointments", "/profile", "/nearby", "/pricing"].includes(loc.pathname);
  return (
    <div className={staged ? "phone-app staged" : "phone-app"}>
      <div className="phone-scroll">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/search" element={<Search />} />
          <Route path="/nearby" element={<AreaPage />} />
          <Route path="/doctors/:id" element={<Doctor />} />
          <Route path="/token" element={<TokenScreen />} />
          <Route path="/appointments" element={<Appointments />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/for-clinics" element={<ForClinics />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </div>
      {showTabs && <TabBar />}
    </div>
  );
}

function Welcome() {
  return (
    <div className="welcome">
      <Logo size={86} />
      <h1>
        <Wordmark />
      </h1>
      <p className="tag">Your Turn. Our Priority.</p>
      <p className="urdu">
        Ab wait nahi, sirf update.
        <i />
      </p>
      <Link className="btn btn-primary btn-block" to="/register">
        Get Started
      </Link>
      <Link className="btn btn-ghost btn-block" to="/login">
        I already have an account
      </Link>
      <Credit />
    </div>
  );
}

function Login() {
  const { login, user } = useAuth();
  const nav = useNavigate();
  const [params] = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (user) nav("/", { replace: true });
  }, [user]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email, password);
      nav(params.get("next") || "/");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-screen">
      <button className="text-back" onClick={() => nav("/")}>
        ← Back
      </button>
      <h2>Sign in</h2>
      <p className="muted">Patient, doctor, reception and admin each have their own login.</p>
      <form onSubmit={submit} className="stack">
        <label>
          Email
          <input className="field" value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        </label>
        <label>
          Password
          <input className="field" value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
        </label>
        <ErrorText>{error}</ErrorText>
        <button className="btn btn-primary btn-block" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <DemoAccounts
        onPick={(nextEmail, nextPassword) => {
          setEmail(nextEmail);
          setPassword(nextPassword);
        }}
      />
      <p className="center muted">
        New patient? <Link to="/register">Create an account</Link>
      </p>
    </div>
  );
}

function AreaPage() {
  return (
    <div className="m-page">
      <h2 className="page-title">Clinic map</h2>
      <p className="muted">Search a city, basti or street. The pin shows the clinic, even if it is outside your token radius.</p>
      <AreaMap />
    </div>
  );
}

function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState<any>({ name: "", email: "", phone: "", password: "", city: "Lahore" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function set(key: string, value: string) {
    setForm((prev: any) => ({ ...prev, [key]: value }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await register(form);
      nav("/");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-screen">
      <button className="text-back" onClick={() => nav("/")}>
        ← Back
      </button>
      <h2>Create your account</h2>
      <p className="muted">Patients use this app free. Consultation fees are paid at the clinic.</p>
      <form onSubmit={submit} className="stack">
        <label>
          Full name
          <input className="field" value={form.name} onChange={(e) => set("name", e.target.value)} required />
        </label>
        <label>
          Email
          <input className="field" type="email" value={form.email} onChange={(e) => set("email", e.target.value)} required />
        </label>
        <label>
          Phone
          <input className="field" value={form.phone} onChange={(e) => set("phone", e.target.value)} placeholder="03xx" />
        </label>
        <label>
          Your place in Pakistan
          <PlacePicker
            placeholder="Lahore, Karachi, Quetta, Gilgit…"
            onPick={(place) =>
              setForm((prev: any) => ({
                ...prev,
                city: place.name,
                lat: place.lat,
                lng: place.lng,
                district: place.district,
                division: place.division,
              }))
            }
          />
        </label>
        <label>
          Password
          <input className="field" type="password" value={form.password} onChange={(e) => set("password", e.target.value)} minLength={6} required />
        </label>
        <ErrorText>{error}</ErrorText>
        <button className="btn btn-primary btn-block" disabled={busy}>
          {busy ? "Creating…" : "Get Started"}
        </button>
      </form>
    </div>
  );
}

function Home() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [q, setQ] = useState("");
  return (
    <div className="m-home">
      <header className="m-top">
        <span className="brand-inline">
          <Logo size={36} />
          <Wordmark />
        </span>
        <Bell />
      </header>
      <h1 className="hero-urdu">Apni turn ka wait ghar se dekhein</h1>
      <p className="lead">Find doctors, check live queue and save your time.</p>
      {user && (
        <p className="muted">
          {user.area_district ? `${user.city} · ${user.area_district} district` : user.city}. Open the map to see clinic pins.
        </p>
      )}
      <form
        className="search-pill"
        onSubmit={(event) => {
          event.preventDefault();
          nav(`/search?q=${encodeURIComponent(q)}`);
        }}
      >
        <Icon d="M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16zm10 2-5.2-5.2" />
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Doctor name, specialty or clinic" />
      </form>
      <div className="tile-grid">
        <Link to="/search" className="tile">
          <span className="bubble blue">
            <Icon d="M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16zm10 2-5.2-5.2" />
          </span>
          <b>Find Doctor</b>
          <small>Search by name, specialty or clinic</small>
        </Link>
        <Link to={user ? "/appointments" : "/login?next=/appointments"} className="tile">
          <span className="bubble teal">
            <Icon d="M7 3v3M17 3v3M4 8h16M6 5h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z" />
          </span>
          <b>My Appointments</b>
          <small>View your booked appointments</small>
        </Link>
        <Link to={user ? "/token" : "/login?next=/token"} className="tile">
          <span className="bubble violet">
            <Icon d="M8 6h8M8 12h8M8 18h5" />
          </span>
          <b>Live Queue</b>
          <small>See current waiting times</small>
        </Link>
        <Link to="/nearby" className="tile">
          <span className="bubble lilac">
            <Icon d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11zM12 11.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z" />
          </span>
          <b>Nearby Clinics</b>
          <small>Doctors near you</small>
        </Link>
      </div>
      <div className="promo">
        <DoctorArt />
        <div>
          <b>Less waiting, More care!</b>
          <span>Track your token from home.</span>
        </div>
        <span className="heart">♡</span>
      </div>
    </div>
  );
}

function DoctorArt() {
  return (
    <svg className="doc-art" viewBox="0 0 86 86" aria-hidden="true">
      <circle cx="43" cy="43" r="40" fill="#e7fffb" />
      <circle cx="43" cy="32" r="12" fill="#f3c7a6" />
      <path d="M22 70c4-14 12-20 21-20s17 6 21 20" fill="#1a6dff" />
      <path d="M30 46c2 8 8 12 13 12s11-4 13-12" fill="#fff" />
      <circle cx="38" cy="31" r="1.3" fill="#173057" />
      <circle cx="48" cy="31" r="1.3" fill="#173057" />
      <path d="M39 36c2 2 6 2 8 0" stroke="#173057" strokeWidth="1.2" fill="none" />
      <path d="M18 58h10l3 8h24l3-8h10" stroke="#12b5a0" strokeWidth="3" fill="none" strokeLinecap="round" />
    </svg>
  );
}

function Search({ nearby = false }: { nearby?: boolean }) {
  const { user } = useAuth();
  const nav = useNavigate();
  const [params, setParams] = useSearchParams();
  const [kind, setKind] = useState(params.get("kind") || "all");
  const [q, setQ] = useState(params.get("q") || (nearby ? "" : ""));
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");
  const [at, setAt] = useState(Date.now());

  async function load(query = q, filter = kind) {
    try {
      if (!user) {
        const featured = await api<any[]>("/api/doctors/featured", {}, false);
        const needle = query.trim().toLowerCase();
        const results = featured.filter((doctor) => {
          if (filter === "clinic" || filter === "hospital") {
            if (doctor.clinic?.kind !== filter) return false;
          }
          const blob = `${doctor.name} ${doctor.specialty} ${doctor.clinic?.name || ""} ${doctor.clinic?.address || ""}`.toLowerCase();
          return !needle || blob.includes(needle);
        });
        setData({ results, radius_km: null, city: "" });
      } else {
        setData(await api<any>(`/api/doctors?q=${encodeURIComponent(query)}&kind=${filter}`));
      }
      setAt(Date.now());
      setError("");
    } catch (err: any) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
    const id = setInterval(() => load(), 5000);
    return () => clearInterval(id);
  }, [user, q, kind]);

  return (
    <div className="m-page">
      <header className="m-top center-title">
        <button className="icon-btn" onClick={() => nav(-1)} aria-label="Back">
          ←
        </button>
        <h2>{nearby ? "Nearby Clinics" : "Search Doctors"}</h2>
        <span className="icon-spacer" />
      </header>
      <label className="search-pill">
        <Icon d="M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16zm10 2-5.2-5.2" />
        <input
          value={q}
          placeholder="General Physician"
          onChange={(e) => {
            setQ(e.target.value);
            setParams({ q: e.target.value, kind }, { replace: true });
          }}
        />
        {q && (
          <button
            type="button"
            className="clear"
            onClick={() => {
              setQ("");
              setParams({ kind }, { replace: true });
            }}
          >
            ×
          </button>
        )}
      </label>
      <div className="chips">
        {["all", "clinic", "hospital"].map((item) => (
          <button
            key={item}
            className={kind === item ? "chip on" : "chip"}
            onClick={() => {
              setKind(item);
              setParams({ q, kind: item }, { replace: true });
            }}
          >
            {item === "all" ? "All" : item === "clinic" ? "Clinic" : "Hospital"}
          </button>
        ))}
      </div>
      <p className="radius-note">
        {user
          ? `Token booking stays inside ${data?.radius_km || user.plan?.radius_km || 2} km of ${user.city}. Clinics in ${user.area_district || "your district"} still show so you can see the location.`
          : "Sign in to book a token and see the live queue inside your plan radius."}
      </p>
      <ErrorText>{error}</ErrorText>
      <div className="stack">
        {(data?.results || []).map((doctor: any) => (
          <DoctorRow key={doctor.id} doctor={doctor} at={at} />
        ))}
        {data && data.results.length === 0 && <div className="empty">No doctors inside your plan radius. Try a wider plan from Profile.</div>}
      </div>
    </div>
  );
}

function DoctorRow({ doctor, at }: { doctor: any; at: number }) {
  return (
    <Link to={`/doctors/${doctor.id}`} className="doc-row">
      <Avatar name={doctor.name} size={52} />
      <div className="doc-copy">
        <b>{doctor.name}</b>
        <span>{doctor.specialty}</span>
        <span className="pin">
          {doctor.clinic?.name}
          {doctor.clinic?.address ? `, ${doctor.clinic.address}` : ""}
          {doctor.distance_km != null ? ` · ${doctor.distance_km} km` : ""}
          {doctor.outside_plan ? " · map only" : ""}
        </span>
        <span className="rate">
          <Stars value={doctor.rating || 0} /> {Number(doctor.rating || 0).toFixed(1)} ({doctor.rating_count}+ patients)
        </span>
        <span className="row-meta">
          <LiveBadge />
          <em>
            {doctor.waiting_count} patients waiting
            <br />
            Est. Wait <Wait seconds={doctor.est_seconds} at={at} />
          </em>
        </span>
      </div>
      <span className="chev">›</span>
    </Link>
  );
}

function Doctor() {
  const { id } = useParams();
  const { user } = useAuth();
  const nav = useNavigate();
  const [doctor, setDoctor] = useState<any>(null);
  const [tab, setTab] = useState<"queue" | "about">("queue");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [at, setAt] = useState(Date.now());

  async function load() {
    try {
      const next = await api(`/api/doctors/${id}`);
      setDoctor(next);
      setAt(Date.now());
      setError("");
    } catch (err: any) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
    const timer = setInterval(load, 5000);
    return () => clearInterval(timer);
  }, [id]);

  async function favorite() {
    if (!user) return nav(`/login?next=/doctors/${id}`);
    const result = await api(`/api/doctors/${id}/favorite`, { method: "POST" });
    setDoctor((prev: any) => ({ ...prev, is_favorite: result.is_favorite }));
  }

  async function book() {
    if (!user) return nav(`/login?next=/doctors/${id}`);
    setBusy(true);
    setError("");
    try {
      const token = await api<any>("/api/tokens", {
        method: "POST",
        body: JSON.stringify({ doctor_id: Number(id), clinic_id: doctor.clinic?.id }),
      });
      nav(`/token?id=${token.id}`);
    } catch (err: any) {
      if (err.status === 409) nav("/token");
      else setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (!doctor && !error) return <div className="m-page muted">Loading doctor…</div>;
  if (!doctor) {
    return (
      <div className="m-page">
        <button className="text-back" onClick={() => nav(-1)}>
          ← Back
        </button>
        <div className="empty">{error}</div>
        <Link to="/pricing" className="btn btn-primary btn-block">
          See radius plans
        </Link>
      </div>
    );
  }

  return (
    <div className="m-page doctor-page">
      <header className="m-top center-title">
        <button className="icon-btn" onClick={() => nav(-1)} aria-label="Back">
          ←
        </button>
        <h2>Doctor Profile</h2>
        <button className={doctor.is_favorite ? "icon-btn liked" : "icon-btn"} onClick={favorite} aria-label="Favourite">
          {doctor.is_favorite ? "♥" : "♡"}
        </button>
      </header>
      <div className="profile-head">
        <Avatar name={doctor.name} size={74} />
        <div>
          <b>{doctor.name}</b>
          <span>{doctor.specialty}</span>
          <span className="rate">
            <Stars value={doctor.rating || 0} /> {Number(doctor.rating || 0).toFixed(1)} ({doctor.rating_count}+ patients)
          </span>
          <span className="pin">
            {doctor.clinic?.name}, {doctor.clinic?.address}
          </span>
          <span className="pin">{doctor.hours_text}</span>
        </div>
      </div>
      {doctor.clinic && (
        <>
          <ClinicMap
            center={[doctor.clinic.lat, doctor.clinic.lng]}
            zoom={15}
            markers={[
              {
                id: doctor.id,
                lat: doctor.clinic.lat,
                lng: doctor.clinic.lng,
                title: doctor.clinic.name,
                detail: `${doctor.clinic.address}, ${doctor.clinic.city}`,
              },
            ]}
          />
          <a className="muted" href={directionsUrl(doctor.clinic.lat, doctor.clinic.lng)} target="_blank" rel="noreferrer">
            Open {doctor.clinic.city}
            {doctor.clinic.district ? ` · ${doctor.clinic.district}` : ""} on the map
          </a>
        </>
      )}
      <div className="soft-card queue-summary">
        <LiveBadge />
        <div>
          <b>{doctor.waiting_count} patients waiting</b>
          <span>
            Est. Wait <Wait seconds={doctor.est_seconds} at={at} />
          </span>
        </div>
        {doctor.queue_status === "paused" && <em className="pause-pill">Paused · {doctor.pause_reason}</em>}
      </div>
      <button className="btn btn-primary btn-block" onClick={book} disabled={busy || doctor.outside_plan}>
        {busy ? "Booking…" : doctor.outside_plan ? "Outside your token radius" : "Book Appointment"}
      </button>
      {doctor.outside_plan && <p className="muted">You can see this clinic. A token needs a plan that covers the distance.</p>}
      <ErrorText>{error}</ErrorText>
      <div className="seg">
        <button className={tab === "queue" ? "on" : ""} onClick={() => setTab("queue")}>
          Queue
        </button>
        <button className={tab === "about" ? "on" : ""} onClick={() => setTab("about")}>
          About
        </button>
      </div>
      {tab === "queue" ? (
        <div>
          <div className="section-label">
            <b>Current Queue</b>
            <span>{doctor.queue_status === "running" ? "Live" : statusLabel(doctor.queue_status)}</span>
          </div>
          {(doctor.queue || []).map((row: any) => (
            <div key={row.number} className={row.status === "in_consultation" ? "q-line hot" : "q-line"}>
              <b>#{row.number}</b>
              <span>{statusLabel(row.status)}{row.is_you ? " · You" : ""}</span>
              <em>{row.status === "in_consultation" ? "Now" : <Wait seconds={row.est_seconds} ticking={doctor.queue_status === "running"} at={at} />}</em>
            </div>
          ))}
          {doctor.queue?.length === 0 && <div className="empty">No one is waiting right now.</div>}
        </div>
      ) : (
        <div className="about">
          <p>{doctor.bio}</p>
          <p>{doctor.fee_note}</p>
          <p>{doctor.experience_years} years of experience.</p>
          <p className="muted">Estimated wait uses a demo average of {doctor.avg_minutes} minutes per patient until the clinic confirms a real average. It is not a guaranteed time.</p>
          {(doctor.reviews || []).map((review: any, index: number) => (
            <div key={index} className="review">
              <Stars value={review.rating} /> <b>{review.author}</b>
              <p>{review.comment || "Rated the visit."}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function TokenScreen() {
  const { user, refresh } = useAuth();
  const nav = useNavigate();
  const [params] = useSearchParams();
  const [tokens, setTokens] = useState<any[] | null>(null);
  const [at, setAt] = useState(Date.now());
  const [error, setError] = useState("");
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    if (!user) return;
    try {
      setTokens(await api("/api/tokens/mine"));
      setAt(Date.now());
    } catch (err: any) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
    const id = setInterval(load, 4000);
    return () => clearInterval(id);
  }, [user]);

  if (!user) {
    return (
      <div className="auth-screen">
        <h2>Sign in to see your token</h2>
        <Link className="btn btn-primary btn-block" to="/login?next=/token">
          Sign in
        </Link>
      </div>
    );
  }

  const wanted = Number(params.get("id"));
  const active = (tokens || []).filter((token) => ["waiting", "checked_in", "in_consultation"].includes(token.status));
  const token = (tokens || []).find((item) => item.id === wanted) || active[0] || (tokens || [])[0];

  async function toggleNotify() {
    await api("/api/me", { method: "PATCH", body: JSON.stringify({ notify_enabled: !user.notify_enabled }) });
    await refresh();
  }

  async function submitReview(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setBusy(true);
    try {
      await api(`/api/tokens/${token.id}/review`, { method: "POST", body: JSON.stringify({ rating, comment }) });
      setComment("");
      await load();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="token-screen">
      <header className="m-top center-title light">
        <button className="icon-btn light" onClick={() => nav(-1)} aria-label="Back">
          ←
        </button>
        <h2>Your Token</h2>
        <button className="icon-btn light" onClick={load} aria-label="Refresh">
          ↻
        </button>
      </header>
      {!token && <div className="empty light">You have no token yet. Book a doctor to join a queue.</div>}
      {token && (
        <>
          <div className="ring-wrap">
            <svg viewBox="0 0 220 220">
              <circle cx="110" cy="110" r="86" stroke="rgba(255,255,255,.22)" strokeWidth="16" fill="none" />
              <circle
                cx="110"
                cy="110"
                r="86"
                stroke="#3df0cf"
                strokeWidth="16"
                fill="none"
                strokeLinecap="round"
                strokeDasharray="420 140"
                transform="rotate(120 110 110)"
              />
            </svg>
            <div className="ring-label">
              <span>Your Token</span>
              <strong>#{token.number}</strong>
              <em>
                {token.status === "in_consultation"
                  ? "It's your turn"
                  : token.status === "completed"
                    ? "Visit completed"
                    : token.status === "cancelled"
                      ? "Cancelled"
                      : token.status === "no_show"
                        ? "Marked absent"
                        : "You are in queue"}
              </em>
            </div>
          </div>
          <div className="wait-card">
            <span className="clock">⏱</span>
            <div>
              <small>Estimated Waiting Time</small>
              <b>
                {token.status === "in_consultation" ? (
                  "Now"
                ) : (
                  <Wait seconds={token.est_seconds} ticking={token.ticking} at={at} />
                )}
              </b>
            </div>
            <button onClick={load} aria-label="Refresh estimate">
              ↻
            </button>
          </div>
          {token.queue_status === "paused" && <div className="hold">Queue paused · {token.pause_reason}. The estimate is on hold.</div>}
          <ul className="steps">
            <li className="done">You are in queue</li>
            <li className={token.ahead <= 1 ? "done" : ""}>
              {token.ahead} patient{token.ahead === 1 ? "" : "s"} ahead
            </li>
            <li>Get notified when it's your turn</li>
          </ul>
          <button className="btn btn-light btn-block" onClick={toggleNotify}>
            <span>🔔 {user.notify_enabled ? "Notifications On" : "Notifications Off"}</span>
            <small>We'll alert you when it's your turn</small>
          </button>
          <p className="fine">
            {token.doctor?.name} · {token.clinic?.name}. This estimate uses a demo average until the clinic sets a confirmed consultation time.
          </p>
          {token.needs_review && (
            <form className="review-card" onSubmit={submitReview}>
              <b>Rate this visit</b>
              <p>A rating is required after a completed visit.</p>
              <div className="star-pick">
                {[1, 2, 3, 4, 5].map((value) => (
                  <button type="button" key={value} className={value <= rating ? "on" : ""} onClick={() => setRating(value)}>
                    ★
                  </button>
                ))}
              </div>
              <textarea className="field" value={comment} onChange={(e) => setComment(e.target.value)} placeholder="How was the visit?" />
              <ErrorText>{error}</ErrorText>
              <button className="btn btn-primary btn-block" disabled={busy}>
                Submit rating
              </button>
            </form>
          )}
          {["waiting", "checked_in"].includes(token.status) && (
            <button
              className="linkish"
              onClick={async () => {
                await api(`/api/tokens/${token.id}/cancel`, { method: "POST" });
                load();
              }}
            >
              Cancel token
            </button>
          )}
        </>
      )}
      <ErrorText>{error}</ErrorText>
    </div>
  );
}

function Appointments() {
  const { user } = useAuth();
  const [tokens, setTokens] = useState<any[]>([]);
  useEffect(() => {
    if (user) api("/api/tokens/mine").then(setTokens).catch(() => setTokens([]));
  }, [user]);
  if (!user) return <Welcome />;
  return (
    <div className="m-page">
      <header className="m-top">
        <span className="brand-inline">
          <Logo size={32} />
          <Wordmark />
        </span>
        <Bell />
      </header>
      <h2 className="page-title">My Appointments</h2>
      <div className="stack">
        {tokens.map((token) => (
          <Link key={token.id} to={`/token?id=${token.id}`} className="appt">
            <b>#{token.number}</b>
            <div>
              <strong>{token.doctor?.name}</strong>
              <span>{token.clinic?.name}</span>
              <span>{token.day}</span>
            </div>
            <em className={`st ${token.status}`}>{statusLabel(token.status)}</em>
          </Link>
        ))}
        {tokens.length === 0 && <div className="empty">No visits yet. Find a doctor and take a token.</div>}
      </div>
    </div>
  );
}

function Profile() {
  const { user, logout, refresh } = useAuth();
  const nav = useNavigate();
  const [plans, setPlans] = useState<any[]>([]);
  const [favs, setFavs] = useState<any[]>([]);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ name: user?.name || "", phone: user?.phone || "", city: user?.city || "Lahore" });
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/meta").then((meta) => setPlans(meta.plans)).catch(() => undefined);
    api("/api/favorites").then(setFavs).catch(() => setFavs([]));
  }, []);

  if (!user) return <Welcome />;

  async function save(event: FormEvent) {
    event.preventDefault();
    try {
      await api("/api/me", { method: "PATCH", body: JSON.stringify(form) });
      await refresh();
      setEditing(false);
    } catch (err: any) {
      setError(err.message);
    }
  }

  async function locate() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(async (pos) => {
      await api("/api/me/location", {
        method: "POST",
        body: JSON.stringify({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      });
      await refresh();
    });
  }

  return (
    <div className="m-page">
      <header className="m-top">
        <span className="brand-inline">
          <Logo size={32} />
          <Wordmark />
        </span>
        <Bell />
      </header>
      <div className="profile-head">
        <Avatar name={user.name} size={64} />
        <div>
          <b>{user.name}</b>
          <span>{user.email}</span>
          <span className="pin">
            {user.city}
            {user.area_district ? ` · ${user.area_district}` : ""} · {user.plan?.name} · {user.plan?.radius_km} km
          </span>
        </div>
      </div>
      {!editing ? (
        <button className="btn btn-ghost btn-block" onClick={() => setEditing(true)}>
          Edit profile
        </button>
      ) : (
        <form className="stack" onSubmit={save}>
          <input className="field" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input className="field" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="Phone" />
          <PlacePicker
            placeholder="Change place — Multan, Ahmadpur East…"
            onPick={async (place) => {
              await api("/api/me/place", { method: "POST", body: JSON.stringify(place) });
              await refresh();
            }}
          />
          <ErrorText>{error}</ErrorText>
          <button className="btn btn-primary">Save</button>
        </form>
      )}
      <button className="btn btn-ghost btn-block" onClick={locate}>
        Use my current location
      </button>
      <h3>Search radius</h3>
      <p className="muted">Plans only change how far you can search. They are separate from the fee you pay at the clinic. Prices here are placeholders.</p>
      <div className="stack">
        {plans.map((plan) => (
          <button
            key={plan.code}
            className={user.plan_code === plan.code ? "plan on" : "plan"}
            onClick={async () => {
              await api("/api/me/plan", { method: "POST", body: JSON.stringify({ plan_code: plan.code }) });
              await refresh();
            }}
          >
            <b>{plan.name}</b>
            <span>{plan.radius_km} km · PKR {plan.price_pkr}</span>
            <small>{plan.blurb}</small>
          </button>
        ))}
      </div>
      <h3>Favourite doctors</h3>
      {favs.map((doctor) => (
        <Link key={doctor.id} to={`/doctors/${doctor.id}`} className="doc-row slim">
          <Avatar name={doctor.name} size={42} />
          <div>
            <b>{doctor.name}</b>
            <span>{doctor.specialty}</span>
          </div>
        </Link>
      ))}
      {favs.length === 0 && <p className="muted">Save a doctor from their profile.</p>}
      <Credit />
      <button
        className="btn btn-ghost btn-block"
        onClick={() => {
          logout();
          nav("/");
        }}
      >
        Log out
      </button>
    </div>
  );
}

function Pricing() {
  const [plans, setPlans] = useState<any[]>([]);
  useEffect(() => {
    api("/api/meta").then((meta) => setPlans(meta.plans));
  }, []);
  return (
    <div className="m-page">
      <h2 className="page-title">Radius plans</h2>
      <p className="muted">Search distance is enforced by the server. Consultation is still paid at the clinic.</p>
      {plans.map((plan) => (
        <div key={plan.code} className="plan">
          <b>{plan.name}</b>
          <span>{plan.radius_km} km · PKR {plan.price_pkr}</span>
          <small>{plan.blurb}</small>
        </div>
      ))}
    </div>
  );
}

function ForClinics() {
  const [form, setForm] = useState<any>({
    name: "",
    email: "",
    phone: "",
    password: "",
    specialty: "General Physician",
    license_no: "",
    clinic_name: "",
    clinic_kind: "clinic",
    address: "",
    city: "Lahore",
  });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const result = await api<any>("/api/auth/register-doctor", { method: "POST", body: JSON.stringify(form) }, false);
      setMessage(result.message);
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <div className="m-page">
      <h2 className="page-title">List your clinic</h2>
      <p className="muted">An admin reviews the request before the doctor can sign in.</p>
      {message ? (
        <div className="empty">{message}</div>
      ) : (
        <form className="stack" onSubmit={submit}>
          {(["name", "email", "phone", "password", "specialty", "license_no", "clinic_name", "address"] as const).map((key) => (
            <input
              key={key}
              className="field"
              type={key === "password" ? "password" : key === "email" ? "email" : "text"}
              placeholder={key.replace("_", " ")}
              value={(form as any)[key]}
              onChange={(e) => setForm({ ...form, [key]: e.target.value })}
              required={key !== "phone" && key !== "license_no"}
            />
          ))}
          <PlacePicker
            placeholder="Clinic place — Bahawalpur, a street…"
            onPick={(place) =>
              setForm({
                ...form,
                city: place.name,
                lat: place.lat,
                lng: place.lng,
                district: place.district,
                division: place.division,
              })
            }
          />
          <select className="field" value={form.clinic_kind} onChange={(e) => setForm({ ...form, clinic_kind: e.target.value })}>
            <option value="clinic">Clinic</option>
            <option value="hospital">Hospital</option>
          </select>
          <ErrorText>{error}</ErrorText>
          <button className="btn btn-primary">Submit for approval</button>
        </form>
      )}
    </div>
  );
}
