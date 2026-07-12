import { useEffect } from 'react';

// Maps a lifecycle/booking/allocation status to a badge modifier class.
const STATUS_CLASS = {
  Available: 'ok',
  Allocated: 'info',
  Reserved: 'info',
  'Under Maintenance': 'warn',
  Lost: 'danger',
  Retired: 'muted',
  Disposed: 'muted',
  Active: 'info',
  Returned: 'muted',
  Upcoming: 'info',
  Ongoing: 'ok',
  Completed: 'muted',
  Cancelled: 'danger',
  Requested: 'warn',
  Approved: 'ok',
  Rejected: 'danger',
  Good: 'ok',
  Fair: 'warn',
  Poor: 'danger',
};

export function Badge({ value }) {
  const cls = STATUS_CLASS[value] || 'muted';
  return <span className={`badge badge-${cls}`}>{value}</span>;
}

export function RoleBadge({ role }) {
  const map = { Admin: 'role-admin', 'Asset Manager': 'role-manager', 'Department Head': 'role-head' };
  return <span className={`role-pill ${map[role] || 'role-emp'}`}>{role}</span>;
}

export function KpiCard({ label, value, tone = 'default', hint }) {
  return (
    <div className={`kpi kpi-${tone}`}>
      <span className="kpi-value">{value}</span>
      <span className="kpi-label">{label}</span>
      {hint ? <span className="kpi-hint">{hint}</span> : null}
    </div>
  );
}

export function Modal({ title, onClose, children, footer }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  return (
    <div className="modal-overlay" onMouseDown={onClose}>
      <div className="modal" onMouseDown={(e) => e.stopPropagation()}>
        <header className="modal-head">
          <h3>{title}</h3>
          <button className="icon-btn" onClick={onClose} aria-label="Close">×</button>
        </header>
        <div className="modal-body">{children}</div>
        {footer ? <footer className="modal-foot">{footer}</footer> : null}
      </div>
    </div>
  );
}

export function Banner({ kind = 'error', children, onClose }) {
  if (!children) return null;
  return (
    <div className={`banner banner-${kind}`}>
      <span>{children}</span>
      {onClose ? <button className="icon-btn" onClick={onClose}>×</button> : null}
    </div>
  );
}

export function EmptyState({ children }) {
  return <div className="empty-state">{children}</div>;
}
