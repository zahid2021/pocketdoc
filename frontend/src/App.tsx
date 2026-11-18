import { useEffect } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import { isPocketDocApp, useAuth, useLayout } from "./auth";
import { Logo, Wordmark } from "./bits";
import { PatientMobile } from "./mobile";
import { PatientWeb } from "./web";
import { AdminDash, DoctorDash, ReceptionDash } from "./dash";

function Splash() {
  return (
    <div className="splash">
      <Logo size={72} />
      <Wordmark />
      <p>Your Turn. Our Priority.</p>
    </div>
  );
}

export function App() {
  const { user, loading } = useAuth();
  const { pathname } = useLocation();
  const { width } = useLayout();
  const native = isPocketDocApp() || width <= 1180;
  useEffect(() => {
    document.body.classList.toggle("native-app", native);
  }, [native]);
  if (loading) return <Splash />;
  if (user?.role === "doctor") return <DoctorDash />;
  if (user?.role === "receptionist") return <ReceptionDash />;
  if (user?.role === "admin" && pathname.startsWith("/admin")) return <AdminDash />;
  if (native && user?.role !== "admin") {
    return (
      <Routes>
        <Route path="/*" element={<PatientMobile />} />
      </Routes>
    );
  }
  return (
    <Routes>
      <Route path="/*" element={<PatientWeb />} />
    </Routes>
  );
}
