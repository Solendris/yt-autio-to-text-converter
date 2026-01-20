/**
 * Main Application Component
 * Simplified composition of Header, VideoInput, and TranscriptSection
 */

import React from 'react';
import Header from './components/Header';
import VideoInput from './components/VideoInput';
import TranscriptSection from './components/TranscriptSection';

function App() {
  return (
    <div className="container">
      <Header />
      <VideoInput />
      <TranscriptSection />
    </div>
  );
}

export default App;
