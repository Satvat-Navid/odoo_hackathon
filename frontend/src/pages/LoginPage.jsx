import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { forgotPassword, register as apiRegister, resetPassword } from '../services/api';
import { Banner } from '../components/ui';

export default function LoginPage() {
  const [mode, setMode] = useState('login'); // 'login' | 'signup' | 'forgot' | 'reset'
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState('');
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
      } else if (mode === 'forgot') {
        const res = await forgotPassword(email);
        // Demo-safe: the reset token is returned directly (would be emailed in prod).
        if (res.reset_token) {
          setToken(res.reset_token);
          setNotice('Reset token generated below — enter a new password to continue.');
          setMode('reset');
        } else {
          setNotice(res.message);
        }
      } else if (mode === 'reset') {
        await resetPassword(token, password);
        setNotice('Password reset. You can sign in with your new password.');
        setPassword('');
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

  const heading = {
    login: 'Welcome back', signup: 'Create your account',
    forgot: 'Reset your password', reset: 'Set a new password',
  }[mode];

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
          <h2>{heading}</h2>
          <p className="muted">
            {mode === 'login' && 'Sign in to your workspace'}
            {mode === 'signup' && 'Sign up creates an Employee account. Roles are assigned by an Admin.'}
            {mode === 'forgot' && 'Enter your email to generate a reset token.'}
            {mode === 'reset' && 'Enter the reset token and choose a new password.'}
          </p>

          <Banner kind="error" onClose={() => setError('')}>{error}</Banner>
          <Banner kind="success" onClose={() => setNotice('')}>{notice}</Banner>

          {mode === 'signup' && (
            <label className="field">
              <span>Full name</span>
              <input value={fullName} onChange={(e) => setFullName(e.target.value)} required placeholder="Jane Doe" />
            </label>
          )}

          {mode !== 'reset' && (
            <label className="field">
              <span>Email</span>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@company.com" />
            </label>
          )}

          {mode === 'reset' && (
            <label className="field">
              <span>Reset token</span>
              <input value={token} onChange={(e) => setToken(e.target.value)} required placeholder="paste your reset token" />
            </label>
          )}

          {mode !== 'forgot' && (
            <label className="field">
              <span>{mode === 'reset' ? 'New password' : 'Password'}</span>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="••••••••" />
            </label>
          )}

          {mode === 'login' && (
            <button type="button" className="link auth-forgot" onClick={() => { setMode('forgot'); setError(''); setNotice(''); }}>
              Forgot password?
            </button>
          )}

          <button className="btn btn-primary btn-block" type="submit" disabled={busy}>
            {busy ? 'Please wait…' : (
              { login: 'Sign in', signup: 'Create account', forgot: 'Send reset token', reset: 'Reset password' }[mode]
            )}
          </button>

          {(mode === 'forgot' || mode === 'reset') ? (
            <p className="auth-switch">
              <button type="button" className="link" onClick={() => { setMode('login'); setError(''); setNotice(''); }}>
                ← Back to sign in
              </button>
            </p>
          ) : (
            <p className="auth-switch">
              {mode === 'login' ? "Don't have an account?" : 'Already registered?'}{' '}
              <button type="button" className="link" onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}>
                {mode === 'login' ? 'Sign up' : 'Sign in'}
              </button>
            </p>
          )}

          <div className="demo-box">
            <span className="demo-title">Demo accounts</span>
            <div className="demo-actions">
              <button type="button" className="chip" onClick={() => useDemo('admin@assetflow.com')}>Admin</button>
              <button type="button" className="chip" onClick={() => useDemo('priya@assetflow.com')}>Asset Manager</button>
              <button type="button" className="chip" onClick={() => useDemo('raj@assetflow.com')}>Dept Head</button>
              <button type="button" className="chip" onClick={() => useDemo('meera@assetflow.com')}>Employee</button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
