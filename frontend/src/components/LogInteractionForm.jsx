import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  createInteraction,
  updateInteraction,
  setEditingId,
  clearError,
} from '../store/interactionsSlice';
import { apiClient } from '../api/client';
import TagInput from './TagInput';

const INTERACTION_TYPES = ['Meeting', 'Call', 'Email', 'Conference', 'Other'];
const SENTIMENTS = ['Positive', 'Neutral', 'Negative'];

const emptyForm = {
  hcp_name: '',
  interaction_type: 'Meeting',
  interaction_date: new Date().toISOString().slice(0, 10),
  interaction_time: '',
  attendees: [],
  topics_discussed: '',
  materials_shared: [],
  samples_distributed: [],
  sentiment: 'Neutral',
  outcomes: '',
  follow_up_actions: '',
};

export default function LogInteractionForm() {
  const dispatch = useDispatch();
  const { items, editingId, error } = useSelector((s) => s.interactions);
  const [form, setForm] = useState(emptyForm);
  const [fieldErrors, setFieldErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [suggestions, setSuggestions] = useState(null);
  const [suggestLoading, setSuggestLoading] = useState(false);

  const editingInteraction = editingId ? items.find((i) => i.id === editingId) : null;

  useEffect(() => {
    if (editingInteraction) {
      setForm({
        hcp_name: editingInteraction.hcp_name || '',
        interaction_type: editingInteraction.interaction_type || 'Meeting',
        interaction_date: editingInteraction.interaction_date || emptyForm.interaction_date,
        interaction_time: editingInteraction.interaction_time || '',
        attendees: editingInteraction.attendees || [],
        topics_discussed: editingInteraction.topics_discussed || '',
        materials_shared: editingInteraction.materials_shared || [],
        samples_distributed: editingInteraction.samples_distributed || [],
        sentiment: editingInteraction.sentiment || 'Neutral',
        outcomes: editingInteraction.outcomes || '',
        follow_up_actions: editingInteraction.follow_up_actions || '',
      });
      setSuggestions(null);
    } else {
      setForm(emptyForm);
    }
  }, [editingId]); 

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function validate() {
    const errs = {};
    if (!form.hcp_name.trim()) errs.hcp_name = 'HCP name is required.';
    if (!form.interaction_date) errs.interaction_date = 'Date is required.';
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!validate()) return;
    setSaving(true);
    dispatch(clearError());
    try {
      let result;
      if (editingId) {
        result = await dispatch(updateInteraction({ id: editingId, changes: form })).unwrap();
      } else {
        result = await dispatch(createInteraction(form)).unwrap();
      }
      // Pull AI-suggested follow-ups for the saved interaction, mirroring the mockup.
      fetchSuggestions(result.id);
    } catch (err) {
      // error already captured in redux state
    } finally {
      setSaving(false);
    }
  }

  async function fetchSuggestions(interactionId) {
    setSuggestLoading(true);
    setSuggestions(null);
    try {
      const res = await apiClient.post('/api/chat', {
        message: `Suggest follow-up actions for interaction ${interactionId}.`,
        thread_id: 'form-suggestions',
      });
      const toolResult = res.data.tool_calls?.find((tc) => tc.tool === 'suggest_follow_up_actions');
      if (toolResult?.result) {
        const parsed = JSON.parse(toolResult.result);
        setSuggestions(parsed.suggestions || []);
      } else if (res.data.reply) {
        setSuggestions([res.data.reply]);
      }
    } catch (err) {
      setSuggestions(null);
    } finally {
      setSuggestLoading(false);
    }
  }

  function handleCancelEdit() {
    dispatch(setEditingId(null));
    setSuggestions(null);
  }

  return (
    <div className="panel">
      <p className="panel-title">{editingId ? 'Edit interaction' : 'Log HCP Interaction'}</p>
      <p className="panel-subtitle">Interaction details</p>

      {error && <div className="top-banner">{typeof error === 'string' ? error : JSON.stringify(error)}</div>}

      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="form-field">
            <label htmlFor="hcp_name">HCP Name</label>
            <input
              id="hcp_name"
              type="text"
              value={form.hcp_name}
              onChange={(e) => update('hcp_name', e.target.value)}
              placeholder="Search or select HCP…"
            />
            {fieldErrors.hcp_name && <span className="form-error">{fieldErrors.hcp_name}</span>}
          </div>

          <div className="form-field">
            <label htmlFor="interaction_type">Interaction Type</label>
            <select
              id="interaction_type"
              value={form.interaction_type}
              onChange={(e) => update('interaction_type', e.target.value)}
            >
              {INTERACTION_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          <div className="form-field">
            <label htmlFor="interaction_date">Date</label>
            <input
              id="interaction_date"
              type="date"
              value={form.interaction_date}
              onChange={(e) => update('interaction_date', e.target.value)}
            />
            {fieldErrors.interaction_date && (
              <span className="form-error">{fieldErrors.interaction_date}</span>
            )}
          </div>

          <div className="form-field">
            <label htmlFor="interaction_time">Time</label>
            <input
              id="interaction_time"
              type="time"
              value={form.interaction_time}
              onChange={(e) => update('interaction_time', e.target.value)}
            />
          </div>

          <TagInput
            label="Attendees"
            values={form.attendees}
            onChange={(v) => update('attendees', v)}
            placeholder="Enter names or search, press Enter to add…"
          />

          <div className="form-field full">
            <label htmlFor="topics_discussed">Topics Discussed</label>
            <textarea
              id="topics_discussed"
              value={form.topics_discussed}
              onChange={(e) => update('topics_discussed', e.target.value)}
              placeholder="Enter key discussion points…"
            />
          </div>

          <TagInput
            label="Materials Shared"
            values={form.materials_shared}
            onChange={(v) => update('materials_shared', v)}
            placeholder="e.g. Product brochure, press Enter to add…"
          />

          <TagInput
            label="Samples Distributed"
            values={form.samples_distributed}
            onChange={(v) => update('samples_distributed', v)}
            placeholder="e.g. OncoBoost 50mg x2, press Enter to add…"
          />

          <div className="form-field full">
            <label>Observed/Inferred HCP Sentiment</label>
            <div className="sentiment-group">
              {SENTIMENTS.map((s) => (
                <button
                  type="button"
                  key={s}
                  className={`sentiment-chip ${form.sentiment === s ? `selected ${s.toLowerCase()}` : ''}`}
                  onClick={() => update('sentiment', s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="form-field full">
            <label htmlFor="outcomes">Outcomes</label>
            <textarea
              id="outcomes"
              value={form.outcomes}
              onChange={(e) => update('outcomes', e.target.value)}
              placeholder="Key outcomes or agreements…"
            />
          </div>

          <div className="form-field full">
            <label htmlFor="follow_up_actions">Follow-up Actions</label>
            <textarea
              id="follow_up_actions"
              value={form.follow_up_actions}
              onChange={(e) => update('follow_up_actions', e.target.value)}
              placeholder="Enter next steps or tasks…"
            />
          </div>
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? 'Saving…' : editingId ? 'Save changes' : 'Log interaction'}
          </button>
          {editingId && (
            <button type="button" className="btn btn-ghost" onClick={handleCancelEdit}>
              Cancel
            </button>
          )}
        </div>
      </form>

      {(suggestLoading || suggestions) && (
        <div className="followups-box">
          <h4>AI Suggested Follow-ups</h4>
          {suggestLoading ? (
            <p style={{ fontSize: 13, color: 'var(--ink-faint)' }}>Thinking…</p>
          ) : (
            <ul>
              {suggestions.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
