import { useState } from 'react';

export default function TagInput({ label, values, onChange, placeholder }) {
  const [draft, setDraft] = useState('');

  function addTag() {
    const trimmed = draft.trim();
    if (trimmed && !values.includes(trimmed)) {
      onChange([...values, trimmed]);
    }
    setDraft('');
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      addTag();
    }
  }

  function removeTag(tag) {
    onChange(values.filter((v) => v !== tag));
  }

  return (
    <div className="form-field full">
      <label>{label}</label>
      <input
        type="text"
        value={draft}
        placeholder={placeholder}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={addTag}
      />
      {values.length > 0 && (
        <div className="tag-input-list">
          {values.map((tag) => (
            <span key={tag} className="tag-pill">
              {tag}
              <button type="button" onClick={() => removeTag(tag)} aria-label={`Remove ${tag}`}>
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
