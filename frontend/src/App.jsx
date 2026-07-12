import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import OrgSetupPage from './pages/OrgSetupPage';
import AssetsPage from './pages/AssetsPage';
import AllocationPage from './pages/AllocationPage';
import BookingPage from './pages/BookingPage';
import MaintenancePage from './pages/MaintenancePage';
import AuditPage from './pages/AuditPage';
import ReportsPage from './pages/ReportsPage';
import ActivityPage from './pages/ActivityPage';

function ProtectedRoute({ children, adminOnly = false, managerOnly = false }) {
  const { isAuthenticated, isAdmin, isManager, loading } = useAuth();

  if (loading) return <div className="app-loading">Loading…</div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (adminOnly && !isAdmin) return <Navigate to="/dashboard" replace />;
  if (managerOnly && !isManager) return <Navigate to="/dashboard" replace />;
  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/assets" element={<AssetsPage />} />
            <Route path="/allocations" element={<AllocationPage />} />
            <Route path="/bookings" element={<BookingPage />} />
            <Route path="/maintenance" element={<MaintenancePage />} />
            <Route path="/audit" element={<AuditPage />} />
            <Route
              path="/reports"
              element={
                <ProtectedRoute managerOnly>
                  <ReportsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/activity"
              element={
                <ProtectedRoute managerOnly>
                  <ActivityPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/organization"
              element={
                <ProtectedRoute adminOnly>
                  <OrgSetupPage />
                </ProtectedRoute>
              }
            />
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
