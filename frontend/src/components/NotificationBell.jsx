import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  fetchNotifications, fetchUnreadCount, markAllNotificationsRead, markNotificationRead,
} from '../services/api';

const POLL_MS = 30000;

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);
  const [unread, setUnread] = useState(0);
  const ref = useRef(null);
  const navigate = useNavigate();

  const loadCount = () => fetchUnreadCount().then((d) => setUnread(d.unread)).catch(() => {});
  const loadList = () => fetchNotifications().then(setItems).catch(() => {});

  useEffect(() => {
    loadCount();
    const t = setInterval(loadCount, POLL_MS);
    return () => clearInterval(t);
  }, []);

  // Close on outside click.
  useEffect(() => {
    const onClick = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  const toggle = () => {
    const next = !open;
    setOpen(next);
    if (next) loadList();
  };

  const onItem = async (n) => {
    if (!n.is_read) {
      try { await markNotificationRead(n.id); } catch { /* noop */ }
      setUnread((u) => Math.max(0, u - 1));
      setItems((list) => list.map((x) => (x.id === n.id ? { ...x, is_read: true } : x)));
    }
    if (n.link) { setOpen(false); navigate(n.link); }
  };

  const markAll = async () => {
    try { await markAllNotificationsRead(); } catch { /* noop */ }
    setUnread(0);
    setItems((list) => list.map((x) => ({ ...x, is_read: true })));
  };

  const fmt = (t) => (t ? new Date(t).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) : '');

  return (
    <div className="notif" ref={ref}>
      <button className="notif-bell" onClick={toggle} aria-label="Notifications">
        <span className="notif-icon">🔔</span>
        {unread > 0 && <span className="notif-badge">{unread > 9 ? '9+' : unread}</span>}
      </button>

      {open && (
        <div className="notif-panel">
          <header className="notif-head">
            <strong>Notifications</strong>
            {items.some((n) => !n.is_read) && (
              <button className="link" onClick={markAll}>Mark all read</button>
            )}
          </header>
          <div className="notif-list">
            {items.length === 0 ? (
              <div className="notif-empty">You're all caught up. 🎉</div>
            ) : (
              items.map((n) => (
                <button key={n.id} className={`notif-item ${n.is_read ? '' : 'unread'}`} onClick={() => onItem(n)}>
                  <span className="notif-msg">{n.message}</span>
                  <span className="notif-time">{fmt(n.created_at)}</span>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
