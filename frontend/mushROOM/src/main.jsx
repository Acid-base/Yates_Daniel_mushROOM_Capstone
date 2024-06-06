// main.jsx - Entry point for the React application
import React from 'react';
import ReactDOM from 'react-dom/client'; // Fix import path
import App from './App.jsx'; // Import the main App component
import './index.css';

// Render the App component into the 'root' element in your HTML
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App /> 
  </React.StrictMode>,
);
