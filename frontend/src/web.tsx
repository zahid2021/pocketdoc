import { FormEvent, ReactNode, useEffect, useRef, useState } from "react";
import { Link, NavLink, Route, Routes, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api, statusLabel } from "./api";
import { AreaMap, ClinicMap, directionsUrl, PlacePicker } from "./mapui";
import { useAuth } from "./auth";
import { Avatar, Bell, Credit, DemoAccounts, ErrorText, LiveBadge, Logo, Stars, Wait, Wordmark } from "./bits";

function Shell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  return (
    <div className="site">
      <header className="site-nav">
        <Link to="/" className="brand-inline">
          <Logo size={40} />
          <Wordmark />
        </Link>
        <nav>
          <NavLink to="/search">Find doctors</NavLink>
          <NavLink to="/nearby">Map</NavLink>
          <NavLink to="/pricing">Pricing</NavLink>
          <NavLink to="/for-clinics">For clinics</NavLink>
          {user?.role === "admin" && <NavLink to="/admin">Admin panel</NavLink>}
          {user && user.role !== "admin" && <NavLink to="/appointments">My visits</NavLink>}
          {user && user.role !== "admin" && <NavLink to="/token">My token</NavLink>}
        </nav>
        <div className="nav-end">
          {user ? (
            <>
              <Bell />
              <Link to={user.role === "admin" ? "/admin" : "/profile"} className="who">
                {user.name.split(" ")[0]}
              </Link>
              <button className="btn btn-ghost tiny" onClick={logout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn btn-ghost tiny">
                Log in
              </Link>
              <Link to="/register" className="btn btn-primary tiny">
                Get started
              </Link>
            </>
          )}
        </div>
      </header>
      <main>{children}</main>
      <footer className="site-foot">
        <div>
          <Wordmark />
          <p>Your Turn. Our Priority. Ab wait nahi, sirf update.</p>
          <Credit />
        </div>
        <small>Live waiting time and queue management for clinics and hospitals.</small>
      </footer>
    </div>
  );
}

export function PatientWeb() {
  return (
    <Shell>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/search" element={<Search />} />
        <Route path="/nearby" element={<div className="panel"><h1>Clinic map</h1><p className="muted">Search any city, town or street in Pakistan and see the clinic pin.</p><AreaMap tall /></div>} />
        <Route path="/doctors/:id" element={<Doctor />} />
        <Route path="/token" element={<TokenPage />} />
        <Route path="/appointments" element={<Appointments />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/for-clinics" element={<ForClinics />} />
        <Route path="*" element={<Home />} />
      </Routes>
    </Shell>
  );
}

function Home() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [q, setQ] = useState("General Physician");
  const [featured, setFeatured] = useState<any[]>([]);
  const [at, setAt] = useState(Date.now());

  useEffect(() => {
    let stop = false;
    async function load() {
      try {
        const rows = await api<any[]>("/api/doctors/featured");
        if (!stop) {
          setFeatured(rows);
          setAt(Date.now());
        }
      } catch {
        /* ignore */
      }
    }
    load();
    const id = setInterval(load, 8000);
    return () => {
      stop = true;
      clearInterval(id);
    };
  }, [user]);

  return (
    <div>
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow">Live queue · Pakistan</span>
          <h1>Know exactly when your doctor will see you.</h1>
          <p>Search a clinic, take a token, and watch the waiting time from home. The same queue the doctor and reception desk are running.</p>
          <form
            className="hero-search"
            onSubmit={(event) => {
              event.preventDefault();
              if (!user) nav(`/login?next=/search?q=${encodeURIComponent(q)}`);
              else nav(`/search?q=${encodeURIComponent(q)}`);
            }}
          >
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Specialty, doctor or clinic" />
            <button className="btn btn-primary">Search</button>
          </form>
          <div className="hero-points">
            <span>Token number</span>
            <span>Patients ahead</span>
            <span>Estimated wait</span>
          </div>
        </div>
        <aside className="preview-card">
          <div className="preview-top">
            <span>Now serving</span>
            <LiveBadge />
          </div>
          <strong>#11</strong>
          <p>Dr. Ahmed Khan · City Clinic</p>
          <div className="preview-row">
            <div>
              <small>Your token</small>
              <b>#18</b>
            </div>
            <div>
              <small>Estimated</small>
              <b>42 min</b>
            </div>
          </div>
          <em>Ab wait nahi, sirf update.</em>
        </aside>
      </section>
      <section className="how-steps">
        {[
          ["01", "Find a doctor", "Search by name, specialty or clinic inside your plan radius."],
          ["02", "Take a token", "Join today’s queue. Walk-ins from reception share the same list."],
          ["03", "Watch it live", "When the doctor taps Next, your wait and alerts update."],
        ].map(([n, title, copy]) => (
          <article key={n}>
            <span>{n}</span>
            <b>{title}</b>
            <p>{copy}</p>
          </article>
        ))}
      </section>
      <section className="band">
        <div className="band-head">
          <h2>Doctors with a live queue</h2>
          <Link to={user ? "/search" : "/login?next=/search"}>See all inside your radius</Link>
        </div>
        <div className="doc-grid">
          {featured.map((doctor) => (
            <Link key={doctor.id} to={`/doctors/${doctor.id}`} className="web-doc">
              <Avatar name={doctor.name} size={56} />
              <div>
                <b>{doctor.name}</b>
                <span>{doctor.specialty}</span>
                <span className="pin">
                  {doctor.clinic?.name}, {doctor.clinic?.address}
                </span>
                <span className="rate">
                  <Stars value={doctor.rating || 0} /> {Number(doctor.rating || 0).toFixed(1)}
                </span>
              </div>
              <div className="web-doc-side">
                <LiveBadge />
                <em>{doctor.waiting_count} waiting</em>
                <strong>
                  {doctor.waiting_count === 0 ? "Quiet" : <Wait seconds={doctor.est_seconds} at={at} />}
                </strong>
              </div>
            </Link>
          ))}
        </div>
      </section>
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
  const openedAdmin = useRef(false);

  function openAdmin() {
    if (openedAdmin.current || window.location.pathname === "/admin") return;
    openedAdmin.current = true;
    window.history.replaceState(window.history.state, "", "/");
    nav("/admin");
  }

  useEffect(() => {
    if (!user || window.location.pathname !== "/login") return;
    if (user.role === "admin") openAdmin();
    else nav(params.get("next") || "/", { replace: true });
  }, [user]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      const account = await login(email, password);
      if (account?.role === "admin") openAdmin();
      else nav(params.get("next") || "/", { replace: true });
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <div className="narrow">
      <h1>Sign in</h1>
      <p className="muted">One login for patients. Doctors, reception and admin land in their own desk.</p>
      <form className="stack" onSubmit={submit}>
        <input className="field" type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input className="field" type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <ErrorText>{error}</ErrorText>
        <button className="btn btn-primary">Sign in</button>
      </form>
      <DemoAccounts
        onPick={(nextEmail, nextPassword) => {
          setEmail(nextEmail);
          setPassword(nextPassword);
        }}
      />
    </div>
  );
}

function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [form, setForm] = useState<any>({ name: "", email: "", phone: "", password: "", city: "Lahore" });
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      await register(form);
      nav("/");
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <div className="narrow">
      <h1>Create a patient account</h1>
      <form className="stack" onSubmit={submit}>
        <input className="field" placeholder="Full name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        <input className="field" type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
        <input className="field" placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
        <PlacePicker
          placeholder="Your place — Bahawalpur, Multan, a street…"
          onPick={(place) => setForm({ ...form, city: place.name, lat: place.lat, lng: place.lng, district: place.district, division: place.division })}
        />
        <input className="field" type="password" placeholder="Password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
        <ErrorText>{error}</ErrorText>
        <button className="btn btn-primary">Get started</button>
      </form>
    </div>
  );
}

function Search({ nearby = false }: { nearby?: boolean }) {
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState(params.get("q") || "");
  const [kind, setKind] = useState("all");
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");
  const [at, setAt] = useState(Date.now());

  async function load(query = q, filter = kind) {
    const next = await api<any>(`/api/doctors?q=${encodeURIComponent(query)}&kind=${filter}`);
    setData(next);
    setAt(Date.now());
  }

  useEffect(() => {
    if (!user) return;
    load().catch((err) => setError(err.message));
    const id = setInterval(() => load().catch(() => undefined), 6000);
    return () => clearInterval(id);
  }, [user, q, kind]);

  if (!user) {
    return (
      <div className="narrow">
        <h1>Sign in to search live queues</h1>
        <p className="muted">Radius rules are checked on the server, from your city or your current location.</p>
        <Link className="btn btn-primary" to="/login?next=/search">
          Sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="panel">
      <div className="band-head">
        <div>
          <h1>{nearby ? "Nearby clinics" : "Find a doctor"}</h1>
          <p className="muted">
            {data ? `${data.results.length} doctors around ${data.city}. Tokens stay inside ${data.radius_km} km. Same-district clinics stay visible.` : "Loading your area…"}
          </p>
        </div>
        <form
          className="hero-search slim"
          onSubmit={(event) => {
            event.preventDefault();
            setParams({ q });
            load().catch((err) => setError(err.message));
          }}
        >
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Name, specialty or clinic" />
          <button className="btn btn-primary">Search</button>
        </form>
      </div>
      <div className="chips">
        {["all", "clinic", "hospital"].map((item) => (
          <button key={item} className={kind === item ? "chip on" : "chip"} onClick={() => setKind(item)}>
            {item[0].toUpperCase() + item.slice(1)}
          </button>
        ))}
      </div>
      <ErrorText>{error}</ErrorText>
      <div className="doc-grid">
        {(data?.results || []).map((doctor: any) => (
          <Link key={doctor.id} to={`/doctors/${doctor.id}`} className="web-doc">
            <Avatar name={doctor.name} size={54} />
            <div>
              <b>{doctor.name}</b>
              <span>{doctor.specialty}</span>
              <span className="pin">
                {doctor.clinic?.name} · {doctor.clinic?.address} · {doctor.distance_km} km{doctor.outside_plan ? " · map only" : ""}
              </span>
              <span className="rate">
                <Stars value={doctor.rating || 0} /> {Number(doctor.rating || 0).toFixed(1)} ({doctor.rating_count})
              </span>
            </div>
            <div className="web-doc-side">
              <LiveBadge />
              <em>{doctor.waiting_count} waiting</em>
              <strong>
                {doctor.waiting_count === 0 ? "Quiet" : <Wait seconds={doctor.est_seconds} at={at} />}
              </strong>
            </div>
          </Link>
        ))}
      </div>
      {data && data.results.length === 0 && <div className="empty">Nothing inside this radius. Widen the plan on your profile.</div>}
    </div>
  );
}

function Doctor() {
  const { id } = useParams();
  const { user } = useAuth();
  const nav = useNavigate();
  const [doctor, setDoctor] = useState<any>(null);
  const [error, setError] = useState("");
  const [at, setAt] = useState(Date.now());
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let stop = false;
    async function load() {
      try {
        const next = await api(`/api/doctors/${id}`);
        if (!stop) {
          setDoctor(next);
          setAt(Date.now());
          setError("");
        }
      } catch (err: any) {
        if (!stop) setError(err.message);
      }
    }
    load();
    const timer = setInterval(load, 5000);
    return () => {
      stop = true;
      clearInterval(timer);
    };
  }, [id]);

  async function book() {
    if (!user) return nav(`/login?next=/doctors/${id}`);
    setBusy(true);
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

  if (error && !doctor) {
    return (
      <div className="narrow">
        <h1>Outside your plan</h1>
        <p>{error}</p>
        <Link to="/pricing">View radius plans</Link>
      </div>
    );
  }
  if (!doctor) return <div className="panel muted">Loading…</div>;

  return (
    <div className="split">
      <section className="card-block">
        <div className="profile-head">
          <Avatar name={doctor.name} size={84} />
          <div>
            <h1>{doctor.name}</h1>
            <p>{doctor.specialty}</p>
            <p className="rate">
              <Stars value={doctor.rating || 0} /> {Number(doctor.rating || 0).toFixed(1)} · {doctor.rating_count} patients
            </p>
            <p className="pin">
              {doctor.clinic?.name}, {doctor.clinic?.address}, {doctor.clinic?.city}
              {doctor.distance_km != null ? ` · ${doctor.distance_km} km` : ""}
            </p>
            <p className="muted">{doctor.hours_text}</p>
          </div>
        </div>
        {doctor.clinic && (
          <>
            <ClinicMap
              center={[doctor.clinic.lat, doctor.clinic.lng]}
              zoom={15}
              markers={[{ id: doctor.id, lat: doctor.clinic.lat, lng: doctor.clinic.lng, title: doctor.clinic.name, detail: `${doctor.clinic.address}, ${doctor.clinic.city}` }]}
            />
            <p>
              <a href={directionsUrl(doctor.clinic.lat, doctor.clinic.lng)} target="_blank" rel="noreferrer">
                {doctor.clinic.address}, {doctor.clinic.city}
                {doctor.clinic.district ? ` · ${doctor.clinic.district} district` : ""}
              </a>
            </p>
          </>
        )}
        <p>{doctor.bio}</p>
        <p>{doctor.fee_note}</p>
        <p className="muted">Estimated wait uses a demo average of {doctor.avg_minutes} min per patient. It updates when the doctor calls Next, pauses, or resumes. It is not a confirmed appointment time.</p>
        <div className="btn-row">
          <button className="btn btn-primary" disabled={busy || doctor.outside_plan} onClick={book}>
            {busy ? "Booking…" : doctor.outside_plan ? "Outside your token radius" : "Take a token"}
          </button>
          {user && (
            <button
              className="btn btn-ghost"
              onClick={async () => {
                const result = await api(`/api/doctors/${id}/favorite`, { method: "POST" });
                setDoctor({ ...doctor, is_favorite: result.is_favorite });
              }}
            >
              {doctor.is_favorite ? "Saved" : "Save doctor"}
            </button>
          )}
        </div>
        <ErrorText>{error}</ErrorText>
        <h3>Reviews</h3>
        {(doctor.reviews || []).length === 0 && <p className="muted">No written reviews yet.</p>}
        {(doctor.reviews || []).map((review: any, index: number) => (
          <div key={index} className="review">
            <Stars value={review.rating} /> <b>{review.author}</b>
            <p>{review.comment}</p>
          </div>
        ))}
      </section>
      <aside className="card-block">
        <div className="section-label">
          <b>Live queue</b>
          <LiveBadge />
        </div>
        <p className="muted">
          {doctor.waiting_count} waiting · {statusLabel(doctor.queue_status)}
          {doctor.pause_reason ? ` · ${doctor.pause_reason}` : ""}
        </p>
        <div className="table">
          {(doctor.queue || []).map((row: any) => (
            <div key={row.number} className={row.status === "in_consultation" ? "q-line hot" : "q-line"}>
              <b>#{row.number}</b>
              <span>
                {statusLabel(row.status)}
                {row.is_you ? " · You" : ""}
              </span>
              <em>
                <Wait seconds={row.est_seconds} ticking={doctor.queue_status === "running" && row.status !== "in_consultation"} at={at} />
              </em>
            </div>
          ))}
        </div>
      </aside>
    </div>
  );
}

function TokenPage() {
  const { user, refresh } = useAuth();
  const [params] = useSearchParams();
  const [tokens, setTokens] = useState<any[]>([]);
  const [at, setAt] = useState(Date.now());
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [error, setError] = useState("");

  async function load() {
    const rows = await api<any[]>("/api/tokens/mine");
    setTokens(rows);
    setAt(Date.now());
  }

  useEffect(() => {
    if (!user) return;
    load().catch((err) => setError(err.message));
    const id = setInterval(() => load().catch(() => undefined), 4000);
    return () => clearInterval(id);
  }, [user]);

  if (!user) {
    return (
      <div className="narrow">
        <h1>Sign in to track your token</h1>
        <Link className="btn btn-primary" to="/login?next=/token">
          Sign in
        </Link>
      </div>
    );
  }

  const wanted = Number(params.get("id"));
  const active = tokens.filter((token) => ["waiting", "checked_in", "in_consultation"].includes(token.status));
  const token = tokens.find((item) => item.id === wanted) || active[0];

  return (
    <div className="split">
      <section className="desk-token">
        <p className="eyebrow">Patient desk</p>
        <h1>{token ? `Token #${token.number}` : "No active token"}</h1>
        {token ? (
          <>
            <p>
              {token.doctor?.name} · {token.clinic?.name}
            </p>
            <div className="big-wait">
              <span>Estimated wait</span>
              <strong>
                {token.status === "in_consultation" ? "It’s your turn" : <Wait seconds={token.est_seconds} ticking={token.ticking} at={at} />}
              </strong>
              <em>{token.ahead} ahead · {statusLabel(token.status)}</em>
            </div>
            {token.queue_status === "paused" && <div className="hold dark">Paused · {token.pause_reason}. Estimate is on hold.</div>}
            <p className="muted">The number moves only when the clinic updates the queue. This page refreshes every few seconds.</p>
            {token.needs_review && (
              <form
                className="stack"
                onSubmit={async (event) => {
                  event.preventDefault();
                  await api(`/api/tokens/${token.id}/review`, { method: "POST", body: JSON.stringify({ rating, comment }) });
                  setComment("");
                  load();
                }}
              >
                <b>Rate the completed visit</b>
                <div className="star-pick">
                  {[1, 2, 3, 4, 5].map((value) => (
                    <button type="button" key={value} className={value <= rating ? "on" : ""} onClick={() => setRating(value)}>
                      ★
                    </button>
                  ))}
                </div>
                <textarea className="field" value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Optional note" />
                <button className="btn btn-primary">Submit rating</button>
              </form>
            )}
          </>
        ) : (
          <Link to="/search" className="btn btn-primary">
            Find a doctor
          </Link>
        )}
        <ErrorText>{error}</ErrorText>
      </section>
      <aside className="card-block">
        <h3>Alerts</h3>
        <button
          className="btn btn-ghost"
          onClick={async () => {
            await api("/api/me", { method: "PATCH", body: JSON.stringify({ notify_enabled: !user.notify_enabled }) });
            refresh();
          }}
        >
          {user.notify_enabled ? "Notifications on" : "Notifications off"}
        </button>
        <h3>Today and earlier</h3>
        {tokens.map((item) => (
          <Link key={item.id} to={`/token?id=${item.id}`} className="appt">
            <b>#{item.number}</b>
            <div>
              <strong>{item.doctor?.name}</strong>
              <span>{item.day}</span>
            </div>
            <em className={`st ${item.status}`}>{statusLabel(item.status)}</em>
          </Link>
        ))}
      </aside>
    </div>
  );
}

function Appointments() {
  const { user } = useAuth();
  const [tokens, setTokens] = useState<any[]>([]);
  useEffect(() => {
    if (user) api("/api/tokens/mine").then(setTokens).catch(() => undefined);
  }, [user]);
  if (!user) return <Login />;
  return (
    <div className="panel">
      <h1>My visits</h1>
      <div className="table-card">
        {tokens.map((token) => (
          <Link key={token.id} to={`/token?id=${token.id}`} className="appt wide">
            <b>#{token.number}</b>
            <div>
              <strong>{token.doctor?.name}</strong>
              <span>
                {token.clinic?.name} · {token.day} · {token.source}
              </span>
            </div>
            <em className={`st ${token.status}`}>{statusLabel(token.status)}</em>
          </Link>
        ))}
        {tokens.length === 0 && <div className="empty">No tokens yet.</div>}
      </div>
    </div>
  );
}

function Profile() {
  const { user, refresh, logout } = useAuth();
  const [plans, setPlans] = useState<any[]>([]);
  const [favs, setFavs] = useState<any[]>([]);
  const [form, setForm] = useState({ name: user?.name || "", phone: user?.phone || "", city: user?.city || "Lahore" });
  const [error, setError] = useState("");

  useEffect(() => {
    api("/api/meta").then((meta) => setPlans(meta.plans));
    if (user) api("/api/favorites").then(setFavs).catch(() => undefined);
  }, [user]);

  if (!user) return <Login />;

  return (
    <div className="split">
      <section className="card-block">
        <h1>Profile</h1>
        <form
          className="stack"
          onSubmit={async (event) => {
            event.preventDefault();
            try {
              await api("/api/me", { method: "PATCH", body: JSON.stringify(form) });
              await refresh();
            } catch (err: any) {
              setError(err.message);
            }
          }}
        >
          <input className="field" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <input className="field" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <PlacePicker
            placeholder="Change place — Bahawalpur, Basti Malook…"
            onPick={async (place) => {
              await api("/api/me/place", { method: "POST", body: JSON.stringify(place) });
              await refresh();
            }}
          />
          <ErrorText>{error}</ErrorText>
          <div className="btn-row">
            <button className="btn btn-primary">Save profile</button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => {
                navigator.geolocation?.getCurrentPosition(async (pos) => {
                  await api("/api/me/location", { method: "POST", body: JSON.stringify({ lat: pos.coords.latitude, lng: pos.coords.longitude }) });
                  refresh();
                });
              }}
            >
              Use my location
            </button>
          </div>
        </form>
        <h3>Favourites</h3>
        {favs.map((doctor) => (
          <Link key={doctor.id} to={`/doctors/${doctor.id}`} className="doc-row slim">
            <Avatar name={doctor.name} />
            <div>
              <b>{doctor.name}</b>
              <span>{doctor.specialty}</span>
            </div>
          </Link>
        ))}
        <button className="btn btn-ghost" onClick={logout}>
          Log out
        </button>
      </section>
      <aside className="card-block">
        <h3>Your search radius</h3>
        <p className="muted">Current plan: {user.plan?.name} · {user.plan?.radius_km} km. Changing a plan does not charge a card in this version.</p>
        {plans.map((plan) => (
          <button
            key={plan.code}
            className={user.plan_code === plan.code ? "plan on" : "plan"}
            onClick={async () => {
              await api("/api/me/plan", { method: "POST", body: JSON.stringify({ plan_code: plan.code }) });
              refresh();
            }}
          >
            <b>{plan.name}</b>
            <span>
              {plan.radius_km} km · PKR {plan.price_pkr}
            </span>
            <small>{plan.blurb}</small>
          </button>
        ))}
      </aside>
    </div>
  );
}

function Pricing() {
  const [plans, setPlans] = useState<any[]>([]);
  useEffect(() => {
    api("/api/meta").then((meta) => setPlans(meta.plans));
  }, []);
  return (
    <div className="panel">
      <h1>How far you can search</h1>
      <p className="muted">PocketDoc does not collect the doctor’s consultation fee. These plans only control search radius, and the server enforces them.</p>
      <div className="plan-grid">
        {plans.map((plan) => (
          <article key={plan.code} className="plan">
            <b>{plan.name}</b>
            <strong>{plan.radius_km} km</strong>
            <span>PKR {plan.price_pkr} / month placeholder</span>
            <p>{plan.blurb}</p>
          </article>
        ))}
      </div>
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
    try {
      const result = await api<any>("/api/auth/register-doctor", { method: "POST", body: JSON.stringify(form) }, false);
      setMessage(result.message);
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <div className="narrow">
      <h1>Bring your clinic onto PocketDoc</h1>
      <p className="muted">Doctors get a queue desk. Reception can check patients in. An admin approves the account first.</p>
      {message ? (
        <div className="empty">{message}</div>
      ) : (
        <form className="stack" onSubmit={submit}>
          <input className="field" placeholder="Doctor name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          <input className="field" type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          <input className="field" placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
          <input className="field" type="password" placeholder="Password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          <input className="field" placeholder="Specialty" value={form.specialty} onChange={(e) => setForm({ ...form, specialty: e.target.value })} required />
          <input className="field" placeholder="Licence number" value={form.license_no} onChange={(e) => setForm({ ...form, license_no: e.target.value })} />
          <input className="field" placeholder="Clinic name" value={form.clinic_name} onChange={(e) => setForm({ ...form, clinic_name: e.target.value })} required />
          <input className="field" placeholder="Address" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} required />
          <PlacePicker
            placeholder="Clinic place — Multan, a gali…"
            onPick={(place) => setForm({ ...form, city: place.name, lat: place.lat, lng: place.lng, district: place.district, division: place.division })}
          />
          <select className="field" value={form.clinic_kind} onChange={(e) => setForm({ ...form, clinic_kind: e.target.value })}>
            <option value="clinic">Clinic</option>
            <option value="hospital">Hospital</option>
          </select>
          <ErrorText>{error}</ErrorText>
          <button className="btn btn-primary">Request approval</button>
        </form>
      )}
    </div>
  );
}
