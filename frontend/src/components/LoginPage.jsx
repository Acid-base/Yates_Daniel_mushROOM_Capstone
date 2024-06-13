// src/components/LoginPage.jsx
import React, { useState } from 'react';
import axios from 'axios'; 

const LoginPage = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState(null); // State for error messages

  const handleSubmit = async (event) => {
    event.preventDefault();
    setErrorMessage(null); // Clear any previous error messages

    try {
      const response = await axios.post('/api/login', { 
        email: email, 
        password: password 
      });

      const token = response.data.token;
      localStorage.setItem('token', token); 
      onLogin(); 
    } catch (error) {
      console.error('Login error:', error);
      // Set error message based on the response from the server
      if (error.response) {
        setErrorMessage(error.response.data.message || 'Invalid credentials'); 
      } else {
        setErrorMessage('An error occurred. Please try again later.');
      }
    }
  };

  return (
    <div>
      <h1>Login</h1>
      {errorMessage && <div className="error-message">{errorMessage}</div>} {/* Display error message */}
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="email">Email:</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required 
          />
        </div>
        <div>
          <label htmlFor="password">Password:</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button type="submit">Login</button>
      </form>
    </div>
  );
};

export default LoginPage;
