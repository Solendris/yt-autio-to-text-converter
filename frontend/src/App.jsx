import React, { useState, useCallback } from 'react';
import Header from './components/Header';
import VideoInput from './components/VideoInput';
import TranscriptSection from './components/TranscriptSection';
import SummarizeSection from './components/SummarizeSection';
import HybridSection from './components/HybridSection';

import { api } from './services/api';

function App() {
  const [videoUrl, setVideoUrl] = useState('');
  const [videoId, setVideoId] = useState(null);

  React.useEffect(() => {
    // Check backend health on load to verify connection
    api.checkHealth().catch(err => {
      console.warn('[App] Initial health check failed:', err);
    });
  }, []);

  const handleUrlChange = useCallback((url, id) => {
    setVideoUrl(url);
    setVideoId(id);
  }, []);

  return (
    <div className="container">
      <Header />

      <VideoInput onUrlChange={handleUrlChange} />

      <div className="sections">
        <TranscriptSection videoUrl={videoUrl} />
        <SummarizeSection videoUrl={videoUrl} />
      </div>

      <HybridSection videoUrl={videoUrl} />
    </div>
  );
}

export default App;
