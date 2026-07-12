import { useEffect, useState } from 'react';
import {
  fetchAssetUtilization, fetchBookingHeatmap, fetchDepartmentAllocation,
  fetchDueMaintenance, fetchMaintenanceFrequency, fetchReportSummary,
} from '../services/api';
import PageHeader from '../components/PageHeader';
import { Badge, Banner, EmptyState, KpiCard } from '../components/ui';

// --- CSV export helper (client-side) -----------------------------------------
function toCsv(rows) {
  return rows
    .map((r) => r.map((c) => {
      const s = c == null ? '' : String(c);
      return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    }).join(','))
    .join('\n');
}

function downloadCsv(filename, rows) {
  const blob = new Blob([toCsv(rows)], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function ExportButton({ filename, rows }) {
  return (
    <button className="btn btn-outline btn-sm" onClick={() => downloadCsv(filename, rows)}>
      ⭳ Export CSV
    </button>
  );
}

// --- Horizontal CSS bar chart ------------------------------------------------
function BarChart({ data, accent = false }) {
  const max = Math.max(1, ...data.map((d) => d.value));
  if (data.length === 0) return <EmptyState>No data yet.</EmptyState>;
  return (
    <div className="barchart">
      {data.map((d) => (
        <div className="bar-row" key={d.label}>
          <span className="bar-label" title={d.label}>{d.label}</span>
          <div className="bar-track">
            <div
              className={`bar-fill ${accent ? 'accent' : ''}`}
              style={{ width: `${(d.value / max) * 100}%` }}
            />
          </div>
          <span className="bar-value">{d.value}</span>
        </div>
      ))}
    </div>
  );
}

export default function ReportsPage() {
  const [summary, setSummary] = useState(null);
  const [util, setUtil] = useState(null);
  const [maint, setMaint] = useState(null);
  const [due, setDue] = useState(null);
  const [dept, setDept] = useState(null);
  const [heat, setHeat] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchReportSummary().then(setSummary).catch((e) => setError(e.message));
    fetchAssetUtilization().then(setUtil).catch(() => {});
    fetchMaintenanceFrequency().then(setMaint).catch(() => {});
    fetchDueMaintenance().then(setDue).catch(() => {});
    fetchDepartmentAllocation().then(setDept).catch(() => {});
    fetchBookingHeatmap().then(setHeat).catch(() => {});
  }, []);

  return (
    <div className="page">
      <PageHeader
        title="Reports & Analytics"
        subtitle="Utilization, maintenance trends, department load and booking demand."
      />
      <Banner kind="error" onClose={() => setError('')}>{error}</Banner>

      {/* Headline KPI cards */}
      {summary && (
        <section className="kpi-grid">
          <KpiCard label="Total Assets" value={summary.total_assets} tone="default" />
          <KpiCard label="Utilization Rate" value={`${summary.utilization_rate}%`} tone="info" hint="Currently allocated" />
          <KpiCard label="Idle Assets" value={summary.idle_assets} tone="warn" hint="Never allocated" />
          <KpiCard label="Under Maintenance" value={summary.under_maintenance} tone="warn" />
          <KpiCard label="Open Maintenance" value={summary.open_maintenance} tone="warn" />
          <KpiCard label="Overdue Returns" value={summary.overdue_returns} tone="danger" />
          <KpiCard label="Available" value={summary.available} tone="ok" />
          <KpiCard label="Bookings" value={summary.total_bookings} tone="info" />
        </section>
      )}

      <div className="split-2">
        {/* Asset utilization */}
        <section className="panel">
          <div className="panel-head">
            <h3>Asset Utilization {util ? <span className="count-pill warn">{util.idle_count} idle</span> : null}</h3>
            {util && (
              <ExportButton
                filename="asset-utilization.csv"
                rows={[['Tag', 'Name', 'Times Allocated', 'Days Allocated'],
                  ...util.assets.map((a) => [a.asset_tag, a.name, a.times_allocated, a.days_allocated])]}
              />
            )}
          </div>
          <div className="panel-body">
            {util ? (
              <BarChart data={util.most_used.map((a) => ({ label: `${a.asset_tag} ${a.name}`, value: a.days_allocated }))} />
            ) : <EmptyState>Loading…</EmptyState>}
            <p className="hint-text">Top assets by total days allocated. {util?.idle_count || 0} asset(s) never allocated.</p>
          </div>
        </section>

        {/* Maintenance frequency */}
        <section className="panel">
          <div className="panel-head">
            <h3>Maintenance Frequency</h3>
            {maint && (
              <ExportButton
                filename="maintenance-frequency.csv"
                rows={[['Tag', 'Name', 'Requests'],
                  ...maint.by_asset.map((a) => [a.asset_tag, a.name, a.count])]}
              />
            )}
          </div>
          <div className="panel-body">
            {maint ? (
              <BarChart accent data={maint.by_category.map((c) => ({ label: c.category, value: c.count }))} />
            ) : <EmptyState>Loading…</EmptyState>}
            <p className="hint-text">Repair requests grouped by category ({maint?.total || 0} total).</p>
          </div>
        </section>
      </div>

      {/* Booking heatmap */}
      <section className="panel">
        <div className="panel-head">
          <h3>Booking Demand — Weekday × Hour {heat?.peak?.count ? <span className="count-pill info">peak {heat.peak.weekday} {heat.peak.hour}:00</span> : null}</h3>
          {heat && (
            <ExportButton
              filename="booking-heatmap.csv"
              rows={[['Weekday', ...heat.hours.map((h) => `${h}:00`)],
                ...heat.matrix.map((row, i) => [heat.weekdays[i], ...row])]}
            />
          )}
        </div>
        <div className="panel-body">
          {heat ? <Heatmap heat={heat} /> : <EmptyState>Loading…</EmptyState>}
        </div>
      </section>

      <div className="split-2">
        {/* Department allocation */}
        <section className="panel">
          <div className="panel-head">
            <h3>Department Allocation</h3>
            {dept && (
              <ExportButton
                filename="department-allocation.csv"
                rows={[['Department', 'Allocated', 'Total Assets'],
                  ...dept.departments.map((d) => [d.department, d.allocated, d.total_assets])]}
              />
            )}
          </div>
          {!dept || dept.departments.length === 0 ? <EmptyState>No departments.</EmptyState> : (
            <table className="table">
              <thead><tr><th>Department</th><th>Allocated</th><th>Total</th></tr></thead>
              <tbody>
                {dept.departments.map((d) => (
                  <tr key={d.department_id}>
                    <td><strong>{d.department}</strong></td>
                    <td>{d.allocated}</td>
                    <td>{d.total_assets}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr><td>Total</td><td>{dept.total_allocated}</td><td>{dept.total_assets}</td></tr>
              </tfoot>
            </table>
          )}
        </section>

        {/* Due maintenance */}
        <section className="panel">
          <div className="panel-head">
            <h3>Due / At-Risk Assets {due ? <span className="count-pill warn">{due.total}</span> : null}</h3>
            {due && (
              <ExportButton
                filename="due-maintenance.csv"
                rows={[['Tag', 'Name', 'Condition', 'Status', 'Reasons'],
                  ...due.items.map((a) => [a.asset_tag, a.name, a.condition, a.status, a.reasons.join('; ')])]}
              />
            )}
          </div>
          {!due || due.items.length === 0 ? <EmptyState>Nothing flagged. 🎉</EmptyState> : (
            <table className="table">
              <thead><tr><th>Asset</th><th>Status</th><th>Flags</th></tr></thead>
              <tbody>
                {due.items.map((a) => (
                  <tr key={a.asset_id}>
                    <td><strong>{a.asset_tag}</strong> {a.name}</td>
                    <td><Badge value={a.status} /></td>
                    <td>{a.reasons.map((r) => <span key={r} className="reason-pill">{r}</span>)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      </div>
    </div>
  );
}

function Heatmap({ heat }) {
  const max = Math.max(1, ...heat.matrix.flat());
  return (
    <div className="heatmap-wrap">
      <div className="heatmap" style={{ gridTemplateColumns: `40px repeat(24, 1fr)` }}>
        <div className="hm-corner" />
        {heat.hours.map((h) => (
          <div key={h} className="hm-hour">{h % 3 === 0 ? h : ''}</div>
        ))}
        {heat.matrix.map((row, i) => (
          <Row key={heat.weekdays[i]} label={heat.weekdays[i]} row={row} max={max} />
        ))}
      </div>
      <p className="hint-text">Darker cells = more bookings starting in that hour. Peak: {heat.peak?.count ? `${heat.peak.weekday} at ${heat.peak.hour}:00 (${heat.peak.count})` : 'none yet'}.</p>
    </div>
  );
}

function Row({ label, row, max }) {
  return (
    <>
      <div className="hm-day">{label}</div>
      {row.map((v, h) => (
        <div
          key={h}
          className="hm-cell"
          title={`${label} ${h}:00 — ${v} booking(s)`}
          style={{ background: v ? `rgba(15, 118, 110, ${0.15 + (v / max) * 0.85})` : 'var(--surface-2)' }}
        />
      ))}
    </>
  );
}
