import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./store/auth";
import Layout from "./components/common/Layout";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import TargetsPage from "./pages/TargetsPage";
import ScansPage from "./pages/ScansPage";
import ScanDetailPage from "./pages/ScanDetailPage";
import NewScanPage from "./pages/NewScanPage";
import FindingsPage from "./pages/FindingsPage";
import FindingDetailPage from "./pages/FindingDetailPage";
import ScanHistoryPage from "./pages/ScanHistoryPage";
import ReportsPage from "./pages/ReportsPage";
import ScanComparePage from "./pages/ScanComparePage";

function PrivateRoute({ children }) {
  const { user } = useAuth();
  return user ? children : <Navigate to="/login" replace />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="targets" element={<TargetsPage />} />
        <Route path="scans" element={<ScansPage />} />
        <Route path="scans/new" element={<NewScanPage />} />
        <Route path="scans/:id" element={<ScanDetailPage />} />
        <Route path="findings" element={<FindingsPage />} />
        <Route path="findings/:id" element={<FindingDetailPage />} />
        <Route path="history" element={<ScanHistoryPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="compare" element={<ScanComparePage />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
