import React, { useState } from 'react';
import Upload from './components/Upload';
import Analysis from './components/Analysis';

function App() {
  const [session, setSession] = useState(null);

  return (
    <div style={{ minHeight: '100vh', background: '#030712', color: '#f9fafb' }}>
      <header style={{ borderBottom: '1px solid #1f2937', padding: '16px 24px' }}>
        <h1 style={{ fontSize: '18px', fontWeight: 600, letterSpacing: '-0.01em' }}>Data Analysis Agent</h1>
        <p style={{ fontSize: '13px', color: '#6b7280', marginTop: '2px' }}>Upload a dataset and ask questions in plain English</p>
      </header>
      <main style={{ maxWidth: '860px', margin: '0 auto', padding: '32px 24px' }}>
        {!session ? (
          <Upload onSessionCreated={setSession} />
        ) : (
          <Analysis session={session} onReset={() => setSession(null)} />
        )}
      </main>
    </div>
  );
}

export default App;