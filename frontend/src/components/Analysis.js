import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { Send, RotateCcw, ChevronDown, ChevronRight, FileText, Code } from 'lucide-react';

function DataQuality({ session }) {
  const issues = [];
  if (Object.keys(session.missing_values).length > 0) {
    issues.push(`Missing values in: ${Object.keys(session.missing_values).join(', ')}`);
  }
  if (session.duplicate_rows > 0) {
    issues.push(`${session.duplicate_rows} duplicate row(s) detected`);
  }

  return (
    <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '10px', padding: '16px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
        <FileText size={16} color='#6366f1' />
        <span style={{ fontWeight: 500, fontSize: '14px' }}>{session.filename}</span>
        <span style={{ color: '#6b7280', fontSize: '13px' }}>— {session.rows} rows × {session.columns} columns</span>
      </div>
      <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        {session.column_names.map(col => (
          <span key={col} style={{ background: '#1f2937', borderRadius: '4px', padding: '2px 8px', fontSize: '12px', color: '#9ca3af' }}>{col}</span>
        ))}
      </div>
      {issues.length > 0 && (
        <div style={{ marginTop: '12px', padding: '10px', background: '#1c1917', borderRadius: '6px', borderLeft: '3px solid #f59e0b' }}>
          {issues.map((issue, i) => (
            <p key={i} style={{ fontSize: '13px', color: '#fbbf24' }}>⚠ {issue}</p>
          ))}
        </div>
      )}
    </div>
  );
}

function DrillDown({ items }) {
  const [open, setOpen] = useState(false);
  if (!items || items.length === 0) return null;

  return (
    <div style={{ marginTop: '12px' }}>
      <button
        onClick={() => setOpen(!open)}
        style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'none', border: 'none', color: '#6366f1', cursor: 'pointer', fontSize: '13px' }}
      >
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        {items.length} follow-up investigation{items.length > 1 ? 's' : ''}
      </button>
      {open && (
        <div style={{ marginTop: '8px', paddingLeft: '16px', borderLeft: '2px solid #1f2937' }}>
          {items.map((item, i) => (
            <div key={i} style={{ marginBottom: '12px' }}>
              <p style={{ fontSize: '13px', color: '#6b7280', marginBottom: '4px' }}>↳ {item.question}</p>
              <p style={{ fontSize: '14px', color: '#d1d5db' }}>{item.answer}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Message({ msg }) {
  const [codeOpen, setCodeOpen] = useState(false);

  if (msg.role === 'user') {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
        <div style={{ background: '#6366f1', borderRadius: '10px 10px 2px 10px', padding: '10px 14px', maxWidth: '70%', fontSize: '14px' }}>
          {msg.content}
        </div>
      </div>
    );
  }

  return (
    <div style={{ marginBottom: '20px' }}>
      <div style={{ background: '#111827', border: '1px solid #1f2937', borderRadius: '10px 10px 10px 2px', padding: '14px 16px', fontSize: '14px', lineHeight: '1.6', color: '#e5e7eb' }}>
        {msg.streaming ? (
          <span>{msg.content}<span style={{ opacity: 0.5 }}>▋</span></span>
        ) : (
          msg.content
        )}
        {msg.code_executed?.length > 0 && !msg.streaming && (
          <div style={{ marginTop: '12px' }}>
            <button
              onClick={() => setCodeOpen(!codeOpen)}
              style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'none', border: 'none', color: '#6b7280', cursor: 'pointer', fontSize: '12px' }}
            >
              <Code size={12} />
              {codeOpen ? 'Hide' : 'Show'} executed code ({msg.code_executed.length} block{msg.code_executed.length > 1 ? 's' : ''})
            </button>
            {codeOpen && msg.code_executed.map((code, i) => (
              <pre key={i} style={{ marginTop: '8px', background: '#0d1117', border: '1px solid #1f2937', borderRadius: '6px', padding: '12px', fontSize: '12px', color: '#7dd3fc', overflowX: 'auto' }}>
                {code}
              </pre>
            ))}
          </div>
        )}
        {msg.drill_down && <DrillDown items={msg.drill_down} />}
        {msg.iterations > 1 && !msg.streaming && (
          <p style={{ marginTop: '8px', fontSize: '12px', color: '#4b5563' }}>Self-corrected in {msg.iterations} iteration{msg.iterations > 1 ? 's' : ''}</p>
        )}
      </div>
    </div>
  );
}

export default function Analysis({ session, onReset }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendQuestion = async () => {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput('');
    setLoading(true);

    setMessages(prev => [...prev, { role: 'user', content: question }]);
    const streamingId = Date.now();
    setMessages(prev => [...prev, { id: streamingId, role: 'assistant', content: '', streaming: true }]);

    try {
      const response = await fetch('http://localhost:8000/api/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: session.session_id, question })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullText = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n').filter(l => l.startsWith('data: '));
        for (const line of lines) {
          const data = JSON.parse(line.slice(6));
          if (data.type === 'text') {
            fullText += data.content;
            setMessages(prev => prev.map(m => m.id === streamingId ? { ...m, content: fullText } : m));
          }
        }
      }

      // Fetch full result for code + drill-down
      const full = await axios.post('http://localhost:8000/api/analyze', {
        session_id: session.session_id,
        question
      });

      setMessages(prev => prev.map(m => m.id === streamingId ? {
        ...m,
        content: full.data.answer || fullText,
        streaming: false,
        code_executed: full.data.code_executed,
        drill_down: full.data.drill_down,
        iterations: full.data.iterations
      } : m));

    } catch (err) {
      setMessages(prev => prev.map(m => m.id === streamingId ? {
        ...m, content: 'Error: Could not get a response.', streaming: false
      } : m));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <DataQuality session={session} />
        <button
          onClick={onReset}
          style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'none', border: '1px solid #374151', borderRadius: '6px', padding: '6px 12px', color: '#9ca3af', cursor: 'pointer', fontSize: '13px', whiteSpace: 'nowrap', marginLeft: '16px', height: 'fit-content' }}
        >
          <RotateCcw size={13} /> New dataset
        </button>
      </div>

      <div style={{ minHeight: '300px', marginBottom: '16px' }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: '#4b5563', marginTop: '60px' }}>
            <p style={{ fontSize: '15px' }}>Ask anything about your dataset</p>
            <p style={{ fontSize: '13px', marginTop: '6px' }}>e.g. "What is the average salary by city?" or "Are there any outliers?"</p>
          </div>
        )}
        {messages.map((msg, i) => <Message key={i} msg={msg} />)}
        <div ref={bottomRef} />
      </div>

      <div style={{ display: 'flex', gap: '10px', position: 'sticky', bottom: '24px' }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendQuestion()}
          placeholder="Ask a question about your data..."
          disabled={loading}
          style={{
            flex: 1, background: '#111827', border: '1px solid #374151', borderRadius: '8px',
            padding: '12px 16px', color: '#f9fafb', fontSize: '14px', outline: 'none'
          }}
        />
        <button
          onClick={sendQuestion}
          disabled={loading || !input.trim()}
          style={{
            background: loading ? '#4338ca80' : '#6366f1', border: 'none', borderRadius: '8px',
            padding: '12px 16px', cursor: loading ? 'not-allowed' : 'pointer', display: 'flex', alignItems: 'center'
          }}
        >
          <Send size={16} color="white" />
        </button>
      </div>
    </div>
  );
}