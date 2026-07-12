import { useEffect, useState } from 'react';
import {
  assignAuditors, closeAuditCycle, createAuditCycle, fetchAuditCycle, fetchAuditCycles,
  fetchAuditDiscrepancies, fetchDepartments, fetchEmployees, updateAuditItem,
} from '../services/api';
import { useAuth } from '../context/AuthContext';
import PageHeader from '../components/PageHeader';
import { Badge, Banner, EmptyState, KpiCard, Modal } from '../components/ui';

const RESULTS = ['Verified', 'Missing', 'Damaged'];

export default function AuditPage() {
  const { isAdmin } = useAuth();
  const [cycles, setCycles] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [createOpen, setCreateOpen] = useState(false);

  const loadCycles = () => fetchAuditCycles().then(setCycles).catch((e) => setError(e.message));
  useEffect(() => { loadCycles(); }, []);

  if (selectedId) {
    return (
      <CycleDetail
        cycleId={selectedId}
        onBack={() => { setSelectedId(null); loadCycles(); }}
        onError={setError}
        onNotice={setNotice}
        error={error}
        notice={notice}
      />
    );
  }

  return (
    <div className="page">
      <PageHeader
        title="Asset Audit"
        subtitle="Run physical verification cycles and reconcile discrepancies."
        actions={isAdmin && <button className="btn btn-primary" onClick={() => setCreateOpen(true)}>+ New Cycle</button>}
      />
      <Banner kind="error" onClose={() => setError('')}>{error}</Banner>
      <Banner kind="success" onClose={() => setNotice('')}>{notice}</Banner>

      <section className="panel">
        <div className="panel-head"><h3>Audit Cycles</h3><span className="count-pill info">{cycles.length}</span></div>
        {cycles.length === 0 ? <EmptyState>No audit cycles yet.</EmptyState> : (
          <table className="table">
            <thead>
              <tr><th>Name</th><th>Scope</th><th>Dates</th><th>Progress</th><th>Status</th><th></th></tr>
            </thead>
            <tbody>
              {cycles.map((c) => (
                <tr key={c.id}>
                  <td><strong>{c.name}</strong></td>
                  <td>{c.scope_type}{c.scope_value ? ` · ${c.scope_value}` : ''}</td>
                  <td>{c.start_date || '—'} → {c.end_date || '—'}</td>
                  <td>{c.verified}/{c.total_items} verified ({c.progress_pct}%)</td>
                  <td><Badge value={c.status} /></td>
                  <td className="cell-actions">
                    <button className="btn btn-outline btn-sm" onClick={() => { setSelectedId(c.id); setError(''); setNotice(''); }}>Open</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {createOpen && (
        <CreateCycleModal
          onClose={() => setCreateOpen(false)}
          onDone={() => { setCreateOpen(false); setNotice('Audit cycle created with items generated.'); loadCycles(); }}
          onError={setError} />
      )}
    </div>
  );
}

function CycleDetail({ cycleId, onBack, onError, onNotice, error, notice }) {
  const { isAdmin } = useAuth();
  const [cycle, setCycle] = useState(null);
  const [discrepancies, setDiscrepancies] = useState(null);
  const [assignOpen, setAssignOpen] = useState(false);
  const [marking, setMarking] = useState(null); // { item, result }

  const load = () => {
    fetchAuditCycle(cycleId).then(setCycle).catch((e) => onError(e.message));
    fetchAuditDiscrepancies(cycleId).then(setDiscrepancies).catch(() => {});
  };
  useEffect(() => { load(); }, [cycleId]);

  if (!cycle) return <div className="page"><EmptyState>Loading cycle…</EmptyState></div>;

  const closed = cycle.status === 'Closed';

  const doClose = async () => {
    if (!window.confirm(`Close "${cycle.name}"? Missing assets become Lost, Damaged become Poor condition, and items lock.`)) return;
    try {
      await closeAuditCycle(cycleId);
      onNotice('Cycle closed and asset statuses reconciled.');
      load();
    } catch (e) { onError(e.message); }
  };

  return (
    <div className="page">
      <PageHeader
        title={cycle.name}
        subtitle={`${cycle.scope_type}${cycle.scope_value ? ` · ${cycle.scope_value}` : ''} · ${cycle.start_date || '—'} → ${cycle.end_date || '—'}`}
        actions={
          <div className="page-actions">
            <button className="btn btn-ghost" onClick={onBack}>← Back</button>
            {isAdmin && !closed && <button className="btn btn-outline" onClick={() => setAssignOpen(true)}>Assign Auditors</button>}
            {isAdmin && !closed && <button className="btn btn-danger" onClick={doClose}>Close Cycle</button>}
          </div>
        }
      />
      <Banner kind="error" onClose={() => onError('')}>{error}</Banner>
      <Banner kind="success" onClose={() => onNotice('')}>{notice}</Banner>

      <section className="kpi-grid">
        <KpiCard label="Progress" value={`${cycle.progress_pct}%`} tone="info" hint={`${cycle.verified}/${cycle.total_items} checked`} />
        <KpiCard label="Verified" value={cycle.verified} tone="ok" />
        <KpiCard label="Missing" value={cycle.missing} tone="danger" />
        <KpiCard label="Damaged" value={cycle.damaged} tone="warn" />
      </section>

      <section className="panel">
        <div className="panel-head">
          <h3>Auditors</h3>
          <Badge value={cycle.status} />
        </div>
        <div className="chip-row">
          {(!cycle.auditors || cycle.auditors.length === 0)
            ? <EmptyState>No auditors assigned yet.</EmptyState>
            : cycle.auditors.map((a) => <div key={a.id} className="stat-chip"><strong>{a.name}</strong></div>)}
        </div>
      </section>

      {discrepancies && discrepancies.total > 0 && (
        <section className="panel">
          <div className="panel-head">
            <h3>Discrepancy Report</h3>
            <span className="count-pill danger">{discrepancies.total}</span>
          </div>
          <div className="chip-row">
            <div className="stat-chip"><Badge value="Missing" /><strong>{discrepancies.missing_count}</strong></div>
            <div className="stat-chip"><Badge value="Damaged" /><strong>{discrepancies.damaged_count}</strong></div>
          </div>
          <table className="table">
            <thead><tr><th>Asset</th><th>Result</th><th>Notes</th><th>Checked by</th></tr></thead>
            <tbody>
              {discrepancies.items.map((i) => (
                <tr key={i.id}>
                  <td><strong>{i.asset_tag}</strong> {i.asset_name}</td>
                  <td><Badge value={i.result} /></td>
                  <td>{i.notes || '—'}</td>
                  <td>{i.checked_by || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <section className="panel">
        <div className="panel-head"><h3>Audit Items</h3><span className="count-pill info">{cycle.items.length}</span></div>
        {cycle.items.length === 0 ? <EmptyState>No items in scope.</EmptyState> : (
          <table className="table">
            <thead>
              <tr><th>Asset</th><th>Result</th><th>Notes</th><th>Checked by</th><th></th></tr>
            </thead>
            <tbody>
              {cycle.items.map((i) => (
                <tr key={i.id}>
                  <td><strong>{i.asset_tag}</strong> {i.asset_name}</td>
                  <td><Badge value={i.result} /></td>
                  <td>{i.notes || '—'}</td>
                  <td>{i.checked_by || '—'}</td>
                  <td className="cell-actions">
                    {closed ? <span className="muted">locked</span> : RESULTS.map((r) => (
                      <button key={r} className={`btn btn-sm ${i.result === r ? 'btn-primary' : 'btn-outline'}`}
                        onClick={() => setMarking({ item: i, result: r })}>{r}</button>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {assignOpen && (
        <AssignAuditorsModal cycle={cycle}
          onClose={() => setAssignOpen(false)}
          onDone={() => { setAssignOpen(false); onNotice('Auditors updated.'); load(); }}
          onError={onError} />
      )}

      {marking && (
        <MarkItemModal marking={marking}
          onClose={() => setMarking(null)}
          onSubmit={async (notes) => {
            try {
              await updateAuditItem(marking.item.id, { result: marking.result, notes: notes || null });
              setMarking(null);
              load();
            } catch (e) { onError(e.message); setMarking(null); }
          }} />
      )}
    </div>
  );
}

function CreateCycleModal({ onClose, onDone, onError }) {
  const [departments, setDepartments] = useState([]);
  const [form, setForm] = useState({ name: '', scope_type: 'All', scope_value: '', start_date: '', end_date: '' });

  useEffect(() => { fetchDepartments().then(setDepartments).catch(() => {}); }, []);

  const save = async (e) => {
    e.preventDefault();
    try {
      await createAuditCycle({
        name: form.name,
        scope_type: form.scope_type,
        scope_value: form.scope_type === 'All' ? null : form.scope_value,
        start_date: form.start_date || null,
        end_date: form.end_date || null,
      });
      onDone();
    } catch (err) { onError(err.message); }
  };

  return (
    <Modal title="New Audit Cycle" onClose={onClose}
      footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" form="ac-form" type="submit">Create</button></>}>
      <form id="ac-form" className="form-grid two-col" onSubmit={save}>
        <label className="field"><span>Name</span>
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
        <label className="field"><span>Scope</span>
          <select value={form.scope_type} onChange={(e) => setForm({ ...form, scope_type: e.target.value, scope_value: '' })}>
            <option>All</option><option>Department</option><option>Location</option>
          </select></label>
        {form.scope_type === 'Department' && (
          <label className="field"><span>Department</span>
            <select required value={form.scope_value} onChange={(e) => setForm({ ...form, scope_value: e.target.value })}>
              <option value="">— select —</option>
              {departments.map((d) => <option key={d.id} value={d.name}>{d.name}</option>)}
            </select></label>
        )}
        {form.scope_type === 'Location' && (
          <label className="field"><span>Location (exact match)</span>
            <input required value={form.scope_value} onChange={(e) => setForm({ ...form, scope_value: e.target.value })} placeholder="e.g. HQ - Floor 3" /></label>
        )}
        <label className="field"><span>Start date</span>
          <input type="date" value={form.start_date} onChange={(e) => setForm({ ...form, start_date: e.target.value })} /></label>
        <label className="field"><span>End date</span>
          <input type="date" value={form.end_date} onChange={(e) => setForm({ ...form, end_date: e.target.value })} /></label>
      </form>
      <p className="hint-text">Audit items are auto-generated for every asset matching the scope.</p>
    </Modal>
  );
}

function AssignAuditorsModal({ cycle, onClose, onDone, onError }) {
  const [employees, setEmployees] = useState([]);
  const assigned = new Set((cycle.auditors || []).map((a) => a.id));
  const [selected, setSelected] = useState(new Set());

  useEffect(() => { fetchEmployees().then(setEmployees).catch(() => {}); }, []);

  const toggle = (id) => {
    const next = new Set(selected);
    next.has(id) ? next.delete(id) : next.add(id);
    setSelected(next);
  };

  const save = async () => {
    if (selected.size === 0) { onClose(); return; }
    try {
      await assignAuditors(cycle.id, [...selected]);
      onDone();
    } catch (err) { onError(err.message); }
  };

  return (
    <Modal title="Assign Auditors" onClose={onClose}
      footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" onClick={save}>Assign</button></>}>
      <p className="hint-text">Select employees to add as auditors for this cycle.</p>
      <div className="form-grid">
        {employees.map((e) => (
          <label key={e.id} className="field checkbox">
            <input type="checkbox" disabled={assigned.has(e.id)} checked={assigned.has(e.id) || selected.has(e.id)} onChange={() => toggle(e.id)} />
            <span>{e.full_name} — {e.role}{assigned.has(e.id) ? ' (assigned)' : ''}</span>
          </label>
        ))}
      </div>
    </Modal>
  );
}

function MarkItemModal({ marking, onClose, onSubmit }) {
  const [notes, setNotes] = useState(marking.item.notes || '');
  return (
    <Modal title={`Mark ${marking.item.asset_tag} — ${marking.result}`} onClose={onClose}
      footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" onClick={() => onSubmit(notes)}>Confirm {marking.result}</button></>}>
      <div className="form-grid">
        <label className="field"><span>Notes (optional)</span>
          <textarea rows="3" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Condition, location remarks…" /></label>
      </div>
    </Modal>
  );
}
