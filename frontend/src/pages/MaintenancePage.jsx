import { useEffect, useState } from 'react';
import {
  approveMaintenance, assignMaintenance, fetchAssets, fetchMaintenanceRequests,
  raiseMaintenanceRequest, rejectMaintenance, resolveMaintenance, startMaintenance,
} from '../services/api';
import { useAuth } from '../context/AuthContext';
import PageHeader from '../components/PageHeader';
import { Badge, Banner, EmptyState, Modal } from '../components/ui';

const STATUSES = ['Pending', 'Approved', 'Technician Assigned', 'In Progress', 'Resolved', 'Rejected'];

export default function MaintenancePage() {
  const { isManager } = useAuth();
  const [requests, setRequests] = useState([]);
  const [assets, setAssets] = useState([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [raiseOpen, setRaiseOpen] = useState(false);
  const [assigning, setAssigning] = useState(null); // request needing a technician
  const [resolving, setResolving] = useState(null); // request being resolved

  const load = () => fetchMaintenanceRequests(statusFilter).then(setRequests).catch((e) => setError(e.message));
  useEffect(() => { load(); }, [statusFilter]);
  useEffect(() => { fetchAssets().then(setAssets).catch(() => {}); }, []);

  const act = async (fn, okMsg) => {
    try {
      await fn();
      if (okMsg) setNotice(okMsg);
      load();
    } catch (e) { setError(e.message); }
  };

  return (
    <div className="page">
      <PageHeader
        title="Maintenance Management"
        subtitle="Raise repair requests and drive them through approval, assignment and resolution."
        actions={<button className="btn btn-primary" onClick={() => setRaiseOpen(true)}>+ Raise Request</button>}
      />
      <Banner kind="error" onClose={() => setError('')}>{error}</Banner>
      <Banner kind="success" onClose={() => setNotice('')}>{notice}</Banner>

      <div className="toolbar">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s}>{s}</option>)}
        </select>
      </div>

      <section className="panel">
        <div className="panel-head"><h3>Maintenance Requests</h3><span className="count-pill info">{requests.length}</span></div>
        {requests.length === 0 ? <EmptyState>No maintenance requests.</EmptyState> : (
          <table className="table">
            <thead>
              <tr><th>Asset</th><th>Requested by</th><th>Description</th><th>Priority</th><th>Technician</th><th>Status</th><th></th></tr>
            </thead>
            <tbody>
              {requests.map((r) => (
                <tr key={r.id}>
                  <td><strong>{r.asset_tag || '—'}</strong> {r.asset_name || ''}</td>
                  <td>{r.requester_name}</td>
                  <td>{r.description}{r.photo_url ? <a className="tag-mini" href={r.photo_url} target="_blank" rel="noreferrer">photo</a> : null}</td>
                  <td><Badge value={r.priority} /></td>
                  <td>{r.technician || '—'}</td>
                  <td><Badge value={r.status} /></td>
                  <td className="cell-actions">
                    {isManager && r.status === 'Pending' && (
                      <>
                        <button className="btn btn-primary btn-sm" onClick={() => act(() => approveMaintenance(r.id), `${r.asset_tag} is now Under Maintenance.`)}>Approve</button>
                        <button className="btn btn-ghost btn-sm" onClick={() => act(() => rejectMaintenance(r.id))}>Reject</button>
                      </>
                    )}
                    {isManager && r.status === 'Approved' && (
                      <button className="btn btn-outline btn-sm" onClick={() => setAssigning(r)}>Assign Technician</button>
                    )}
                    {isManager && r.status === 'Technician Assigned' && (
                      <button className="btn btn-primary btn-sm" onClick={() => act(() => startMaintenance(r.id))}>Start</button>
                    )}
                    {isManager && r.status === 'In Progress' && (
                      <button className="btn btn-primary btn-sm" onClick={() => setResolving(r)}>Resolve</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {raiseOpen && (
        <RaiseModal assets={assets}
          onClose={() => setRaiseOpen(false)}
          onDone={() => { setRaiseOpen(false); setNotice('Maintenance request submitted.'); load(); }}
          onError={setError} />
      )}

      {assigning && (
        <AssignModal request={assigning}
          onClose={() => setAssigning(null)}
          onSubmit={(technician) => { setAssigning(null); act(() => assignMaintenance(assigning.id, technician), 'Technician assigned.'); }} />
      )}

      {resolving && (
        <ResolveModal request={resolving}
          onClose={() => setResolving(null)}
          onSubmit={(notes) => { setResolving(null); act(() => resolveMaintenance(resolving.id, notes), `${resolving.asset_tag} back to Available.`); }} />
      )}
    </div>
  );
}

function RaiseModal({ assets, onClose, onDone, onError }) {
  const [form, setForm] = useState({ asset_id: '', description: '', priority: 'Medium', photo_url: '' });
  const save = async (e) => {
    e.preventDefault();
    try {
      await raiseMaintenanceRequest({
        asset_id: Number(form.asset_id),
        description: form.description,
        priority: form.priority,
        photo_url: form.photo_url || null,
      });
      onDone();
    } catch (err) { onError(err.message); }
  };
  return (
    <Modal title="Raise Maintenance Request" onClose={onClose}
      footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" form="mr-form" type="submit">Submit</button></>}>
      <form id="mr-form" className="form-grid" onSubmit={save}>
        <label className="field"><span>Asset</span>
          <select required value={form.asset_id} onChange={(e) => setForm({ ...form, asset_id: e.target.value })}>
            <option value="">— select —</option>
            {assets.map((a) => <option key={a.id} value={a.id}>{a.asset_tag} · {a.name}</option>)}
          </select></label>
        <label className="field"><span>Description</span>
          <textarea rows="3" required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="What's wrong with it?" /></label>
        <label className="field"><span>Priority</span>
          <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })}>
            <option>Low</option><option>Medium</option><option>High</option>
          </select></label>
        <label className="field"><span>Photo URL (optional)</span>
          <input value={form.photo_url} onChange={(e) => setForm({ ...form, photo_url: e.target.value })} placeholder="https://…" /></label>
      </form>
    </Modal>
  );
}

function AssignModal({ request, onClose, onSubmit }) {
  const [technician, setTechnician] = useState('');
  return (
    <Modal title={`Assign Technician — ${request.asset_tag}`} onClose={onClose}
      footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" disabled={!technician.trim()} onClick={() => onSubmit(technician.trim())}>Assign</button></>}>
      <div className="form-grid">
        <label className="field"><span>Technician name</span>
          <input required value={technician} onChange={(e) => setTechnician(e.target.value)} placeholder="e.g. Sam the Repair Tech" /></label>
      </div>
    </Modal>
  );
}

function ResolveModal({ request, onClose, onSubmit }) {
  const [notes, setNotes] = useState('');
  return (
    <Modal title={`Resolve — ${request.asset_tag}`} onClose={onClose}
      footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" onClick={() => onSubmit(notes || null)}>Mark Resolved</button></>}>
      <div className="form-grid">
        <label className="field"><span>Resolution notes</span>
          <textarea rows="3" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="What was done to fix it?" /></label>
      </div>
      <p className="hint-text">Resolving returns the asset to <strong>Available</strong>.</p>
    </Modal>
  );
}
