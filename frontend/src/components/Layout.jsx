import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { RoleBadge } from './ui';
import NotificationBell from './NotificationBell';

const NAV = [
  { to: '/dashboard', label: 'Dashboard', icon: '▚' },
  { to: '/assets', label: 'Assets', icon: '▤' },
  { to: '/allocations', label: 'Allocation & Transfer', icon: '⇄' },
  { to: '/bookings', label: 'Resource Booking', icon: '◷' },
  { to: '/maintenance', label: 'Maintenance', icon: '⚒' },
  { to: '/audit', label: 'Asset Audit', icon: '☑' },
  { to: '/reports', label: 'Reports & Analytics', icon: '📊', managerOnly: true },
  { to: '/activity', label: 'Activity Log', icon: '🕑', managerOnly: true },
  { to: '/organization', label: 'Organization Setup', icon: '⚙', adminOnly: true },
];

export default function Layout() {
  const { user, isAdmin, isManager, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  const initials = (user?.full_name || '?')
    .split(' ')
    .map((n) => n[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  const visibleNav = NAV.filter(
    (item) => (!item.adminOnly || isAdmin) && (!item.managerOnly || isManager)
  );

  return (
    <div className="app-shell">
      {/* Mobile top bar */}
      <header className="topbar">
        <button className="hamburger" onClick={() => setMobileOpen(true)} aria-label="Open menu">☰</button>
        <div className="brand-mini"><span className="brand-mark sm">AF</span> AssetFlow</div>
        <div className="topbar-spacer" />
        <NotificationBell />
      </header>

      {mobileOpen && <div className="drawer-backdrop" onClick={() => setMobileOpen(false)} />}

      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
        <div className="brand">
          <span className="brand-mark">AF</span>
          <div>
            <strong>AssetFlow</strong>
            <small>Asset & Resource ERP</small>
          </div>
          <div className="brand-bell"><NotificationBell /></div>
          <button className="icon-btn drawer-close" onClick={() => setMobileOpen(false)} aria-label="Close menu">×</button>
        </div>

        <nav className="nav">
          {visibleNav.map((item) => (
            <NavLink key={item.to} to={item.to} className="nav-link" onClick={() => setMobileOpen(false)}>
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-foot">
          <div className="user-chip">
            <span className="avatar">{initials}</span>
            <div className="user-meta">
              <strong>{user?.full_name}</strong>
              <RoleBadge role={user?.role} />
            </div>
          </div>
          <button className="btn btn-ghost btn-block" onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </aside>

      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
