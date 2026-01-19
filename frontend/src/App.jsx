import React, { useState, useCallback } from 'react';
import Header from './components/Header';
import VideoInput from './components/VideoInput';
import TranscriptSection from './components/TranscriptSection';

import { api } from './services/api';

function App() {
  const [videoUrl, setVideoUrl] = useState('');
  const [videoId, setVideoId] = useState(null);
  const [videoDuration, setVideoDuration] = useState(null);

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

  const handleDurationChange = useCallback((duration) => {
    setVideoDuration(duration);
  }, []);

  return (
    <div className="container">
      <Header />

      <VideoInput onUrlChange={handleUrlChange} onDurationChange={handleDurationChange} />

      <TranscriptSection videoUrl={videoUrl} videoDuration={videoDuration} />
    </div>
  );
}

export default App;
