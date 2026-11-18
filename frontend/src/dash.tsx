import { FormEvent, ReactNode, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, statusLabel } from "./api";
import { PlacePicker } from "./mapui";
import { useAuth } from "./auth";
import { Bell, Credit, ErrorText, Logo, Wait, Wordmark } from "./bits";

function Desk({
  title,
  items,
  tab,
  setTab,
  children,
}: {
  title: string;
  items: string[];
  tab: string;
  setTab: (tab: string) => void;
  children: ReactNode;
}) {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  useEffect(() => {
    if (title === "Super admin") return;
    if (window.location.pathname !== "/") nav("/", { replace: true });
  }, [title]);
  return (
    <div className="dash">
      <aside className="side">
        <div className="brand-inline">
          <Logo size={36} />
          <Wordmark />
        </div>
        <small className="side-kicker">{title}</small>
        {title === "Super admin" && (
          <button className="side-link" onClick={() => nav("/")}>
            Main page
          </button>
        )}
        {items.map((item) => (
          <button key={item} className={tab === item ? "side-link on" : "side-link"} onClick={() => setTab(item)}>
            {item}
          </button>
        ))}
        <div className="side-user">
          <b>{user?.name}</b>
          <span>{user?.email}</span>
          <button
            onClick={() => {
              logout();
              nav("/");
            }}
          >
            Log out
          </button>
        </div>
      </aside>
      <section className="desk-main">
        <header className="desk-top">
          <div>
            <p className="eyebrow">{title}</p>
            <h1>{tab}</h1>
          </div>
          <Bell />
        </header>
        {children}
        <Credit />
      </section>
    </div>
  );
}

function Stats({ counts }: { counts: Record<string, number> }) {
  const items = [
    ["Total", counts.total],
    ["Waiting", counts.waiting],
    ["Checked in", counts.checked_in],
    ["In room", counts.in_consultation],
    ["Done", counts.completed],
    ["Absent", counts.no_show],
    ["Cancelled", counts.cancelled],
  ];
  return (
    <div className="stat-grid">
      {items.map(([label, value]) => (
        <article key={String(label)}>
          <span>{label}</span>
          <b>{value ?? 0}</b>
        </article>
      ))}
    </div>
  );
}

function QueueTable({ rows, at, full, onCheck, onMiss, onCancel }: any) {
  return (
    <div className="table-card">
      <div className="t-head">
        <span>Token</span>
        <span>Patient</span>
        <span>Status</span>
        <span>Wait</span>
        {full && <span>Actions</span>}
      </div>
      {rows.map((row: any) => (
        <div className="t-row" key={row.id}>
          <b>#{row.number}</b>
          <span>
            {row.patient_name}
            {full && row.phone ? <small>{row.phone}</small> : null}
            <small>{row.source}</small>
          </span>
          <em className={`st ${row.status}`}>{statusLabel(row.status)}</em>
          <span>{row.status === "in_consultation" ? "Now" : ["waiting", "checked_in"].includes(row.status) ? <Wait seconds={row.est_seconds || 0} at={at} /> : "—"}</span>
          {full && (
            <span className="btn-row tight">
              {row.status === "waiting" && (
                <button className="btn tiny" onClick={() => onCheck(row.id)}>
                  Check in
                </button>
              )}
              {["waiting", "checked_in"].includes(row.status) && (
                <>
                  <button className="btn tiny ghost" onClick={() => onMiss(row.id)}>
                    No-show
                  </button>
                  <button className="btn tiny ghost" onClick={() => onCancel(row.id)}>
                    Cancel
                  </button>
                </>
              )}
            </span>
          )}
        </div>
      ))}
      {rows.length === 0 && <div className="empty">No tokens today.</div>}
    </div>
  );
}

function Controls({ status, can, onStart, onPause, onResume, onNext }: any) {
  const [reason, setReason] = useState("Prayer Time");
  const [open, setOpen] = useState(false);
  if (!can) return <p className="muted">Queue controls are off for this account. You can still check patients in.</p>;
  return (
    <div className="controls">
      <div className={`run-state ${status}`}>{statusLabel(status)}</div>
      {status === "not_started" || status === "completed" ? (
        <button className="btn btn-primary" onClick={onStart}>
          Start
        </button>
      ) : null}
      {status === "running" && (
        <button className="btn btn-ghost" onClick={() => setOpen(true)}>
          Pause
        </button>
      )}
      {status === "paused" && (
        <button className="btn btn-primary" onClick={onResume}>
          Resume
        </button>
      )}
      <button className="btn btn-teal" type="button" onClick={onNext} disabled={status !== "running"} title={status === "running" ? "Call the next patient" : "Start the queue before calling Next"}>
        Next
      </button>
      {open && (
        <div className="pause-box">
          {["Lunch Break", "Prayer Time", "Short Delay", "Other"].map((item) => (
            <button key={item} className={reason === item ? "chip on" : "chip"} onClick={() => setReason(item)}>
              {item}
            </button>
          ))}
          <button
            className="btn btn-primary tiny"
            onClick={() => {
              setOpen(false);
              onPause(reason);
            }}
          >
            Confirm pause
          </button>
        </div>
      )}
    </div>
  );
}

export function DoctorDash() {
  const [tab, setTab] = useState("Today’s queue");
  const [board, setBoard] = useState<any>(null);
  const [at, setAt] = useState(Date.now());
  const [error, setError] = useState("");
  const [avg, setAvg] = useState(6);
  const [bio, setBio] = useState("");
  const [hours, setHours] = useState("");

  async function load() {
    const next = await api<any>("/api/doctor/queue");
    setBoard(next);
    setAt(Date.now());
    setAvg(next.doctor.avg_minutes);
  }

  useEffect(() => {
    load().catch((err) => setError(err.message));
    const id = setInterval(() => load().catch(() => undefined), 4000);
    return () => clearInterval(id);
  }, []);

  async function act(path: string, body?: any) {
    setError("");
    try {
      const next = await api<any>(path, { method: "POST", body: body ? JSON.stringify(body) : "{}" });
      setBoard(next);
      setAt(Date.now());
    } catch (err: any) {
      setError(err.message);
    }
  }

  return (
    <Desk title="Doctor desk" items={["Today’s queue", "Settings"]} tab={tab} setTab={setTab}>
      <ErrorText>{error}</ErrorText>
      {tab === "Today’s queue" && board && (
        <>
          <div className="desk-intro">
            <div>
              <h2>
                {board.clinic?.name} · {board.doctor.specialty}
              </h2>
              <p className="muted">Patients are shown by token only. Full phone numbers stay at reception.</p>
            </div>
            <Controls
              status={board.queue_status}
              can
              onStart={() => act("/api/doctor/queue/start")}
              onResume={() => act("/api/doctor/queue/resume")}
              onNext={() => act("/api/doctor/queue/next")}
              onPause={(reason: string) => act("/api/doctor/queue/pause", { reason })}
            />
          </div>
          {board.pause_reason && <div className="hold dark">Paused · {board.pause_reason}</div>}
          <Stats counts={board.counts} />
          <QueueTable rows={board.tokens.filter((row: any) => row.status !== "cancelled")} at={at} full={false} />
        </>
      )}
      {tab === "Settings" && (
        <form
          className="card-block narrow-form"
          onSubmit={async (event) => {
            event.preventDefault();
            await api("/api/doctor/settings", {
              method: "PATCH",
              body: JSON.stringify({
                avg_minutes: Number(avg),
                ...(bio.trim() ? { bio } : {}),
                ...(hours.trim() ? { hours_text: hours } : {}),
              }),
            });
            setError("");
            load();
            setTab("Today’s queue");
          }}
        >
          <h2>Consultation estimate</h2>
          <p className="muted">This is a demo average used only to estimate waiting time. Do not treat it as a confirmed duration until you have observed real visits.</p>
          <label>
            Average minutes per patient
            <input className="field" type="number" min={3} max={60} value={avg} onChange={(e) => setAvg(Number(e.target.value))} />
          </label>
          <label>
            About you
            <textarea className="field" value={bio} onChange={(e) => setBio(e.target.value)} />
          </label>
          <label>
            Hours
            <input className="field" value={hours} onChange={(e) => setHours(e.target.value)} placeholder="Mon – Sat 9:00 AM – 5:00 PM" />
          </label>
          <button className="btn btn-primary">Save</button>
        </form>
      )}
    </Desk>
  );
}

export function ReceptionDash() {
  const [tab, setTab] = useState("Front desk");
  const [data, setData] = useState<any>(null);
  const [at, setAt] = useState(Date.now());
  const [error, setError] = useState("");
  const [form, setForm] = useState({ doctor_id: "", name: "", phone: "" });
  const [flash, setFlash] = useState("");

  async function load() {
    const next = await api<any>("/api/reception/overview");
    setData(next);
    setAt(Date.now());
    if (!form.doctor_id && next.boards[0]) setForm((prev) => ({ ...prev, doctor_id: String(next.boards[0].doctor.id) }));
  }

  useEffect(() => {
    load().catch((err) => setError(err.message));
    const id = setInterval(() => load().catch(() => undefined), 4000);
    return () => clearInterval(id);
  }, []);

  async function call(path: string, body?: any) {
    setError("");
    try {
      await api(path, { method: "POST", body: body ? JSON.stringify(body) : "{}" });
      await load();
    } catch (err: any) {
      setError(err.message);
    }
  }

  function download() {
    if (!data) return;
    const lines = [["token", "patient", "phone", "doctor", "status", "source"]];
    data.boards.forEach((board: any) => {
      board.tokens.forEach((row: any) => {
        lines.push([row.number, row.patient_name, row.phone || "", board.doctor.name, row.status, row.source]);
      });
    });
    const csv = lines.map((line) => line.map((cell: string) => `"${String(cell).replaceAll('"', '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "pocketdoc-today.csv";
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <Desk title="Reception" items={["Front desk", "Walk-in", "Report"]} tab={tab} setTab={setTab}>
      <ErrorText>{error}</ErrorText>
      {flash && <div className="empty">{flash}</div>}
      {tab === "Front desk" && data && (
        <>
          <Stats counts={data.counts} />
          {data.boards.map((board: any) => (
            <section key={board.doctor.id} className="card-block">
              <div className="desk-intro">
                <div>
                  <h2>{board.doctor.name}</h2>
                  <p className="muted">
                    {board.clinic?.name} · {statusLabel(board.queue_status)}
                    {board.pause_reason ? ` · ${board.pause_reason}` : ""}
                  </p>
                </div>
                <Controls
                  status={board.queue_status}
                  can={board.can_operate}
                  onStart={() => call(`/api/reception/queue/${board.doctor.id}/start`)}
                  onResume={() => call(`/api/reception/queue/${board.doctor.id}/resume`)}
                  onNext={() => call(`/api/reception/queue/${board.doctor.id}/next`)}
                  onPause={(reason: string) => call(`/api/reception/queue/${board.doctor.id}/pause`, { reason })}
                />
              </div>
              <QueueTable
                rows={board.tokens}
                at={at}
                full
                onCheck={(id: number) => call(`/api/reception/tokens/${id}/checkin`)}
                onMiss={(id: number) => call(`/api/reception/tokens/${id}/noshow`)}
                onCancel={(id: number) => call(`/api/reception/tokens/${id}/cancel`)}
              />
            </section>
          ))}
          {data.boards.length === 0 && <div className="empty">No doctors are assigned to your clinic.</div>}
        </>
      )}
      {tab === "Walk-in" && data && (
        <form
          className="card-block narrow-form"
          onSubmit={async (event: FormEvent) => {
            event.preventDefault();
            setFlash("");
            try {
              const found = form.phone ? await api<any>(`/api/reception/lookup?phone=${encodeURIComponent(form.phone)}`) : { found: false };
              const result = await api<any>("/api/reception/walkin", {
                method: "POST",
                body: JSON.stringify({ doctor_id: Number(form.doctor_id), name: found.found ? found.name : form.name, phone: form.phone }),
              });
              setFlash(`Token #${result.number} issued to ${result.patient_name}.`);
              setForm({ ...form, name: "", phone: "" });
              load();
            } catch (err: any) {
              setError(err.message);
            }
          }}
        >
          <h2>Register a walk-in</h2>
          <p className="muted">If the phone matches an existing patient, the token is linked to that account and no duplicate is created.</p>
          <label>
            Doctor
            <select className="field" value={form.doctor_id} onChange={(e) => setForm({ ...form, doctor_id: e.target.value })}>
              {data.boards.map((board: any) => (
                <option key={board.doctor.id} value={board.doctor.id}>
                  {board.doctor.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Patient name
            <input className="field" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
          </label>
          <label>
            Phone
            <input
              className="field"
              value={form.phone}
              onChange={(e) => setForm({ ...form, phone: e.target.value })}
              onBlur={async () => {
                if (form.phone.length < 6) return;
                const found = await api<any>(`/api/reception/lookup?phone=${encodeURIComponent(form.phone)}`);
                if (found.found) setForm((prev) => ({ ...prev, name: found.name }));
              }}
            />
          </label>
          <button className="btn btn-primary">Issue token</button>
        </form>
      )}
      {tab === "Report" && data && (
        <div className="card-block">
          <div className="desk-intro">
            <h2>Today’s list</h2>
            <button className="btn btn-ghost" onClick={download}>
              Download CSV
            </button>
          </div>
          <Stats counts={data.counts} />
          <p className="muted">Detailed exports stay available to the clinic desk. Medical notes are not stored in PocketDoc.</p>
        </div>
      )}
    </Desk>
  );
}

export function AdminDash() {
  const tabs = ["Overview", "Accounts", "Doctors", "Clinics", "Reception", "Patients", "Queues", "Reviews", "Plans", "Audit"];
  const [tab, setTab] = useState("Overview");
  const [overview, setOverview] = useState<any>(null);
  const [doctors, setDoctors] = useState<any[]>([]);
  const [clinics, setClinics] = useState<any[]>([]);
  const [staff, setStaff] = useState<any[]>([]);
  const [patients, setPatients] = useState<any[]>([]);
  const [queues, setQueues] = useState<any[]>([]);
  const [reviews, setReviews] = useState<any[]>([]);
  const [plans, setPlans] = useState<any[]>([]);
  const [audit, setAudit] = useState<any[]>([]);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [clinicForm, setClinicForm] = useState<any>({ name: "", kind: "clinic", address: "", city: "Lahore", phone: "" });
  const [staffForm, setStaffForm] = useState({ name: "", email: "", phone: "", password: "", clinic_id: "", can_operate_queue: false });

  async function load() {
    setError("");
    try {
      if (tab === "Overview") setOverview(await api("/api/admin/overview"));
      if (tab === "Accounts") setAccounts(await api("/api/admin/accounts"));
      if (tab === "Doctors") setDoctors(await api("/api/admin/doctors"));
      if (tab === "Clinics") setClinics(await api("/api/admin/clinics"));
      if (tab === "Reception") {
        setStaff(await api("/api/admin/receptionists"));
        setClinics(await api("/api/admin/clinics"));
      }
      if (tab === "Patients") setPatients(await api("/api/admin/patients"));
      if (tab === "Queues") setQueues(await api("/api/admin/queues"));
      if (tab === "Reviews") setReviews(await api("/api/admin/reviews"));
      if (tab === "Plans") setPlans(await api("/api/admin/plans"));
      if (tab === "Audit") setAudit(await api("/api/admin/audit"));
    } catch (err: any) {
      setError(err.message);
    }
  }

  useEffect(() => {
    load();
    const id = setInterval(load, 8000);
    return () => clearInterval(id);
  }, [tab]);

  return (
    <Desk title="Super admin" items={tabs} tab={tab} setTab={setTab}>
      <ErrorText>{error}</ErrorText>
      {tab === "Overview" && overview && (
        <div className="stat-grid">
          {Object.entries(overview).map(([key, value]) => (
            <article key={key}>
              <span>{key.replaceAll("_", " ")}</span>
              <b>{String(value)}</b>
            </article>
          ))}
        </div>
      )}
      {tab === "Accounts" && (
        <div className="table-card">
          <p className="muted">One database for the phone app, the website and this panel. Remove a patient, doctor or receptionist and that login stops on every screen.</p>
          {accounts.map((person) => (
            <div className="t-row" key={person.id}>
              <div>
                <b>{person.name}</b>
                <small>{person.role} · {person.profile}</small>
                <small>Login: {person.email}</small>
                <small>Password: {person.password || "—"}</small>
              </div>
              {person.role !== "admin" && (
                <button
                  className="btn tiny ghost"
                  onClick={async () => {
                    if (!window.confirm(`Remove ${person.name}? They will not be able to sign in.`)) return;
                    await api(`/api/admin/accounts/${person.id}/remove`, { method: "POST" });
                    load();
                  }}
                >
                  Remove
                </button>
              )}
            </div>
          ))}
        </div>
      )}
      {tab === "Doctors" && (
        <div className="table-card">
          {doctors.map((doctor) => (
            <div className="t-row" key={doctor.id}>
              <div>
                <b>{doctor.name}</b>
                <small>
                  {doctor.specialty} · {doctor.clinic} · {doctor.city} · {doctor.license_no}
                </small>
              </div>
              <em className={`st ${doctor.status}`}>{doctor.status}</em>
              <span className="btn-row tight">
                {doctor.status !== "approved" && (
                  <button className="btn tiny" onClick={async () => { await api(`/api/admin/doctors/${doctor.id}/approve`, { method: "POST" }); load(); }}>
                    Approve
                  </button>
                )}
                {doctor.status === "pending" && (
                  <button className="btn tiny ghost" onClick={async () => { await api(`/api/admin/doctors/${doctor.id}/reject`, { method: "POST" }); load(); }}>
                    Reject
                  </button>
                )}
                {doctor.status === "approved" && (
                  <button className="btn tiny ghost" onClick={async () => { await api(`/api/admin/doctors/${doctor.id}/deactivate`, { method: "POST" }); load(); }}>
                    Deactivate
                  </button>
                )}
              </span>
            </div>
          ))}
        </div>
      )}
      {tab === "Clinics" && (
        <div className="split">
          <div className="table-card">
            {clinics.map((clinic) => (
              <div className="t-row" key={clinic.id}>
                <div>
                  <b>{clinic.name}</b>
                  <small>
                    {clinic.kind} · {clinic.address} · {clinic.city} · {clinic.doctors} doctors
                  </small>
                </div>
              </div>
            ))}
          </div>
          <form
            className="card-block"
            onSubmit={async (event) => {
              event.preventDefault();
              await api("/api/admin/clinics", { method: "POST", body: JSON.stringify(clinicForm) });
              setClinicForm({ name: "", kind: "clinic", address: "", city: "Lahore", phone: "" });
              load();
            }}
          >
            <h3>Add clinic</h3>
            <div className="stack">
              <input className="field" placeholder="Name" value={clinicForm.name} onChange={(e) => setClinicForm({ ...clinicForm, name: e.target.value })} required />
              <input className="field" placeholder="Address" value={clinicForm.address} onChange={(e) => setClinicForm({ ...clinicForm, address: e.target.value })} />
              <PlacePicker
                placeholder="Clinic place — Bahawalpur, Basti Malook…"
                onPick={(place) =>
                  setClinicForm({
                    ...clinicForm,
                    city: place.name,
                    lat: place.lat,
                    lng: place.lng,
                    district: place.district,
                    division: place.division,
                  })
                }
              />
              <select className="field" value={clinicForm.kind} onChange={(e) => setClinicForm({ ...clinicForm, kind: e.target.value })}>
                <option value="clinic">Clinic</option>
                <option value="hospital">Hospital</option>
              </select>
              <button className="btn btn-primary">Save clinic</button>
            </div>
          </form>
        </div>
      )}
      {tab === "Reception" && (
        <div className="split">
          <div className="table-card">
            {staff.map((person) => (
              <div className="t-row" key={person.id}>
                <div>
                  <b>{person.name}</b>
                  <small>
                    {person.email} · {person.assignments.map((item: any) => `${item.clinic}${item.can_operate_queue ? " (can run queue)" : ""}`).join(", ")}
                  </small>
                </div>
                <button
                  className="btn tiny ghost"
                  onClick={async () => {
                    const enabled = person.assignments.some((item: any) => item.can_operate_queue);
                    await api(`/api/admin/receptionists/${person.id}`, {
                      method: "PATCH",
                      body: JSON.stringify({ can_operate_queue: !enabled }),
                    });
                    load();
                  }}
                >
                  Toggle queue control
                </button>
              </div>
            ))}
          </div>
          <form
            className="card-block"
            onSubmit={async (event) => {
              event.preventDefault();
              await api("/api/admin/receptionists", {
                method: "POST",
                body: JSON.stringify({ ...staffForm, clinic_id: Number(staffForm.clinic_id) }),
              });
              setStaffForm({ name: "", email: "", phone: "", password: "", clinic_id: "", can_operate_queue: false });
              load();
            }}
          >
            <h3>New receptionist</h3>
            <div className="stack">
              <input className="field" placeholder="Name" value={staffForm.name} onChange={(e) => setStaffForm({ ...staffForm, name: e.target.value })} required />
              <input className="field" placeholder="Email" value={staffForm.email} onChange={(e) => setStaffForm({ ...staffForm, email: e.target.value })} required />
              <input className="field" placeholder="Phone" value={staffForm.phone} onChange={(e) => setStaffForm({ ...staffForm, phone: e.target.value })} />
              <input className="field" placeholder="Password" value={staffForm.password} onChange={(e) => setStaffForm({ ...staffForm, password: e.target.value })} required />
              <select className="field" value={staffForm.clinic_id} onChange={(e) => setStaffForm({ ...staffForm, clinic_id: e.target.value })} required>
                <option value="">Clinic</option>
                {clinics.map((clinic) => (
                  <option key={clinic.id} value={clinic.id}>
                    {clinic.name}
                  </option>
                ))}
              </select>
              <label className="check">
                <input type="checkbox" checked={staffForm.can_operate_queue} onChange={(e) => setStaffForm({ ...staffForm, can_operate_queue: e.target.checked })} />
                Allow Start, Pause, Resume and Next
              </label>
              <button className="btn btn-primary">Create account</button>
            </div>
          </form>
        </div>
      )}
      {tab === "Patients" && (
        <div className="table-card">
          {patients.map((patient) => (
            <div className="t-row" key={patient.id}>
              <div>
                <b>{patient.name}</b>
                <small>
                  {patient.email} · {patient.phone} · {patient.city} · {patient.plan_code}
                </small>
              </div>
              <span className="btn-row tight">
                <select
                  value={patient.plan_code}
                  onChange={async (e) => {
                    await api(`/api/admin/patients/${patient.id}/plan`, { method: "POST", body: JSON.stringify({ plan_code: e.target.value }) });
                    load();
                  }}
                >
                  {["basic", "plus", "family", "premium"].map((code) => (
                    <option key={code}>{code}</option>
                  ))}
                </select>
                <button
                  className="btn tiny ghost"
                  onClick={async () => {
                    await api(`/api/admin/patients/${patient.id}/active`, {
                      method: "POST",
                      body: JSON.stringify({ status: patient.active ? "inactive" : "active" }),
                    });
                    load();
                  }}
                >
                  {patient.active ? "Deactivate" : "Activate"}
                </button>
              </span>
            </div>
          ))}
        </div>
      )}
      {tab === "Queues" && (
        <div className="table-card">
          {queues.map((queue) => (
            <div className="t-row" key={queue.doctor_id}>
              <div>
                <b>{queue.doctor}</b>
                <small>
                  {queue.clinic} · {queue.city} · {queue.specialty}
                </small>
              </div>
              <em className={`st ${queue.queue_status}`}>{statusLabel(queue.queue_status)}{queue.pause_reason ? ` · ${queue.pause_reason}` : ""}</em>
              <span>
                Now #{queue.current || "—"} · {queue.waiting} waiting
              </span>
            </div>
          ))}
          {queues.length === 0 && <div className="empty">No active queues today.</div>}
        </div>
      )}
      {tab === "Reviews" && (
        <div className="table-card">
          {reviews.length === 0 && <div className="empty">No reviews yet. They appear after a completed visit.</div>}
          {reviews.map((review) => (
            <div className="t-row" key={review.id}>
              <div>
                <b>
                  {review.rating}★ · {review.doctor}
                </b>
                <small>
                  {review.patient}: {review.comment || "No comment"}
                </small>
              </div>
              <button className="btn tiny ghost" onClick={async () => { await api(`/api/admin/reviews/${review.id}/hide`, { method: "POST" }); load(); }}>
                {review.hidden ? "Unhide" : "Hide"}
              </button>
            </div>
          ))}
        </div>
      )}
      {tab === "Plans" && (
        <div className="plan-grid">
          {plans.map((plan) => (
            <form
              key={plan.code}
              className="plan"
              onSubmit={async (event) => {
                event.preventDefault();
                const formData = new FormData(event.currentTarget);
                await api(`/api/admin/plans/${plan.code}`, {
                  method: "PATCH",
                  body: JSON.stringify({
                    name: formData.get("name"),
                    radius_km: Number(formData.get("radius")),
                    price_pkr: Number(formData.get("price")),
                    blurb: formData.get("blurb"),
                  }),
                });
                load();
              }}
            >
              <input className="field" name="name" defaultValue={plan.name} />
              <input className="field" name="radius" type="number" defaultValue={plan.radius_km} />
              <input className="field" name="price" type="number" defaultValue={plan.price_pkr} />
              <input className="field" name="blurb" defaultValue={plan.blurb} />
              <button className="btn tiny">Save {plan.code}</button>
            </form>
          ))}
        </div>
      )}
      {tab === "Audit" && (
        <div className="table-card">
          {audit.map((row) => (
            <div className="t-row" key={row.id}>
              <div>
                <b>{row.action}</b>
                <small>
                  {row.actor} · {row.detail}
                </small>
              </div>
              <span>{row.created_at?.replace("T", " ").slice(0, 16)}</span>
            </div>
          ))}
        </div>
      )}
    </Desk>
  );
}
