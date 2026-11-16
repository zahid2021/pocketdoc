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

export function initials(name: string) {
  const parts = (name || "").replace(/^Dr\.?\s+/i, "").split(" ").filter(Boolean);
  return ((parts[0]?.[0] || "P") + (parts[1]?.[0] || "")).toUpperCase();
}

const COLORS = ["#1f6bff", "#12b5a0", "#7c6bf2", "#ef6d3a", "#0ea5e9", "#db4f8a"];

export function avatarColor(name: string) {
  let hash = 0;
  for (const ch of name || "P") hash = (hash * 33 + ch.charCodeAt(0)) >>> 0;
  return COLORS[hash % COLORS.length];
}

export function Avatar({ name, size = 48 }: { name: string; size?: number }) {
  return (
    <span className="avatar" style={{ width: size, height: size, background: avatarColor(name), fontSize: size * 0.34 }}>
      {initials(name)}
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
