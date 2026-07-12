import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { fetchKpis } from '../services/api';
import { useAuth } from '../context/AuthContext';
import PageHeader from '../components/PageHeader';
import { Badge, Banner, EmptyState, KpiCard } from '../components/ui';

export default function DashboardPage() {
  const { user, isManager } = useAuth();
  const [kpis, setKpis] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchKpis().then(setKpis).catch((e) => setError(e.message));
  }, []);

  const fmtDate = (d) => (d ? new Date(d).toLocaleDateString() : '—');

  return (
    <div className="page">
      <PageHeader
        title={`Welcome, ${user?.full_name?.split(' ')[0] || 'there'}`}
        subtitle="Real-time operational snapshot of your assets and resources."
        actions={
          <div className="page-actions">
            {isManager && <Link className="btn btn-primary" to="/assets">Register Asset</Link>}
            <Link className="btn btn-outline" to="/bookings">Book Resource</Link>
          </div>
        }
      />

      <Banner kind="error" onClose={() => setError('')}>{error}</Banner>

      {!kpis ? (
        <EmptyState>Loading dashboard…</EmptyState>
      ) : (
        <>
          <section className="kpi-grid">
            <KpiCard label="Assets Available" value={kpis.assets_available} tone="ok" />
            <KpiCard label="Assets Allocated" value={kpis.assets_allocated} tone="info" />
            <KpiCard label="Under Maintenance" value={kpis.under_maintenance} tone="warn" />
            <KpiCard label="Active Bookings" value={kpis.active_bookings} tone="info" />
            <KpiCard label="Pending Transfers" value={kpis.pending_transfers} tone="warn" />
            <KpiCard label="Upcoming Returns" value={kpis.upcoming_returns} tone="default" />
            <KpiCard label="Overdue Returns" value={kpis.overdue_returns} tone="danger" hint="Past expected return date" />
            <KpiCard label="Total Assets" value={kpis.total_assets} tone="default" />
          </section>

          <div className="split-2">
            <section className="panel">
              <div className="panel-head">
                <h3>Overdue Returns</h3>
                <span className="count-pill danger">{kpis.overdue_list.length}</span>
              </div>
              {kpis.overdue_list.length === 0 ? (
                <EmptyState>No overdue returns. 🎉</EmptyState>
              ) : (
                <table className="table">
                  <thead>
                    <tr><th>Asset</th><th>Holder</th><th>Due</th></tr>
                  </thead>
                  <tbody>
                    {kpis.overdue_list.map((a) => (
                      <tr key={a.id}>
                        <td><strong>{a.asset_tag}</strong> {a.asset_name}</td>
                        <td>{a.employee_name}</td>
                        <td><span className="text-danger">{fmtDate(a.expected_return_date)}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>

            <section className="panel">
              <div className="panel-head">
                <h3>Upcoming Returns (7 days)</h3>
                <span className="count-pill info">{kpis.upcoming_list.length}</span>
              </div>
              {kpis.upcoming_list.length === 0 ? (
                <EmptyState>Nothing due this week.</EmptyState>
              ) : (
                <table className="table">
                  <thead>
                    <tr><th>Asset</th><th>Holder</th><th>Due</th></tr>
                  </thead>
                  <tbody>
                    {kpis.upcoming_list.map((a) => (
                      <tr key={a.id}>
                        <td><strong>{a.asset_tag}</strong> {a.asset_name}</td>
                        <td>{a.employee_name}</td>
                        <td>{fmtDate(a.expected_return_date)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </section>
          </div>

          <section className="panel">
            <div className="panel-head"><h3>Lifecycle Breakdown</h3></div>
            <div className="chip-row">
              {Object.entries(kpis.status_breakdown).length === 0 ? (
                <EmptyState>No assets registered yet.</EmptyState>
              ) : (
                Object.entries(kpis.status_breakdown).map(([status, count]) => (
                  <div key={status} className="stat-chip">
                    <Badge value={status} />
                    <strong>{count}</strong>
                  </div>
                ))
              )}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
