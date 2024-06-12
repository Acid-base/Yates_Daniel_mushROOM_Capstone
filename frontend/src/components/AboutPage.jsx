// In AboutPage.jsx
import React, { useState } from 'react';

function AboutPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    // Send the form data to your backend endpoint
    try {
      const response = await fetch('/api/contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, email, message }),
      });
      if (response.ok) {
        // Handle successful submission (e.g., display a success message)
      } else {
        // Handle error (e.g., display an error message)
      }
    } catch (error) {
      // Handle network error
    }
  };

  return (
    <div>
      <h1>About Mushroom Explorer</h1>
      {/* ... about content */}
      <h2>Contact Us</h2>
      <form onSubmit={handleSubmit}>
        <label htmlFor="name">Name:</label>
        <input
          type="text"
          id="name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        {/* ... other form fields (email, message) */}
        <button type="submit">Submit</button>
      </form>
    </div>
  );
}
export default AboutPage;