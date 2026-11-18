import { useEffect, useId, useState } from "react";
import { api, waitLabel } from "./api";

export function Logo({ size = 40 }: { size?: number }) {
  const gid = useId().replace(/:/g, "");
  return (
    <svg className="logo" width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#3b82f6" />
          <stop offset="1" stopColor="#1557e8" />
        </linearGradient>
      </defs>
      <rect width="64" height="64" rx="16" fill={`url(#${gid})`} />
      <path fill="#fff" d="M16 12h16c9 0 15 5.2 15 13.2S41 38.4 32 38.4H24v13.6h-8V12zm8 6.6V32h7.2c4.2 0 7-2.2 7-6.7s-2.8-6.7-7-6.7H24z" />
      <circle cx="44" cy="20" r="8" fill="#2ee6c8" />
      <path d="M44 15.4v9.2M39.4 20h9.2" stroke="#0f3f86" strokeWidth="2.2" strokeLinecap="round" />
      <circle cx="22" cy="46" r="6" fill="none" stroke="#d7fff6" strokeWidth="2.2" />
      <path d="M26.2 50.2 30.5 54.5" stroke="#d7fff6" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  );
}

export function Wordmark() {
  return (
    <span className="wordmark">
      Pocket<b>Doc</b>
    </span>
  );
}

export function Credit() {
  return <p className="credit">Developed by Engineer Zahid Mehmood</p>;
}

function hashName(name: string) {
  let hash = 0;
  for (const ch of name || "P") hash = (hash * 33 + ch.charCodeAt(0)) >>> 0;
  return hash;
}

const WOMEN = new Set("ayesha sana hina farah saima amina rabia hira saba fiza zahra maham sara noor".split(" "));

export function Avatar({ name, size = 48 }: { name: string; size?: number }) {
  const hash = hashName(name);
  const first = (name || "").replace(/^Dr\.?\s+/i, "").split(/\s+/)[0]?.toLowerCase() || "";
  const woman = WOMEN.has(first);
  const skin = ["#f6d3b4", "#e7b892", "#d59a74", "#c4845a", "#8d5a3c"][hash % 5];
  const hair = ["#241910", "#1a1a1a", "#4a3024", "#111827"][hash % 4];
  const hijab = woman && hash % 3 !== 1;
  return (
    <span className="avatar" style={{ width: size, height: size }} aria-label={name}>
      <svg viewBox="0 0 80 80" width={size} height={size} aria-hidden="true">
        <rect width="80" height="80" fill="#e8f1fb" />
        <path d="M8 84c4-20 16-30 32-30s28 10 32 30" fill={hair} />
        <path d="M18 62c2-10 10-16 22-16s20 6 22 16v22H18z" fill="#ffffff" />
        <path d="M37 60h6l1.5 16h-9z" fill="#1a6dff" />
        {hijab ? <path d="M14 42c2-24 12-32 26-32s24 8 26 32c-2 4-8 2-10-4-2 10-8 16-16 16s-14-6-16-16c-2 6-8 8-10 4z" fill={hair} /> : null}
        {!hijab && woman ? <path d="M16 46c0-24 10-34 24-34s24 10 24 32c0 6-4 8-8 4-2 8-8 12-16 12s-14-4-16-12c-4 4-8 2-8-2z" fill={hair} /> : null}
        {!hijab && !woman ? <path d="M20 40c0-18 8-28 20-28s20 10 20 26c0 4-4 6-6 2-1-8-5-12-14-12s-13 4-14 12c-3 4-6 2-6 0z" fill={hair} /> : null}
        <circle cx="40" cy="38" r="14" fill={skin} />
        {hijab ? <path d="M24 34c2-12 8-16 16-16s14 4 16 16c-6 3-12 4-16 4s-12-1-16-4z" fill={hair} /> : null}
        {!hijab && woman ? <path d="M24 34c1-10 7-14 16-14 6 0 11 2 14 8-6 2-12 2-16 0-4 2-10 2-14 6z" fill={hair} /> : null}
        {!hijab && !woman ? <path d="M26 32c1-8 6-12 14-12s13 4 14 12c-8 2-20 2-28 0z" fill={hair} /> : null}
        <circle cx="34.5" cy="38" r="1.3" fill="#1c2430" />
        <circle cx="45.5" cy="38" r="1.3" fill="#1c2430" />
        <path d="M36 44c1.8 1.8 6.2 1.8 8 0" stroke="#a15d48" strokeWidth="1.15" fill="none" strokeLinecap="round" />
      </svg>
    </span>
  );
}

export function Stars({ value }: { value: number }) {
  const full = Math.round(value);
  return (
    <span className="stars" aria-label={`${value} stars`}>
      {"★★★★★".slice(0, full)}
      <i>{"★★★★★".slice(full)}</i>
    </span>
  );
}

export function useNow() {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  return now;
}

export function Wait({ seconds, ticking, at }: { seconds: number; ticking?: boolean; at: number }) {
  const now = useNow();
  const remain = ticking ? Math.max(0, seconds - (now - at) / 1000) : Math.max(0, seconds);
  return <>{waitLabel(remain)}</>;
}

export function Bell() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<any[]>([]);

  async function load() {
    try {
      setItems(await api("/api/notifications"));
    } catch {
      setItems([]);
    }
  }

  useEffect(() => {
    load();
    const id = setInterval(load, 8000);
    return () => clearInterval(id);
  }, []);

  const unread = items.filter((item) => !item.read).length;

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next && unread) {
      await api("/api/notifications/read", { method: "POST" });
      setItems((list) => list.map((item) => ({ ...item, read: true })));
    }
  }

  return (
    <div className="bell-wrap">
      <button className="icon-btn" onClick={toggle} aria-label="Notifications">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M6 9a6 6 0 1 1 12 0c0 7 2 7 2 9H4c0-2 2-2 2-9z" />
          <path d="M10 20a2 2 0 0 0 4 0" />
        </svg>
        {unread > 0 && <span className="dot" />}
      </button>
      {open && (
        <div className="bell-sheet">
          <strong>Notifications</strong>
          {items.length === 0 && <p className="muted">No alerts yet.</p>}
          {items.slice(0, 8).map((item) => (
            <div key={item.id} className="note">
              <b>{item.title}</b>
              <span>{item.body}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export const DEMOS = [
  { role: "Patient", email: "patient@pocketdoc.app", password: "patient123", hint: "Ali Hassan · Lahore" },
  { role: "Bahawalpur", email: "bahawalpur@pocketdoc.app", password: "patient123", hint: "Hassan · Model Town clinic" },
  { role: "Doctor", email: "doctor@pocketdoc.app", password: "doctor123", hint: "Dr. Ahmed Khan" },
  { role: "Reception", email: "reception@pocketdoc.app", password: "reception123", hint: "City Clinic desk" },
  { role: "Admin", email: "admin@pocketdoc.app", password: "admin123", hint: "Approvals and plans" },
];

export function DemoAccounts({ onPick }: { onPick: (email: string, password: string) => void }) {
  return (
    <div className="demo-box">
      <span>Demo accounts</span>
      <div className="demo-grid">
        {DEMOS.map((demo) => (
          <button key={demo.email} type="button" onClick={() => onPick(demo.email, demo.password)}>
            <b>{demo.role}</b>
            <small>{demo.hint}</small>
          </button>
        ))}
      </div>
    </div>
  );
}

export function ErrorText({ children }: { children?: string }) {
  if (!children) return null;
  return <p className="error">{children}</p>;
}

export function LiveBadge() {
  return (
    <span className="live-badge">
      <i /> Live Queue
    </span>
  );
}
