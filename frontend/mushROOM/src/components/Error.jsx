// src/components/Error.jsx - A simple component to display errors

// Import React 
import React from 'react';

// Functional component for Error
function Error({ message }) {
  // Return a div containing the error message
  return (
    <div className="error-message">
      <p>{message}</p>
    </div>
  );
}

// Export the Error component as the default export
export default Error;

