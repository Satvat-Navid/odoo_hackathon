import { useEffect, useState } from 'react';
import { fetchActivityLogs, fetchEmployees } from '../services/api';
import PageHeader from '../components/PageHeader';
import { Badge, Banner, EmptyState } from '../components/ui';

const ENTITY_TYPES = ['asset', 'booking', 'employee'];

export default function ActivityPage() {
  const [logs, setLogs] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [filters, setFilters] = useState({ entity_type: '', actor_id: '' });
  const [error, setError] = useState('');

  const load = () =>
    fetchActivityLogs(filters).then(setLogs).catch((e) => setError(e.message));

  useEffect(() => { load(); }, [filters]);
  useEffect(() => { fetchEmployees().then(setEmployees).catch(() => {}); }, []);

  const fmt = (t) => (t ? new Date(t).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : '—');

  return (
    <div className="page">
      <PageHeader
        title="Activity Log"
        subtitle="A chronological trail of who did what across the workspace."
      />
      <Banner kind="error" onClose={() => setError('')}>{error}</Banner>

      <div className="toolbar">
        <select value={filters.entity_type} onChange={(e) => setFilters({ ...filters, entity_type: e.target.value })}>
          <option value="">All entities</option>
          {ENTITY_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select value={filters.actor_id} onChange={(e) => setFilters({ ...filters, actor_id: e.target.value })}>
          <option value="">All actors</option>
          {employees.map((emp) => <option key={emp.id} value={emp.id}>{emp.full_name}</option>)}
        </select>
      </div>

      <section className="panel">
        <div className="panel-head"><h3>Recent Activity</h3><span className="count-pill info">{logs.length}</span></div>
        {logs.length === 0 ? <EmptyState>No activity matches your filters.</EmptyState> : (
          <table className="table">
            <thead>
              <tr><th>When</th><th>Actor</th><th>Action</th><th>Summary</th><th>Entity</th></tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id}>
                  <td>{fmt(l.created_at)}</td>
                  <td>{l.actor_name}</td>
                  <td><code className="action-code">{l.action}</code></td>
                  <td>{l.summary}</td>
                  <td>{l.entity_type ? <Badge value={l.entity_type} /> : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
