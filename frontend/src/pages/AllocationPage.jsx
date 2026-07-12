import { useEffect, useState } from 'react';
import {
  allocateAsset, approveTransfer, fetchAllocations, fetchAssets, fetchDepartments, fetchEmployees,
  fetchTransfers, rejectTransfer, requestTransfer, returnAllocation,
} from '../services/api';
import { useAuth } from '../context/AuthContext';
import PageHeader from '../components/PageHeader';
import { Badge, Banner, EmptyState, Modal } from '../components/ui';

export default function AllocationPage() {
  const { isManager } = useAuth();
  const [allocations, setAllocations] = useState([]);
  const [transfers, setTransfers] = useState([]);
  const [assets, setAssets] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [allocOpen, setAllocOpen] = useState(false);
  const [returning, setReturning] = useState(null);
  const [transferFor, setTransferFor] = useState(null); // asset needing a transfer request

  const load = () => {
    fetchAllocations('Active').then(setAllocations).catch((e) => setError(e.message));
    fetchTransfers().then(setTransfers).catch(() => {});
  };
  useEffect(() => {
    load();
    fetchAssets().then(setAssets).catch(() => {});
    fetchEmployees().then(setEmployees).catch(() => {});
    fetchDepartments().then(setDepartments).catch(() => {});
  }, []);

  const employeeName = (id) => employees.find((e) => e.id === id)?.full_name || `#${id}`;

  const doReturn = async (notes, condition) => {
    try {
      await returnAllocation(returning.id, { checkin_notes: notes, condition });
      setReturning(null);
      setNotice(`${returning.asset_tag} returned to Available.`);
      load();
    } catch (e) { setError(e.message); }
  };

  return (
    <div className="page">
      <PageHeader
        title="Allocation & Transfer"
        subtitle="Manage who holds what, with conflict-safe allocation and transfer approvals."
        actions={isManager && <button className="btn btn-primary" onClick={() => setAllocOpen(true)}>+ Allocate Asset</button>}
      />
      <Banner kind="error" onClose={() => setError('')}>{error}</Banner>
      <Banner kind="success" onClose={() => setNotice('')}>{notice}</Banner>

      <section className="panel">
        <div className="panel-head"><h3>Active Allocations</h3><span className="count-pill info">{allocations.length}</span></div>
        {allocations.length === 0 ? <EmptyState>Nothing allocated right now.</EmptyState> : (
          <table className="table">
            <thead><tr><th>Asset</th><th>Holder</th><th>Since</th><th>Expected return</th><th></th></tr></thead>
            <tbody>
              {allocations.map((a) => (
                <tr key={a.id} className={a.overdue ? 'row-danger' : ''}>
                  <td><strong>{a.asset_tag}</strong> {a.asset_name}</td>
                  <td>{a.holder || '—'}{a.department_id ? <span className="tag-mini">dept</span> : null}</td>
                  <td>{a.allocated_date ? new Date(a.allocated_date).toLocaleDateString() : '—'}</td>
                  <td>{a.expected_return_date || '—'} {a.overdue && <Badge value="Overdue" />}</td>
                  <td>{isManager && <button className="btn btn-outline btn-sm" onClick={() => setReturning(a)}>Return</button>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="panel">
        <div className="panel-head"><h3>Transfer Requests</h3><span className="count-pill warn">{transfers.filter((t) => t.status === 'Requested').length}</span></div>
        {transfers.length === 0 ? <EmptyState>No transfer requests.</EmptyState> : (
          <table className="table">
            <thead><tr><th>Asset</th><th>From</th><th>To</th><th>Reason</th><th>Status</th><th></th></tr></thead>
            <tbody>
              {transfers.map((t) => (
                <tr key={t.id}>
                  <td><strong>{t.asset_tag}</strong></td>
                  <td>{t.from_employee_name || '—'}</td>
                  <td>{t.to_employee_name}</td>
                  <td>{t.reason || '—'}</td>
                  <td><Badge value={t.status} /></td>
                  <td>
                    {isManager && t.status === 'Requested' && (
                      <div className="row-actions">
                        <button className="btn btn-primary btn-sm" onClick={async () => {
                          try { await approveTransfer(t.id); load(); } catch (e) { setError(e.message); }
                        }}>Approve</button>
                        <button className="btn btn-ghost btn-sm" onClick={async () => {
                          try { await rejectTransfer(t.id); load(); } catch (e) { setError(e.message); }
                        }}>Reject</button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {allocOpen && (
        <AllocateModal
          assets={assets.filter((a) => a.status === 'Available')}
          employees={employees}
          departments={departments}
          onClose={() => setAllocOpen(false)}
          onDone={() => { setAllocOpen(false); load(); fetchAssets().then(setAssets); }}
          onConflict={(assetId) => { setAllocOpen(false); setTransferFor(assets.find((a) => a.id === assetId)); }}
          onError={setError}
        />
      )}

      {returning && (
        <ReturnModal alloc={returning} onClose={() => setReturning(null)} onSubmit={doReturn} />
      )}

      {transferFor && (
        <TransferModal asset={transferFor} employees={employees}
          onClose={() => setTransferFor(null)}
          onDone={() => { setTransferFor(null); setNotice('Transfer request submitted.'); load(); }}
          onError={setError} />
      )}
    </div>
  );
}

function AllocateModal({ assets, employees, departments, onClose, onDone, onConflict, onError }) {
  const [form, setForm] = useState({ asset_id: '', target_type: 'employee', employee_id: '', department_id: '', expected_return_date: '' });

  const save = async (e) => {
    e.preventDefault();
    const toEmployee = form.target_type === 'employee';
    try {
      await allocateAsset({
        asset_id: Number(form.asset_id),
        employee_id: toEmployee ? Number(form.employee_id) : null,
        department_id: toEmployee ? null : Number(form.department_id),
        expected_return_date: form.expected_return_date || null,
      });
      onDone();
    } catch (err) {
      // 409 conflict -> route the user to a transfer request instead.
      if (/currently held/i.test(err.message)) {
        onError(err.message);
        onConflict(Number(form.asset_id));
      } else {
        onError(err.message);
      }
    }
  };

  return (
    <Modal title="Allocate Asset" onClose={onClose}
      footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" form="alloc-form" type="submit">Allocate</button></>}>
      <form id="alloc-form" className="form-grid" onSubmit={save}>
        <label className="field"><span>Asset (Available only)</span>
          <select required value={form.asset_id} onChange={(e) => setForm({ ...form, asset_id: e.target.value })}>
            <option value="">— select —</option>
            {assets.map((a) => <option key={a.id} value={a.id}>{a.asset_tag} · {a.name}</option>)}
          </select></label>
        <label className="field"><span>Allocate to</span>
          <select value={form.target_type} onChange={(e) => setForm({ ...form, target_type: e.target.value, employee_id: '', department_id: '' })}>
            <option value="employee">An Employee</option>
            <option value="department">A Department</option>
          </select></label>
        {form.target_type === 'employee' ? (
          <label className="field"><span>Assign to Employee</span>
            <select required value={form.employee_id} onChange={(e) => setForm({ ...form, employee_id: e.target.value })}>
              <option value="">— select —</option>
              {employees.map((emp) => <option key={emp.id} value={emp.id}>{emp.full_name}</option>)}
            </select></label>
        ) : (
          <label className="field"><span>Assign to Department</span>
            <select required value={form.department_id} onChange={(e) => setForm({ ...form, department_id: e.target.value })}>
              <option value="">— select —</option>
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select></label>
        )}
        <label className="field"><span>Expected Return Date (optional)</span>
          <input type="date" value={form.expected_return_date} onChange={(e) => setForm({ ...form, expected_return_date: e.target.value })} /></label>
      </form>
    </Modal>
  );
}

function ReturnModal({ alloc, onClose, onSubmit }) {
  const [notes, setNotes] = useState('');
  const [condition, setCondition] = useState('Good');
  return (
    <Modal title={`Return ${alloc.asset_tag}`} onClose={onClose}
      footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" onClick={() => onSubmit(notes, condition)}>Confirm Return</button></>}>
      <div className="form-grid">
        <label className="field"><span>Condition on check-in</span>
          <select value={condition} onChange={(e) => setCondition(e.target.value)}>
            <option>Good</option><option>Fair</option><option>Poor</option>
          </select></label>
        <label className="field"><span>Check-in notes</span>
          <textarea rows="3" value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Any damage or remarks…" /></label>
      </div>
    </Modal>
  );
}

function TransferModal({ asset, employees, onClose, onDone, onError }) {
  const [form, setForm] = useState({ to_employee_id: '', reason: '' });
  const save = async (e) => {
    e.preventDefault();
    try {
      await requestTransfer({ asset_id: asset.id, to_employee_id: Number(form.to_employee_id), reason: form.reason || null });
      onDone();
    } catch (err) { onError(err.message); }
  };
  return (
    <Modal title={`Request Transfer — ${asset.asset_tag}`} onClose={onClose}
      footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" form="tr-form" type="submit">Submit Request</button></>}>
      <p className="hint-text">{asset.name} is currently held by <strong>{asset.held_by || 'another user'}</strong>. Request a transfer to reassign it.</p>
      <form id="tr-form" className="form-grid" onSubmit={save}>
        <label className="field"><span>Transfer to</span>
          <select required value={form.to_employee_id} onChange={(e) => setForm({ ...form, to_employee_id: e.target.value })}>
            <option value="">— select —</option>
            {employees.map((emp) => <option key={emp.id} value={emp.id}>{emp.full_name}</option>)}
          </select></label>
        <label className="field"><span>Reason</span>
          <input value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} /></label>
      </form>
    </Modal>
  );
}
