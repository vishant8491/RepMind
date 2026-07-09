import { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { sendChatMessage } from '../store/chatSlice';
import { fetchInteractions } from '../store/interactionsSlice';

const TOOL_LABELS = {
  log_interaction: 'Logged interaction',
  edit_interaction: 'Edited interaction',
  search_interactions: 'Searched interactions',
  summarize_hcp_history: 'Summarized history',
  suggest_follow_up_actions: 'Suggested follow-ups',
};

export default function ChatPanel() {
  const dispatch = useDispatch();
  const { messages, sending } = useSelector((s) => s.chat);
  const [draft, setDraft] = useState('');
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, sending]);

  async function handleSend() {
    const text = draft.trim();
    if (!text || sending) return;
    setDraft('');
    const result = await dispatch(sendChatMessage(text));
  
    const toolCalls = result.payload?.tool_calls || [];
    if (toolCalls.some((tc) => ['log_interaction', 'edit_interaction'].includes(tc.tool))) {
      dispatch(fetchInteractions());
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="panel chat-panel">
      <p className="panel-title">AI Assistant</p>
      <p className="panel-subtitle">Log interaction via chat</p>

      <div className="chat-messages" ref={scrollRef}>
        {messages.map((msg, i) => (
          <div key={i}>
            <div className={`chat-bubble ${msg.role} ${msg.isError ? 'error' : ''}`}>{msg.content}</div>
            {msg.toolCalls?.length > 0 && (
              <div>
                {msg.toolCalls.map((tc, j) => (
                  <span className="tool-call-badge" key={j} title={JSON.stringify(tc.args)}>
                    ⚙ {TOOL_LABELS[tc.tool] || tc.tool}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        {sending && <div className="chat-bubble assistant">Thinking…</div>}
      </div>

      <div className="chat-input-row">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe interaction…"
          disabled={sending}
        />
        <button className="btn btn-primary" onClick={handleSend} disabled={sending || !draft.trim()}>
          Log
        </button>
      </div>
    </div>
  );
}
