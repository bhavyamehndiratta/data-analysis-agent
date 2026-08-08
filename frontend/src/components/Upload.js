import React, { useState, useCallback } from 'react';
import axios from 'axios';
import { Upload as UploadIcon, FileText, AlertCircle } from 'lucide-react';

export default function Upload({ onSessionCreated }) {
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = React.useRef();

  const handleFile = async (file) => {
    if (!file) return;
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post('http://localhost:8000/api/upload', formData);
      onSessionCreated(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed.');
    } finally {
      setLoading(false);
    }
  };

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current.click()}
        style={{
          border: `2px dashed ${dragging ? '#6366f1' : '#374151'}`,
          borderRadius: '12px',
          padding: '48px 64px',
          cursor: 'pointer',
          textAlign: 'center',
          background: dragging ? '#1e1b4b20' : '#111827',
          transition: 'all 0.2s',
          width: '100%',
          maxWidth: '480px'
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          style={{ display: 'none' }}
          onChange={(e) => handleFile(e.target.files[0])}
        />
        <UploadIcon size={36} color={dragging ? '#6366f1' : '#6b7280'} style={{ margin: '0 auto 16px' }} />
        {loading ? (
          <p style={{ color: '#9ca3af' }}>Uploading and analysing dataset...</p>
        ) : (
          <>
            <p style={{ fontWeight: 500, marginBottom: '8px' }}>Drop your CSV or Excel file here</p>
            <p style={{ color: '#6b7280', fontSize: '14px' }}>or click to browse</p>
          </>
        )}
      </div>
      {error && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '16px', color: '#f87171' }}>
          <AlertCircle size={16} />
          <span style={{ fontSize: '14px' }}>{error}</span>
        </div>
      )}
    </div>
  );
}