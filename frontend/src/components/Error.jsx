// src/components/Error.jsx - A simple component to display errors
// eslint-disable-next-line no-unused-vars
import React from 'react';
import PropTypes from 'prop-types'; // Import PropTypes

const Error = ({ message }) => (
  <div className="error-message">
    <p>{message}</p>
  </div>
);

// Add prop validation
Error.propTypes = {
  message: PropTypes.string.isRequired 
};

export default Error;
