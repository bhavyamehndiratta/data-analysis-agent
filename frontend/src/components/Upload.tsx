import React, { useState, useCallback, useRef } from 'react';
import axios, { AxiosError } from 'axios';
import { Upload as UploadIcon, AlertCircle } from 'lucide-react';
import type { SessionInfo, ApiErrorBody } from '../types';

interface UploadProps {
  onSessionCreated: (session: SessionInfo) => void;
}

export default function Upload({ onSessionCreated }: UploadProps) {
  const [dragging, setDragging] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(async (file: File | undefined) => {
    if (!file) return;
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post<SessionInfo>('http://localhost:8000/api/upload', formData);
      onSessionCreated(res.data);
    } catch (err) {
      const axiosErr = err as AxiosError<ApiErrorBody>;
      setError(axiosErr.response?.data?.detail || 'Upload failed.');
    } finally {
      setLoading(false);
    }
  }, [onSessionCreated]);

  const onDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    handleFile(file);
  }, [handleFile]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
      <div
        onDragOver={(e: React.DragEvent<HTMLDivElement>) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={(e: React.MouseEvent<HTMLDivElement>) => { e.stopPropagation(); inputRef.current?.click(); }}
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
          onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleFile(e.target.files?.[0])}
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
