import { useAuth } from '../context/AuthContext';

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="dashboard-shell">
      <header className="dashboard-header">
        <div>
          <h1>Dashboard</h1>
          <p>Welcome back, {user?.email || 'Admin'}.</p>
        </div>
        <button onClick={logout}>Logout</button>
      </header>

      <section className="cards">
        <div className="card">Assets Available: 24</div>
        <div className="card">Assets Allocated: 11</div>
        <div className="card">Maintenance Today: 3</div>
        <div className="card">Active Bookings: 6</div>
      </section>
    </div>
  );
}
