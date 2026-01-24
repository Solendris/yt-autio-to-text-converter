/**
 * Application Entry Point
 * Wraps App with AppProvider for global state management
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';
import { AppProvider } from './context/AppContext.jsx';
import './index.css';

console.log('%c Frontend Version: 2.1 (Fix Applied) ', 'background: #222; color: #bada55; font-size: 20px');

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AppProvider>
      <App />
    </AppProvider>
  </React.StrictMode>
);
