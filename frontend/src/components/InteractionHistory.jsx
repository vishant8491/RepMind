import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchInteractions, deleteInteraction, setEditingId } from '../store/interactionsSlice';

export default function InteractionHistory() {
  const dispatch = useDispatch();
  const { items, status } = useSelector((s) => s.interactions);
  const [search, setSearch] = useState('');
  const [pendingDelete, setPendingDelete] = useState(null);

  useEffect(() => {
    dispatch(fetchInteractions());
  }, [dispatch]);

  function handleSearch(e) {
    e.preventDefault();
    dispatch(fetchInteractions(search));
  }

  async function confirmDelete() {
    if (pendingDelete == null) return;
    await dispatch(deleteInteraction(pendingDelete));
    setPendingDelete(null);
  }

  return (
    <div className="panel history-panel">
      <p className="panel-title">Interaction history</p>
      <p className="panel-subtitle">All logged interactions, newest first</p>

      <form onSubmit={handleSearch} style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
        <input
          type="text"
          placeholder="Search by HCP name…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            flex: 1,
            border: '1px solid var(--line)',
            borderRadius: 8,
            padding: '9px 11px',
          }}
        />
        <button type="submit" className="btn btn-ghost">
          Search
        </button>
        {search && (
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => {
              setSearch('');
              dispatch(fetchInteractions());
            }}
          >
            Clear
          </button>
        )}
      </form>

      {status === 'loading' && <p className="empty-state">Loading…</p>}

      {status !== 'loading' && items.length === 0 && (
        <p className="empty-state">No interactions logged yet — use the form or chat above.</p>
      )}

      {items.length > 0 && (
        <table className="history-table">
          <thead>
            <tr>
              <th>HCP</th>
              <th>Type</th>
              <th>Date</th>
              <th>Sentiment</th>
              <th>Topics</th>
              <th>Source</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id}>
                <td>{item.hcp_name}</td>
                <td>{item.interaction_type}</td>
                <td>{item.interaction_date}</td>
                <td>
                  <span className={`sentiment-badge ${item.sentiment.toLowerCase()}`}>{item.sentiment}</span>
                </td>
                <td style={{ maxWidth: 260 }}>{item.topics_discussed}</td>
                <td>
                  <span className="source-tag">{item.source}</span>
                </td>
                <td>
                  <div className="row-actions">
                    <button
                      type="button"
                      className="btn-danger-text"
                      style={{ color: 'var(--teal-dark)' }}
                      onClick={() => dispatch(setEditingId(item.id))}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="btn-danger-text"
                      onClick={() => setPendingDelete(item.id)}
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {pendingDelete != null && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(16,24,40,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 50,
          }}
          onClick={() => setPendingDelete(null)}
        >
          <div
            className="panel"
            style={{ maxWidth: 360, width: '90%' }}
            onClick={(e) => e.stopPropagation()}
          >
            <p className="panel-title">Delete this interaction?</p>
            <p style={{ fontSize: 13, color: 'var(--ink-soft)' }}>
              This can't be undone.
            </p>
            <div className="form-actions">
              <button className="btn btn-ghost" onClick={() => setPendingDelete(null)}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                style={{ background: 'var(--rose)' }}
                onClick={confirmDelete}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
