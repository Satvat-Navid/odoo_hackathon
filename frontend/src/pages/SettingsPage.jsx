import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { fetchMe, updateMe } from '../services/api';
import PageHeader from '../components/PageHeader';
import { Banner } from '../components/ui';

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const [profile, setProfile] = useState(null);
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    fetchMe()
      .then((data) => {
        setProfile(data);
        setFullName(data.full_name);
      })
      .catch((err) => setError(err.message));
  }, []);

  const save = async (e) => {
    e.preventDefault();
    try {
      const updated = await updateMe({ full_name: fullName });
      setProfile(updated);
      setNotice('Personal settings updated.');
      setError('');
      if (refreshUser) refreshUser();
    } catch (err) {
      setError(err.message);
    }
  };

  if (!profile) {
    return <div className="page"><PageHeader title="Settings" subtitle="Manage your personal profile." /><p>Loading…</p></div>;
  }

  return (
    <div className="page">
      <PageHeader title="Settings" subtitle="Manage your personal profile." />
      <Banner kind="error" onClose={() => setError('')}>{error}</Banner>
      <Banner kind="success" onClose={() => setNotice('')}>{notice}</Banner>

      <section className="panel">
        <div className="panel-head"><h3>Personal information</h3></div>
        <form className="form-grid" onSubmit={save}>
          <label className="field"><span>Full name</span>
            <input required value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </label>
          <label className="field"><span>Email</span>
            <input disabled value={profile.email} />
          </label>
          <label className="field"><span>Role</span>
            <input disabled value={profile.role} />
          </label>
          <label className="field"><span>Department</span>
            <input disabled value={profile.department_name || '—'} />
          </label>
          <div className="form-actions">
            <button className="btn btn-primary" type="submit">Save changes</button>
          </div>
        </form>
      </section>
    </div>
  );
}
