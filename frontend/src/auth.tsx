import React, { createContext, useContext, useEffect, useState } from "react";
import { api, getToken, setToken } from "./api";

type AuthValue = {
  user: any;
  loading: boolean;
  login: (email: string, password: string) => Promise<any>;
  register: (body: any) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthValue>(null as any);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    if (!getToken()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      setUser(await api("/api/me"));
    } catch {
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function login(email: string, password: string) {
    const data = await api<any>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }, false);
    setToken(data.token);
    setUser(data.user);
    return data.user;
  }

  async function register(body: any) {
    const data = await api<any>("/api/auth/register", { method: "POST", body: JSON.stringify(body) }, false);
    setToken(data.token);
    setUser(data.user);
  }

  function logout() {
    setToken(null);
    setUser(null);
  }

  return <AuthContext.Provider value={{ user, loading, login, register, logout, refresh }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}

const LayoutContext = createContext<any>(null);

export function LayoutProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState(() => localStorage.getItem("pocketdoc_layout") || "auto");
  const [width, setWidth] = useState(window.innerWidth);

  useEffect(() => {
    const onResize = () => setWidth(window.innerWidth);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  function setMode(next: string) {
    localStorage.setItem("pocketdoc_layout", next);
    setModeState(next);
  }

  const phone = mode === "mobile" || (mode !== "desktop" && width < 880);

  useEffect(() => {
    document.body.classList.toggle("layout-mobile", phone);
    document.body.classList.toggle("layout-desktop", !phone);
  }, [phone]);

  return <LayoutContext.Provider value={{ phone, mode, setMode, width }}>{children}</LayoutContext.Provider>;
}

export function useLayout() {
  return useContext(LayoutContext);
}

export function isPocketDocApp() {
  try {
    const params = new URLSearchParams(window.location.search);
    if (params.get("app") === "1" || navigator.userAgent.includes("PocketDocAndroid")) {
      localStorage.setItem("pocketdoc_app", "1");
    }
    if (localStorage.getItem("pocketdoc_app") === "1") return true;
  } catch {
    return false;
  }
  return /\bwv\b/.test(navigator.userAgent);
}
