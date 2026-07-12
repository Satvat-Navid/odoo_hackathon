import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { register as apiRegister } from '../services/api';
import { Banner } from '../components/ui';

export default function LoginPage() {
  const [mode, setMode] = useState('login'); // 'login' | 'signup'
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    setNotice('');
    setBusy(true);
    try {
      if (mode === 'signup') {
        await apiRegister(fullName, email, password);
        setNotice('Account created as an Employee. You can sign in now.');
        setMode('login');
      } else {
        await login(email, password);
        navigate('/dashboard', { replace: true });
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const useDemo = (demoEmail) => {
    setEmail(demoEmail);
    setPassword(demoEmail.startsWith('admin') ? 'admin123' : 'password123');
    setMode('login');
  };

  return (
    <div className="auth-shell">
      <div className="auth-hero">
        <span className="brand-mark lg">AF</span>
        <h1>AssetFlow</h1>
        <p>Enterprise Asset &amp; Resource Management</p>
        <ul className="auth-points">
          <li>Track assets through their full lifecycle</li>
          <li>Allocate &amp; transfer with conflict handling</li>
          <li>Book shared resources without overlaps</li>
          <li>Role-based access — Admin, Managers, Employees</li>
        </ul>
      </div>

      <div className="auth-panel">
        <form className="auth-card" onSubmit={submit}>
          <h2>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h2>
          <p className="muted">
            {mode === 'login'
              ? 'Sign in to your workspace'
              : 'Sign up creates an Employee account. Roles are assigned by an Admin.'}
          </p>

          <Banner kind="error" onClose={() => setError('')}>{error}</Banner>
          <Banner kind="success" onClose={() => setNotice('')}>{notice}</Banner>

          {mode === 'signup' && (
            <label className="field">
              <span>Full name</span>
              <input value={fullName} onChange={(e) => setFullName(e.target.value)} required placeholder="Jane Doe" />
            </label>
          )}

          <label className="field">
            <span>Email</span>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@company.com" />
          </label>

          <label className="field">
            <span>Password</span>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="••••••••" />
          </label>

          <button className="btn btn-primary btn-block" type="submit" disabled={busy}>
            {busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
          </button>

          <p className="auth-switch">
            {mode === 'login' ? "Don't have an account?" : 'Already registered?'}{' '}
            <button type="button" className="link" onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}>
              {mode === 'login' ? 'Sign up' : 'Sign in'}
            </button>
          </p>

          <div className="demo-box">
            <span className="demo-title">Demo accounts</span>
            <div className="demo-actions">
              <button type="button" className="chip" onClick={() => useDemo('admin@assetflow.com')}>Admin</button>
              <button type="button" className="chip" onClick={() => useDemo('priya@assetflow.com')}>Asset Manager</button>
              <button type="button" className="chip" onClick={() => useDemo('meera@assetflow.com')}>Employee</button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
