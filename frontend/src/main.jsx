// main.jsx - Entry point for the React application
// Import the React library for using JSX.
import React from 'react';
// Import the ReactDOM library to render the React application into the DOM.
import ReactDOM from 'react-dom/client'; 
// Import the main App component from the App.jsx file.
import App from './App.jsx';
// Import the global CSS file.
import './index.css';

// Get the root element from the DOM using its ID 'root'.
// This is where the React application will be mounted.
// Create a root using ReactDOM.createRoot.
const root = ReactDOM.createRoot(document.getElementById('root'));
// Render the App component wrapped in React.StrictMode to enable additional checks and warnings during development.
root.render(
  <React.StrictMode>
    <App /> 
  </React.StrictMode>
);

