import { useEffect, useState } from 'react';
import {
  deleteAsset, fetchAssetHistory, fetchAssets, fetchCategories, fetchDepartments, registerAsset,
} from '../services/api';
import { useAuth } from '../context/AuthContext';
import PageHeader from '../components/PageHeader';
import { Badge, Banner, EmptyState, Modal } from '../components/ui';

const LIFECYCLE = ['Available', 'Allocated', 'Reserved', 'Under Maintenance', 'Lost', 'Retired', 'Disposed'];

export default function AssetsPage() {
  const { isManager } = useAuth();
  const [assets, setAssets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [filters, setFilters] = useState({ search: '', status: '', category_id: '' });
  const [error, setError] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [history, setHistory] = useState(null);

  const load = () => fetchAssets(filters).then(setAssets).catch((e) => setError(e.message));
  useEffect(() => { load(); }, [filters]);
  useEffect(() => {
    fetchCategories().then(setCategories).catch(() => {});
    fetchDepartments().then(setDepartments).catch(() => {});
  }, []);

  const openHistory = async (asset) => {
    try {
      const rows = await fetchAssetHistory(asset.id);
      setHistory({ asset, rows });
    } catch (e) { setError(e.message); }
  };

  const remove = async (asset) => {
    if (!window.confirm(`Delete asset ${asset.asset_tag} (${asset.name})? This removes its history too.`)) return;
    try { await deleteAsset(asset.id); load(); } catch (e) { setError(e.message); }
  };

  return (
    <div className="page">
      <PageHeader
        title="Asset Directory"
        subtitle="Register assets and track them across their lifecycle."
        actions={isManager && <button className="btn btn-primary" onClick={() => setShowForm(true)}>+ Register Asset</button>}
      />
      <Banner kind="error" onClose={() => setError('')}>{error}</Banner>

      <div className="toolbar">
        <input className="search" placeholder="Search tag, name, serial, location…"
          value={filters.search} onChange={(e) => setFilters({ ...filters, search: e.target.value })} />
        <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
          <option value="">All statuses</option>
          {LIFECYCLE.map((s) => <option key={s}>{s}</option>)}
        </select>
        <select value={filters.category_id} onChange={(e) => setFilters({ ...filters, category_id: e.target.value })}>
          <option value="">All categories</option>
          {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </div>

      <section className="panel">
        {assets.length === 0 ? <EmptyState>No assets match your filters.</EmptyState> : (
          <table className="table">
            <thead>
              <tr><th>Tag</th><th>Name</th><th>Category</th><th>Location</th><th>Condition</th><th>Held by</th><th>Status</th><th></th></tr>
            </thead>
            <tbody>
              {assets.map((a) => (
                <tr key={a.id}>
                  <td><strong>{a.asset_tag}</strong></td>
                  <td>{a.name}{a.shared_flag ? <span className="tag-mini">shared</span> : null}</td>
                  <td>{a.category_name || '—'}</td>
                  <td>{a.location || '—'}</td>
                  <td><Badge value={a.condition} /></td>
                  <td>{a.held_by || '—'}</td>
                  <td><Badge value={a.status} /></td>
                  <td className="cell-actions">
                    <button className="btn btn-outline btn-sm" onClick={() => openHistory(a)}>History</button>
                    {isManager && <button className="btn btn-danger btn-sm" onClick={() => remove(a)}>Delete</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {showForm && (
        <RegisterModal categories={categories} departments={departments}
          onClose={() => setShowForm(false)}
          onSaved={() => { setShowForm(false); load(); }}
          onError={setError} />
      )}

      {history && (
        <Modal title={`History — ${history.asset.asset_tag} ${history.asset.name}`} onClose={() => setHistory(null)}>
          {history.rows.length === 0 ? <EmptyState>No allocation history yet.</EmptyState> : (
            <table className="table">
              <thead><tr><th>Holder</th><th>Allocated</th><th>Expected return</th><th>Returned</th><th>Status</th></tr></thead>
              <tbody>
                {history.rows.map((h) => (
                  <tr key={h.id}>
                    <td>{h.employee_name}</td>
                    <td>{h.allocated_date ? new Date(h.allocated_date).toLocaleDateString() : '—'}</td>
                    <td>{h.expected_return_date || '—'}</td>
                    <td>{h.returned_date ? new Date(h.returned_date).toLocaleDateString() : '—'}</td>
                    <td><Badge value={h.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Modal>
      )}
    </div>
  );
}

function RegisterModal({ categories, departments, onClose, onSaved, onError }) {
  const [form, setForm] = useState({
    name: '', category_id: '', department_id: '', serial_number: '', acquisition_date: '',
    acquisition_cost: '', condition: 'Good', location: '', shared_flag: false,
  });

  const save = async (e) => {
    e.preventDefault();
    try {
      await registerAsset({
        name: form.name,
        category_id: form.category_id ? Number(form.category_id) : null,
        department_id: form.department_id ? Number(form.department_id) : null,
        serial_number: form.serial_number || null,
        acquisition_date: form.acquisition_date || null,
        acquisition_cost: form.acquisition_cost ? Number(form.acquisition_cost) : null,
        condition: form.condition,
        location: form.location || null,
        shared_flag: form.shared_flag,
      });
      onSaved();
    } catch (err) { onError(err.message); }
  };

  return (
    <Modal title="Register Asset" onClose={onClose}
      footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" form="asset-form" type="submit">Register</button></>}>
      <form id="asset-form" className="form-grid two-col" onSubmit={save}>
        <label className="field"><span>Name</span>
          <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
        <label className="field"><span>Category</span>
          <select value={form.category_id} onChange={(e) => setForm({ ...form, category_id: e.target.value })}>
            <option value="">— none —</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select></label>
        <label className="field"><span>Department</span>
          <select value={form.department_id} onChange={(e) => setForm({ ...form, department_id: e.target.value })}>
            <option value="">— none —</option>
            {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select></label>
        <label className="field"><span>Serial Number</span>
          <input value={form.serial_number} onChange={(e) => setForm({ ...form, serial_number: e.target.value })} /></label>
        <label className="field"><span>Acquisition Date</span>
          <input type="date" value={form.acquisition_date} onChange={(e) => setForm({ ...form, acquisition_date: e.target.value })} /></label>
        <label className="field"><span>Acquisition Cost</span>
          <input type="number" min="0" value={form.acquisition_cost} onChange={(e) => setForm({ ...form, acquisition_cost: e.target.value })} /></label>
        <label className="field"><span>Condition</span>
          <select value={form.condition} onChange={(e) => setForm({ ...form, condition: e.target.value })}>
            <option>Good</option><option>Fair</option><option>Poor</option>
          </select></label>
        <label className="field"><span>Location</span>
          <input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} /></label>
        <label className="field checkbox">
          <input type="checkbox" checked={form.shared_flag} onChange={(e) => setForm({ ...form, shared_flag: e.target.checked })} />
          <span>Shared / bookable resource</span>
        </label>
      </form>
      <p className="hint-text">Asset Tag is auto-generated (e.g. AF-0007).</p>
    </Modal>
  );
}
