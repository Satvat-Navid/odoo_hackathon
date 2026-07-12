import { useEffect, useMemo, useState } from 'react';
import { cancelBooking, createBooking, fetchAssets, fetchBookings, rescheduleBooking } from '../services/api';
import PageHeader from '../components/PageHeader';
import { Badge, Banner, EmptyState, Modal } from '../components/ui';

export default function BookingPage() {
  const [bookings, setBookings] = useState([]);
  const [resources, setResources] = useState([]);
  const [resourceFilter, setResourceFilter] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [open, setOpen] = useState(false);
  const [rescheduling, setRescheduling] = useState(null);

  const load = () => fetchBookings(resourceFilter).then(setBookings).catch((e) => setError(e.message));
  useEffect(() => { load(); }, [resourceFilter]);
  useEffect(() => {
    // Bookable resources = assets flagged shared/bookable.
    fetchAssets().then((a) => setResources(a.filter((x) => x.shared_flag))).catch(() => {});
  }, []);

  const fmt = (t) => new Date(t).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });

  const grouped = useMemo(() => {
    const map = {};
    for (const b of bookings) (map[b.resource_name] ||= []).push(b);
    return map;
  }, [bookings]);

  return (
    <div className="page">
      <PageHeader
        title="Resource Booking"
        subtitle="Book shared resources by time slot — overlaps are rejected automatically."
        actions={<button className="btn btn-primary" onClick={() => setOpen(true)}>+ New Booking</button>}
      />
      <Banner kind="error" onClose={() => setError('')}>{error}</Banner>
      <Banner kind="success" onClose={() => setNotice('')}>{notice}</Banner>

      <div className="toolbar">
        <select value={resourceFilter} onChange={(e) => setResourceFilter(e.target.value)}>
          <option value="">All resources</option>
          {resources.map((r) => <option key={r.id} value={r.name}>{r.name}</option>)}
        </select>
      </div>

      {Object.keys(grouped).length === 0 ? (
        <section className="panel"><EmptyState>No bookings yet.</EmptyState></section>
      ) : (
        Object.entries(grouped).map(([resource, rows]) => (
          <section className="panel" key={resource}>
            <div className="panel-head"><h3>{resource}</h3><span className="count-pill info">{rows.length}</span></div>
            <div className="timeline">
              {rows.map((b) => (
                <div key={b.id} className={`slot slot-${b.status.toLowerCase()}`}>
                  <div className="slot-time">{fmt(b.start_time)} → {new Date(b.end_time).toLocaleTimeString([], { timeStyle: 'short' })}</div>
                  <div className="slot-meta">
                    <span>{b.purpose || 'Booking'} · {b.booked_by}</span>
                    <Badge value={b.status} />
                  </div>
                  {b.status === 'Upcoming' && (
                    <div className="row-actions">
                      <button className="btn btn-outline btn-sm" onClick={() => setRescheduling(b)}>Reschedule</button>
                      <button className="btn btn-ghost btn-sm" onClick={async () => {
                        try { await cancelBooking(b.id); setNotice('Booking cancelled.'); load(); }
                        catch (e) { setError(e.message); }
                      }}>Cancel</button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>
        ))
      )}

      {open && (
        <BookingModal resources={resources}
          onClose={() => setOpen(false)}
          onDone={() => { setOpen(false); setNotice('Booking confirmed.'); load(); }}
          onError={setError} />
      )}

      {rescheduling && (
        <RescheduleModal booking={rescheduling}
          onClose={() => setRescheduling(null)}
          onDone={() => { setRescheduling(null); setNotice('Booking rescheduled.'); load(); }}
          onError={setError} />
      )}
    </div>
  );
}

function toLocalInput(iso) {
  // Convert an ISO timestamp to a value usable by <input type="datetime-local">.
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function RescheduleModal({ booking, onClose, onDone, onError }) {
  const [form, setForm] = useState({
    start_time: toLocalInput(booking.start_time),
    end_time: toLocalInput(booking.end_time),
  });

  const save = async (e) => {
    e.preventDefault();
    try {
      await rescheduleBooking(booking.id, {
        start_time: new Date(form.start_time).toISOString(),
        end_time: new Date(form.end_time).toISOString(),
      });
      onDone();
    } catch (err) { onError(err.message); }
  };

  return (
    <Modal title={`Reschedule — ${booking.resource_name}`} onClose={onClose}
      footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" form="resched-form" type="submit">Save New Time</button></>}>
      <form id="resched-form" className="form-grid" onSubmit={save}>
        <label className="field"><span>Start</span>
          <input type="datetime-local" required value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} /></label>
        <label className="field"><span>End</span>
          <input type="datetime-local" required value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} /></label>
      </form>
      <p className="hint-text">The same overlap check applies — the slot can't clash with another booking of this resource.</p>
    </Modal>
  );
}

function BookingModal({ resources, onClose, onDone, onError }) {
  const [form, setForm] = useState({ resource_name: '', asset_id: '', start_time: '', end_time: '', purpose: '' });

  const onResource = (name) => {
    const match = resources.find((r) => r.name === name);
    setForm({ ...form, resource_name: name, asset_id: match ? match.id : '' });
  };

  const save = async (e) => {
    e.preventDefault();
    try {
      await createBooking({
        resource_name: form.resource_name,
        asset_id: form.asset_id ? Number(form.asset_id) : null,
        start_time: new Date(form.start_time).toISOString(),
        end_time: new Date(form.end_time).toISOString(),
        purpose: form.purpose || null,
      });
      onDone();
    } catch (err) { onError(err.message); }
  };

  return (
    <Modal title="New Booking" onClose={onClose}
      footer={<><button className="btn btn-ghost" onClick={onClose}>Cancel</button>
        <button className="btn btn-primary" form="book-form" type="submit">Book Slot</button></>}>
      <form id="book-form" className="form-grid" onSubmit={save}>
        <label className="field"><span>Resource</span>
          {resources.length ? (
            <select required value={form.resource_name} onChange={(e) => onResource(e.target.value)}>
              <option value="">— select —</option>
              {resources.map((r) => <option key={r.id} value={r.name}>{r.name}</option>)}
            </select>
          ) : (
            <input required value={form.resource_name} onChange={(e) => setForm({ ...form, resource_name: e.target.value })}
              placeholder="e.g. Meeting Room B2" />
          )}
        </label>
        <label className="field"><span>Start</span>
          <input type="datetime-local" required value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} /></label>
        <label className="field"><span>End</span>
          <input type="datetime-local" required value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} /></label>
        <label className="field"><span>Purpose</span>
          <input value={form.purpose} onChange={(e) => setForm({ ...form, purpose: e.target.value })} placeholder="e.g. Sprint planning" /></label>
      </form>
      <p className="hint-text">Adjacent slots are fine (e.g. 10:00–11:00 right after 9:00–10:00). Overlaps are rejected.</p>
    </Modal>
  );
}
