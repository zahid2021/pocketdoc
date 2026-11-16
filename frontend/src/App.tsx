import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth, useLayout } from "./auth";
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
  const { phone } = useLayout();
  if (loading) return <Splash />;
  if (user?.role === "doctor") return <DoctorDash />;
  if (user?.role === "receptionist") return <ReceptionDash />;
  if (user?.role === "admin") return <AdminDash />;
  return (
    <Routes>
      <Route path="/*" element={phone ? <PatientMobile /> : <PatientWeb />} />
      <Route path="/desk" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
