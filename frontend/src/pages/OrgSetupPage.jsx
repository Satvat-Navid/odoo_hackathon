import { useEffect, useState } from 'react';
import {
  createCategory, createDepartment, createEmployee, deleteCategory, deleteDepartment,
  deleteEmployee, fetchCategories, fetchDepartments, fetchEmployees, updateEmployee,
} from '../services/api';
import { useAuth } from '../context/AuthContext';
import { ROLES } from '../context/AuthContext';
import PageHeader from '../components/PageHeader';
import { Badge, Banner, EmptyState, Modal, RoleBadge } from '../components/ui';

const TABS = [
  { key: 'departments', label: 'Departments' },
  { key: 'categories', label: 'Asset Categories' },
  { key: 'employees', label: 'Employee Directory' },
];

export default function OrgSetupPage() {
  const [tab, setTab] = useState('departments');
  const [error, setError] = useState('');

  return (
    <div className="page">
      <PageHeader title="Organization Setup" subtitle="Master data everything else depends on. Admin only." />
      <Banner kind="error" onClose={() => setError('')}>{error}</Banner>

      <div className="tabs">
        {TABS.map((t) => (
          <button key={t.key} className={`tab ${tab === t.key ? 'active' : ''}`} onClick={() => setTab(t.key)}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'departments' && <DepartmentsTab onError={setError} />}
      {tab === 'categories' && <CategoriesTab onError={setError} />}
      {tab === 'employees' && <EmployeesTab onError={setError} />}
    </div>
  );
}

function DepartmentsTab({ onError }) {
  const [rows, setRows] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: '', head_id: '', parent_id: '', status: 'Active' });
  const [employees, setEmployees] = useState([]);

  const load = () => fetchDepartments().then(setRows).catch((e) => onError(e.message));
  useEffect(() => {
    load();
    fetchEmployees().then(setEmployees).catch(() => {});
  }, []);

  const remove = async (dep) => {
    if (!window.confirm(`Delete department "${dep.name}"?`)) return;
    try { await deleteDepartment(dep.id); load(); } catch (err) { onError(err.message); }
  };

  const save = async (e) => {
    e.preventDefault();
    try {
      await createDepartment({
        name: form.name,
        head_id: form.head_id ? Number(form.head_id) : null,
        parent_id: form.parent_id ? Number(form.parent_id) : null,
        status: form.status,
      });
      setOpen(false);
      setForm({ name: '', head_id: '', parent_id: '', status: 'Active' });
      load();
    } catch (err) {
      onError(err.message);
    }
  };

  return (
    <section className="panel">
      <div className="panel-head">
        <h3>Departments</h3>
        <button className="btn btn-primary" onClick={() => setOpen(true)}>+ New Department</button>
      </div>
      {rows.length === 0 ? <EmptyState>No departments yet.</EmptyState> : (
        <table className="table">
          <thead><tr><th>Name</th><th>Head</th><th>Parent</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {rows.map((d) => (
              <tr key={d.id}>
                <td><strong>{d.name}</strong></td>
                <td>{d.head_name || '—'}</td>
                <td>{rows.find((p) => p.id === d.parent_id)?.name || '—'}</td>
                <td><Badge value={d.status} /></td>
                <td className="cell-actions"><button className="btn btn-danger btn-sm" onClick={() => remove(d)}>Delete</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {open && (
        <Modal title="New Department" onClose={() => setOpen(false)}
          footer={<><button className="btn btn-ghost" onClick={() => setOpen(false)}>Cancel</button>
            <button className="btn btn-primary" form="dep-form" type="submit">Create</button></>}>
          <form id="dep-form" className="form-grid" onSubmit={save}>
            <label className="field"><span>Name</span>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
            <label className="field"><span>Department Head</span>
              <select value={form.head_id} onChange={(e) => setForm({ ...form, head_id: e.target.value })}>
                <option value="">— none —</option>
                {employees.map((emp) => <option key={emp.id} value={emp.id}>{emp.full_name}</option>)}
              </select></label>
            <label className="field"><span>Parent Department</span>
              <select value={form.parent_id} onChange={(e) => setForm({ ...form, parent_id: e.target.value })}>
                <option value="">— none —</option>
                {rows.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select></label>
            <label className="field"><span>Status</span>
              <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                <option>Active</option><option>Inactive</option>
              </select></label>
          </form>
        </Modal>
      )}
    </section>
  );
}

function CategoriesTab({ onError }) {
  const [rows, setRows] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: '', description: '', warranty_months: '' });

  const load = () => fetchCategories().then(setRows).catch((e) => onError(e.message));
  useEffect(() => { load(); }, []);

  const remove = async (cat) => {
    if (!window.confirm(`Delete category "${cat.name}"?`)) return;
    try { await deleteCategory(cat.id); load(); } catch (err) { onError(err.message); }
  };

  const save = async (e) => {
    e.preventDefault();
    try {
      await createCategory({
        name: form.name,
        description: form.description || null,
        warranty_months: form.warranty_months ? Number(form.warranty_months) : null,
      });
      setOpen(false);
      setForm({ name: '', description: '', warranty_months: '' });
      load();
    } catch (err) { onError(err.message); }
  };

  return (
    <section className="panel">
      <div className="panel-head">
        <h3>Asset Categories</h3>
        <button className="btn btn-primary" onClick={() => setOpen(true)}>+ New Category</button>
      </div>
      {rows.length === 0 ? <EmptyState>No categories yet.</EmptyState> : (
        <table className="table">
          <thead><tr><th>Name</th><th>Description</th><th>Warranty (months)</th><th></th></tr></thead>
          <tbody>
            {rows.map((c) => (
              <tr key={c.id}><td><strong>{c.name}</strong></td><td>{c.description || '—'}</td>
                <td>{c.warranty_months ?? '—'}</td>
                <td className="cell-actions"><button className="btn btn-danger btn-sm" onClick={() => remove(c)}>Delete</button></td></tr>
            ))}
          </tbody>
        </table>
      )}

      {open && (
        <Modal title="New Category" onClose={() => setOpen(false)}
          footer={<><button className="btn btn-ghost" onClick={() => setOpen(false)}>Cancel</button>
            <button className="btn btn-primary" form="cat-form" type="submit">Create</button></>}>
          <form id="cat-form" className="form-grid" onSubmit={save}>
            <label className="field"><span>Name</span>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
            <label className="field"><span>Description</span>
              <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>
            <label className="field"><span>Warranty period (months, optional)</span>
              <input type="number" min="0" value={form.warranty_months}
                onChange={(e) => setForm({ ...form, warranty_months: e.target.value })} /></label>
          </form>
        </Modal>
      )}
    </section>
  );
}

function EmployeesTab({ onError }) {
  const { user } = useAuth();
  const [rows, setRows] = useState([]);
  const [editing, setEditing] = useState(null);
  const [creating, setCreating] = useState(false);
  const [newEmp, setNewEmp] = useState({ full_name: '', email: '', password: 'password123', role: 'Employee', department_id: '', status: 'Active' });
  const [departments, setDepartments] = useState([]);

  const load = () => fetchEmployees().then(setRows).catch((e) => onError(e.message));
  useEffect(() => {
    load();
    fetchDepartments().then(setDepartments).catch(() => {});
  }, []);

  const save = async (e) => {
    e.preventDefault();
    try {
      await updateEmployee(editing.id, {
        role: editing.role,
        department_id: editing.department_id ? Number(editing.department_id) : null,
        status: editing.status,
      });
      setEditing(null);
      load();
    } catch (err) { onError(err.message); }
  };

  const create = async (e) => {
    e.preventDefault();
    try {
      await createEmployee({
        full_name: newEmp.full_name,
        email: newEmp.email,
        password: newEmp.password || 'password123',
        role: newEmp.role,
        department_id: newEmp.department_id ? Number(newEmp.department_id) : null,
        status: newEmp.status,
      });
      setCreating(false);
      setNewEmp({ full_name: '', email: '', password: 'password123', role: 'Employee', department_id: '', status: 'Active' });
      load();
    } catch (err) { onError(err.message); }
  };

  const remove = async (emp) => {
    if (!window.confirm(`Delete employee "${emp.full_name}"?`)) return;
    try { await deleteEmployee(emp.id); load(); } catch (err) { onError(err.message); }
  };

  return (
    <section className="panel">
      <div className="panel-head">
        <h3>Employee Directory</h3>
        <button className="btn btn-primary" onClick={() => setCreating(true)}>+ New Employee</button>
      </div>
      {rows.length === 0 ? <EmptyState>No employees.</EmptyState> : (
        <table className="table">
          <thead><tr><th>Name</th><th>Email</th><th>Department</th><th>Role</th><th>Status</th><th></th></tr></thead>
          <tbody>
            {rows.map((emp) => (
              <tr key={emp.id}>
                <td><strong>{emp.full_name}</strong></td>
                <td>{emp.email}</td>
                <td>{emp.department_name || '—'}</td>
                <td><RoleBadge role={emp.role} /></td>
                <td><Badge value={emp.status} /></td>
                <td className="cell-actions">
                  <button className="btn btn-outline btn-sm" onClick={() => setEditing({ ...emp })}>Manage</button>
                  {emp.id !== user?.id && <button className="btn btn-danger btn-sm" onClick={() => remove(emp)}>Delete</button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {creating && (
        <Modal title="New Employee" onClose={() => setCreating(false)}
          footer={<><button className="btn btn-ghost" onClick={() => setCreating(false)}>Cancel</button>
            <button className="btn btn-primary" form="new-emp-form" type="submit">Create</button></>}>
          <form id="new-emp-form" className="form-grid" onSubmit={create}>
            <label className="field"><span>Full name</span>
              <input required value={newEmp.full_name} onChange={(e) => setNewEmp({ ...newEmp, full_name: e.target.value })} /></label>
            <label className="field"><span>Email</span>
              <input type="email" required value={newEmp.email} onChange={(e) => setNewEmp({ ...newEmp, email: e.target.value })} /></label>
            <label className="field"><span>Initial password</span>
              <input value={newEmp.password} onChange={(e) => setNewEmp({ ...newEmp, password: e.target.value })} /></label>
            <label className="field"><span>Role</span>
              <select value={newEmp.role} onChange={(e) => setNewEmp({ ...newEmp, role: e.target.value })}>
                {Object.values(ROLES).map((r) => <option key={r}>{r}</option>)}
              </select></label>
            <label className="field"><span>Department</span>
              <select value={newEmp.department_id} onChange={(e) => setNewEmp({ ...newEmp, department_id: e.target.value })}>
                <option value="">— none —</option>
                {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select></label>
            <label className="field"><span>Status</span>
              <select value={newEmp.status} onChange={(e) => setNewEmp({ ...newEmp, status: e.target.value })}>
                <option>Active</option><option>Inactive</option>
              </select></label>
          </form>
        </Modal>
      )}

      {editing && (
        <Modal title={`Manage ${editing.full_name}`} onClose={() => setEditing(null)}
          footer={<><button className="btn btn-ghost" onClick={() => setEditing(null)}>Cancel</button>
            <button className="btn btn-primary" form="emp-form" type="submit">Save</button></>}>
          <form id="emp-form" className="form-grid" onSubmit={save}>
            <label className="field"><span>Role</span>
              <select value={editing.role} onChange={(e) => setEditing({ ...editing, role: e.target.value })}>
                {Object.values(ROLES).map((r) => <option key={r}>{r}</option>)}
              </select></label>
            <label className="field"><span>Department</span>
              <select value={editing.department_id || ''} onChange={(e) => setEditing({ ...editing, department_id: e.target.value })}>
                <option value="">— none —</option>
                {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select></label>
            <label className="field"><span>Status</span>
              <select value={editing.status} onChange={(e) => setEditing({ ...editing, status: e.target.value })}>
                <option>Active</option><option>Inactive</option>
              </select></label>
          </form>
        </Modal>
      )}
    </section>
  );
}
