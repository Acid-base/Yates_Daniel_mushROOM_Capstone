// src/main.jsx
import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter as Router } from 'react-router-dom';
import App from './App';
import { MushroomProvider } from './components/MushroomContext';

const container = document.getElementById('root');
const root = createRoot(container);
root.render(
  <MushroomProvider>
    <Router>
      <App />
    </Router>
  </MushroomProvider>
);
