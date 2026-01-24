/**
 * Main Application Component
 * Simplified composition of Header, VideoInput, and TranscriptSection
 */

import React from 'react';
import Header from './components/Header';
import VideoInput from './components/VideoInput';
import TranscriptSection from './components/TranscriptSection';
import ProcessingOverlay from './components/ProcessingOverlay/ProcessingOverlay';
import { useAppContext } from './context/AppContext';

function App() {
  // Use context directly here (AppContext provider wraps App in main.jsx)
  // Wait... AppProvider wraps <App /> in main.jsx, so we can use the hook here.
  // Actually, main.jsx structure is: <AppProvider><App /></AppProvider>
  // So yes, we can use the hook.

  // NOTE: If App.jsx was the provider itself, we couldn't use the hook here.
  // I verified main.jsx earlier, it wraps App.

  // Let's safe check imports.
  // We need to wrap App content to use hook safely or move Overlay inside a child?
  // main.jsx:
  // ReactDOM...render(
  //   <AppProvider>
  //     <App />
  //   </AppProvider>
  // )
  // So yes, App is a child of AppProvider.

  const { isLoading } = useAppContext();

  return (
    <div className="container">
      <ProcessingOverlay isVisible={isLoading} />
      <Header />
      <VideoInput />
      <TranscriptSection />
    </div>
  );
}

export default App;
